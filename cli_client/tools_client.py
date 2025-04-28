import requests
import json
import os
import argparse

## mitmproxy を利用するため、環境変数でプロキシ設定を行います
os.environ["HTTP_PROXY"] = "http://127.0.0.1:8080"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:8080"

# mitmproxy の証明書を設定
ca_cert_path = "/Users/takagi/.mitmproxy/mitmproxy-ca-cert.pem"
os.environ['SSL_CERT_FILE'] = ca_cert_path
os.environ['REQUESTS_CA_BUNDLE'] = ca_cert_path

# LiteLLMプロキシのエンドポイント
LITELLM_PROXY_URL = "http://localhost:4000/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
}

# サンプル関数: 指定した場所の天気を返す
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

def run_tool_call(message, model):
    """Function callingを使ってメッセージを処理し、必要に応じてツールを呼び出す"""

    # ツール定義
    tools = [
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

    # メッセージの準備
    messages = [{"role": "user", "content": message}]

    # リクエストペイロード
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }

    print(f"🚀 {model}にリクエストを送信中...")

    # リクエスト実行
    try:
        response = requests.post(LITELLM_PROXY_URL, headers=HEADERS, json=payload)
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
                if function_name == "get_current_weather":
                    function_response = get_current_weather(
                        location=function_args.get("location", ""),
                        unit=function_args.get("unit", "fahrenheit")
                    )

                    print(f"🌤 天気情報: {function_response}")

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
                "tools": tools, # anthropicでは2回目も必要
                "tool_choice": "auto", # anthropicでは2回目も必要
            }

            print("\n🔄 関数の結果を含めて再度リクエストを送信中...")

            second_response = requests.post(LITELLM_PROXY_URL, headers=HEADERS, json=second_payload)
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
        return None

def main():
    """メイン関数: コマンドライン引数を解析して実行"""
    parser = argparse.ArgumentParser(description="Function Callingクライアント: OpenAIのFunction Callingを使ったデモ")
    parser.add_argument("message", help="LLMに送信するメッセージ")
    parser.add_argument("-m", "--model", help="使用するモデル", default="OpenAI/gpt-4o-mini")

    args = parser.parse_args()
    run_tool_call(args.message, args.model)

if __name__ == "__main__":
    main()
