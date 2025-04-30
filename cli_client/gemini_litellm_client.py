#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Geminiクライアント (統合版)
OpenAIクライアントまたはrequestsライブラリを使用してLiteLLM ProxyのOpenAI互換APIを呼び出す
ユーザーはクライアントタイプ（openai/requests）を選択できます
"""

import os
import sys
import json
import base64
import argparse
import requests
from PIL import Image
import io
import re
from pathlib import Path
from typing import Optional, Dict, Any, Union, List

# OpenAIクライアントのインポート (optional)
try:
    from openai import OpenAI
    OPENAI_CLIENT_AVAILABLE = True
except ImportError:
    OPENAI_CLIENT_AVAILABLE = False
    print("OpenAIクライアントライブラリがインストールされていません。requestsモードのみ使用可能です。")

# 環境変数からAPIキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# LiteLLM Proxy APIのベースURL
BASE_URL = "http://0.0.0.0:4000/v1"

# OpenAIクライアントのインスタンス（利用可能な場合）
openai_client = None
if OPENAI_CLIENT_AVAILABLE:
    openai_client = OpenAI(
        base_url=BASE_URL,
        api_key=GEMINI_API_KEY
    )

def chat_with_openai(prompt: str, model: str = "Google/gemini-2.0-flash") -> str:
    """
    OpenAIクライアントを使用してAIモデルとチャットする（テキストのみ）
    
    Args:
        prompt: チャットプロンプト
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト回答
    """
    try:
        # OpenAIクライアントを使用してリクエストを送信
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # レスポンスからテキストを抽出
        if response.choices and len(response.choices) > 0:
            text_response = response.choices[0].message.content
            print("\n📝 回答:")
            print(text_response)
            return text_response
        else:
            print("❌ 応答が見つかりません")
            return ""
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return ""

def chat_with_requests(prompt: str, model: str = "Google/gemini-2.0-flash") -> str:
    """
    requestsライブラリを使用してAIモデルとチャットする（テキストのみ）
    
    Args:
        prompt: チャットプロンプト
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト回答
    """
    try:
        # LiteLLMプロキシのエンドポイント
        url = f"{BASE_URL}/chat/completions"
        
        # ヘッダー
        headers = {
            "Content-Type": "application/json"
        }
        
        # APIキーが設定されている場合はヘッダーに追加
        if GEMINI_API_KEY:
            headers["Authorization"] = f"Bearer {GEMINI_API_KEY}"
        
        # ペイロード
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        }
        
        # LiteLLMプロキシAPIを呼び出す
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # レスポンスをパース
        result = response.json()
        
        # テキスト応答を抽出
        if "choices" in result and len(result["choices"]) > 0:
            text_response = result["choices"][0]["message"]["content"]
            print("\n📝 回答:")
            print(text_response)
            return text_response
        else:
            print("❌ 応答が見つかりません")
            return ""
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def chat(prompt: str, model: str = "Google/gemini-2.0-flash", client_type: str = "auto") -> str:
    """
    AIモデルとチャットをする（テキストのみ）- 統合インターフェース
    
    Args:
        prompt: チャットプロンプト
        model: 使用するモデル名
        client_type: クライアントタイプ（openai/requests/auto）
        
    Returns:
        生成されたテキスト回答
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print(f"🔧 クライアントタイプ: {client_type}")
    print("🔄 応答を生成中...")
    
    if client_type == "openai" and OPENAI_CLIENT_AVAILABLE:
        return chat_with_openai(prompt, model)
    elif client_type == "requests" or not OPENAI_CLIENT_AVAILABLE:
        return chat_with_requests(prompt, model)
    else:  # auto
        try:
            # まずrequestsクライアントを試す
            return chat_with_requests(prompt, model)
        except Exception as e:
            print(f"❌ requestsクライアントでエラーが発生しました: {str(e)}")
            print("↪️ OpenAIクライアントで再試行します")
            
            # OpenAIクライアントが利用可能ならフォールバック
            if OPENAI_CLIENT_AVAILABLE:
                return chat_with_openai(prompt, model)
            else:
                print("❌ OpenAIクライアントが利用できません")
                return ""

def encode_image_to_base64(image_path: str) -> str:
    """
    画像をBase64エンコードする
    
    Args:
        image_path: 画像ファイルのパス
        
    Returns:
        Base64エンコードされた画像データ
    """
    try:
        # 画像ファイルを開く
        with open(image_path, "rb") as image_file:
            # 画像データを読み込む
            image_data = image_file.read()
            
            # 画像形式を検出
            try:
                image = Image.open(io.BytesIO(image_data))
                image_format = image.format.lower()
            except Exception:
                # 画像形式を検出できない場合はjpegと仮定
                image_format = "jpeg"
            
            # Base64エンコード
            base64_data = base64.b64encode(image_data).decode("utf-8")
            
            # 正しいMIMEタイプでフォーマット
            return f"data:image/{image_format};base64,{base64_data}"
            
    except Exception as e:
        print(f"❌ 画像のエンコード中にエラーが発生しました: {str(e)}")
        return ""

