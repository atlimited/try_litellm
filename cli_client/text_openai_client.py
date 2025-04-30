#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
テキスト生成クライアント
OpenAIクライアントライブラリを使用してLiteLLM ProxyのOpenAI互換APIを呼び出す
"""

import os
import sys
import json
import argparse
from openai import OpenAI

# LiteLLM Proxy APIのベースURL
BASE_URL = "http://0.0.0.0:4000/v1"

# APIキー（環境変数から取得するか、空文字列を使用）
API_KEY = os.environ.get("OPENAI_API_KEY", "")

# OpenAIクライアントの初期化
client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

# モデル選択（使用したいモデルのコメントを外す）
#model_name = "OpenAI/gpt-4o-mini"
#model_name = "Google/gemini-2.0-flash"
model_name = "SambaNova/Meta-Llama-3.2-3B-Instruct"
#model_name = "SambaNova/Llama-4-Maverick-17B-128E-Instruct"

def generate_text(prompt, model=model_name):
    """
    テキスト生成リクエストを送信
    
    Args:
        prompt: ユーザーからのプロンプト
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print("🔄 応答を生成中...")
    
    try:
        # OpenAIクライアントを使用してリクエスト送信
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        
        # レスポンスから応答テキストを取得
        if response.choices and len(response.choices) > 0:
            text_response = response.choices[0].message.content
            print(f"\n📝 回答:\n{text_response}")
            return text_response
        
        print(f"❌ テキスト回答が見つかりません: {response}")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return ""

def main():
    """
    メイン関数：コマンドライン引数を解析して機能を実行
    """
    parser = argparse.ArgumentParser(description='OpenAIクライアントを使用したテキスト生成')
    parser.add_argument('message', help='テキストプロンプト')
    parser.add_argument('--model', '-m', default=model_name, help='使用するモデル名')
    
    args = parser.parse_args()
    
    generate_text(args.message, args.model)

if __name__ == "__main__":
    main()