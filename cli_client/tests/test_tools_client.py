import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock, Mock

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# テスト対象のモジュールをインポート
import tools_client


# get_current_weather関数のテスト
class TestGetCurrentWeather:
    def test_tokyo_weather(self):
        """東京の天気を取得するテスト"""
        result = tools_client.get_current_weather("Tokyo")
        result_json = json.loads(result)
        
        assert result_json["location"] == "Tokyo"
        assert result_json["temperature"] == "10"
        assert result_json["unit"] == "celsius"
    
    def test_san_francisco_weather(self):
        """サンフランシスコの天気を取得するテスト"""
        result = tools_client.get_current_weather("San Francisco")
        result_json = json.loads(result)
        
        assert result_json["location"] == "San Francisco"
        assert result_json["temperature"] == "72"
        assert result_json["unit"] == "fahrenheit"
    
    def test_paris_weather(self):
        """パリの天気を取得するテスト"""
        result = tools_client.get_current_weather("Paris")
        result_json = json.loads(result)
        
        assert result_json["location"] == "Paris"
        assert result_json["temperature"] == "22"
        assert result_json["unit"] == "celsius"
    
    def test_unknown_location(self):
        """未知の場所の天気を取得するテスト"""
        result = tools_client.get_current_weather("Unknown Location")
        result_json = json.loads(result)
        
        assert result_json["location"] == "Unknown Location"
        assert result_json["temperature"] == "undefined"
        assert result_json["unit"] == "fahrenheit"
    
    def test_case_insensitive(self):
        """大文字小文字を区別しないテスト"""
        result = tools_client.get_current_weather("TOKYO")
        result_json = json.loads(result)
        
        assert result_json["location"] == "Tokyo"
        assert result_json["temperature"] == "10"
        assert result_json["unit"] == "celsius"
    
    def test_custom_unit(self):
        """カスタム単位で天気を取得するテスト"""
        result = tools_client.get_current_weather("Unknown Location", unit="celsius")
        result_json = json.loads(result)
        
        assert result_json["location"] == "Unknown Location"
        assert result_json["temperature"] == "undefined"
        assert result_json["unit"] == "celsius"


# get_tools_definition関数のテスト
class TestGetToolsDefinition:
    def test_tools_definition(self):
        """ツール定義が正しいかテスト"""
        tools = tools_client.get_tools_definition()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "get_current_weather"
        assert "parameters" in tools[0]["function"]


