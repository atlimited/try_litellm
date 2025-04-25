import os
import requests
from openai import OpenAI
from pathlib import Path
import time

client = OpenAI(
    base_url="http://localhost:4000/v1", # LiteLLMプロキシURL
)

# 出力ディレクトリの設定
output_dir = Path("./generated_images")
output_dir.mkdir(exist_ok=True)

response = client.images.generate(
    model="dall-e-3",  # シンプルな標準モデル名
    prompt="A futuristic Japanese garden with cherry blossoms, traditional elements, and modern technology integrated seamlessly.",
    n=1,
    size="1024x1024",  # サイズを明示的に指定
    quality="standard",  # 品質を明示的に指定
    response_format="url",
)

# 画像URLの取得
image_url = response.data[0].url
print("Image URL:", image_url)

# 画像をダウンロードして保存
try:
    # 画像のダウンロード
    image_response = requests.get(image_url)
    
    if image_response.status_code == 200:
        # タイムスタンプを使ってユニークなファイル名を生成
        timestamp = int(time.time())
        image_path = output_dir / f"generated_image_{timestamp}.png"
        
        # 画像の保存
        with open(image_path, "wb") as f:
            f.write(image_response.content)
        
        print(f"Image successfully saved to: {image_path}")
    else:
        print(f"Failed to download image: Status code {image_response.status_code}")
        
except Exception as e:
    print(f"Error occurred while saving the image: {e}")