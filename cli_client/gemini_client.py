#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gemini マルチモーダルクライアント
Gemini API を直接呼び出すクライアント
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
import time
import wave
from pathlib import Path

# Gemini APIキー
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Gemini API エンドポイント
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

def chat_with_model(
    prompt: str,
    model: str = "gemini-2.0-flash"
) -> str:
    """
    AIモデルとチャットをする（テキストのみ）
    Gemini APIを直接呼び出す
    
    Args:
        prompt: チャットプロンプト
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト回答
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print("🔄 応答を生成中...")
    
    # Geminiモデル名を正規化
    model_name = model.replace("Google/", "")
    
    # APIエンドポイント（APIキーをクエリパラメータとして追加）
    url = f"{GEMINI_API_BASE}/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    # ヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    # リクエスト本文
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    try:
        # API呼び出し
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # レスポンスをパース
        result = response.json()
        
        # テキスト回答を抽出
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        text_response = part["text"]
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

def generate_image(
    prompt: str, 
    output_path: str = "generated_images/generated_image.png",
    model: str = "gemini-2.0-flash-exp-image-generation"
) -> str:
    """
    プロンプトに基づいて画像を生成し、指定されたパスに保存する
    Gemini APIを直接呼び出す
    
    Args:
        prompt: 画像生成のプロンプト
        output_path: 生成した画像を保存するパス
        model: 使用するモデル名
        
    Returns:
        生成された画像のパス
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print("🔄 画像を生成中...")
    
    # Geminiモデル名を正規化（Google/プレフィックスがあれば削除）
    model_name = model.replace("Google/", "")
    
    # Gemini APIエンドポイント
    url = f"{GEMINI_API_BASE}/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    # ヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    # リクエスト本文 - Gemini 画像生成用の正しい形式
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.4,
            "top_p": 1,
            "top_k": 32,
            "responseModalities": ["TEXT", "IMAGE"]
        }
    }
    
    try:
        # API呼び出し
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # エラーがあれば例外を発生
        
        # レスポンスをパース
        result = response.json()
        
        # デバッグ用にレスポンス全体を表示
        print(f"📊 レスポンス: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # レスポンスから画像データを取得
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
                    # 注意: JSONキー名は 'inline_data' ではなく 'inlineData'
                    if "inlineData" in part and part["inlineData"]["mimeType"].startswith("image/"):
                        # Base64エンコードされた画像データ
                        image_data = base64.b64decode(part["inlineData"]["data"])
                        
                        # 出力ディレクトリが存在しない場合は作成
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        
                        # 画像を保存
                        with open(output_path, "wb") as f:
                            f.write(image_data)
                        
                        print(f"✅ 画像を {output_path} に保存しました")
                        return output_path
        
        # 最新のImagen APIモデルを使う方法を試す
        try:
            imagen_url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-flash:generateContent?key=" + GEMINI_API_KEY
            
            imagen_payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            imagen_response = requests.post(imagen_url, headers=headers, json=imagen_payload)
            imagen_response.raise_for_status()
            
            imagen_result = imagen_response.json()
            print(f"📊 Imagen APIレスポンス: {json.dumps(imagen_result, indent=2, ensure_ascii=False)}")
            
            # 画像データ取得のロジック
            if "candidates" in imagen_result and len(imagen_result["candidates"]) > 0:
                candidate = imagen_result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        # 注意: JSONキー名は 'inline_data' ではなく 'inlineData'
                        if "inlineData" in part and part["inlineData"]["mimeType"].startswith("image/"):
                            image_data = base64.b64decode(part["inlineData"]["data"])
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, "wb") as f:
                                f.write(image_data)
                            print(f"✅ Imagen APIで画像を {output_path} に保存しました")
                            return output_path
            
            print("❌ 画像データが見つかりません")
            return ""
            
        except Exception as alt_e:
            print(f"❌ Imagen API呼び出しでエラーが発生しました: {str(alt_e)}")
            if hasattr(alt_e, 'response') and hasattr(alt_e.response, 'text'):
                print(f"レスポンス: {alt_e.response.text}")
            return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        # デバッグ情報
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        print(f"リクエスト: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        return ""

def get_base64_encoded_image(image_path: str) -> str:
    """
    画像ファイルをBase64エンコードした文字列を返す
    
    Args:
        image_path: 画像ファイルのパス
        
    Returns:
        Base64エンコードされた画像データ
    """
    with open(image_path, "rb") as img_file:
        img_data = img_file.read()
        
        # MIMEタイプを推測
        ext = os.path.splitext(image_path)[1].lower()
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

def analyze_image(
    image_path: str,
    prompt: str = "これはなんの画像ですか",
    model: str = "gemini-2.0-flash"
) -> str:
    """
    画像とテキストプロンプトを使用して応答を生成する
    Gemini APIを直接呼び出す
    
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
    
    # Geminiモデル名を正規化
    model_name = model.replace("Google/", "")
    
    # 画像を読み込みBase64エンコード
    image_base64 = get_base64_encoded_image(image_path)
    
    # 画像のMIMEタイプを取得
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    mime_type = mime_map.get(ext, 'image/jpeg')
    
    # APIエンドポイント（APIキーをクエリパラメータとして追加）
    url = f"{GEMINI_API_BASE}/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    # ヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    # マルチモーダルリクエスト本文
    payload = {
        "contents": [{
            "parts": [
                {
                    "text": prompt
                },
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": image_base64
                    }
                }
            ]
        }]
    }
    
    try:
        # API呼び出し
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # レスポンスをパース
        result = response.json()
        
        # テキスト回答を抽出
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        text_response = part["text"]
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


def transcribe_audio(
    audio_path: str,
    language: str = "ja",
    model: str = "gemini-2.0-flash"
) -> str:
    """
    音声ファイルをテキストに変換する（音声認識）
    Gemini APIを直接呼び出す
    
    Args:
        audio_path: 音声ファイルのパス
        language: 言語コード（ja, en, zh など）
        model: 使用するモデル名
        
    Returns:
        音声から認識されたテキスト
    """
    print(f"🎤 音声ファイル: {audio_path}")
    print(f"🌐 言語: {language}")
    print(f"🤖 モデル: {model}")
    print("🔄 音声を認識中...")
    
    # Geminiモデル名を正規化
    model_name = model.replace("Google/", "")
    
    # 音声ファイルを読み込みBase64エンコード
    with open(audio_path, "rb") as audio_file:
        audio_data = audio_file.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    
    # 音声のMIMEタイプを取得
    ext = os.path.splitext(audio_path)[1].lower()
    mime_map = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.m4a': 'audio/m4a',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
    }
    mime_type = mime_map.get(ext, 'audio/mpeg')
    
    # APIエンドポイント（APIキーをクエリパラメータとして追加）
    url = f"{GEMINI_API_BASE}/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    # ヘッダー
    headers = {
        "Content-Type": "application/json"
    }
    
    # マルチモーダルリクエスト本文（音声）
    payload = {
        "contents": [{
            "parts": [
                {
                    "text": f"この音声を文字起こししてください。言語は{language}です。"
                },
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": audio_base64
                    }
                }
            ]
        }]
    }
    
    try:
        # API呼び出し
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # レスポンスをパース
        result = response.json()
        
        # テキスト回答を抽出
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        text_response = part["text"]
                        print(f"\n📝 認識結果:\n{text_response}")
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
    """メイン関数: コマンドライン引数を解析して機能を実行する"""
    parser = argparse.ArgumentParser(description="Geminiクライアント: 画像生成、チャット、音声認識などの機能を提供")
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # テキストチャットコマンド
    chat_parser = subparsers.add_parser("chat", help="テキストチャット")
    chat_parser.add_argument("prompt", help="チャットプロンプト")
    chat_parser.add_argument("-m", "--model", help="使用するモデル", default="gemini-2.0-flash")
    
    # 画像生成コマンド
    image_parser = subparsers.add_parser("image", help="画像を生成")
    image_parser.add_argument("prompt", help="画像生成のプロンプト")
    image_parser.add_argument("-o", "--output", help="出力ファイルパス", default="generated_images/generated_image.png")
    image_parser.add_argument("-m", "--model", help="使用するモデル", default="gemini-2.0-flash-exp-image-generation")
    
    # 画像認識コマンド
    vision_parser = subparsers.add_parser("vision", help="画像とテキストを使用して回答を生成")
    vision_parser.add_argument("image", help="分析する画像のパス")
    vision_parser.add_argument("-p", "--prompt", help="画像に関する質問や指示", default="これはなんの画像ですか")
    vision_parser.add_argument("-m", "--model", help="使用するモデル", default="gemini-2.0-flash")
    
    # 音声認識コマンド
    speech_parser = subparsers.add_parser("speech", help="音声認識")
    speech_parser.add_argument("audio", help="音声ファイルのパス")
    speech_parser.add_argument("-l", "--language", help="言語コード", default="ja")
    speech_parser.add_argument("-m", "--model", help="使用するモデル", default="gemini-2.0-flash")
    
    args = parser.parse_args()
    
    # サブコマンドに基づいて機能を実行
    if args.command == "image":
        generate_image(args.prompt, args.output, args.model)
    elif args.command == "vision":
        analyze_image(args.image, args.prompt, args.model)
    elif args.command == "chat":
        chat_with_model(args.prompt, args.model)
    elif args.command == "speech":
        transcribe_audio(args.audio, args.language, args.model)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()