# OpenAIクライアントでの関数呼び出しテスト
class TestRunToolCallWithOpenAI:
    @patch('tools_client.openai_client.chat.completions.create')
    def test_run_tool_call_with_openai_without_function_calling(self, mock_create):
        """OpenAIクライアント：関数呼び出しがない場合のレスポンステスト"""
        # モックレスポンスの設定
        mock_message = MagicMock()
        mock_message.content = "東京の天気は晴れです。"
        mock_message.tool_calls = []
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response
        
        # OpenAIクライアントが利用可能なことを保証
        tools_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = tools_client.run_tool_call_with_openai("東京の天気を教えて", "gpt-4")
        
        # 検証
        assert result == "東京の天気は晴れです。"
        mock_create.assert_called_once()
        
        # 送信されたパラメータを検証
        call_args = mock_create.call_args
        kwargs = call_args[1]
        assert kwargs['model'] == "gpt-4"
        assert kwargs['messages'][0]['content'] == "東京の天気を教えて"
        assert 'tools' in kwargs
    
    @patch('tools_client.openai_client.chat.completions.create')
    def test_run_tool_call_with_openai_with_function_calling(self, mock_create):
        """OpenAIクライアント：関数呼び出しがある場合のレスポンステスト"""
        # 1回目のAPIコールのモックレスポンス
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "get_current_weather"
        mock_tool_call.function.arguments = json.dumps({"location": "Tokyo"})
        
        mock_first_message = MagicMock()
        mock_first_message.content = None
        mock_first_message.tool_calls = [mock_tool_call]
        
        mock_first_choice = MagicMock()
        mock_first_choice.message = mock_first_message
        
        mock_first_response = MagicMock()
        mock_first_response.choices = [mock_first_choice]
        
        # 2回目のAPIコールのモックレスポンス
        mock_second_message = MagicMock()
        mock_second_message.content = "東京の気温は10度（摂氏）です。"
        mock_second_message.tool_calls = []
        
        mock_second_choice = MagicMock()
        mock_second_choice.message = mock_second_message
        
        mock_second_response = MagicMock()
        mock_second_response.choices = [mock_second_choice]
        
        # create メソッドが2回呼ばれたとき、異なるレスポンスを返すよう設定
        mock_create.side_effect = [mock_first_response, mock_second_response]
        
        # OpenAIクライアントが利用可能なことを保証
        tools_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = tools_client.run_tool_call_with_openai("東京の天気を教えて", "gpt-4")
        
        # 検証
        assert result == "東京の気温は10度（摂氏）です。"
        assert mock_create.call_count == 2
        
        # 2回目の呼び出しで送信されたメッセージを検証
        second_call_args = mock_create.call_args_list[1]
        second_kwargs = second_call_args[1]
        assert len(second_kwargs['messages']) > 1  # 最初のメッセージ + 関数の結果
        assert second_kwargs['messages'][0]['role'] == "user"
        assert second_kwargs['messages'][0]['content'] == "東京の天気を教えて"
    
    @patch('tools_client.openai_client.chat.completions.create')
    @patch('tools_client.run_tool_call_with_requests')
    def test_run_tool_call_with_openai_error_fallback(self, mock_requests, mock_create):
        """OpenAIクライアントエラー時のフォールバックテスト"""
        # OpenAIクライアントでエラーを発生させる
        mock_create.side_effect = Exception("API Error")
        
        # requestsモードの戻り値をモック
        mock_requests.return_value = "Fallback response"
        
        # OpenAIクライアントが利用可能なことを保証
        tools_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = tools_client.run_tool_call_with_openai("東京の天気を教えて", "gpt-4")
        
        # 検証
        assert result == "Fallback response"
        mock_create.assert_called_once()
        mock_requests.assert_called_once_with("東京の天気を教えて", "gpt-4")


