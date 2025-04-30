#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
image_generation_client.pyのテストコード
"""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# テスト対象のモジュールをインポート
import image_generation_client


class TestSaveImageFromUrl:
    """画像保存機能のテスト"""
    
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_image_from_url_success(self, mock_file, mock_get):
        """画像保存の成功ケース"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'test_image_data'
        mock_get.return_value = mock_response
        
        # テスト実行
        result = image_generation_client.save_image_from_url("http://example.com/image.png")
        
        # 検証
        assert "generated_image_" in result
        mock_get.assert_called_once_with("http://example.com/image.png")
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with(b'test_image_data')
    
    @patch('requests.get')
    def test_save_image_from_url_download_error(self, mock_get):
        """画像ダウンロードエラーのテスト"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # テスト実行
        result = image_generation_client.save_image_from_url("http://example.com/image.png")
        
        # 検証
        assert result == ""
        mock_get.assert_called_once_with("http://example.com/image.png")
    
    @patch('requests.get')
    def test_save_image_from_url_exception(self, mock_get):
        """例外発生のテスト"""
        # 例外をシミュレート
        mock_get.side_effect = Exception("Network error")
        
        # テスト実行
        result = image_generation_client.save_image_from_url("http://example.com/image.png")
        
        # 検証
        assert result == ""
        mock_get.assert_called_once_with("http://example.com/image.png")


class TestGenerateImageWithOpenAI:
    """OpenAIクライアントでの画像生成テスト"""
    
    @patch('image_generation_client.openai_client.images.generate')
    @patch('image_generation_client.save_image_from_url')
    def test_generate_image_with_openai_success(self, mock_save, mock_generate):
        """OpenAIクライアントでの画像生成成功ケース"""
        # OpenAIレスポンスのモック
        mock_data = MagicMock()
        mock_data.url = "http://example.com/generated.png"
        
        mock_response = MagicMock()
        mock_response.data = [mock_data]
        mock_generate.return_value = mock_response
        
        # 画像保存のモック
        mock_save.return_value = "/path/to/saved/image.png"
        
        # OpenAIクライアントが利用可能なことを保証
        image_generation_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = image_generation_client.generate_image_with_openai("A cute cat", "OpenAI/dall-e-3")
        
        # 検証
        assert result == "http://example.com/generated.png"
        mock_generate.assert_called_once()
        mock_save.assert_called_once_with("http://example.com/generated.png")
        
        # 適切なパラメータが送信されたか検証
        call_args = mock_generate.call_args
        kwargs = call_args[1]
        assert kwargs['model'] == "OpenAI/dall-e-3"
        assert kwargs['prompt'] == "A cute cat"
        assert kwargs['n'] == 1
        assert kwargs['size'] == "1024x1024"
    
    @patch('image_generation_client.openai_client.images.generate')
    @patch('image_generation_client.generate_image_with_requests')
    def test_generate_image_with_openai_error_fallback(self, mock_requests, mock_generate):
        """OpenAIクライアントエラー時のフォールバックテスト"""
        # OpenAIエラーをシミュレート
        mock_generate.side_effect = Exception("API Error")
        
        # requestsモードの戻り値をモック
        mock_requests.return_value = "http://example.com/fallback.png"
        
        # OpenAIクライアントが利用可能なことを保証
        image_generation_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = image_generation_client.generate_image_with_openai("A cute cat", "OpenAI/dall-e-3")
        
        # 検証
        assert result == "http://example.com/fallback.png"
        mock_generate.assert_called_once()
        mock_requests.assert_called_once_with("A cute cat", "OpenAI/dall-e-3", "1024x1024", "standard", True)
    
    def test_generate_image_with_openai_not_available(self):
        """OpenAIクライアント利用不可のテスト"""
        # OpenAIクライアントが利用不可能なことを設定
        image_generation_client.OPENAI_CLIENT_AVAILABLE = False
        
        # generate_image_with_requestsをモック
        with patch('image_generation_client.generate_image_with_requests') as mock_requests:
            mock_requests.return_value = "http://example.com/requests.png"
            
            # テスト実行
            result = image_generation_client.generate_image_with_openai("A cute cat")
            
            # 検証
            assert result == "http://example.com/requests.png"
            mock_requests.assert_called_once()


class TestGenerateImageWithRequests:
    """requestsライブラリでの画像生成テスト"""
    
    @patch('requests.post')
    @patch('image_generation_client.save_image_from_url')
    def test_generate_image_with_requests_success(self, mock_save, mock_post):
        """requestsでの画像生成成功ケース"""
        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "url": "http://example.com/generated.png"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # 画像保存のモック
        mock_save.return_value = "/path/to/saved/image.png"
        
        # テスト実行
        result = image_generation_client.generate_image_with_requests("A cute cat", "OpenAI/dall-e-3")
        
        # 検証
        assert result == "http://example.com/generated.png"
        mock_post.assert_called_once()
        mock_save.assert_called_once_with("http://example.com/generated.png")
        
        # 送信されたペイロードを検証
        call_args = mock_post.call_args
        args, kwargs = call_args
        assert kwargs['json']['model'] == "OpenAI/dall-e-3"
        assert kwargs['json']['prompt'] == "A cute cat"
        assert kwargs['json']['n'] == 1
        assert kwargs['json']['size'] == "1024x1024"
        assert kwargs['headers']['Content-Type'] == "application/json"
    
    @patch('requests.post')
    def test_generate_image_with_requests_gemini_model(self, mock_post):
        """Geminiモデルでの特殊パラメータテスト"""
        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "url": "http://example.com/generated.png"
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # テスト実行 - save_imageをFalseに設定して画像保存をスキップ
        result = image_generation_client.generate_image_with_requests("A cute cat", "Google/gemini-2.0-flash", save_image=False)
        
        # 検証
        assert result == "http://example.com/generated.png"
        mock_post.assert_called_once()
        
        # Gemini用の特殊パラメータを確認
        call_args = mock_post.call_args
        args, kwargs = call_args
        assert kwargs['json']['model'] == "Google/gemini-2.0-flash"
        assert "modalities" in kwargs['json']
        assert kwargs['json']['modalities'] == ["image"]
    
    @patch('requests.post')
    def test_generate_image_with_requests_error(self, mock_post):
        """requestsクライアントエラー処理のテスト"""
        # エラーをシミュレート
        mock_post.side_effect = Exception("API Error")
        
        # テスト実行
        result = image_generation_client.generate_image_with_requests("A cute cat")
        
        # 検証
        assert result == ""
        mock_post.assert_called_once()


class TestIntegratedInterface:
    """統合インターフェースのテスト"""
    
    @patch('image_generation_client.generate_image_with_openai')
    @patch('image_generation_client.generate_image_with_requests')
    def test_generate_image_openai_mode(self, mock_requests, mock_openai):
        """OpenAIモードの検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        image_generation_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = image_generation_client.generate_image("A cute cat", client_type="openai")
        
        # 検証
        assert result == "OpenAI result"
        mock_openai.assert_called_once()
        mock_requests.assert_not_called()
    
    @patch('image_generation_client.generate_image_with_openai')
    @patch('image_generation_client.generate_image_with_requests')
    def test_generate_image_requests_mode(self, mock_requests, mock_openai):
        """Requestsモードの検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        image_generation_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = image_generation_client.generate_image("A cute cat", client_type="requests")
        
        # 検証
        assert result == "Requests result"
        mock_requests.assert_called_once()
        mock_openai.assert_not_called()
    
    @patch('image_generation_client.generate_image_with_openai')
    @patch('image_generation_client.generate_image_with_requests')
    def test_generate_image_auto_mode_with_openai(self, mock_requests, mock_openai):
        """自動モード（OpenAI利用可能時）の検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用可能なことを保証
        image_generation_client.OPENAI_CLIENT_AVAILABLE = True
        
        # テスト実行
        result = image_generation_client.generate_image("A cute cat", client_type="auto")
        
        # 検証
        assert result == "OpenAI result"
        mock_openai.assert_called_once()
        mock_requests.assert_not_called()
    
    @patch('image_generation_client.generate_image_with_openai')
    @patch('image_generation_client.generate_image_with_requests')
    def test_generate_image_auto_mode_without_openai(self, mock_requests, mock_openai):
        """自動モード（OpenAI利用不可時）の検証"""
        # モックの設定
        mock_openai.return_value = "OpenAI result"
        mock_requests.return_value = "Requests result"
        
        # OpenAIクライアントが利用不可能に設定
        image_generation_client.OPENAI_CLIENT_AVAILABLE = False
        
        # テスト実行
        result = image_generation_client.generate_image("A cute cat", client_type="auto")
        
        # 検証
        assert result == "Requests result"
        mock_requests.assert_called_once()
        mock_openai.assert_not_called()


class TestCommandLineInterface:
    """コマンドラインインターフェースのテスト"""
    
    @patch('image_generation_client.generate_image')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_function(self, mock_parse_args, mock_generate):
        """mainメソッドの検証"""
        # ArgumentParserの戻り値をモック
        mock_args = MagicMock()
        mock_args.prompt = "A cute cat"
        mock_args.model = "OpenAI/dall-e-3"
        mock_args.size = "1024x1024"
        mock_args.quality = "standard"
        mock_args.no_save = False
        mock_args.client = "auto"
        mock_parse_args.return_value = mock_args
        
        # generateメソッドの戻り値をモック
        mock_generate.return_value = "Test result"
        
        # テスト実行
        image_generation_client.main()
        
        # 検証
        mock_generate.assert_called_once_with("A cute cat", "OpenAI/dall-e-3", "1024x1024", "standard", True, "auto")


if __name__ == "__main__":
    pytest.main(["-v", "test_image_generation_client.py"])
