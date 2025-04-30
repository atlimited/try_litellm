#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
画像認識クライアント (統合版)
OpenAIクライアントまたはrequestsライブラリを使用してLiteLLM ProxyのOpenAI互換APIを呼び出す
ユーザーはクライアントタイプ（openai/requests）を選択できます
"""

import os
import sys
import json
import argparse
import requests
import base64
from typing import Optional, Dict, Any, Union, List

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
model_name = "Google/gemini-2.0-flash"
#model_name = "SambaNova/Llama-4-Maverick-17B-128E-Instruct"

# OpenAIクライアントのインスタンス（利用可能な場合）
openai_client = None
if OPENAI_CLIENT_AVAILABLE:
    openai_client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )

def get_base64_encoded_image(image_url: str) -> str:
    """
    画像URLからBase64エンコードされた画像を取得
    
    Args:
        image_url: 画像のURL（ローカルファイルパスも可）
        
    Returns:
        Base64エンコードされた画像データ（data URLスキーム形式）
    """
    # URLがhttpまたはhttpsで始まるか確認
    if image_url.startswith(('http://', 'https://')):
        # URLから画像をダウンロード
        response = requests.get(image_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download image: {response.status_code}")
        image_content = response.content
    else:
        # ローカルファイルとして読み込み
        with open(image_url, 'rb') as image_file:
            image_content = image_file.read()
    
    # 画像のMIMEタイプを判断（単純化のためURLから拡張子を抽出）
    extension = image_url.split('.')[-1].lower()
    if extension in ['jpg', 'jpeg']:
        mime_type = 'image/jpeg'
    elif extension == 'png':
        mime_type = 'image/png'
    elif extension == 'webp':
        mime_type = 'image/webp'
    else:
        mime_type = 'image/jpeg'  # デフォルト
    
    # Base64エンコード
    base64_image = base64.b64encode(image_content).decode('utf-8')
    
    # 適切な形式で返す
    return f"data:{mime_type};base64,{base64_image}"

def analyze_image_with_openai(image_url: str, prompt: str, model: str = model_name) -> str:
    """
    OpenAIクライアントを使用して画像分析リクエストを送信
    
    Args:
        image_url: 分析する画像のURL
        prompt: 画像に関する質問や指示
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト回答
    """
    if not OPENAI_CLIENT_AVAILABLE or openai_client is None:
        print("❌ OpenAIクライアントが利用できません。requestsモードに切り替えます。")
        return analyze_image_with_requests(image_url, prompt, model)
    
    try:
        # 画像をBase64エンコード
        base64_image = get_base64_encoded_image(image_url)
        
        # OpenAIクライアントを使用してリクエスト送信
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": base64_image
                            }
                        }
                    ]
                }
            ]
        )
        
        # レスポンスから応答テキストを取得
        if response.choices and len(response.choices) > 0:
            text_response = response.choices[0].message.content
            return text_response
        
        print(f"❌ テキスト回答が見つかりません: {response}")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        # デバッグ情報
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        # エラー発生時はrequestsモードに切り替える
        print("↪️ requestsモードで再試行します")
        return analyze_image_with_requests(image_url, prompt, model)

def analyze_image_with_requests(image_url: str, prompt: str, model: str = model_name) -> str:
    """
    requestsライブラリを使用して画像分析リクエストを送信
    
    Args:
        image_url: 分析する画像のURL
        prompt: 画像に関する質問や指示
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト回答
    """
    try:
        # 画像をBase64エンコード
        base64_image = get_base64_encoded_image(image_url)
        
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
            # Gemini用のリクエスト形式（contentが配列形式）
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": base64_image
                                }
                            }
                        ]
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
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": base64_image
                                }
                            }
                        ]
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

def analyze_image(image_url: str, prompt: str, model: str = model_name, client_type: str = "auto") -> str:
    """
    画像分析リクエストを送信（統合インターフェース）
    
    Args:
        image_url: 分析する画像のURL
        prompt: 画像に関する質問や指示
        model: 使用するモデル名
        client_type: クライアントタイプ（openai/requests/auto）
        
    Returns:
        生成されたテキスト回答
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🖼️ 画像URL: {image_url}")
    print(f"🤖 モデル: {model}")
    print(f"🔧 クライアントタイプ: {client_type}")
    print("🔄 応答を生成中...")
    
    if client_type == "openai" and OPENAI_CLIENT_AVAILABLE:
        result = analyze_image_with_openai(image_url, prompt, model)
    elif client_type == "requests" or not OPENAI_CLIENT_AVAILABLE:
        result = analyze_image_with_requests(image_url, prompt, model)
    else:  # auto
        # OpenAIクライアントが利用可能ならそれを使用、そうでなければrequests
        if OPENAI_CLIENT_AVAILABLE:
            result = analyze_image_with_openai(image_url, prompt, model)
        else:
            result = analyze_image_with_requests(image_url, prompt, model)
    
    print(f"\n📝 回答:\n{result}")
    return result

def main():
    """
    メイン関数：コマンドライン引数を解析して機能を実行
    """
    parser = argparse.ArgumentParser(description='統合画像認識クライアント')
    parser.add_argument('image_url', help='分析する画像のURL')
    parser.add_argument('--prompt', '-p', help='画像に関する質問や指示', default="What's in this image?")
    parser.add_argument('--model', '-m', default=model_name, help='使用するモデル名')
    parser.add_argument('--client', '-c', choices=['openai', 'requests', 'auto'], default='auto',
                       help='使用するクライアントタイプ（openai/requests/auto）')
    
    args = parser.parse_args()
    
    analyze_image(args.image_url, args.prompt, args.model, args.client)

if __name__ == "__main__":
    main()
