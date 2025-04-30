import unittest
import os
import sys
import tempfile
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# テスト対象のモジュールをインポートパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テスト対象モジュールをインポート
import gemini_litellm_client

class TestGeminiLiteLLMClient(unittest.TestCase):
    """gemini_litellm_client.pyのユニットテスト"""
    
    def setUp(self):
        """各テスト前の準備"""
        # 一時ディレクトリを作成してテスト画像を保存
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_image_path = os.path.join(self.temp_dir.name, "test_image.jpg")
        
        # テスト用の空画像ファイルを作成
        with open(self.test_image_path, "wb") as f:
            f.write(b"dummy image data")
    
    def tearDown(self):
        """各テスト後のクリーンアップ"""
        self.temp_dir.cleanup()
    
    def test_chat_with_requests(self):
        """requestsクライアントを使用したチャット機能のテスト"""
        # モックレスポンスを設定
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "テスト応答"
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        # テスト実行前に必要なモジュールパッチ
        with patch('requests.post', return_value=mock_response):
            with patch.object(gemini_litellm_client, 'BASE_URL', 'http://test.url'):
                with patch.object(gemini_litellm_client, 'GEMINI_API_KEY', 'test_key'):
                    with patch('builtins.print'):  # printを抑制
                        result = gemini_litellm_client.chat_with_requests("テストメッセージ")
                        
                        # 検証
                        self.assertEqual(result, "テスト応答")
    
    def test_chat_with_openai(self):
        """OpenAIクライアントを使用したチャット機能のテスト"""
        # テスト用のモッククライアント
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="テスト応答"))
        ]
        
        # モックメソッドの設定
        mock_completions_create = MagicMock(return_value=mock_response)
        mock_completions = MagicMock()
        mock_completions.create = mock_completions_create
        mock_openai_client.chat = MagicMock(completions=mock_completions)
        
        # テスト実行
        with patch.object(gemini_litellm_client, 'openai_client', mock_openai_client):
            with patch('builtins.print'):  # printを抑制
                result = gemini_litellm_client.chat_with_openai("テストメッセージ")
                
                # 検証
                self.assertEqual(result, "テスト応答")
                mock_completions_create.assert_called_once()
    
    def test_analyze_image_with_requests(self):
        """requestsクライアントを使用した画像分析機能のテスト"""
        # Base64エンコードのモック
        mock_encoded = "encoded_image_data"
        
        # レスポンスモック
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "画像分析結果"
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        # テスト実行
        with patch('gemini_litellm_client.encode_image_to_base64', return_value=mock_encoded):
            with patch('requests.post', return_value=mock_response):
                with patch.object(gemini_litellm_client, 'BASE_URL', 'http://test.url'):
                    with patch.object(gemini_litellm_client, 'GEMINI_API_KEY', 'test_key'):
                        with patch('builtins.print'):  # printを抑制
                            result = gemini_litellm_client.analyze_image_with_requests(self.test_image_path, "画像を分析")
                            
                            # 検証
                            self.assertEqual(result, "画像分析結果")
    
    def test_analyze_image_with_openai(self):
        """OpenAIクライアントを使用した画像分析機能のテスト"""
        # テスト用のモッククライアント
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="画像分析結果"))
        ]
        
        # モックメソッドの設定
        mock_completions_create = MagicMock(return_value=mock_response)
        mock_completions = MagicMock()
        mock_completions.create = mock_completions_create
        mock_openai_client.chat = MagicMock(completions=mock_completions)
        
        # Base64エンコードのモック
        mock_encoded = "encoded_image_data"
        
        with patch('gemini_litellm_client.encode_image_to_base64', return_value=mock_encoded):
            with patch.object(gemini_litellm_client, 'openai_client', mock_openai_client):
                with patch('builtins.print'):  # printを抑制
                    result = gemini_litellm_client.analyze_image_with_openai(self.test_image_path, "画像を分析")
                    
                    # 検証
                    self.assertEqual(result, "画像分析結果")
                    mock_completions_create.assert_called_once()
    
    def test_chat_auto(self):
        """自動クライアント選択機能のテスト（チャット）"""
        with patch('gemini_litellm_client.OPENAI_CLIENT_AVAILABLE', True):
            with patch('builtins.print'):  # printを抑制
                # requestsクライアントが失敗するように設定
                with patch('gemini_litellm_client.chat_with_requests', side_effect=Exception("Requests client failed")) as mock_requests:
                    # OpenAIクライアントが成功するように設定
                    with patch('gemini_litellm_client.chat_with_openai', return_value="OpenAI response") as mock_openai:
                        # テスト実行
                        result = gemini_litellm_client.chat("テストメッセージ", client_type="auto")
                        
                        # 検証
                        self.assertEqual(result, "OpenAI response")
                        mock_requests.assert_called_once()
                        mock_openai.assert_called_once()
    
    def test_analyze_image_auto(self):
        """自動クライアント選択機能のテスト（画像分析）"""
        with patch('gemini_litellm_client.OPENAI_CLIENT_AVAILABLE', True):
            with patch('builtins.print'):  # printを抑制
                # requestsクライアントが失敗するように設定
                with patch('gemini_litellm_client.analyze_image_with_requests', side_effect=Exception("Requests client failed")) as mock_requests:
                    # OpenAIクライアントが成功するように設定
                    with patch('gemini_litellm_client.analyze_image_with_openai', return_value="OpenAI image analysis") as mock_openai:
                        # テスト実行
                        result = gemini_litellm_client.analyze_image(self.test_image_path, "テストメッセージ", client_type="auto")
                        
                        # 検証
                        self.assertEqual(result, "OpenAI image analysis")
                        mock_requests.assert_called_once()
                        mock_openai.assert_called_once()

if __name__ == "__main__":
    unittest.main()
