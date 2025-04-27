import os
from openai import OpenAI
from pathlib import Path
import time

# OpenAI クライアントの初期化
client = OpenAI(
    base_url="http://localhost:4000/v1",  # litellm-proxy-base url
)

# 出力ディレクトリの設定
output_dir = Path("./generated_audio")
output_dir.mkdir(exist_ok=True)

# TTS モデルの設定
model_name = "tts-1"  # 標準モデル
# model_name = "tts-1-hd"  # 高品質モデル（こちらは計算コストが高い）

# 変換するテキスト
text = "こんにちは。これはLiteLLMプロキシを通じて生成された音声サンプルです。Text-to-Speech APIを使用して、テキストから音声への変換を行っています。"

# 音声生成パラメータ
voice = "alloy"  # 利用可能な声: alloy, echo, fable, onyx, nova, shimmer
# voice = "shimmer"  # 女性っぽい声
# voice = "echo"     # 男性っぽい声

print(f"Generating audio with model: {model_name}, voice: {voice}")
print(f"Text: {text}")

try:
    # 音声生成
    response = client.audio.speech.create(
        model=model_name,
        voice=voice,
        input=text
    )

    # 音声ファイルの保存
    timestamp = int(time.time())
    audio_path = output_dir / f"speech_{voice}_{timestamp}.mp3"
    
    response.stream_to_file(str(audio_path))
    print(f"Audio saved to: {audio_path}")

except Exception as e:
    print(f"Error occurred: {e}")