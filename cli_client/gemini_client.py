#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gemini マルチモーダルクライアント
LiteLLM プロキシを通じて Gemini API を利用するためのクライアント
"""

import os
import argparse
import json
import sys
import base64
from typing import Optional, List, Dict, Any, Union
import requests
from PIL import Image
import io

# LiteLLM プロキシの URL
LITELLM_PROXY_URL = "http://localhost:4000/v1"

def generate_image(
    prompt: str, 
    output_path: Optional[str],
    model: str = "gemini-2.0-flash-exp-image-generation"
) -> str:
    """
    Gemini モデルを使用して画像を生成する
    
    Args:
        prompt: 画像生成のためのプロンプト
        output_path: 生成された画像を保存するパス（省略可能）
        model: 使用するモデル名
        
    Returns:
        生成された画像のパス、または出力パスが指定されていない場合は Base64 エンコードされた画像データ
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print("🔄 画像を生成中...")
    
    # Geminiの画像生成リクエストを構築
    url = f"{LITELLM_PROXY_URL}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    # Geminiでは modalities パラメータが必要
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image", "text"],  # 画像と文字両方の機能を有効化
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # レスポンスをパース
        result = response.json()
        
        # レスポンス全体を表示（デバッグ用）
        print(f"📊 レスポンス構造: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 画像データを取得（base64形式）
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Base64エンコードされた画像データを取得
            if content.startswith("data:image"):
                # "data:image/png;base64," などのプレフィックスを除去
                image_data = content.split(",", 1)[1]
                
                if output_path:
                    # Base64をデコードして画像ファイルとして保存
                    img_data = base64.b64decode(image_data)
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    print(f"✅ 画像を {output_path} に保存しました")
                    return output_path
                else:
                    # 出力パスが指定されていない場合は Base64 データを返す
                    return content
            else:
                print(f"❌ 画像データが見つかりません: {content}")
                return ""
        else:
            print(f"❌ 画像生成に失敗しました: {result}")
            return ""
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def get_base64_encoded_image(image_path: str) -> str:
    """
    画像ファイルを Base64 エンコードする
    
    Args:
        image_path: 画像ファイルのパス
        
    Returns:
        Base64 エンコードされた画像データ（MIMEタイプ付き）
    """
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    
    extension = os.path.splitext(image_path)[1].lower()
    mime_type = mime_map.get(extension, 'image/jpeg')
    
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    return f"data:{mime_type};base64,{encoded_string}"

def generate_response_with_image(
    prompt: str,
    image_path: str,
    model: str = "gemini/gemini-2.0-flash"
) -> str:
    """
    画像とテキストを使用して Gemini にリクエストを送信する
    
    Args:
        prompt: テキストプロンプト
        image_path: 画像ファイルのパス
        model: 使用するモデル名
        
    Returns:
        Gemini からの応答テキスト
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🖼️ 画像: {image_path}")
    print(f"🤖 モデル: {model}")
    print("🔄 応答を生成中...")
    
    # 画像を Base64 エンコード
    base64_image = get_base64_encoded_image(image_path)
    
    # Gemini のマルチモーダルリクエストを構築（メッセージの内容が配列になる点に注意）
    url = f"{LITELLM_PROXY_URL}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    # Gemini では LiteLLM を通して以下のような形式でマルチモーダルメッセージを送信
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
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # レスポンスをパース
        result = response.json()
        
        # レスポンス全体を表示（デバッグ用）
        # print(f"📊 レスポンス構造: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print(f"\n📝 回答:\n{content}")
            return content
        else:
            print(f"❌ 応答の生成に失敗しました: {result}")
            return ""
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def chat_with_gemini(
    prompt: str,
    model: str = "gemini/gemini-2.0-flash"
) -> str:
    """
    テキストのみで Gemini とチャットする
    
    Args:
        prompt: テキストプロンプト
        model: 使用するモデル名
        
    Returns:
        Gemini からの応答テキスト
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print("🔄 応答を生成中...")
    
    # Gemini のテキストチャットリクエストを構築
    url = f"{LITELLM_PROXY_URL}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
    }
    
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
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # レスポンスをパース
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print(f"\n📝 回答:\n{content}")
            return content
        else:
            print(f"❌ 応答の生成に失敗しました: {result}")
            return ""
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def main():
    parser = argparse.ArgumentParser(description="Gemini マルチモーダルクライアント")
    subparsers = parser.add_subparsers(dest="command", help="実行するコマンド")
    
    # 画像生成コマンド
    image_parser = subparsers.add_parser("image", help="画像を生成")
    image_parser.add_argument("prompt", help="画像生成のプロンプト")
    image_parser.add_argument("-o", "--output", help="出力ファイルパス", default="generated_images/generated_image.png")
    image_parser.add_argument("-m", "--model", help="使用するモデル", default="Google/gemini-2.0-flash")
    
    # 画像認識コマンド
    vision_parser = subparsers.add_parser("vision", help="画像とテキストを使用して回答を生成")
    vision_parser.add_argument("prompt", help="テキストプロンプト")
    vision_parser.add_argument("image", help="画像ファイルのパス")
    vision_parser.add_argument("-m", "--model", help="使用するモデル", default="Google/gemini-2.0-flash")
    
    # テキストチャットコマンド
    chat_parser = subparsers.add_parser("chat", help="テキストのみでチャット")
    chat_parser.add_argument("prompt", help="テキストプロンプト")
    chat_parser.add_argument("-m", "--model", help="使用するモデル", default="Google/gemini-2.0-flash")
    
    # コマンドライン引数をパース
    args = parser.parse_args()
    
    if args.command == "image":
        generate_image(args.prompt, args.output, args.model)
    elif args.command == "vision":
        generate_response_with_image(args.prompt, args.image, args.model)
    elif args.command == "chat":
        chat_with_gemini(args.prompt, args.model)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
