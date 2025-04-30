import os
import sys
import json
import pytest
import base64
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import io

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# テスト対象のモジュールをインポート
import gemini_direct_requests_client


class TestChatWithModel:
    @patch('gemini_direct_requests_client.requests.post')
    def test_chat_with_model_success(self, mock_post):
        """テキストチャット機能の正常系テスト"""
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "こんにちは！お手伝いできることはありますか？"
                            }
                        ],
                        "role": "model"
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # テスト実行
        result = gemini_direct_requests_client.chat_with_model("こんにちは", "gemini-2.0-flash")
        
        # 検証
        assert "こんにちは！お手伝いできることはありますか？" in result
        mock_post.assert_called_once()
        
        # リクエストペイロードの検証
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['contents'][0]['parts'][0]['text'] == "こんにちは"
        
        # URLにAPIキーが含まれているか検証
        url = call_args[0][0]
        assert "gemini-2.0-flash" in url
        assert "key=" in url

    @patch('gemini_direct_requests_client.requests.post')
    def test_chat_with_model_error(self, mock_post):
        """テキストチャット機能のエラー系テスト"""
        # APIエラーをシミュレート
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Invalid request"}}
        mock_post.return_value = mock_response
        
        # テスト実行
        result = gemini_direct_requests_client.chat_with_model("エラーを発生させるプロンプト")
        
        # 検証 - 空文字列を返すのが実際の挙動
        assert result == ""
        mock_post.assert_called_once()


class TestAnalyzeImage:
    @patch('gemini_direct_requests_client.requests.post')
    @patch('gemini_direct_requests_client.get_base64_encoded_image')
    @patch('gemini_direct_requests_client.Image.open')
    @patch('gemini_direct_requests_client.os.path.splitext')
    def test_analyze_image_success(self, mock_splitext, mock_image_open, mock_get_base64, mock_post):
        """画像分析機能の正常系テスト"""
        # 画像モックの設定
        mock_image = MagicMock()
        mock_image.size = (100, 100)
        mock_image_open.return_value = mock_image
        
        # 画像拡張子のモック
        mock_splitext.return_value = ["test_image", ".jpg"]
        
        # Base64エンコード画像のモック
        mock_get_base64.return_value = "base64encodedimagedata"
        
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "これは猫の画像です。茶色の猫が座っています。"
                            }
                        ],
                        "role": "model"
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # テスト実行
        result = gemini_direct_requests_client.analyze_image("test_image.jpg", "この画像は何ですか？")
        
        # 検証
        assert "猫の画像" in result
        mock_post.assert_called_once()
        
        # リクエストペイロードの検証
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        
        # contentが配列形式になっているか検証（Gemini APIの特性）
        assert isinstance(payload['contents'][0]['parts'], list)
        assert len(payload['contents'][0]['parts']) == 2  # テキストと画像の2つ
        
        # テキストプロンプトの検証
        text_part = None
        image_part = None
        for part in payload['contents'][0]['parts']:
            if 'text' in part:
                text_part = part
            elif 'inline_data' in part:
                image_part = part
        
        assert text_part is not None
        assert text_part['text'] == "この画像は何ですか？"
        
        # 画像データの検証
        assert image_part is not None
        assert image_part['inline_data']['mime_type'] == "image/jpeg"
        assert image_part['inline_data']['data'] == "base64encodedimagedata"

    @patch('builtins.open')
    def test_analyze_image_error(self, mock_open):
        """画像分析機能のエラー系テスト - ファイルアクセスエラー"""
        # ファイルオープンに失敗する例外を設定
        mock_open.side_effect = FileNotFoundError("File not found")
        
        # テスト実行
        # 実際のコードではtry-exceptの外でopen()が呼ばれるので、
        # 例外が捕捉されずにそのまま発生することをテスト
        with pytest.raises(FileNotFoundError):
            gemini_direct_requests_client.analyze_image("non_existent_image.jpg")


class TestGenerateImage:
    @patch('gemini_direct_requests_client.requests.post')
    @patch('gemini_direct_requests_client.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('base64.b64decode')
    def test_generate_image_success(self, mock_b64decode, mock_file, mock_makedirs, mock_post):
        """画像生成機能の正常系テスト - Gemini API成功"""
        # 正常応答のモック - 画像データあり
        mock_b64decode.return_value = b'fake_image_data'
        
        # モックレスポンスの設定
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "data": "base64encodedimagecontent",
                                    "mimeType": "image/png"
                                }
                            }
                        ],
                        "role": "model"
                    }
                }
            ]
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # 実際のoutput_pathを使用
        output_path = "test_output.png"
        
        # テスト実行
        result = gemini_direct_requests_client.generate_image("綺麗な富士山", output_path)
        
        # 検証 - 実際の実装では成功時にパスを返す
        assert output_path == result
        mock_post.assert_called_once()
        
        # リクエストペイロードの検証
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        
        # Gemini API特有のresponseModalities設定を検証
        assert 'generationConfig' in payload
        assert 'responseModalities' in payload['generationConfig']
        assert "IMAGE" in payload['generationConfig']['responseModalities']
        
        # プロンプト検証
        assert payload['contents'][0]['parts'][0]['text'] == "綺麗な富士山"
        
        # ファイル保存の検証
        mock_file.assert_called_once_with(output_path, "wb")
        mock_file().write.assert_called_once()

    @patch('gemini_direct_requests_client.requests.post')
    def test_generate_image_error(self, mock_post):
        """画像生成機能のエラー系テスト - 両方のAPI呼び出しが失敗"""
        # 最初のAPIリクエスト失敗をシミュレート
        first_response = MagicMock()
        first_response.status_code = 400
        first_response.json.return_value = {"error": {"message": "Invalid request"}}
        
        # 2回目のAPIリクエスト失敗をシミュレート
        second_response = MagicMock()
        second_response.status_code = 400
        second_response.json.return_value = {"error": {"message": "Invalid request"}}
        
        # requestsのpostメソッドが2回呼ばれたとき、異なるレスポンスを返すよう設定
        mock_post.side_effect = [first_response, second_response]
        
        # テスト実行
        result = gemini_direct_requests_client.generate_image("エラーを発生させるプロンプト")
        
        # 検証 - 空文字列が返されることを期待
        assert result == ""
        assert mock_post.call_count == 2  # 両方のAPIが呼ばれるはず


