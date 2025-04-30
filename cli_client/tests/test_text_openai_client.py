#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
text_openai_client.pyのテストコード
"""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

# テスト対象のモジュールをインポートするためのパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# テスト対象のモジュールをインポート
import text_openai_client


class TestOpenAIClient:
    @patch('text_openai_client.client.chat.completions.create')
    def test_generate_text_success(self, mock_create):
        """テキスト生成機能の正常系テスト"""
        # モックレスポンスの設定
        mock_choice = MagicMock()
        mock_choice.message.content = "こんにちは！お手伝いできることはありますか？"
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_create.return_value = mock_response
        
        # テスト実行
        result = text_openai_client.generate_text("こんにちは", "SambaNova/Meta-Llama-3.2-3B-Instruct")
        
        # 検証
        assert result == "こんにちは！お手伝いできることはありますか？"
        mock_create.assert_called_once()
        
        # リクエストパラメータの検証
        call_args = mock_create.call_args
        kwargs = call_args[1]
        assert kwargs['model'] == "SambaNova/Meta-Llama-3.2-3B-Instruct"
        assert kwargs['messages'][0]['role'] == "user"
        assert kwargs['messages'][0]['content'] == "こんにちは"

    @patch('text_openai_client.client.chat.completions.create')
    def test_generate_text_empty_response(self, mock_create):
        """テキスト生成機能のレスポンス空テスト"""
        # 空の応答をシミュレート
        mock_response = MagicMock()
        mock_response.choices = []
        mock_create.return_value = mock_response
        
        # テスト実行
        result = text_openai_client.generate_text("こんにちは")
        
        # 検証
        assert result == ""
        mock_create.assert_called_once()

    @patch('text_openai_client.client.chat.completions.create')
    def test_generate_text_error(self, mock_create):
        """テキスト生成機能のエラー系テスト"""
        # APIエラーをシミュレート
        mock_create.side_effect = Exception("API Error")
        
        # テスト実行
        result = text_openai_client.generate_text("エラーを発生させるプロンプト")
        
        # 検証
        assert result == ""
        mock_create.assert_called_once()

    @patch('text_openai_client.generate_text')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_function(self, mock_parse_args, mock_generate_text):
        """main関数のテスト"""
        # ArgumentParserの戻り値をモック
        mock_args = MagicMock()
        mock_args.message = "こんにちは"
        mock_args.model = "SambaNova/Meta-Llama-3.2-3B-Instruct"
        mock_parse_args.return_value = mock_args
        
        # generate_textの戻り値をモック
        mock_generate_text.return_value = "こんにちは！お手伝いできることはありますか？"
        
        # テスト実行
        text_openai_client.main()
        
        # 検証
        mock_generate_text.assert_called_once_with("こんにちは", "SambaNova/Meta-Llama-3.2-3B-Instruct")


if __name__ == "__main__":
    pytest.main(["-v", "test_text_openai_client.py"])
