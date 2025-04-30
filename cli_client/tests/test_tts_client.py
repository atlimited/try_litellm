#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
tts_client.pyのテストコード
"""

import os
import sys
import json
import time
from unittest import mock
from pathlib import Path

import pytest
import requests

# テスト対象のモジュールをインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tts_client

# モックレスポンス用のデータ
DUMMY_AUDIO_CONTENT = b"dummy audio content for testing"

# OpenAIクライアントのモッククラス
class MockOpenAIResponse:
    def stream_to_file(self, path):
        with open(path, "wb") as f:
            f.write(DUMMY_AUDIO_CONTENT)


class TestGenerateSpeechWithOpenAI:
    """OpenAIクライアントを使用した音声合成のテスト"""
    
    @mock.patch('tts_client.openai_client')
    @mock.patch('os.path.exists')
    def test_generate_speech_with_openai_success(self, mock_exists, mock_openai_client):
        """OpenAIクライアントでの音声合成成功ケースのテスト"""
        # モックを設定
        mock_exists.return_value = True
        mock_response = MockOpenAIResponse()
        mock_openai_client.audio.speech.create.return_value = mock_response
        
        # OpenAIクライアントが利用可能なことを確認
        tts_client.OPENAI_CLIENT_AVAILABLE = True
        
        # 一時的な出力パスを作成
        output_path = "test_output.mp3"
        
        # 関数を実行
        result = tts_client.generate_speech_with_openai(
            "テスト音声です",
            voice="alloy",
            model="OpenAI/tts-1",
            output_path=output_path
        )
        
        # アサーション
        assert result == output_path
        mock_openai_client.audio.speech.create.assert_called_once_with(
            model="OpenAI/tts-1",
            voice="alloy",
            input="テスト音声です"
        )
    
    @mock.patch('tts_client.openai_client')
    @mock.patch('tts_client.generate_speech_with_requests')
    def test_generate_speech_with_openai_error_fallback(self, mock_generate_with_requests, mock_openai_client):
        """OpenAIクライアントエラー時のフォールバックテスト"""
        # モックを設定
        mock_openai_client.audio.speech.create.side_effect = Exception("OpenAI client error")
        mock_generate_with_requests.return_value = "fallback_output.mp3"
        
        # OpenAIクライアントが利用可能なことを確認
        tts_client.OPENAI_CLIENT_AVAILABLE = True
        
        # 関数を実行
        result = tts_client.generate_speech_with_openai(
            "テスト音声です",
            voice="alloy",
            model="OpenAI/tts-1"
        )
        
        # アサーション
        assert result == "fallback_output.mp3"
        mock_generate_with_requests.assert_called_once()
    
    @mock.patch('tts_client.generate_speech_with_requests')
    def test_generate_speech_with_openai_not_available(self, mock_generate_with_requests):
        """OpenAIクライアント利用不可時のテスト"""
        # モックを設定
        mock_generate_with_requests.return_value = "fallback_output.mp3"
        
        # OpenAIクライアントが利用不可に設定
        tts_client.OPENAI_CLIENT_AVAILABLE = False
        
        # 関数を実行
        result = tts_client.generate_speech_with_openai(
            "テスト音声です",
            voice="alloy",
            model="OpenAI/tts-1"
        )
        
        # アサーション
        assert result == "fallback_output.mp3"
        mock_generate_with_requests.assert_called_once()


class TestGenerateSpeechWithRequests:
    """requestsライブラリを使用した音声合成のテスト"""
    
    @mock.patch('requests.post')
    @mock.patch('builtins.open', new_callable=mock.mock_open)
    def test_generate_speech_with_requests_success(self, mock_file, mock_post):
        """requestsライブラリでの音声合成成功ケースのテスト"""
        # モックレスポンスを設定
        mock_response = mock.Mock()
        mock_response.content = DUMMY_AUDIO_CONTENT
        mock_post.return_value = mock_response
        
        # 一時的な出力パスを作成
        output_path = "test_output.mp3"
        
        # 関数を実行
        result = tts_client.generate_speech_with_requests(
            "テスト音声です",
            voice="alloy",
            model="OpenAI/tts-1",
            output_path=output_path
        )
        
        # アサーション
        assert result == output_path
        mock_post.assert_called_once()
        expected_payload = {
            "model": "OpenAI/tts-1",
            "voice": "alloy",
            "input": "テスト音声です"
        }
        # ペイロードの確認
        actual_payload = mock_post.call_args[1]['json']
        assert actual_payload == expected_payload
        
        # ファイルに書き込まれたコンテンツを確認
        mock_file().write.assert_called_once_with(DUMMY_AUDIO_CONTENT)
    
    @mock.patch('requests.post')
    def test_generate_speech_with_requests_error(self, mock_post):
        """requestsエラー時のテスト"""
        # モックを設定
        mock_post.side_effect = requests.exceptions.RequestException("API request error")
        
        # 関数を実行
        result = tts_client.generate_speech_with_requests(
            "テスト音声です",
            voice="alloy",
            model="OpenAI/tts-1"
        )
        
        # アサーション
        assert result == ""


class TestIntegratedInterface:
    """統合インターフェースのテスト"""
    
    @mock.patch('tts_client.generate_speech_with_openai')
    def test_generate_speech_openai_mode(self, mock_generate_with_openai):
        """OpenAIモードでの処理テスト"""
        # モックを設定
        mock_generate_with_openai.return_value = "openai_output.mp3"
        
        # OpenAIクライアントが利用可能なことを確認
        tts_client.OPENAI_CLIENT_AVAILABLE = True
        
        # 関数を実行
        result = tts_client.generate_speech(
            "テスト音声です",
            voice="alloy",
            model="OpenAI/tts-1",
            output_path="test_output.mp3",
            client_type="openai"
        )
        
        # アサーション
        assert result == "openai_output.mp3"
        mock_generate_with_openai.assert_called_once_with(
            "テスト音声です", "alloy", "OpenAI/tts-1", "test_output.mp3"
        )
    
    @mock.patch('tts_client.generate_speech_with_requests')
    def test_generate_speech_requests_mode(self, mock_generate_with_requests):
        """requestsモードでの処理テスト"""
        # モックを設定
        mock_generate_with_requests.return_value = "requests_output.mp3"
        
        # 関数を実行
        result = tts_client.generate_speech(
            "テスト音声です",
            voice="alloy",
            model="OpenAI/tts-1",
            output_path="test_output.mp3",
            client_type="requests"
        )
        
        # アサーション
        assert result == "requests_output.mp3"
        mock_generate_with_requests.assert_called_once_with(
            "テスト音声です", "alloy", "OpenAI/tts-1", "test_output.mp3"
        )
    
    @mock.patch('tts_client.generate_speech_with_openai')
    def test_generate_speech_auto_mode_with_openai(self, mock_generate_with_openai):
        """自動モードでOpenAIクライアントが利用可能な場合のテスト"""
        # モックを設定
        mock_generate_with_openai.return_value = "auto_openai_output.mp3"
        
        # OpenAIクライアントが利用可能なことを確認
        tts_client.OPENAI_CLIENT_AVAILABLE = True
        
        # 関数を実行
        result = tts_client.generate_speech(
            "テスト音声です",
            voice="alloy",
            model="OpenAI/tts-1",
            output_path=None,
            client_type="auto"
        )
        
        # アサーション
        assert result == "auto_openai_output.mp3"
        mock_generate_with_openai.assert_called_once()
    
    @mock.patch('tts_client.generate_speech_with_requests')
    def test_generate_speech_auto_mode_without_openai(self, mock_generate_with_requests):
        """自動モードでOpenAIクライアントが利用不可な場合のテスト"""
        # モックを設定
        mock_generate_with_requests.return_value = "auto_requests_output.mp3"
        
        # OpenAIクライアントが利用不可に設定
        tts_client.OPENAI_CLIENT_AVAILABLE = False
        
        # 関数を実行
        result = tts_client.generate_speech(
            "テスト音声です",
            voice="alloy",
            model="OpenAI/tts-1",
            output_path=None,
            client_type="auto"
        )
        
        # アサーション
        assert result == "auto_requests_output.mp3"
        mock_generate_with_requests.assert_called_once()


class TestCommandLineInterface:
    """コマンドラインインターフェースのテスト"""
    
    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('tts_client.generate_speech')
    def test_main_function(self, mock_generate_speech, mock_parse_args):
        """main関数のテスト"""
        # モックを設定
        args = mock.Mock()
        args.text = "テスト音声です"
        args.voice = "alloy"
        args.model = "OpenAI/tts-1"
        args.output = "test_output.mp3"
        args.client = "auto"
        mock_parse_args.return_value = args
        mock_generate_speech.return_value = "test_output.mp3"
        
        # 関数を実行
        tts_client.main()
        
        # アサーション
        mock_generate_speech.assert_called_once_with(
            "テスト音声です", "alloy", "OpenAI/tts-1", "test_output.mp3", "auto"
        )


if __name__ == "__main__":
    pytest.main(["-v", __file__])
