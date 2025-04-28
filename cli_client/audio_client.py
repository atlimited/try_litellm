import requests
import os
import base64
from openai import OpenAI

client = OpenAI(
    base_url="http://0.0.0.0:4000/v1" # litellm-proxy-base url
)


# Fetch the audio file and convert it to a base64 encoded string
url = "https://openaiassets.blob.core.windows.net/$web/API/docs/audio/alloy.wav"
response = requests.get(url)
response.raise_for_status()
wav_data = response.content
encoded_string = base64.b64encode(wav_data).decode('utf-8')

# モデル選択（使用したいモデルのコメントを外す）
#model_name = "gpt-4o-audio-preview"
#model_name = "SambaNova/Whisper-Large-v3"
model_name = "SambaNova/Qwen2-Audio-7B-Instruct"
#model_name = 'OpenAI/whisper-1'
#model_name = 'OpenAI/gpt-4o-mini-transcribe'

if model_name == "gpt-4o-audio-preview":
    completion = client.chat.completions.create(
        model=model_name,
#    modalities=["text", "audio"],
#    audio={"voice": "alloy", "format": "wav"},
        messages=[
            {
                "role": "user",
                "content": [
                    { 
                        "type": "text",
                        "text": "What is in this recording?"
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encoded_string,
                            "format": "wav"
                        }
                    }
                ]
            },
        ]
    )
    print(completion.choices[0].message)

else:
    audio_url = "/tmp/temp_audio.wav"
    with open(audio_url, "wb") as f:
        f.write(wav_data)
    
    with open(audio_url, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model=model_name,
            file=audio_file,
            #language="ja"  # 明示的に日本語を指定
        )
    
    print(response)
    os.remove(audio_url)  # 一時ファイルを削除
    