# requestsクライアントでの関数呼び出しテスト
class TestRunToolCallWithRequests:
    @patch('requests.post')
    def test_run_tool_call_with_requests_without_function_calling(self, mock_post):
        """requestsクライアント：関数呼び出しがない場合のレスポンステスト"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "東京の天気は晴れです。",
                        "role": "assistant"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # テスト実行
        result = tools_client.run_tool_call_with_requests("東京の天気を教えて", "gpt-4")
        
        # 検証
        assert result == "東京の天気は晴れです。"
        mock_post.assert_called_once()
        
        # 送信されたペイロードを検証
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['model'] == "gpt-4"
        assert payload['messages'][0]['content'] == "東京の天気を教えて"
        assert 'tools' in payload
    
    @patch('requests.post')
    def test_run_tool_call_with_requests_with_function_calling(self, mock_post):
        """requestsクライアント：関数呼び出しがある場合のレスポンステスト"""
        # 1回目のAPIコールのモックレスポンス
        first_response = MagicMock()
        first_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "function": {
                                    "name": "get_current_weather",
                                    "arguments": json.dumps({
                                        "location": "Tokyo"
                                    })
                                },
                                "type": "function"
                            }
                        ]
                    }
                }
            ]
        }
        
        # 2回目のAPIコールのモックレスポンス
        second_response = MagicMock()
        second_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "東京の気温は10度（摂氏）です。",
                        "role": "assistant"
                    }
                }
            ]
        }
        
        # requestsのpostメソッドが2回呼ばれたとき、異なるレスポンスを返すよう設定
        mock_post.side_effect = [first_response, second_response]
        
        # テスト実行
        result = tools_client.run_tool_call_with_requests("東京の天気を教えて", "gpt-4")
        
        # 検証
        assert result == "東京の気温は10度（摂氏）です。"
        assert mock_post.call_count == 2
        
        # 2回目の呼び出しで送信されたペイロードを検証
        second_call_args = mock_post.call_args_list[1]
        second_payload = second_call_args[1]['json']
        assert len(second_payload['messages']) > 1  # 最初のメッセージ + 関数の結果
        assert second_payload['messages'][0]['role'] == "user"
        assert second_payload['messages'][0]['content'] == "東京の天気を教えて"
    
    @patch('requests.post')
    def test_run_tool_call_with_requests_error(self, mock_post):
        """requestsクライアントエラー処理のテスト"""
        # エラーをシミュレート
        mock_post.side_effect = Exception("API Error")
        
        # テスト実行
        result = tools_client.run_tool_call_with_requests("東京の天気を教えて", "gpt-4")
        
        # 検証
        assert result == ""
        mock_post.assert_called_once()


# 統合インターフェースのテスト
class TestRunToolCall:
    @patch('tools_client.run_tool_call_with_openai')
    @patch('tools_client.run_tool_call_with_requests')
    def test_run_tool_call_openai_mode(self, mock_requests, mock_openai):
        """OpenAIモードの検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        tools_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = tools_client.run_tool_call("東京の天気を教えて", "gpt-4", "openai")
        
        # 検証
        assert result == "OpenAI result"
        mock_openai.assert_called_once_with("東京の天気を教えて", "gpt-4")
        mock_requests.assert_not_called()
    
    @patch('tools_client.run_tool_call_with_openai')
    @patch('tools_client.run_tool_call_with_requests')
    def test_run_tool_call_requests_mode(self, mock_requests, mock_openai):
        """Requestsモードの検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        tools_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = tools_client.run_tool_call("東京の天気を教えて", "gpt-4", "requests")
        
        # 検証
        assert result == "Requests result"
        mock_requests.assert_called_once_with("東京の天気を教えて", "gpt-4")
        mock_openai.assert_not_called()
    
    @patch('tools_client.run_tool_call_with_openai')
    @patch('tools_client.run_tool_call_with_requests')
    def test_run_tool_call_auto_mode_with_openai(self, mock_requests, mock_openai):
        """自動モード（OpenAI利用可能時）の検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        tools_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = tools_client.run_tool_call("東京の天気を教えて", "gpt-4", "auto")
        
        # 検証
        assert result == "OpenAI result"
        mock_openai.assert_called_once_with("東京の天気を教えて", "gpt-4")
        mock_requests.assert_not_called()
    
    @patch('tools_client.run_tool_call_with_openai')
    @patch('tools_client.run_tool_call_with_requests')
    def test_run_tool_call_auto_mode_without_openai(self, mock_requests, mock_openai):
        """自動モード（OpenAI利用不可時）の検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用不可能に設定
        tools_client.OPENAI_CLIENT_AVAILABLE = False
        
        # テスト実行
        result = tools_client.run_tool_call("東京の天気を教えて", "gpt-4", "auto")
        
        # 検証
        assert result == "Requests result"
        mock_requests.assert_called_once_with("東京の天気を教えて", "gpt-4")
        mock_openai.assert_not_called()


# main関数のテスト
class TestMain:
    @patch('tools_client.run_tool_call')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_function(self, mock_parse_args, mock_run_tool_call):
        """mainメソッドの検証"""
        # ArgumentParserの戻り値をモック
        mock_args = MagicMock()
        mock_args.message = "東京の天気を教えて"
        mock_args.model = "gpt-4"
        mock_args.client = "auto"
        mock_parse_args.return_value = mock_args
        
        # run_tool_callメソッドの戻り値をモック
        mock_run_tool_call.return_value = "Test result"
        
        # テスト実行
        tools_client.main()
        
        # 検証
        mock_run_tool_call.assert_called_once_with("東京の天気を教えて", "gpt-4", "auto")


if __name__ == "__main__":
    pytest.main(["-v", "test_tools_client.py"])
