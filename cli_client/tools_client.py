#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Function Callingクライアント (統合版)
OpenAIクライアントまたはrequestsライブラリを使用してLiteLLM ProxyのFunction Calling機能を呼び出す
ユーザーはクライアントタイプ（openai/requests）を選択できます
"""

import os
import sys
import json
import argparse
import requests
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
#model_name = "Google/gemini-2.0-flash"
model_name = "SambaNova/Meta-Llama-3.3-70B-Instruct"
#model_name = "SambaNova/Llama-4-Maverick-17B-128E-Instruct"

# OpenAIクライアントのインスタンス（利用可能な場合）
openai_client = None
if OPENAI_CLIENT_AVAILABLE:
    openai_client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )

## サンプル関数: 指定した場所の天気を返す
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        location = "Tokyo"
        temperature = "10"
        unit = "celsius"
    elif "san francisco" in location.lower():
        location = "San Francisco"
        temperature = "72"
        unit = "fahrenheit"
    elif "paris" in location.lower():
        location = "Paris"
        temperature = "22"
        unit = "celsius"
    else:
        temperature = "undefined"
    return json.dumps({"location": location, "temperature": temperature, "unit": unit})

def get_tools_definition():
    """ツール定義を返す"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ]

def execute_function_call(function_name, function_args):
    """関数名と引数から適切な関数を実行して結果を返す"""
    if function_name == "get_current_weather":
        return get_current_weather(
            location=function_args.get("location", ""),
            unit=function_args.get("unit", "fahrenheit")
        )
    else:
        return json.dumps({"error": f"Unknown function: {function_name}"})

def run_tool_call_with_openai(message: str, model: str = model_name) -> str:
    """
    OpenAIクライアントを使用してFunction Callingリクエストを送信
    
    Args:
        message: ユーザーからのメッセージ
        model: 使用するモデル名
        
    Returns:
        生成されたテキスト
    """
    if not OPENAI_CLIENT_AVAILABLE or openai_client is None:
        print("❌ OpenAIクライアントが利用できません。requestsモードに切り替えます。")
        return run_tool_call_with_requests(message, model)
    
    try:
        # ツール定義
        tools = get_tools_definition()
        
        # メッセージの準備
        messages = [{"role": "user", "content": message}]
        
        # 最初のリクエスト
        print(f"🚀 {model}にOpenAIクライアントでリクエストを送信中...")
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        # レスポンスを処理
        print("\n🤖 LLMレスポンス:\n")
        response_message = response.choices[0].message
        
        # ツール呼び出しがあるか確認
        if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            tool_calls = response_message.tool_calls
            print(f"🔧 ツール呼び出しが検出されました: {len(tool_calls)}個")
            
            # 各ツール呼び出しを処理
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"\n📝 関数 '{function_name}' を呼び出します。引数: {function_args}")
                
                # 関数を実行
                function_response = execute_function_call(function_name, function_args)
                
                print(f"🌤 関数の結果: {function_response}")
                
                # 関数の結果をメッセージに追加
                messages.append({
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_response,
                })
            
            # 関数結果を含めて再度リクエスト
            print("\n🔄 関数の結果を含めて再度リクエストを送信中...")
            
            second_response = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,  # anthropicでは2回目も必要
                tool_choice="auto"  # anthropicでは2回目も必要
            )
            
            print("\n🤖 最終レスポンス:\n")
            final_message = second_response.choices[0].message.content
            print(final_message)
            return final_message
        else:
            # ツール呼び出しがない場合は直接メッセージを表示
            content = response_message.content
            print(content)
            return content
            
    except Exception as e:
        print(f"❌ OpenAIクライアントでエラーが発生しました: {e}")
        print("↪️ requestsモードで再試行します")
        return run_tool_call_with_requests(message, model)

def run_tool_call_with_requests(message: str, model: str = model_name) -> str:
    """
    requestsライブラリを使用してFunction Callingリクエストを送信
    
    Args:
        message: ユーザーからのメッセージ
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
        
        # ツール定義
        tools = get_tools_definition()
        
        # メッセージの準備
        messages = [{"role": "user", "content": message}]
        
        # リクエストペイロード
        payload = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }
        
        print(f"🚀 {model}にrequestsでリクエストを送信中...")
        
        # リクエスト実行
        response = requests.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # レスポンスを処理
        print("\n🤖 LLMレスポンス:\n")
        response_message = result["choices"][0]["message"]
        
        # ツール呼び出しがあるか確認
        if "tool_calls" in response_message:
            tool_calls = response_message["tool_calls"]
            print(f"🔧 ツール呼び出しが検出されました: {len(tool_calls)}個")
            
            # 各ツール呼び出しを処理
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                
                print(f"\n📝 関数 '{function_name}' を呼び出します。引数: {function_args}")
                
                # 関数を実行
                function_response = execute_function_call(function_name, function_args)
                
                print(f"🌤 関数の結果: {function_response}")
                
                # 関数の結果をメッセージに追加
                messages.append(response_message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": function_name,
                    "content": function_response,
                })
            
            # 関数結果を含めて再度リクエスト
            second_payload = {
                "model": model,
                "messages": messages,
                "tools": tools,  # anthropicでは2回目も必要
                "tool_choice": "auto",  # anthropicでは2回目も必要
            }
            
            print("\n🔄 関数の結果を含めて再度リクエストを送信中...")
            
            second_response = requests.post(endpoint, headers=headers, json=second_payload)
            second_response.raise_for_status()
            second_result = second_response.json()
            
            print("\n🤖 最終レスポンス:\n")
            final_message = second_result["choices"][0]["message"]["content"]
            print(final_message)
            return final_message
        else:
            # ツール呼び出しがない場合は直接メッセージを表示
            content = response_message["content"]
            print(content)
            return content
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"レスポンス: {e.response.text}")
        return ""

def run_tool_call(message: str, model: str = model_name, client_type: str = "auto") -> str:
    """
    Function Callingリクエストを送信（統合インターフェース）
    
    Args:
        message: ユーザーからのメッセージ
        model: 使用するモデル名
        client_type: クライアントタイプ（openai/requests/auto）
        
    Returns:
        生成されたテキスト
    """
    print(f"📝 メッセージ: {message}")
    print(f"🤖 モデル: {model}")
    print(f"🔧 クライアントタイプ: {client_type}")
    
    if client_type == "openai" and OPENAI_CLIENT_AVAILABLE:
        return run_tool_call_with_openai(message, model)
    elif client_type == "requests" or not OPENAI_CLIENT_AVAILABLE:
        return run_tool_call_with_requests(message, model)
    else:  # auto
        # OpenAIクライアントが利用可能ならそれを使用、そうでなければrequests
        if OPENAI_CLIENT_AVAILABLE:
            return run_tool_call_with_openai(message, model)
        else:
            return run_tool_call_with_requests(message, model)

def main():
    """
    メイン関数：コマンドライン引数を解析して機能を実行
    """
    parser = argparse.ArgumentParser(description="統合Function Callingクライアント")
    parser.add_argument("message", help="LLMに送信するメッセージ")
    parser.add_argument("--model", "-m", default=model_name, help="使用するモデル名")
    parser.add_argument("--client", "-c", choices=["openai", "requests", "auto"], default="auto",
                      help="使用するクライアントタイプ（openai/requests/auto）")
    
    args = parser.parse_args()
    
    run_tool_call(args.message, args.model, args.client)

if __name__ == "__main__":
    main()
