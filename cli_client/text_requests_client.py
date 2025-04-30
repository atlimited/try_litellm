#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
テキスト生成クライアント
requestsライブラリを使用してLiteLLM ProxyのOpenAI互換APIを呼び出す
"""

import requests
import json
import os
import sys

# LiteLLM Proxy APIのベースURL
BASE_URL = "http://0.0.0.0:4000/v1"

# APIキー（環境変数から取得するか、空文字列を使用）
API_KEY = os.environ.get("OPENAI_API_KEY", "")

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
    
    # エンドポイント
    endpoint = f"{BASE_URL}/chat/completions"
    
    # ヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    # APIキーが設定されている場合はヘッダーに追加
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    
    # リクエスト本文
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        # API呼び出し
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()  # エラーがあれば例外を発生
        
        # レスポンスをパース
        result = response.json()
        
        # テキスト応答を抽出
        if "choices" in result and len(result["choices"]) > 0:
            message = result["choices"][0]["message"]
            if "content" in message:
                text_response = message["content"]
                print(f"\n📝 回答:\n{text_response}")
                return text_response
        
        print(f"❌ テキスト回答が見つかりません: {result}")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        # デバッグ情報
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def main():
    """
    メイン関数：コマンドライン引数を解析して機能を実行
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='requestsを使用したテキスト生成クライアント')
    parser.add_argument('message', help='テキストプロンプト')
    parser.add_argument('--model', '-m', default=model_name, help='使用するモデル名')
    
    args = parser.parse_args()
    
    generate_text(args.message, args.model)

if __name__ == "__main__":
    main()
