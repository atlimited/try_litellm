#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
audio_client.pyのテストコード
"""

import os
import sys
import json
import base64
import tempfile
from unittest import mock
from pathlib import Path

import pytest
import requests

# テスト対象のモジュールをインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import audio_client

# テスト用のサンプル音声ファイル
SAMPLE_AUDIO_URL = "https://openaiassets.blob.core.windows.net/$web/API/docs/audio/alloy.wav"
SAMPLE_AUDIO_CONTENT = b"dummy audio content for testing"
SAMPLE_AUDIO_FORMAT = "wav"

# モックレスポンス
MOCK_TRANSCRIPTION_RESPONSE = {
    "text": "Sample transcription text for testing."
}

MOCK_CHAT_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": "This is a sample response from the audio chat model."
            }
        }
    ]
}

# OpenAIクライアントのモッククラス
class MockOpenAICompletionsResponse:
    class Message:
        content = "This is a sample response from the audio chat model."
    
    class Choice:
        def __init__(self):
            self.message = MockOpenAICompletionsResponse.Message()
    
    def __init__(self):
        self.choices = [MockOpenAICompletionsResponse.Choice()]

class MockOpenAITranscriptionsResponse:
    def __init__(self, text="Sample transcription text for testing."):
        self.text = text


class TestGetAudioData:
    """音声データ取得機能のテスト"""
    
    @mock.patch('requests.get')
    def test_get_audio_data_from_url(self, mock_get):
        """URLから音声データを取得するテスト"""
        # モックレスポンスを設定
        mock_response = mock.Mock()
        mock_response.content = SAMPLE_AUDIO_CONTENT
        mock_get.return_value = mock_response
        
        # 関数を実行
        audio_data, file_format = audio_client.get_audio_data(SAMPLE_AUDIO_URL)
        
        # アサーション
        assert audio_data == SAMPLE_AUDIO_CONTENT
        assert file_format == SAMPLE_AUDIO_FORMAT
        mock_get.assert_called_once_with(SAMPLE_AUDIO_URL)
    
    @mock.patch('os.path.exists')
    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data=SAMPLE_AUDIO_CONTENT)
    def test_get_audio_data_from_file(self, mock_file, mock_exists):
        """ローカルファイルから音声データを取得するテスト"""
        # モックを設定
        mock_exists.return_value = True
        
        # 関数を実行
        audio_data, file_format = audio_client.get_audio_data("sample.wav")
        
        # アサーション
        assert audio_data == SAMPLE_AUDIO_CONTENT
        assert file_format == "wav"
        mock_file.assert_called_once_with("sample.wav", 'rb')
    
    @mock.patch('requests.get')
    def test_get_audio_data_download_error(self, mock_get):
        """ダウンロードエラー時のテスト"""
        # モックレスポンスを設定
        mock_get.side_effect = requests.exceptions.RequestException("Download error")
        
        # 関数を実行し、例外が発生することを確認
        with pytest.raises(SystemExit):
            audio_client.get_audio_data(SAMPLE_AUDIO_URL)
    
    @mock.patch('os.path.exists')
    @mock.patch('builtins.open')
    def test_get_audio_data_file_error(self, mock_file, mock_exists):
        """ファイル読み込みエラー時のテスト"""
        # モックを設定
        mock_exists.return_value = True
        mock_file.side_effect = IOError("File read error")
        
        # 関数を実行し、例外が発生することを確認
        with pytest.raises(SystemExit):
            audio_client.get_audio_data("sample.wav")


class TestProcessAudioWithOpenAI:
    """OpenAIクライアントを使用した音声処理のテスト"""
    
    @mock.patch('audio_client.get_audio_data')
    @mock.patch('audio_client.openai_client')
    def test_process_audio_with_openai_chat_model(self, mock_openai_client, mock_get_audio_data):
        """チャットモデルでの音声処理テスト"""
        # モックを設定
        mock_get_audio_data.return_value = (SAMPLE_AUDIO_CONTENT, SAMPLE_AUDIO_FORMAT)
        mock_openai_client.chat.completions.create.return_value = MockOpenAICompletionsResponse()
        
        # OpenAIクライアントが利用可能なことを確認
        audio_client.OPENAI_CLIENT_AVAILABLE = True
        
        # 関数を実行
        result = audio_client.process_audio_with_openai(
            SAMPLE_AUDIO_URL,
            prompt="What is in this recording?",
            model="gpt-4o-audio-preview"
        )
        
        # アサーション
        assert result == "This is a sample response from the audio chat model."
        mock_openai_client.chat.completions.create.assert_called_once()
    
    @mock.patch('audio_client.get_audio_data')
    @mock.patch('audio_client.openai_client')
    @mock.patch('tempfile.NamedTemporaryFile')
    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data=SAMPLE_AUDIO_CONTENT)
    @mock.patch('os.remove')
    def test_process_audio_with_openai_transcription_model(self, mock_remove, mock_open, mock_temp_file, mock_openai_client, mock_get_audio_data):
        """文字起こしモデルでの音声処理テスト"""
        # モックを設定
        mock_get_audio_data.return_value = (SAMPLE_AUDIO_CONTENT, SAMPLE_AUDIO_FORMAT)
        mock_openai_client.audio.transcriptions.create.return_value = MockOpenAITranscriptionsResponse()
        
        # 一時ファイルのモック
        mock_temp = mock.MagicMock()
        mock_temp.name = "/tmp/temp_audio.wav"
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        
        # OpenAIクライアントが利用可能なことを確認
        audio_client.OPENAI_CLIENT_AVAILABLE = True
        
        # 関数を実行
        result = audio_client.process_audio_with_openai(
            SAMPLE_AUDIO_URL,
            model="SambaNova/Whisper-Large-v3",
            language="ja"
        )
        
        # アサーション
        assert result == "Sample transcription text for testing."
        mock_openai_client.audio.transcriptions.create.assert_called_once()
        mock_remove.assert_called_once_with(mock_temp.name)
    
    @mock.patch('audio_client.get_audio_data')
    @mock.patch('audio_client.openai_client')
    @mock.patch('audio_client.process_audio_with_requests')
    def test_process_audio_with_openai_error_fallback(self, mock_process_with_requests, mock_openai_client, mock_get_audio_data):
        """OpenAIクライアントエラー時のフォールバックテスト"""
        # モックを設定
        mock_get_audio_data.return_value = (SAMPLE_AUDIO_CONTENT, SAMPLE_AUDIO_FORMAT)
        mock_openai_client.chat.completions.create.side_effect = Exception("OpenAI client error")
        mock_process_with_requests.return_value = "Fallback response from requests"
        
        # OpenAIクライアントが利用可能なことを確認
        audio_client.OPENAI_CLIENT_AVAILABLE = True
        
        # 関数を実行
        result = audio_client.process_audio_with_openai(
            SAMPLE_AUDIO_URL,
            model="gpt-4o-audio-preview"
        )
        
        # アサーション
        assert result == "Fallback response from requests"
        mock_process_with_requests.assert_called_once()
    
    @mock.patch('audio_client.process_audio_with_requests')
    def test_process_audio_with_openai_not_available(self, mock_process_with_requests):
        """OpenAIクライアント利用不可時のフォールバックテスト"""
        # モックを設定
        mock_process_with_requests.return_value = "Fallback response from requests"
        
        # OpenAIクライアントが利用不可に設定
        audio_client.OPENAI_CLIENT_AVAILABLE = False
        
        # 関数を実行
        result = audio_client.process_audio_with_openai(
            SAMPLE_AUDIO_URL,
            model="SambaNova/Whisper-Large-v3"
        )
        
        # アサーション
        assert result == "Fallback response from requests"
        mock_process_with_requests.assert_called_once()


class TestProcessAudioWithRequests:
    """requestsライブラリを使用した音声処理のテスト"""
    
    @mock.patch('audio_client.get_audio_data')
    @mock.patch('requests.post')
    def test_process_audio_with_requests_chat_model(self, mock_post, mock_get_audio_data):
        """チャットモデルでの音声処理テスト"""
        # モックを設定
        mock_get_audio_data.return_value = (SAMPLE_AUDIO_CONTENT, SAMPLE_AUDIO_FORMAT)
        mock_response = mock.Mock()
        mock_response.json.return_value = MOCK_CHAT_RESPONSE
        mock_post.return_value = mock_response
        
        # 関数を実行
        result = audio_client.process_audio_with_requests(
            SAMPLE_AUDIO_URL,
            prompt="What is in this recording?",
            model="gpt-4o-audio-preview"
        )
        
        # アサーション
        assert result == "This is a sample response from the audio chat model."
        mock_post.assert_called_once()
    
    @mock.patch('audio_client.get_audio_data')
    @mock.patch('requests.post')
    @mock.patch('tempfile.NamedTemporaryFile')
    @mock.patch('builtins.open', new_callable=mock.mock_open, read_data=SAMPLE_AUDIO_CONTENT)
    @mock.patch('os.path.exists')
    @mock.patch('os.remove')
    def test_process_audio_with_requests_transcription_model(self, mock_remove, mock_exists, mock_open, mock_temp_file, mock_post, mock_get_audio_data):
        """文字起こしモデルでの音声処理テスト"""
        # モックを設定
        mock_get_audio_data.return_value = (SAMPLE_AUDIO_CONTENT, SAMPLE_AUDIO_FORMAT)
        mock_response = mock.Mock()
        mock_response.json.return_value = MOCK_TRANSCRIPTION_RESPONSE
        mock_post.return_value = mock_response
        
        # 一時ファイルのモック
        mock_temp = mock.MagicMock()
        mock_temp.name = "/tmp/temp_audio.wav"
        mock_temp_file.return_value.__enter__.return_value = mock_temp
        mock_exists.return_value = True
        
        # 関数を実行
        result = audio_client.process_audio_with_requests(
            SAMPLE_AUDIO_URL,
            model="SambaNova/Whisper-Large-v3",
            language="ja"
        )
        
        # アサーション
        assert result == "Sample transcription text for testing."
        mock_post.assert_called_once()
        mock_remove.assert_called_once_with(mock_temp.name)
    
    @mock.patch('audio_client.get_audio_data')
    @mock.patch('requests.post')
    def test_process_audio_with_requests_error(self, mock_post, mock_get_audio_data):
        """requestsエラー時のテスト"""
        # モックを設定
        mock_get_audio_data.return_value = (SAMPLE_AUDIO_CONTENT, SAMPLE_AUDIO_FORMAT)
        mock_post.side_effect = requests.exceptions.RequestException("API request error")
        
        # 関数を実行
        result = audio_client.process_audio_with_requests(
            SAMPLE_AUDIO_URL,
            model="gpt-4o-audio-preview"
        )
        
        # アサーション
        assert result == ""


class TestIntegratedInterface:
    """統合インターフェースのテスト"""
    
    @mock.patch('audio_client.process_audio_with_openai')
    def test_process_audio_openai_mode(self, mock_process_with_openai):
        """OpenAIモードでの処理テスト"""
        # モックを設定
        mock_process_with_openai.return_value = "OpenAI client response"
        
        # OpenAIクライアントが利用可能なことを確認
        audio_client.OPENAI_CLIENT_AVAILABLE = True
        
        # 関数を実行
        result = audio_client.process_audio(
            SAMPLE_AUDIO_URL,
            prompt="Test prompt",
            model="SambaNova/Whisper-Large-v3",
            language="ja",
            client_type="openai"
        )
        
        # アサーション
        assert result == "OpenAI client response"
        mock_process_with_openai.assert_called_once_with(SAMPLE_AUDIO_URL, "Test prompt", "SambaNova/Whisper-Large-v3", "ja")
    
    @mock.patch('audio_client.process_audio_with_requests')
    def test_process_audio_requests_mode(self, mock_process_with_requests):
        """requestsモードでの処理テスト"""
        # モックを設定
        mock_process_with_requests.return_value = "Requests client response"
        
        # 関数を実行
        result = audio_client.process_audio(
            SAMPLE_AUDIO_URL,
            prompt="Test prompt",
            model="gpt-4o-audio-preview",
            language=None,
            client_type="requests"
        )
        
        # アサーション
        assert result == "Requests client response"
        mock_process_with_requests.assert_called_once_with(SAMPLE_AUDIO_URL, "Test prompt", "gpt-4o-audio-preview", None)
    
    @mock.patch('audio_client.process_audio_with_openai')
    def test_process_audio_auto_mode_with_openai(self, mock_process_with_openai):
        """自動モードでOpenAIクライアントが利用可能な場合のテスト"""
        # モックを設定
        mock_process_with_openai.return_value = "Auto mode - OpenAI client response"
        
        # OpenAIクライアントが利用可能なことを確認
        audio_client.OPENAI_CLIENT_AVAILABLE = True
        
        # 関数を実行
        result = audio_client.process_audio(
            SAMPLE_AUDIO_URL,
            model="SambaNova/Whisper-Large-v3",
            client_type="auto"
        )
        
        # アサーション
        assert result == "Auto mode - OpenAI client response"
        mock_process_with_openai.assert_called_once()
    
    @mock.patch('audio_client.process_audio_with_requests')
    def test_process_audio_auto_mode_without_openai(self, mock_process_with_requests):
        """自動モードでOpenAIクライアントが利用不可な場合のテスト"""
        # モックを設定
        mock_process_with_requests.return_value = "Auto mode - Requests client response"
        
        # OpenAIクライアントが利用不可に設定
        audio_client.OPENAI_CLIENT_AVAILABLE = False
        
        # 関数を実行
        result = audio_client.process_audio(
            SAMPLE_AUDIO_URL,
            model="SambaNova/Whisper-Large-v3",
            client_type="auto"
        )
        
        # アサーション
        assert result == "Auto mode - Requests client response"
        mock_process_with_requests.assert_called_once()


class TestCommandLineInterface:
    """コマンドラインインターフェースのテスト"""
    
    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('audio_client.process_audio')
    def test_main_function(self, mock_process_audio, mock_parse_args):
        """main関数のテスト"""
        # モックを設定
        args = mock.Mock()
        args.audio_path = SAMPLE_AUDIO_URL
        args.prompt = "Test prompt"
        args.model = "SambaNova/Whisper-Large-v3"
        args.language = "ja"
        args.client = "auto"
        mock_parse_args.return_value = args
        
        # 関数を実行
        audio_client.main()
        
        # アサーション
        mock_process_audio.assert_called_once_with(SAMPLE_AUDIO_URL, "Test prompt", "SambaNova/Whisper-Large-v3", "ja", "auto")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
