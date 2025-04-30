#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
テキスト生成クライアント (統合版)
OpenAIクライアントまたはrequestsライブラリを使用してLiteLLM ProxyのOpenAI互換APIを呼び出す
ユーザーはクライアントタイプ（openai/requests）を選択できます
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any, Union

# OpenAIクライアントのインポート (optional)
try:
    from openai import OpenAI
    OPENAI_CLIENT_AVAILABLE = True
except ImportError:
    OPENAI_CLIENT_AVAILABLE = False
    print("OpenAIクライアントライブラリがインストールされていません。requestsモードのみ使用可能です。")

# LiteLLM Proxy APIのベースURL
BASE_URL = "http://0.0.0.0:4000/v1"

# APIキー（環境変数から取得するか、空文字列を使用）
API_KEY = os.environ.get("OPENAI_API_KEY", "")

# モデル選択（使用したいモデルのコメントを外す）
#model_name = "OpenAI/gpt-4o-mini"
#model_name = "Google/gemini-2.0-flash"
model_name = "SambaNova/Meta-Llama-3.2-3B-Instruct"
#model_name = "SambaNova/Llama-4-Maverick-17B-128E-Instruct"

# OpenAIクライアントのインスタンス（利用可能な場合）
openai_client = None
if OPENAI_CLIENT_AVAILABLE:
    openai_client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )

def generate_text_with_openai(prompt: str, model: str = model_name) -> str:
    """
    OpenAIクライアントを使用してテキスト生成リクエストを送信
    
    Args:
        prompt: ユーザーからのプロンプト
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト
    """
    if not OPENAI_CLIENT_AVAILABLE or openai_client is None:
        print("❌ OpenAIクライアントが利用できません。requestsモードに切り替えます。")
        return generate_text_with_requests(prompt, model)
    
    try:
        # OpenAIクライアントを使用してリクエスト送信
        response = openai_client.chat.completions.create(
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
            return text_response
        
        print(f"❌ テキスト回答が見つかりません: {response}")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        # エラー発生時はrequestsモードに切り替える
        print("↪️ requestsモードで再試行します")
        return generate_text_with_requests(prompt, model)

def generate_text_with_requests(prompt: str, model: str = model_name) -> str:
    """
    requestsライブラリを使用してテキスト生成リクエストを送信
    
    Args:
        prompt: ユーザーからのプロンプト
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト
    """
    try:
        # エンドポイント
        endpoint = f"{BASE_URL}/chat/completions"
        
        # ヘッダー
        headers = {
            "Content-Type": "application/json"
        }
        
        # APIキーが設定されている場合はヘッダーに追加
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        
        # リクエスト本文 - モデルに応じて形式を調整
        if "Google/gemini" in model:
            # Gemini用のリクエスト形式
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        else:
            # 通常のリクエスト形式
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        
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
                return text_response
        
        print(f"❌ テキスト回答が見つかりません: {result}")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        # デバッグ情報
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def generate_text(prompt: str, model: str = model_name, client_type: str = "auto") -> str:
    """
    テキスト生成リクエストを送信（統合インターフェース）
    
    Args:
        prompt: ユーザーからのプロンプト
        model: 使用するモデル名
        client_type: クライアントタイプ（openai/requests/auto）
        
    Returns:
        生成されたテキスト
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print(f"🔧 クライアントタイプ: {client_type}")
    print("🔄 応答を生成中...")
    
    if client_type == "openai" and OPENAI_CLIENT_AVAILABLE:
        result = generate_text_with_openai(prompt, model)
    elif client_type == "requests" or not OPENAI_CLIENT_AVAILABLE:
        result = generate_text_with_requests(prompt, model)
    else:  # auto
        # OpenAIクライアントが利用可能ならそれを使用、そうでなければrequests
        if OPENAI_CLIENT_AVAILABLE:
            result = generate_text_with_openai(prompt, model)
        else:
            result = generate_text_with_requests(prompt, model)
    
    print(f"\n📝 回答:\n{result}")
    return result

def main():
    """
    メイン関数：コマンドライン引数を解析して機能を実行
    """
    parser = argparse.ArgumentParser(description='統合テキスト生成クライアント')
    parser.add_argument('message', help='テキストプロンプト')
    parser.add_argument('--model', '-m', default=model_name, help='使用するモデル名')
    parser.add_argument('--client', '-c', choices=['openai', 'requests', 'auto'], default='auto',
                       help='使用するクライアントタイプ（openai/requests/auto）')
    
    args = parser.parse_args()
    
    generate_text(args.message, args.model, args.client)

if __name__ == "__main__":
    main()
