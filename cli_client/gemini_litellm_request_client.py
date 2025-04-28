#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import base64
import argparse
from typing import List, Dict, Any, Optional
import requests
from PIL import Image
import io
import time
import re

## mitmproxy を利用するため、環境変数でプロキシ設定を行います
os.environ["HTTP_PROXY"] = "http://127.0.0.1:8080"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:8080"

# mitmproxy の証明書を設定
ca_cert_path = "/Users/takagi/.mitmproxy/mitmproxy-ca-cert.pem"
os.environ['SSL_CERT_FILE'] = ca_cert_path
os.environ['REQUESTS_CA_BUNDLE'] = ca_cert_path

# 環境変数からAPIキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# LiteLLMプロキシのエンドポイント
LITELLM_API_BASE = "http://0.0.0.0:4000/v1"

def chat_with_model(
    prompt: str,
    model: str = "Google/gemini-2.0-flash"
) -> str:
    """
    AIモデルとチャットをする（テキストのみ）
    requestsライブラリで直接LiteLLMプロキシに接続
    
    Args:
        prompt: チャットプロンプト
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト回答
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print("🔄 応答を生成中...")
    
    url = f"{LITELLM_API_BASE}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}"
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
        response.raise_for_status()  # エラーがあれば例外を発生
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            text_response = result["choices"][0]["message"]["content"]
            print(f"\n📝 回答:\n{text_response}")
            return text_response
            
        print(f"❌ 応答が不正な形式です: {result}")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def analyze_image(
    image_path: str,
    prompt: str = "これはなんの画像ですか",
    model: str = "Google/gemini-2.0-flash"
) -> str:
    """
    画像とテキストプロンプトを使用して応答を生成する
    requestsライブラリで直接LiteLLMプロキシに接続
    
    Args:
        image_path: 分析する画像のパス
        prompt: 画像に関する質問や指示
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト回答
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🖼️ 画像: {image_path}")
    print(f"🤖 モデル: {model}")
    print("🔄 画像を分析中...")
    
    url = f"{LITELLM_API_BASE}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}"
    }
    
    # 画像をBase64エンコード
    image_base64 = encode_image_to_base64(image_path)
    if not image_base64:
        return ""
    
    # マルチモーダル入力用のペイロード
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
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            text_response = result["choices"][0]["message"]["content"]
            print(f"\n📝 回答:\n{text_response}")
            return text_response
            
        print(f"❌ 応答が不正な形式です: {result}")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def transcribe_audio(
    audio_path: str,
    language: str = "ja",
    model: str = "Google/gemini-2.0-flash"
) -> str:
    """
    音声ファイルを文字起こしする
    
    Args:
        audio_path (str): 音声ファイルパス
        language (str): 言語コード
        model (str): 使用するモデル
        
    Returns:
        str: 文字起こし結果
    """
    print(f"🎤 音声ファイル: {audio_path}")
    print(f"🌐 言語: {language}")
    print(f"🤖 モデル: {model}")
    print(f"🔄 音声を認識中...")
    
    # LiteLLMプロキシのエンドポイント
    url = f"{LITELLM_API_BASE}/chat/completions"
    
    # ヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # 音声ファイルをBase64エンコード
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # マルチモーダル入力用のペイロード
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"この音声を文字起こししてください。言語: {language}"
                        },
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_base64,
                                "format": "mp3"
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # レスポンスをパース
        result = response.json()
        
        # 文字起こし結果を取得
        if "choices" in result and len(result["choices"]) > 0:
            transcription = result["choices"][0]["message"]["content"]
            print("\n📝 文字起こし結果:")
            print(transcription)
            return transcription
        else:
            print("❌ 文字起こし結果を取得できませんでした")
            print(result)
            return None
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        
        # プロキシ経由での認識に失敗した場合、直接Gemini APIを呼び出す
        try:
            print("🔄 直接Gemini APIでの音声認識を試します...")
            # Gemini APIエンドポイント
            GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
            gemini_url = f"{GEMINI_API_BASE}/{model.replace('Google/', '')}:generateContent?key={GEMINI_API_KEY}"
            
            # 再度音声ファイルをBase64エンコード
            with open(audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            
            # Gemini APIに適したペイロード形式
            gemini_payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"この音声を文字起こししてください。言語: {language}"
                            },
                            {
                                "inline_data": {
                                    "mime_type": "audio/mp3",
                                    "data": audio_base64
                                }
                            }
                        ]
                    }
                ]
            }
            
            gemini_headers = {
                "Content-Type": "application/json"
            }
            
            gemini_response = requests.post(gemini_url, headers=gemini_headers, json=gemini_payload)
            gemini_response.raise_for_status()
            
            gemini_result = gemini_response.json()
            
            # レスポンスからテキストを抽出
            if "candidates" in gemini_result and len(gemini_result["candidates"]) > 0:
                candidate = gemini_result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            text_response = part["text"]
                            print(f"\n📝 文字起こし結果 (直接API):\n{text_response}")
                            return text_response
                            
            print(f"❌ Gemini APIの応答が不正な形式です: {gemini_result}")
            
        except Exception as gemini_e:
            print(f"❌ 直接Gemini API呼び出しでエラーが発生しました: {str(gemini_e)}")
            if hasattr(gemini_e, 'response') and hasattr(gemini_e.response, 'text'):
                print(f"レスポンス: {gemini_e.response.text}")
        
        return ""

