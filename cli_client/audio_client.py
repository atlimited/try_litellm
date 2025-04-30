#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音声処理クライアント (統合版)
OpenAIクライアントまたはrequestsライブラリを使用してLiteLLM ProxyのOpenAI互換APIを呼び出す
ユーザーはクライアントタイプ（openai/requests）を選択できます
"""

import os
import sys
import json
import argparse
import requests
import tempfile
import base64
from typing import Optional, Dict, Any, Union, List, Tuple

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
#model_name = "gpt-4o-audio-preview"
model_name = "SambaNova/Whisper-Large-v3"
#model_name = "SambaNova/Qwen2-Audio-7B-Instruct"
#model_name = 'OpenAI/whisper-1'
#model_name = 'OpenAI/gpt-4o-mini-transcribe'

# OpenAIクライアントのインスタンス（利用可能な場合）
openai_client = None
if OPENAI_CLIENT_AVAILABLE:
    openai_client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )

def get_audio_data(audio_path: str) -> Tuple[bytes, str]:
    """
    音声ファイルまたはURLからデータを取得
    
    Args:
        audio_path: 音声ファイルのパスまたはURL
        
    Returns:
        (バイナリデータ, ファイル形式)
    """
    # ファイル形式を取得
    file_format = audio_path.split('.')[-1].lower() if '.' in audio_path else 'mp3'
    
    # URLの場合はダウンロード
    if audio_path.startswith(('http://', 'https://')):
        try:
            response = requests.get(audio_path)
            response.raise_for_status()
            return response.content, file_format
        except Exception as e:
            print(f"❌ 音声ファイルのダウンロードに失敗しました: {e}")
            sys.exit(1)
    # ローカルファイルの場合は読み込み
    else:
        try:
            with open(audio_path, 'rb') as f:
                return f.read(), file_format
        except Exception as e:
            print(f"❌ 音声ファイルの読み込みに失敗しました: {e}")
            sys.exit(1)

def process_audio_with_openai(audio_path: str, prompt: str = "What is in this recording?", model: str = model_name, language: str = None) -> str:
    """
    OpenAIクライアントを使用して音声処理リクエストを送信
    
    Args:
        audio_path: 音声ファイルのパスまたはURL
        prompt: 音声に関する質問や指示（chat対応モデルのみ）
        model: 使用するモデル名
        language: 音声の言語（省略可）
        
    Returns:
        処理結果のテキスト
    """
    if not OPENAI_CLIENT_AVAILABLE or openai_client is None:
        print("❌ OpenAIクライアントが利用できません。requestsモードに切り替えます。")
        return process_audio_with_requests(audio_path, prompt, model, language)
    
    try:
        # 音声データの取得
        audio_data, file_format = get_audio_data(audio_path)
        
        # chat completionsモデルとtranscriptionモデルを区別
        is_chat_model = model in ["gpt-4o-audio-preview", "OpenAI/gpt-4o-mini-transcribe", "SambaNova/Qwen2-Audio-7B-Instruct"]
        
        if is_chat_model:
            # Base64エンコード
            encoded_audio = base64.b64encode(audio_data).decode('utf-8')
            
            # chat completions形式でリクエスト
            completion = openai_client.chat.completions.create(
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
                                "type": "input_audio",
                                "input_audio": {
                                    "data": encoded_audio,
                                    "format": file_format
                                }
                            }
                        ]
                    },
                ]
            )
            
            result = completion.choices[0].message.content
            print(f"📝 処理結果:\n{result}")
            return result
            
        else:
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_format}') as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(audio_data)
            
            try:
                # transcription形式でリクエスト
                with open(temp_file_path, "rb") as audio_file:
                    # language引数の処理
                    kwargs = {}
                    if language:
                        kwargs["language"] = language
                    
                    response = openai_client.audio.transcriptions.create(
                        model=model,
                        file=audio_file,
                        **kwargs
                    )
                
                result = response.text
                print(f"📝 処理結果:\n{result}")
                return result
                
            finally:
                # 一時ファイルを削除
                os.remove(temp_file_path)
        
    except Exception as e:
        print(f"❌ OpenAIクライアントでエラーが発生しました: {str(e)}")
        print("↪️ requestsモードで再試行します")
        return process_audio_with_requests(audio_path, prompt, model, language)

def process_audio_with_requests(audio_path: str, prompt: str = "What is in this recording?", model: str = model_name, language: str = None) -> str:
    """
    requestsライブラリを使用して音声処理リクエストを送信
    
    Args:
        audio_path: 音声ファイルのパスまたはURL
        prompt: 音声に関する質問や指示（chat対応モデルのみ）
        model: 使用するモデル名
        language: 音声の言語（省略可）
        
    Returns:
        処理結果のテキスト
    """
    try:
        # 音声データの取得
        audio_data, file_format = get_audio_data(audio_path)
        
        # chat completionsモデルとtranscriptionモデルを区別
        is_chat_model = model in ["gpt-4o-audio-preview", "OpenAI/gpt-4o-mini-transcribe", "SambaNova/Qwen2-Audio-7B-Instruct"]
        
        # ヘッダー
        headers = {
            "Content-Type": "application/json"
        }
        
        # APIキーが設定されている場合はヘッダーに追加
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        
        if is_chat_model:
            # Base64エンコード
            encoded_audio = base64.b64encode(audio_data).decode('utf-8')
            
            # エンドポイント
            endpoint = f"{BASE_URL}/chat/completions"
            
            # リクエスト本文
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
                                "type": "input_audio",
                                "input_audio": {
                                    "data": encoded_audio,
                                    "format": file_format
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Geminiモデルの場合の特別処理
            if "Google/gemini" in model:
                # Geminiの場合はmodalitiesパラメータが必要かもしれない
                payload["modalities"] = ["text", "audio"]
            
            # API呼び出し
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            
            # レスポンスをパース
            result = response.json()
            
            # テキスト応答を抽出
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]
                if "content" in message:
                    text_response = message["content"]
                    print(f"📝 処理結果:\n{text_response}")
                    return text_response
            
            print(f"❌ テキスト応答が見つかりません: {result}")
            return ""
            
        else:
            # transcriptionの場合は一時ファイルに保存してmultipart/form-dataでアップロード
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_format}') as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(audio_data)
            
            try:
                # エンドポイント
                endpoint = f"{BASE_URL}/audio/transcriptions"
                
                # リクエストヘッダー（multipart/form-dataの場合はContent-Typeを削除）
                if "Content-Type" in headers:
                    del headers["Content-Type"]
                
                # フォームデータの準備
                files = {
                    'file': (os.path.basename(temp_file_path), open(temp_file_path, 'rb'), f'audio/{file_format}')
                }
                
                # フォームフィールドの準備
                data = {
                    'model': model
                }
                
                # 言語が指定されている場合は追加
                if language:
                    data['language'] = language
                
                # API呼び出し
                response = requests.post(endpoint, headers=headers, files=files, data=data)
                response.raise_for_status()
                
                # レスポンスをパース
                result = response.json()
                
                # テキスト応答を抽出
                if "text" in result:
                    text_response = result["text"]
                    print(f"📝 処理結果:\n{text_response}")
                    return text_response
                
                print(f"❌ テキスト応答が見つかりません: {result}")
                return ""
                
            finally:
                # 一時ファイルを削除
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        # デバッグ情報
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def process_audio(audio_path: str, prompt: str = "What is in this recording?", model: str = model_name, language: str = None, client_type: str = "auto") -> str:
    """
    音声処理リクエストを送信（統合インターフェース）
    
    Args:
        audio_path: 音声ファイルのパスまたはURL
        prompt: 音声に関する質問や指示（chat対応モデルのみ）
        model: 使用するモデル名
        language: 音声の言語（省略可）
        client_type: クライアントタイプ（openai/requests/auto）
        
    Returns:
        処理結果のテキスト
    """
    print(f"🎵 音声ファイル: {audio_path}")
    print(f"🤖 モデル: {model}")
    if language:
        print(f"🌐 言語: {language}")
    print(f"🔧 クライアントタイプ: {client_type}")
    
    # chat対応モデルの場合はプロンプトを表示
    if model in ["gpt-4o-audio-preview", "OpenAI/gpt-4o-mini-transcribe", "SambaNova/Qwen2-Audio-7B-Instruct"]:
        print(f"📝 プロンプト: {prompt}")
    
    print("🔄 処理中...")
    
    if client_type == "openai" and OPENAI_CLIENT_AVAILABLE:
        return process_audio_with_openai(audio_path, prompt, model, language)
    elif client_type == "requests" or not OPENAI_CLIENT_AVAILABLE:
        return process_audio_with_requests(audio_path, prompt, model, language)
    else:  # auto
        # OpenAIクライアントが利用可能ならそれを使用、そうでなければrequests
        if OPENAI_CLIENT_AVAILABLE:
            return process_audio_with_openai(audio_path, prompt, model, language)
        else:
            return process_audio_with_requests(audio_path, prompt, model, language)

def main():
    """
    メイン関数：コマンドライン引数を解析して機能を実行
    """
    parser = argparse.ArgumentParser(description='統合音声処理クライアント')
    parser.add_argument('audio_path', help='音声ファイルのパスまたはURL')
    parser.add_argument('--prompt', '-p', default="What is in this recording?", help='音声に関する質問や指示（chat対応モデルのみ）')
    parser.add_argument('--model', '-m', default=model_name, help='使用するモデル名')
    parser.add_argument('--language', '-l', help='音声の言語（例: ja, en）')
    parser.add_argument('--client', '-c', choices=['openai', 'requests', 'auto'], default='auto',
                       help='使用するクライアントタイプ（openai/requests/auto）')
    
    args = parser.parse_args()
    
    process_audio(args.audio_path, args.prompt, args.model, args.language, args.client)

if __name__ == "__main__":
    main()