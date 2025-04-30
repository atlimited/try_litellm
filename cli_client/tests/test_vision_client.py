#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
vision_client.pyのテストコード
"""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# テスト対象のモジュールをインポート
import vision_client


class TestBase64Encoding:
    """Base64エンコード機能のテスト"""
    
    @patch('requests.get')
    def test_get_base64_encoded_image_url(self, mock_get):
        """URL画像のBase64エンコードテスト"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'test_image_data'
        mock_get.return_value = mock_response
        
        # テスト実行
        result = vision_client.get_base64_encoded_image("http://example.com/image.jpg")
        
        # 検証
        assert "data:image/jpeg;base64," in result
        assert "dGVzdF9pbWFnZV9kYXRh" in result  # 'test_image_data'のBase64エンコード
        mock_get.assert_called_once_with("http://example.com/image.jpg")

    @patch('builtins.open', new_callable=mock_open, read_data=b'test_image_data')
    def test_get_base64_encoded_image_local(self, mock_file):
        """ローカル画像のBase64エンコードテスト"""
        # テスト実行
        result = vision_client.get_base64_encoded_image("image.png")
        
        # 検証
        assert "data:image/png;base64," in result
        assert "dGVzdF9pbWFnZV9kYXRh" in result  # 'test_image_data'のBase64エンコード
        mock_file.assert_called_once_with("image.png", 'rb')
    
    @patch('requests.get')
    def test_get_base64_encoded_image_error(self, mock_get):
        """画像取得エラーのテスト"""
        # エラーをシミュレート
        mock_get.side_effect = Exception("Failed to download image")
        
        # テスト実行 & 検証
        with pytest.raises(Exception) as excinfo:
            vision_client.get_base64_encoded_image("http://example.com/image.jpg")
        assert "Failed to download image" in str(excinfo.value)


class TestOpenAIClientMode:
    """OpenAIクライアントモードのテスト"""
    
    @patch('vision_client.get_base64_encoded_image')
    @patch('vision_client.openai_client.chat.completions.create')
    def test_analyze_image_with_openai_success(self, mock_create, mock_get_base64):
        """OpenAIクライアントでの画像分析成功ケース"""
        # Base64エンコードのモック
        mock_get_base64.return_value = "data:image/jpeg;base64,base64_image_data"
        
        # OpenAIレスポンスのモック
        mock_choice = MagicMock()
        mock_choice.message.content = "This is a test image description."
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response
        
        # OpenAIクライアントが利用可能なことを保証
        vision_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = vision_client.analyze_image_with_openai("image.jpg", "What's in this image?", "test-model")
        
        # 検証
        assert result == "This is a test image description."
        mock_create.assert_called_once()
        
        # リクエストパラメータの検証
        call_args = mock_create.call_args
        kwargs = call_args[1]
        assert kwargs['model'] == "test-model"
        assert kwargs['messages'][0]['role'] == "user"
        assert kwargs['messages'][0]['content'][0]['type'] == "text"
        assert kwargs['messages'][0]['content'][0]['text'] == "What's in this image?"
        assert kwargs['messages'][0]['content'][1]['type'] == "image_url"
        assert kwargs['messages'][0]['content'][1]['image_url']['url'] == "data:image/jpeg;base64,base64_image_data"

    @patch('vision_client.get_base64_encoded_image')
    @patch('vision_client.openai_client.chat.completions.create')
    @patch('vision_client.analyze_image_with_requests')
    def test_analyze_image_with_openai_error_fallback(self, mock_requests, mock_create, mock_get_base64):
        """OpenAIクライアントエラー時のフォールバックテスト"""
        # Base64エンコードのモック
        mock_get_base64.return_value = "data:image/jpeg;base64,base64_image_data"
        
        # OpenAIエラーをシミュレート
        mock_create.side_effect = Exception("API Error")
        
        # requestsモードの戻り値をモック
        mock_requests.return_value = "Fallback response"
        
        # OpenAIクライアントが利用可能なことを保証
        vision_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = vision_client.analyze_image_with_openai("image.jpg", "What's in this image?", "test-model")
        
        # 検証
        assert result == "Fallback response"
        mock_create.assert_called_once()
        mock_requests.assert_called_once_with("image.jpg", "What's in this image?", "test-model")


