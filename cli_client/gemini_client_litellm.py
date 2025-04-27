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
from openai import OpenAI

# 環境変数からAPIキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# LiteLLMプロキシに接続するOpenAIクライアント
client = OpenAI(
    base_url="http://0.0.0.0:4000/v1", # litellm-proxy-base url
    api_key=GEMINI_API_KEY
)

def chat_with_model(
    prompt: str,
    model: str = "gemini-2.0-flash"
) -> str:
    """
    AIモデルとチャットをする（テキストのみ）
    LiteLLMプロキシを使用
    
    Args:
        prompt: チャットプロンプト
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト回答
    """
    print(f"📝 プロンプト: {prompt}")
    print(f"🤖 モデル: {model}")
    print("🔄 応答を生成中...")
    
    try:
        # Geminiモデルを呼び出す
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # レスポンスからテキストを取得
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            text_response = response.choices[0].message.content
            print(f"\n📝 回答:\n{text_response}")
            return text_response
            
        print("❌ 応答が見つかりません")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return ""

def analyze_image(
    image_path: str,
    prompt: str = "これはなんの画像ですか",
    model: str = "gemini-2.0-flash"
) -> str:
    """
    画像とテキストプロンプトを使用して応答を生成する
    LiteLLMプロキシを使用
    
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
    
    try:
        # 画像を読み込んでBase64にエンコード
        image_base64 = encode_image_to_base64(image_path)
        
        # マルチモーダル入力用のメッセージを構築
        response = client.chat.completions.create(
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
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
        )
        
        # レスポンスからテキストを取得
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            text_response = response.choices[0].message.content
            print(f"\n📝 回答:\n{text_response}")
            return text_response
            
        print("❌ 応答が見つかりません")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return ""

def transcribe_audio(
    audio_path: str,
    language: str = "ja",
    model: str = "gemini-2.0-flash"
) -> str:
    """
    音声ファイルからテキストを抽出する（音声認識）
    LiteLLMプロキシを使用
    
    Args:
        audio_path: 音声ファイルのパス
        language: 音声の言語コード
        model: 使用するモデル名
        
    Returns:
        抽出されたテキスト
    """
    print(f"🎤 音声ファイル: {audio_path}")
    print(f"🌐 言語: {language}")
    print(f"🤖 モデル: {model}")
    print("🔄 音声を認識中...")
    
    try:
        # 音声ファイルをBase64エンコード
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        # マルチモーダル入力用のメッセージを構築
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"この音声を文字起こししてください。言語: {language}"
                        },
                        {
                            "type": "audio_url",
                            "audio_url": {
                                "url": f"data:audio/wav;base64,{audio_base64}"
                            }
                        }
                    ]
                }
            ]
        )
        
        # レスポンスからテキストを取得
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            text_response = response.choices[0].message.content
            print(f"\n📝 文字起こし結果:\n{text_response}")
            return text_response
            
        print("❌ 応答が見つかりません")
        return ""
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        # Whisperモデルを試す別のアプローチを試す
        try:
            print("🔄 Whisperモデルでの音声認識を試します...")
            # OpenAI互換のWhisper APIを使用
            audio_file = open(audio_path, "rb")
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language
            )
            text_response = transcript.text
            print(f"\n📝 文字起こし結果 (Whisper):\n{text_response}")
            return text_response
        except Exception as whisper_e:
            print(f"❌ Whisperでのエラー: {str(whisper_e)}")
            return ""
        return ""

def generate_image(
    prompt: str, 
    output_path: str = "generated_images/generated_image.png",
    model: str = "gemini-2.0-flash-exp-image-generation"
) -> str:
    """
    プロンプトに基づいて画像を生成し、指定されたパスに保存する
    LiteLLMプロキシを使用（注：画像生成はプロキシがサポートしていない場合、
    Gemini APIを直接呼び出すバックアップコードを使用）
    
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
    
    try:
        # まずLiteLLMプロキシ経由で画像生成を試みる
        try:
            response = client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
            if response and hasattr(response, 'data') and len(response.data) > 0:
                # 画像URLまたはBase64データを取得
                image_data = response.data[0]
                if hasattr(image_data, 'url') and image_data.url:
                    # URLから画像をダウンロード
                    img_response = requests.get(image_data.url)
                    img_response.raise_for_status()
                    # 出力ディレクトリが存在しない場合は作成
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    # 画像を保存
                    with open(output_path, "wb") as f:
                        f.write(img_response.content)
                    print(f"✅ 画像を {output_path} に保存しました")
                    return output_path
                elif hasattr(image_data, 'b64_json') and image_data.b64_json:
                    # Base64データから画像を保存
                    img_data = base64.b64decode(image_data.b64_json)
                    # 出力ディレクトリが存在しない場合は作成
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    # 画像を保存
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    print(f"✅ 画像を {output_path} に保存しました")
                    return output_path
            
        except Exception as proxy_e:
            print(f"⚠️ LiteLLMプロキシでのエラー: {str(proxy_e)}。直接APIを呼び出します...")
        
        # 以下は直接Gemini APIを呼び出すバックアップコード
        # Gemini APIエンドポイント
        GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
        url = f"{GEMINI_API_BASE}/{model}:generateContent?key={GEMINI_API_KEY}"
        
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
        
        # API呼び出し
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        # レスポンスをパース
        result = response.json()
        
        # レスポンスから画像データを取得
        if "candidates" in result and len(result["candidates"]) > 0:
            candidate = result["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
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
            
            # 画像データ取得のロジック
            if "candidates" in imagen_result and len(imagen_result["candidates"]) > 0:
                candidate = imagen_result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
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
    parser = argparse.ArgumentParser(description="Geminiクライアント (LiteLLM使用): 画像生成、チャット、音声認識などの機能を提供")
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
        generate_image(args.prompt, args.output, args.model)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()