def analyze_image_with_openai(image_path: str, prompt: str = "これはなんの画像ですか", model: str = "Google/gemini-2.0-flash") -> str:
    """
    OpenAIクライアントを使用して画像を分析する
    
    Args:
        image_path: 分析する画像のパス
        prompt: 画像に関する質問や指示
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト回答
    """
    try:
        # 画像をBase64エンコード
        base64_image = encode_image_to_base64(image_path)
        
        if not base64_image:
            print("❌ 画像のエンコードに失敗しました")
            return ""
        
        # OpenAIクライアントを使用してリクエストを送信
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": base64_image}
                        }
                    ]
                }
            ]
        )
        
        # レスポンスからテキストを抽出
        if response.choices and len(response.choices) > 0:
            text_response = response.choices[0].message.content
            print("\n📝 回答:")
            print(text_response)
            return text_response
        else:
            print("❌ 応答が見つかりません")
            return ""
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return ""

def analyze_image_with_requests(image_path: str, prompt: str = "これはなんの画像ですか", model: str = "Google/gemini-2.0-flash") -> str:
    """
    requestsライブラリを使用して画像を分析する
    
    Args:
        image_path: 分析する画像のパス
        prompt: 画像に関する質問や指示
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト回答
    """
    try:
        # 画像をBase64エンコード
        base64_image = encode_image_to_base64(image_path)
        
        if not base64_image:
            print("❌ 画像のエンコードに失敗しました")
            return ""
        
        # LiteLLMプロキシのエンドポイント
        url = f"{BASE_URL}/chat/completions"
        
        # ヘッダー
        headers = {
            "Content-Type": "application/json"
        }
        
        # APIキーが設定されている場合はヘッダーに追加
        if GEMINI_API_KEY:
            headers["Authorization"] = f"Bearer {GEMINI_API_KEY}"
        
        # Geminiのマルチモーダル入力用ペイロード
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
            ],
            "modalities": ["image", "text"]  # モダリティパラメータを追加
        }
        
        try:
            # LiteLLMプロキシAPIを呼び出す
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # レスポンスをパース
            result = response.json()
            
            # テキスト応答を抽出
            if "choices" in result and len(result["choices"]) > 0:
                text_response = result["choices"][0]["message"]["content"]
                print("\n📝 回答:")
                print(text_response)
                return text_response
            else:
                print("❌ 応答が見つかりません")
                return ""
                
        except Exception as e:
            print(f"❌ エラーが発生しました: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"レスポンス: {e.response.text}")
            return ""
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return ""

def analyze_image(image_path: str, prompt: str = "これはなんの画像ですか", model: str = "Google/gemini-2.0-flash", client_type: str = "auto") -> str:
    """
    画像とテキストプロンプトを使用して応答を生成する - 統合インターフェース
    
    Args:
        image_path: 分析する画像のパス
        prompt: 画像に関する質問や指示
        model: 使用するモデル名
        client_type: クライアントタイプ（openai/requests/auto）
        
    Returns:
        生成されたテキスト回答
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🖼️ 画像: {image_path}")
    print(f"🤖 モデル: {model}")
    print(f"🔧 クライアントタイプ: {client_type}")
    print("🔄 画像を分析中...")
    
    if client_type == "openai" and OPENAI_CLIENT_AVAILABLE:
        return analyze_image_with_openai(image_path, prompt, model)
    elif client_type == "requests" or not OPENAI_CLIENT_AVAILABLE:
        return analyze_image_with_requests(image_path, prompt, model)
    else:  # auto
        try:
            # まずrequestsクライアントを試す
            return analyze_image_with_requests(image_path, prompt, model)
        except Exception as e:
            print(f"❌ requestsクライアントでエラーが発生しました: {str(e)}")
            print("↪️ OpenAIクライアントで再試行します")
            
            # OpenAIクライアントが利用可能ならフォールバック
            if OPENAI_CLIENT_AVAILABLE:
                return analyze_image_with_openai(image_path, prompt, model)
            else:
                print("❌ OpenAIクライアントが利用できません")
                return ""

def main():
    """コマンドライン引数を解析して機能を実行"""
    parser = argparse.ArgumentParser(description='Gemini API クライアント')
    subparsers = parser.add_subparsers(dest='command', help='サブコマンド')
    
    # チャットサブコマンド
    chat_parser = subparsers.add_parser('chat', help='テキストチャット')
    chat_parser.add_argument('prompt', help='チャットプロンプト')
    chat_parser.add_argument('--model', default="Google/gemini-2.0-flash", help='使用するモデル名')
    chat_parser.add_argument('--client', choices=['openai', 'requests', 'auto'], default='auto', 
                             help='クライアントタイプ (openai/requests/auto)')
    
    # 画像認識サブコマンド
    vision_parser = subparsers.add_parser('vision', help='画像認識')
    vision_parser.add_argument('prompt', help='画像に関する質問や指示')
    vision_parser.add_argument('image', help='分析する画像のパス')
    vision_parser.add_argument('--model', default="Google/gemini-2.0-flash", help='使用するモデル名')
    vision_parser.add_argument('--client', choices=['openai', 'requests', 'auto'], default='auto', 
                             help='クライアントタイプ (openai/requests/auto)')
    
    args = parser.parse_args()
    
    if args.command == 'chat':
        chat(args.prompt, args.model, args.client)
    elif args.command == 'vision':
        analyze_image(args.image, args.prompt, args.model, args.client)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