class TestRequestsClientMode:
    """requestsクライアントモードのテスト"""
    
    @patch('vision_client.get_base64_encoded_image')
    @patch('requests.post')
    def test_analyze_image_with_requests_success(self, mock_post, mock_get_base64):
        """requestsクライアントでの画像分析成功ケース"""
        # Base64エンコードのモック
        mock_get_base64.return_value = "data:image/jpeg;base64,base64_image_data"
        
        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test image description.",
                        "role": "assistant"
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # テスト実行
        result = vision_client.analyze_image_with_requests("image.jpg", "What's in this image?", "test-model")
        
        # 検証
        assert result == "This is a test image description."
        mock_post.assert_called_once()
        
        # リクエストパラメータの検証
        call_args = mock_post.call_args
        args, kwargs = call_args
        assert kwargs['json']['model'] == "test-model"
        assert kwargs['json']['messages'][0]['role'] == "user"
        assert kwargs['headers']['Content-Type'] == "application/json"

    @patch('vision_client.get_base64_encoded_image')
    @patch('requests.post')
    def test_analyze_image_with_requests_gemini_model(self, mock_post, mock_get_base64):
        """Gemini特有のリクエスト形式テスト"""
        # Base64エンコードのモック
        mock_get_base64.return_value = "data:image/jpeg;base64,base64_image_data"
        
        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test image description.",
                        "role": "assistant"
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # テスト実行 - Geminiモデルを使用
        result = vision_client.analyze_image_with_requests("image.jpg", "What's in this image?", "Google/gemini-2.0-flash")
        
        # 検証
        assert result == "This is a test image description."
        mock_post.assert_called_once()
        
        # Geminiのリクエスト形式を検証
        call_args = mock_post.call_args
        args, kwargs = call_args
        assert kwargs['json']['model'] == "Google/gemini-2.0-flash"
        assert isinstance(kwargs['json']['messages'][0]['content'], list)  # contentが配列形式になっているか
        
    @patch('vision_client.get_base64_encoded_image')
    @patch('requests.post')
    def test_analyze_image_with_requests_error(self, mock_post, mock_get_base64):
        """requestsクライアントエラー処理のテスト"""
        # Base64エンコードのモック
        mock_get_base64.return_value = "data:image/jpeg;base64,base64_image_data"
        
        # エラーをシミュレート
        mock_post.side_effect = Exception("API Error")
        
        # テスト実行
        result = vision_client.analyze_image_with_requests("image.jpg", "What's in this image?", "test-model")
        
        # 検証
        assert result == ""
        mock_post.assert_called_once()


class TestIntegratedInterface:
    """統合インターフェースのテスト"""
    
    @patch('vision_client.analyze_image_with_openai')
    @patch('vision_client.analyze_image_with_requests')
    def test_analyze_image_openai_mode(self, mock_requests, mock_openai):
        """OpenAIモードの検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        vision_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = vision_client.analyze_image("image.jpg", "What's in this image?", "test-model", "openai")
        
        # 検証
        assert result == "OpenAI result"
        mock_openai.assert_called_once_with("image.jpg", "What's in this image?", "test-model")
        mock_requests.assert_not_called()
    
    @patch('vision_client.analyze_image_with_openai')
    @patch('vision_client.analyze_image_with_requests')
    def test_analyze_image_requests_mode(self, mock_requests, mock_openai):
        """Requestsモードの検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        vision_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = vision_client.analyze_image("image.jpg", "What's in this image?", "test-model", "requests")
        
        # 検証
        assert result == "Requests result"
        mock_requests.assert_called_once_with("image.jpg", "What's in this image?", "test-model")
        mock_openai.assert_not_called()
    
    @patch('vision_client.analyze_image_with_openai')
    @patch('vision_client.analyze_image_with_requests')
    def test_analyze_image_auto_mode_with_openai(self, mock_requests, mock_openai):
        """自動モード（OpenAI利用可能時）の検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        vision_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = vision_client.analyze_image("image.jpg", "What's in this image?", "test-model", "auto")
        
        # 検証
        assert result == "OpenAI result"
        mock_openai.assert_called_once_with("image.jpg", "What's in this image?", "test-model")
        mock_requests.assert_not_called()
    
    @patch('vision_client.analyze_image_with_openai')
    @patch('vision_client.analyze_image_with_requests')
    def test_analyze_image_auto_mode_without_openai(self, mock_requests, mock_openai):
        """自動モード（OpenAI利用不可時）の検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用不可能に設定
        vision_client.OPENAI_CLIENT_AVAILABLE = False
        
        # テスト実行
        result = vision_client.analyze_image("image.jpg", "What's in this image?", "test-model", "auto")
        
        # 検証
        assert result == "Requests result"
        mock_requests.assert_called_once_with("image.jpg", "What's in this image?", "test-model")
        mock_openai.assert_not_called()


class TestCommandLineInterface:
    """コマンドラインインターフェースのテスト"""
    
    @patch('vision_client.analyze_image')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_function(self, mock_parse_args, mock_analyze):
        """mainメソッドの検証"""
        # ArgumentParserの戻り値をモック
        mock_args = MagicMock()
        mock_args.image_url = "image.jpg"
        mock_args.prompt = "What's in this image?"
        mock_args.model = "test-model"
        mock_args.client = "auto"
        mock_parse_args.return_value = mock_args
        
        # analyzeメソッドの戻り値をモック
        mock_analyze.return_value = "Test result"
        
        # テスト実行
        vision_client.main()
        
        # 検証
        mock_analyze.assert_called_once_with("image.jpg", "What's in this image?", "test-model", "auto")


if __name__ == "__main__":
    pytest.main(["-v", "test_vision_client.py"])
