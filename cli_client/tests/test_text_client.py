#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
text_client.pyのテストコード
"""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# テスト対象のモジュールをインポート
import text_client


class TestOpenAIClientMode:
    """OpenAIクライアントモードのテスト"""
    
    @patch('text_client.openai_client.chat.completions.create')
    def test_generate_text_with_openai_success(self, mock_create):
        """OpenAIクライアントでのテキスト生成成功ケース"""
        # OpenAIレスポンスのモック
        mock_choice = MagicMock()
        mock_choice.message.content = "This is a test response."
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response
        
        # OpenAIクライアントが利用可能なことを保証
        text_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = text_client.generate_text_with_openai("こんにちは", "test-model")
        
        # 検証
        assert result == "This is a test response."
        mock_create.assert_called_once()
        
        # リクエストパラメータの検証
        call_args = mock_create.call_args
        kwargs = call_args[1]
        assert kwargs['model'] == "test-model"
        assert kwargs['messages'][0]['role'] == "user"
        assert kwargs['messages'][0]['content'] == "こんにちは"

    @patch('text_client.openai_client.chat.completions.create')
    @patch('text_client.generate_text_with_requests')
    def test_generate_text_with_openai_error_fallback(self, mock_requests, mock_create):
        """OpenAIクライアントエラー時のフォールバックテスト"""
        # OpenAIエラーをシミュレート
        mock_create.side_effect = Exception("API Error")
        
        # requestsモードの戻り値をモック
        mock_requests.return_value = "Fallback response"
        
        # OpenAIクライアントが利用可能なことを保証
        text_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = text_client.generate_text_with_openai("こんにちは", "test-model")
        
        # 検証
        assert result == "Fallback response"
        mock_create.assert_called_once()
        mock_requests.assert_called_once_with("こんにちは", "test-model")


class TestRequestsClientMode:
    """requestsクライアントモードのテスト"""
    
    @patch('requests.post')
    def test_generate_text_with_requests_success(self, mock_post):
        """requestsクライアントでのテキスト生成成功ケース"""
        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response.",
                        "role": "assistant"
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # テスト実行
        result = text_client.generate_text_with_requests("こんにちは", "test-model")
        
        # 検証
        assert result == "This is a test response."
        mock_post.assert_called_once()
        
        # リクエストパラメータの検証
        call_args = mock_post.call_args
        args, kwargs = call_args
        assert kwargs['json']['model'] == "test-model"
        assert kwargs['json']['messages'][0]['role'] == "user"
        assert kwargs['json']['messages'][0]['content'] == "こんにちは"
        assert kwargs['headers']['Content-Type'] == "application/json"

    @patch('requests.post')
    def test_generate_text_with_requests_gemini_model(self, mock_post):
        """Gemini特有のリクエスト形式テスト"""
        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response.",
                        "role": "assistant"
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # テスト実行 - Geminiモデルを使用
        result = text_client.generate_text_with_requests("こんにちは", "Google/gemini-2.0-flash")
        
        # 検証
        assert result == "This is a test response."
        mock_post.assert_called_once()
        
        # Geminiのリクエスト形式を検証（テキスト用はrequestsでも通常形式）
        call_args = mock_post.call_args
        args, kwargs = call_args
        assert kwargs['json']['model'] == "Google/gemini-2.0-flash"
        
    @patch('requests.post')
    def test_generate_text_with_requests_error(self, mock_post):
        """requestsクライアントエラー処理のテスト"""
        # エラーをシミュレート
        mock_post.side_effect = Exception("API Error")
        
        # テスト実行
        result = text_client.generate_text_with_requests("こんにちは", "test-model")
        
        # 検証
        assert result == ""
        mock_post.assert_called_once()


class TestIntegratedInterface:
    """統合インターフェースのテスト"""
    
    @patch('text_client.generate_text_with_openai')
    @patch('text_client.generate_text_with_requests')
    def test_generate_text_openai_mode(self, mock_requests, mock_openai):
        """OpenAIモードの検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        text_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = text_client.generate_text("こんにちは", "test-model", "openai")
        
        # 検証
        assert result == "OpenAI result"
        mock_openai.assert_called_once_with("こんにちは", "test-model")
        mock_requests.assert_not_called()
    
    @patch('text_client.generate_text_with_openai')
    @patch('text_client.generate_text_with_requests')
    def test_generate_text_requests_mode(self, mock_requests, mock_openai):
        """Requestsモードの検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        text_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = text_client.generate_text("こんにちは", "test-model", "requests")
        
        # 検証
        assert result == "Requests result"
        mock_requests.assert_called_once_with("こんにちは", "test-model")
        mock_openai.assert_not_called()
    
    @patch('text_client.generate_text_with_openai')
    @patch('text_client.generate_text_with_requests')
    def test_generate_text_auto_mode_with_openai(self, mock_requests, mock_openai):
        """自動モード（OpenAI利用可能時）の検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        text_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = text_client.generate_text("こんにちは", "test-model", "auto")
        
        # 検証
        assert result == "OpenAI result"
        mock_openai.assert_called_once_with("こんにちは", "test-model")
        mock_requests.assert_not_called()
    
    @patch('text_client.generate_text_with_openai')
    @patch('text_client.generate_text_with_requests')
    def test_generate_text_auto_mode_without_openai(self, mock_requests, mock_openai):
        """自動モード（OpenAI利用不可時）の検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用不可能に設定
        text_client.OPENAI_CLIENT_AVAILABLE = False
        
        # テスト実行
        result = text_client.generate_text("こんにちは", "test-model", "auto")
        
        # 検証
        assert result == "Requests result"
        mock_requests.assert_called_once_with("こんにちは", "test-model")
        mock_openai.assert_not_called()


class TestCommandLineInterface:
    """コマンドラインインターフェースのテスト"""
    
    @patch('text_client.generate_text')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_function(self, mock_parse_args, mock_generate):
        """mainメソッドの検証"""
        # ArgumentParserの戻り値をモック
        mock_args = MagicMock()
        mock_args.message = "こんにちは"
        mock_args.model = "test-model"
        mock_args.client = "auto"
        mock_parse_args.return_value = mock_args
        
        # generateメソッドの戻り値をモック
        mock_generate.return_value = "Test result"
        
        # テスト実行
        text_client.main()
        
        # 検証
        mock_generate.assert_called_once_with("こんにちは", "test-model", "auto")


if __name__ == "__main__":
    pytest.main(["-v", "test_text_client.py"])
