#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音声合成（TTS）クライアント (統合版)
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

# 出力ディレクトリの設定
output_dir = Path("./generated_audio")
output_dir.mkdir(exist_ok=True)

# TTS モデルの設定
model_name = "OpenAI/tts-1"  # 標準モデル
# model_name = "OpenAI/tts-1-hd"  # 高品質モデル（こちらは計算コストが高い）

# OpenAIクライアントのインスタンス（利用可能な場合）
openai_client = None
if OPENAI_CLIENT_AVAILABLE:
    openai_client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )

def generate_speech_with_openai(text: str, voice: str = "alloy", model: str = model_name, output_path: Optional[str] = None) -> str:
    """
    OpenAIクライアントを使用して音声合成リクエストを送信
    
    Args:
        text: 音声に変換するテキスト
        voice: 音声の種類 (alloy, echo, fable, onyx, nova, shimmer)
        model: 使用するモデル名 (tts-1, tts-1-hd など)
        output_path: 保存するファイルパス（省略時は自動生成）
        
    Returns:
        生成された音声ファイルのパス
    """
    if not OPENAI_CLIENT_AVAILABLE or openai_client is None:
        print("❌ OpenAIクライアントが利用できません。requestsモードに切り替えます。")
        return generate_speech_with_requests(text, voice, model, output_path)
    
    try:
        # 保存先ファイルパスの設定
        if output_path is None:
            timestamp = int(time.time())
            output_path = str(output_dir / f"speech_{voice}_{timestamp}.mp3")
        
        # 音声生成
        response = openai_client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        
        # 音声ファイルの保存
        response.stream_to_file(output_path)
        print(f"✅ 音声ファイルを保存しました: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ OpenAIクライアントでエラーが発生しました: {str(e)}")
        print("↪️ requestsモードで再試行します")
        return generate_speech_with_requests(text, voice, model, output_path)

def generate_speech_with_requests(text: str, voice: str = "alloy", model: str = model_name, output_path: Optional[str] = None) -> str:
    """
    requestsライブラリを使用して音声合成リクエストを送信
    
    Args:
        text: 音声に変換するテキスト
        voice: 音声の種類 (alloy, echo, fable, onyx, nova, shimmer)
        model: 使用するモデル名 (tts-1, tts-1-hd など)
        output_path: 保存するファイルパス（省略時は自動生成）
        
    Returns:
        生成された音声ファイルのパス
    """
    try:
        # 保存先ファイルパスの設定
        if output_path is None:
            timestamp = int(time.time())
            output_path = str(output_dir / f"speech_{voice}_{timestamp}.mp3")
        
        # エンドポイント
        endpoint = f"{BASE_URL}/audio/speech"
        
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
            "voice": voice,
            "input": text
        }
        
        # API呼び出し
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        
        # 音声データを取得して保存
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        print(f"✅ 音声ファイルを保存しました: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        # デバッグ情報
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def generate_speech(text: str, voice: str = "alloy", model: str = model_name, output_path: Optional[str] = None, client_type: str = "auto") -> str:
    """
    音声合成リクエストを送信（統合インターフェース）
    
    Args:
        text: 音声に変換するテキスト
        voice: 音声の種類 (alloy, echo, fable, onyx, nova, shimmer)
        model: 使用するモデル名 (tts-1, tts-1-hd など)
        output_path: 保存するファイルパス（省略時は自動生成）
        client_type: クライアントタイプ（openai/requests/auto）
        
    Returns:
        生成された音声ファイルのパス
    """
    print(f"📝 テキスト: {text}")
    print(f"🤖 モデル: {model}")
    print(f"🔊 音声: {voice}")
    print(f"🔧 クライアントタイプ: {client_type}")
    
    print("🔄 音声生成中...")
    
    if client_type == "openai" and OPENAI_CLIENT_AVAILABLE:
        return generate_speech_with_openai(text, voice, model, output_path)
    elif client_type == "requests" or not OPENAI_CLIENT_AVAILABLE:
        return generate_speech_with_requests(text, voice, model, output_path)
    else:  # auto
        # OpenAIクライアントが利用可能ならそれを使用、そうでなければrequests
        if OPENAI_CLIENT_AVAILABLE:
            return generate_speech_with_openai(text, voice, model, output_path)
        else:
            return generate_speech_with_requests(text, voice, model, output_path)

def main():
    """
    メイン関数：コマンドライン引数を解析して機能を実行
    """
    parser = argparse.ArgumentParser(description='統合音声合成クライアント')
    parser.add_argument('text', help='音声に変換するテキスト')
    parser.add_argument('--voice', '-v', default="alloy", choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"], 
                       help='音声の種類 (alloy, echo, fable, onyx, nova, shimmer)')
    parser.add_argument('--model', '-m', default=model_name, help='使用するモデル名 (tts-1, tts-1-hd など)')
    parser.add_argument('--output', '-o', help='出力ファイルパス (省略時は自動生成)')
    parser.add_argument('--client', '-c', choices=['openai', 'requests', 'auto'], default='auto',
                       help='使用するクライアントタイプ（openai/requests/auto）')
    
    args = parser.parse_args()
    
    generate_speech(args.text, args.voice, args.model, args.output, args.client)

if __name__ == "__main__":
    main()