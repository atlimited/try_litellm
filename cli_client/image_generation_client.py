#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
画像生成クライアント (統合版)
OpenAIクライアントまたはrequestsライブラリを使用してLiteLLM ProxyのOpenAI互換APIを呼び出す
ユーザーはクライアントタイプ（openai/requests）を選択できます
"""

import os
import sys
import json
import argparse
import requests
import time
from pathlib import Path
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
model_name = "OpenAI/dall-e-3"

# 出力ディレクトリの設定
output_dir = Path("./generated_images")
output_dir.mkdir(exist_ok=True)

# OpenAIクライアントのインスタンス（利用可能な場合）
openai_client = None
if OPENAI_CLIENT_AVAILABLE:
    openai_client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )

def save_image_from_url(image_url: str) -> str:
    """
    画像URLから画像をダウンロードして保存
    
    Args:
        image_url: 画像のURL
        
    Returns:
        保存されたファイルのパス
    """
    try:
        # 画像のダウンロード
        image_response = requests.get(image_url)
        
        if image_response.status_code == 200:
            # タイムスタンプを使ってユニークなファイル名を生成
            timestamp = int(time.time())
            image_path = output_dir / f"generated_image_{timestamp}.png"
            
            # 画像の保存
            with open(image_path, "wb") as f:
                f.write(image_response.content)
            
            print(f"✅ 画像が保存されました: {image_path}")
            return str(image_path)
        else:
            print(f"❌ 画像のダウンロードに失敗しました: ステータスコード {image_response.status_code}")
            return ""
            
    except Exception as e:
        print(f"❌ 画像の保存中にエラーが発生しました: {e}")
        return ""

def generate_image_with_openai(prompt: str, model: str = model_name, size: str = "1024x1024", quality: str = "standard", save_image: bool = True) -> str:
    """
    OpenAIクライアントを使用して画像生成リクエストを送信
    
    Args:
        prompt: 画像生成のプロンプト
        model: 使用するモデル名
        size: 画像サイズ (例: "1024x1024")
        quality: 画像品質 (例: "standard", "hd")
        save_image: 画像を保存するかどうか
        
    Returns:
        生成された画像のURL
    """
    if not OPENAI_CLIENT_AVAILABLE or openai_client is None:
        print("❌ OpenAIクライアントが利用できません。requestsモードに切り替えます。")
        return generate_image_with_requests(prompt, model, size, quality, save_image)
    
    try:
        # モデル名からプロバイダー接頭辞を削除（LiteLLMプロキシ用）
        actual_model = model.split("/")[-1] if "/" in model else model
        
        # OpenAIクライアントを使用してリクエスト送信
        response = openai_client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size=size,
            quality=quality,
            response_format="url",
        )
        
        # 画像URLを取得
        image_url = response.data[0].url
        print(f"🖼️ 画像URL: {image_url}")
        
        # 画像をダウンロードして保存（オプション）
        if save_image:
            save_image_from_url(image_url)
        
        return image_url
        
    except Exception as e:
        print(f"❌ OpenAIクライアントでエラーが発生しました: {str(e)}")
        print("↪️ requestsモードで再試行します")
        return generate_image_with_requests(prompt, model, size, quality, save_image)

def generate_image_with_requests(prompt: str, model: str = model_name, size: str = "1024x1024", quality: str = "standard", save_image: bool = True) -> str:
    """
    requestsライブラリを使用して画像生成リクエストを送信
    
    Args:
        prompt: 画像生成のプロンプト
        model: 使用するモデル名
        size: 画像サイズ (例: "1024x1024")
        quality: 画像品質 (例: "standard", "hd")
        save_image: 画像を保存するかどうか
        
    Returns:
        生成された画像のURL
    """
    try:
        # エンドポイント
        endpoint = f"{BASE_URL}/images/generations"
        
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
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "response_format": "url"
        }
        
        # Geminiモデルの場合の特別処理
        if "Google/gemini" in model:
            payload["modalities"] = ["image"]  # Geminiモデルの場合はmodalitiesパラメータが必要
            
        # API呼び出し
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()  # エラーがあれば例外を発生
        
        # レスポンスをパース
        result = response.json()
        
        # 画像URLを取得
        if "data" in result and len(result["data"]) > 0 and "url" in result["data"][0]:
            image_url = result["data"][0]["url"]
            print(f"🖼️ 画像URL: {image_url}")
            
            # 画像をダウンロードして保存（オプション）
            if save_image:
                save_image_from_url(image_url)
            
            return image_url
        
        print(f"❌ 画像URLが見つかりません: {result}")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        # デバッグ情報
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def generate_image(prompt: str, model: str = model_name, size: str = "1024x1024", quality: str = "standard", save_image: bool = True, client_type: str = "auto") -> str:
    """
    画像生成リクエストを送信（統合インターフェース）
    
    Args:
        prompt: 画像生成のプロンプト
        model: 使用するモデル名
        size: 画像サイズ (例: "1024x1024")
        quality: 画像品質 (例: "standard", "hd")
        save_image: 画像を保存するかどうか
        client_type: クライアントタイプ（openai/requests/auto）
        
    Returns:
        生成された画像のURL
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print(f"📏 サイズ: {size}")
    print(f"📊 品質: {quality}")
    print(f"🔧 クライアントタイプ: {client_type}")
    print("🔄 画像を生成中...")
    
    if client_type == "openai" and OPENAI_CLIENT_AVAILABLE:
        return generate_image_with_openai(prompt, model, size, quality, save_image)
    elif client_type == "requests" or not OPENAI_CLIENT_AVAILABLE:
        return generate_image_with_requests(prompt, model, size, quality, save_image)
    else:  # auto
        # OpenAIクライアントが利用可能ならそれを使用、そうでなければrequests
        if OPENAI_CLIENT_AVAILABLE:
            return generate_image_with_openai(prompt, model, size, quality, save_image)
        else:
            return generate_image_with_requests(prompt, model, size, quality, save_image)

def main():
    """
    メイン関数：コマンドライン引数を解析して機能を実行
    """
    parser = argparse.ArgumentParser(description='統合画像生成クライアント')
    parser.add_argument('prompt', help='画像生成のプロンプト')
    parser.add_argument('--model', '-m', default=model_name, help='使用するモデル名')
    parser.add_argument('--size', '-s', default="1024x1024", help='画像サイズ (例: 1024x1024, 512x512)')
    parser.add_argument('--quality', '-q', default="standard", choices=["standard", "hd"], help='画像品質 (standard または hd)')
    parser.add_argument('--no-save', action='store_true', help='画像を保存しない')
    parser.add_argument('--client', '-c', choices=['openai', 'requests', 'auto'], default='auto',
                       help='使用するクライアントタイプ（openai/requests/auto）')
    
    args = parser.parse_args()
    
    generate_image(args.prompt, args.model, args.size, args.quality, not args.no_save, args.client)

if __name__ == "__main__":
    main()