class TestGetBase64EncodedImage:
    @patch('builtins.open', new_callable=mock_open, read_data=b'test image data')
    def test_get_base64_encoded_image(self, mock_file):
        """画像のBase64エンコード機能のテスト"""
        # テスト実行
        result = gemini_direct_requests_client.get_base64_encoded_image("test_image.jpg")
        
        # 検証
        assert isinstance(result, str)
        # Base64エンコードされた文字列かを確認
        try:
            decoded = base64.b64decode(result)
            assert decoded == b'test image data'
        except Exception:
            pytest.fail("Invalid base64 string")


class TestMain:
    @patch('gemini_direct_requests_client.chat_with_model')
    @patch('gemini_direct_requests_client.analyze_image')
    @patch('gemini_direct_requests_client.generate_image')
    @patch('gemini_direct_requests_client.argparse.ArgumentParser.parse_args')
    def test_main_chat_command(self, mock_parse_args, mock_generate, mock_analyze, mock_chat):
        """mainメソッドのchatコマンドテスト"""
        # ArgumentParserの戻り値をモック
        mock_args = MagicMock()
        mock_args.command = "chat"
        mock_args.prompt = "こんにちは"
        mock_args.model = "gemini-2.0-flash"
        mock_args.image = None
        mock_parse_args.return_value = mock_args
        
        # 結果のモック
        mock_chat.return_value = "こんにちは！お手伝いできることはありますか？"
        
        # テスト実行
        gemini_direct_requests_client.main()
        
        # 検証
        mock_chat.assert_called_once_with("こんにちは", "gemini-2.0-flash")
        mock_analyze.assert_not_called()
        mock_generate.assert_not_called()

    @patch('gemini_direct_requests_client.chat_with_model')
    @patch('gemini_direct_requests_client.analyze_image')
    @patch('gemini_direct_requests_client.generate_image')
    @patch('gemini_direct_requests_client.argparse.ArgumentParser.parse_args')
    def test_main_vision_command(self, mock_parse_args, mock_generate, mock_analyze, mock_chat):
        """mainメソッドのvisionコマンドテスト"""
        # ArgumentParserの戻り値をモック
        mock_args = MagicMock()
        mock_args.command = "vision"
        mock_args.prompt = "この画像は何ですか？"
        mock_args.model = "gemini-2.0-flash"
        mock_args.image = "test_image.jpg"
        mock_parse_args.return_value = mock_args
        
        # 結果のモック
        mock_analyze.return_value = "これは猫の画像です。"
        
        # テスト実行
        gemini_direct_requests_client.main()
        
        # 検証
        mock_analyze.assert_called_once_with("test_image.jpg", "この画像は何ですか？", "gemini-2.0-flash")
        mock_chat.assert_not_called()
        mock_generate.assert_not_called()

    @patch('gemini_direct_requests_client.chat_with_model')
    @patch('gemini_direct_requests_client.analyze_image')
    @patch('gemini_direct_requests_client.generate_image')
    @patch('gemini_direct_requests_client.argparse.ArgumentParser.parse_args')
    def test_main_image_command(self, mock_parse_args, mock_generate, mock_analyze, mock_chat):
        """mainメソッドのimageコマンドテスト"""
        # ArgumentParserの戻り値をモック
        mock_args = MagicMock()
        mock_args.command = "image"
        mock_args.prompt = "綺麗な富士山"
        mock_args.model = "gemini-2.0-flash-exp-image-generation"
        mock_args.output = "test_output.png"
        mock_parse_args.return_value = mock_args
        
        # 結果のモック
        mock_generate.return_value = "test_output.png"
        
        # テスト実行
        gemini_direct_requests_client.main()
        
        # 検証
        mock_generate.assert_called_once_with("綺麗な富士山", "test_output.png", "gemini-2.0-flash-exp-image-generation")
        mock_chat.assert_not_called()
        mock_analyze.assert_not_called()


if __name__ == "__main__":
    pytest.main(["-v", "test_gemini_direct_requests_client.py"])
