# LiteLLM クライアントアプリケーション

LiteLLM プロキシを通じて様々な言語モデル（OpenAI、Anthropic、Gemini など）にアクセスできるクライアントアプリケーションです。Web インターフェースとコマンドラインの両方から利用できます。

## 主な機能

- **テキスト生成**: 様々なモデルを使用したテキスト生成
- **画像生成**: DALL-E や Stable Diffusion などによる画像生成
- **画像認識**: 画像の分析とテキスト説明（Vision API）
- **音声認識**: 音声からテキストへの変換（Speech-to-Text）
- **音声合成**: テキストから音声への変換（Text-to-Speech）
- **関数呼び出し**: LLMによる関数呼び出し機能（Function Calling）
- **マルチモーダル対応**: テキスト、画像、音声を組み合わせた入力が可能

## 前提条件

- Python 3.8以上
- Node.js 16以上（Webクライアント用）
- [LiteLLM](https://github.com/BerriAI/litellm) がインストールされていること
- 各種APIキー（OpenAI、Anthropic、Googleなど使用するサービスに応じて）

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/try_litellm.git
cd try_litellm
```

### 2. 依存パッケージのインストール

```bash
pip install -r requiremens.txt
```

Webクライアント用の依存パッケージも必要な場合：

```bash
cd web_client
npm install
```

### 3. 環境変数の設定

各種APIキーを環境変数として設定します：

```bash
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export GOOGLE_API_KEY="your_google_api_key"
# 他にも必要なAPIキーがあれば設定
```

### 4. LiteLLM プロキシの起動

```bash
./run_proxy.sh
```

または直接実行：

```bash
litellm --config litellm.config --port 4000
```

## 使用方法

### Webクライアント

1. Webクライアントを起動します：

```bash
cd web_client
# 必要に応じて npm run build を実行
# シンプルな HTTP サーバーで提供
python -m http.server 8000
```

2. ブラウザで `http://localhost:8000` にアクセスします
3. 各種機能タブ（テキスト、画像生成、音声など）を選択して利用できます

### コマンドラインクライアント

各機能ごとに専用のクライアントが用意されています：

**テキスト生成**:
```bash
cd cli_client
python text_client.py "ここに質問やプロンプトを入力"
```

**画像生成**:
```bash
python image_generation_client.py "画像の説明"
```

**画像認識**:
```bash
python vision_client.py "画像について質問" path/to/image.jpg
```

**音声認識**:
```bash
python audio_client.py path/to/audio_file.mp3
```

**テキスト読み上げ**:
```bash
python tts_client.py "読み上げるテキスト"
```

**関数呼び出し**:
```bash
python tools_client.py "天気を教えて" 
```

## 設定カスタマイズ

`litellm.config` ファイルを編集することで、使用可能なモデルの設定をカスタマイズできます。
詳細は [LiteLLMのドキュメント](https://litellm.vercel.app/docs/proxy/configuration) を参照してください。

## 開発とテスト

### Webクライアントのテスト

Webクライアントには包括的なテストが実装されています：

```bash
cd web_client
npm test
```

特定のモジュールのみテストする場合：

```bash
npm test -- __tests__/text-generation.test.js
```

カバレッジレポートの生成：

```bash
npm test -- --coverage
```

## Gemini対応

このクライアントは、LiteLLM プロキシを通じて Gemini のマルチモーダル機能を使用することができます。
Gemini APIの特性に合わせたリクエスト形式を自動的に構築します：

- 画像生成時には `modalities` パラメータを適切に設定
- マルチモーダル入力（テキスト＋画像）の場合、`content` フィールドを配列形式で構成
- 画像入力には `image_url` 形式でBase64エンコード画像を含める

## 注意事項

- APIキーは環境変数として設定し、ソースコード内に直接記述しないでください
- APIの使用には料金が発生する場合があります。各サービスプロバイダーの料金体系を確認してください
- 実運用環境では適切なセキュリティ対策を施してください

## ライセンス

MIT
