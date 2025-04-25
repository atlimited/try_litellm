import os
import requests
import base64
from openai import OpenAI

client = OpenAI(
    base_url="http://0.0.0.0:8000/v1" # litellm-proxy-base url
)

def get_base64_encoded_image(image_url):
    # URLから画像をダウンロード
    response = requests.get(image_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image: {response.status_code}")
    
    # 画像のMIMEタイプを判断（単純化のためURLから拡張子を抽出）
    extension = image_url.split('.')[-1].lower()
    if extension in ['jpg', 'jpeg']:
        mime_type = 'image/jpeg'
    elif extension == 'png':
        mime_type = 'image/png'
    elif extension == 'webp':
        mime_type = 'image/webp'
    else:
        mime_type = 'image/jpeg'  # デフォルト
    
    # Base64エンコード
    base64_image = base64.b64encode(response.content).decode('utf-8')
    
    # 適切な形式で返す
    return f"data:{mime_type};base64,{base64_image}"

# サンプル画像URL
image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

# モデル選択（使用したいモデルのコメントを外す）
#model_name = "gpt-4o-mini"
model_name = "gemini-2.0-flash"
# model_name = "Meta-Llama-3.2-3B-Instruct"
#model_name = "Llama-4-Maverick-17B-128E-Instruct"

# ベース64エンコードされた画像を取得
base64_image = get_base64_encoded_image(image_url)

response = client.chat.completions.create(
    model=model_name,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What's in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": base64_image
                    }
                }
            ]
        }
    ],
)

print(response)