def generate_image(
    prompt, 
    output_dir="generated_images",
    filename="generated_image.png",
    model="Google/gemini-2.0-flash-exp-image-generation"
):
    """
    プロンプトから画像を生成する
    
    Args:
        prompt: 画像生成のプロンプト
        output_dir: 出力ディレクトリ
        filename: 出力ファイル名
        model: 使用するモデル
        
    Returns:
        生成された画像のパス
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print(f"🔄 画像を生成中...")
    
    # 出力パス
    output_path = os.path.join(output_dir, filename)
    
    # LiteLLMプロキシのエンドポイント
    url = f"{LITELLM_API_BASE}/chat/completions"
    
    # ヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # LiteLLMプロキシ用のペイロード
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "modalities": ["image", "text"]  # モダリティパラメータを追加
        }
        
        # LiteLLMプロキシAPIを呼び出す
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # レスポンスをパース
        result = response.json()
        
        # 画像データを探す
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
                
                # Base64エンコードされた画像を探す
                image_pattern = r"data:image\/(\w+);base64,([^\"]+)"
                matches = re.findall(image_pattern, content)
                
                if matches:
                    # 最初の画像を使用
                    img_format, img_data = matches[0]
                    # Base64データをデコード
                    img_bytes = base64.b64decode(img_data)
                    
                    # 出力ディレクトリが存在しない場合は作成
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # 画像を保存
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    
                    print(f"✅ 画像を {output_path} に保存しました")
                    return output_path
        else:
            print("❌ 画像データが見つかりません")
            return ""
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def encode_image_to_base64(image_path: str) -> str:
    """
    画像をBase64エンコードする
    
    Args:
        image_path: 画像ファイルのパス
        
    Returns:
        Base64エンコードされた画像データ
    """
    # 拡張子からMIMEタイプを推測
    _, ext = os.path.splitext(image_path.lower())
    
    try:
        # 画像をバイナリで読み込む
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
            
        # 拡張子からMIMEタイプを決定
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        mime_type = mime_map.get(ext, 'image/jpeg')
        
        # Base64エンコード
        return base64.b64encode(img_data).decode('utf-8')
        
    except Exception as e:
        print(f"❌ 画像のエンコードに失敗しました: {str(e)}")
        return ""

def main():
    """メイン関数: コマンドライン引数を解析して機能を実行する"""
    parser = argparse.ArgumentParser(description="Geminiクライアント (requests使用): 画像生成、チャット、音声認識などの機能を提供")
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # テキストチャットコマンド
    chat_parser = subparsers.add_parser("chat", help="テキストチャット")
    chat_parser.add_argument("prompt", help="チャットプロンプト")
    chat_parser.add_argument("-m", "--model", help="使用するモデル", default="Google/gemini-2.0-flash")
    
    # 画像認識コマンド
    vision_parser = subparsers.add_parser("vision", help="画像とテキストを使用して回答を生成")
    vision_parser.add_argument("image", help="分析する画像のパス")
    vision_parser.add_argument("-p", "--prompt", help="画像に関する質問や指示", default="これはなんの画像ですか")
    vision_parser.add_argument("-m", "--model", help="使用するモデル", default="Google/gemini-2.0-flash")
    
    # 音声認識コマンド
    speech_parser = subparsers.add_parser("speech", help="音声認識")
    speech_parser.add_argument("audio", help="音声ファイルのパス")
    speech_parser.add_argument("-l", "--language", help="言語コード", default="ja")
    speech_parser.add_argument("-m", "--model", help="使用するモデル", default="Google/gemini-2.0-flash")

    # 画像生成コマンド
    image_parser = subparsers.add_parser("image", help="画像を生成")
    image_parser.add_argument("prompt", help="画像生成のプロンプト")
    image_parser.add_argument("-o", "--output", help="出力ファイルパス", default="generated_images/generated_image.png")
    image_parser.add_argument("-m", "--model", help="使用するモデル", default="Google/gemini-2.0-flash-exp-image-generation")
    
    args = parser.parse_args()
    
    # サブコマンドに基づいて機能を実行
    if args.command == "chat":
        chat_with_model(args.prompt, args.model)
    elif args.command == "vision":
        analyze_image(args.image, args.prompt, args.model)
    elif args.command == "speech":
        transcribe_audio(args.audio, args.language, args.model)
    elif args.command == "image":
        generate_image(args.prompt, os.path.dirname(args.output), os.path.basename(args.output), args.model)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()