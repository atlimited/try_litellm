# LiteLLM クライアントアプリケーション

このプロジェクトは、[LiteLLM](https://github.com/BerriAI/litellm) プロキシを通じて様々な言語モデル（OpenAI、Anthropic、Gemini など）にアクセスできる統合クライアントアプリケーションです。LiteLLMの主な利点は、複数のLLMプロバイダーに対して統一されたインターフェースを提供することで、アプリケーションがプロバイダー間で簡単に切り替えられることです。

## 主な機能

- **統一インターフェース**: 様々なLLMプロバイダーに対して一貫したAPIを提供
- **テキスト生成**: 各種モデルを使用したテキスト生成と会話
- **画像認識**: マルチモーダルモデルを活用した画像分析（Vision API）
- **音声認識**: 音声からテキストへの変換（Speech-to-Text）
- **音声合成**: テキストから音声への変換（Text-to-Speech）
- **関数呼び出し**: LLMによる関数呼び出し機能（Function Calling）
- **フォールバック機能**: 一つのプロバイダーが失敗した場合に別のプロバイダーに切り替え可能

## アーキテクチャ

このプロジェクトは主にLiteLLMプロキシを使用して、様々なLLMプロバイダーにアクセスします：

1. **コアクライアント**
   - `text_client.py` - テキスト生成のための基本クライアント
   - `vision_client.py` - 画像認識のためのクライアント
   - `speech_client.py` - 音声認識（Speech-to-Text）のためのクライアント
   - `tts_client.py` - 音声合成（Text-to-Speech）のためのクライアント
   - `tools_client.py` - 関数呼び出し機能のためのクライアント

2. **モデル特化クライアント**
   - `gemini_litellm_client.py` - Gemini向けのLiteLLMクライアント実装
   - `gemini_direct_requests_client.py` - 比較用の直接API呼び出し実装

## 前提条件

- Python 3.8以上
- Node.js 16以上（Webクライアント用）
- [LiteLLM](https://github.com/BerriAI/litellm) がインストールされていること
- 各種APIキー（使用するプロバイダーに応じて）

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/atlimited/try_litellm.git
cd try_litellm
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
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
3. 各種機能タブを選択して利用できます

### コマンドラインクライアント

#### テキスト生成

```bash
cd cli_client
python text_client.py "ここに質問やプロンプトを入力"
```

#### 画像認識

```bash
python vision_client.py "画像について質問" path/to/image.jpg
```

#### 音声認識

```bash
python speech_client.py path/to/audio_file.mp3
```

#### 音声合成

```bash
python tts_client.py "読み上げるテキスト" output_filename.mp3
```

#### 関数呼び出し

```bash
python tools_client.py "天気を教えて" 
```

#### Geminiモデル向けクライアント

テキストチャット:
```bash
python gemini_litellm_client.py chat "ここに質問やプロンプトを入力"
```

画像認識:
```bash
python gemini_litellm_client.py vision "画像について質問" path/to/image.jpg
```

## LiteLLMのメリット

このプロジェクトでは、LiteLLMを使用することで以下のメリットを得ています：

1. **プロバイダーの抽象化**: 複数のLLMプロバイダー（OpenAI、Anthropic、Googleなど）を統一インターフェースで利用
2. **簡単な切り替え**: 設定を変更するだけで、異なるプロバイダーやモデルに切り替え可能
3. **コスト最適化**: プロバイダーごとの価格差を活用して、利用コストを最適化
4. **フォールバック**: 一つのプロバイダーが停止していても、別のプロバイダーに自動的に切り替え可能
5. **一貫した応答形式**: 異なるプロバイダーからの応答を統一された形式で受け取れる

## LiteLLM設定

`litellm.config` ファイルでは、利用可能なモデルとルーティングを設定できます。詳細は [LiteLLMのドキュメント](https://litellm.vercel.app/docs/proxy/configuration) を参照してください。

例えば、以下のような設定が可能です：
- 異なるプロバイダー間のフェイルオーバー
- コスト最適化のためのモデル選択
- キャッシュ設定
- レート制限

## テスト

### Pythonクライアントのテスト

クライアントの機能を検証するためのテスト：

```bash
cd cli_client
python -m unittest tests/test_text_client.py
python -m unittest tests/test_gemini_litellm_client.py
pytest tests/test_gemini_direct_requests_client.py
```

### JavaScriptクライアントのテスト

Webクライアントのテスト：

```bash
cd web_client
npm test
```

特定のテストファイルだけを実行：

```bash
npm test -- __tests__/text-generation.test.js
```

カバレッジレポートの生成：

```bash
npm test -- --coverage
```

## 注意事項

- APIキーは環境変数として設定し、ソースコード内に直接記述しないでください
- APIの使用には料金が発生する場合があります。各サービスプロバイダーの料金体系を確認してください
- 実運用環境では適切なセキュリティ対策を施してください

## ライセンス

MIT
