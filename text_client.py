from openai import OpenAI

client = OpenAI(
    base_url="http://0.0.0.0:8000/v1" # litellm-proxy-base url
)

# モデル選択（使用したいモデルのコメントを外す）
#model_name = "gpt-4o-mini"
#model_name = "gemini-2.0-flash"
#model_name = "Meta-Llama-3.2-3B-Instruct"
model_name = "Llama-4-Maverick-17B-128E-Instruct"

response = client.chat.completions.create(
    model=model_name,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "hello!"
                }
            ]
        }
    ],
)

print(response)