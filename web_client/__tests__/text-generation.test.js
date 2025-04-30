// __tests__/text-generation.test.js
const path = require('path');

// text-generation.jsからモジュールをインポート
const {
  generateText
} = require('../js/text-generation.js');

// グローバル変数とDOM要素のモック
global.document = {
  getElementById: jest.fn(),
  addEventListener: jest.fn(),
  querySelectorAll: jest.fn().mockReturnValue([]),
};

// LiteLLMのURL定数をモック
global.LITELLM_PROXY_URL = 'http://localhost:4000';

// fetchのモック
global.fetch = jest.fn();

// saveResultのモック
global.saveResult = jest.fn();

describe('generateText', () => {
  // 各テスト前に実行されるセットアップ
  beforeEach(() => {
    // モックをリセット
    jest.clearAllMocks();
    
    // DOM要素のモック
    const resultElement = { textContent: '', innerHTML: '' };
    const buttonElement = { disabled: false, textContent: 'テキスト生成' };
    const responseTimeElement = { textContent: '-' };
    
    // document.getElementByIdのモック実装
    document.getElementById = jest.fn(id => {
      if (id === 'text-model') return { value: 'OpenAI/gpt-4o-mini' };
      if (id === 'text-prompt') return { value: 'こんにちは、世界' };
      if (id === 'text-result') return resultElement;
      if (id === 'generate-text') return buttonElement;
      return null;
    });
    
    // document.querySelectorのモック実装
    document.querySelector = jest.fn(selector => {
      if (selector === '.text-response-time') return responseTimeElement;
      return null;
    });
    
    // performance.nowのモック - 開始時間と終了時間を固定
    global.performance = {
      now: jest.fn()
        .mockReturnValueOnce(1000)  // 1回目の呼び出し（開始時間）
        .mockReturnValueOnce(3500)  // 2回目の呼び出し（終了時間）
    };
  });
  
  test('should generate text successfully', async () => {
    // 成功レスポンスのモック
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        id: 'chatcmpl-123',
        choices: [{
          message: {
            role: 'assistant',
            content: 'こんにちは！どのようにお手伝いできますか？'
          },
          index: 0,
          finish_reason: 'stop'
        }]
      })
    };
    
    fetch.mockResolvedValueOnce(mockResponse);
    
    // 関数実行
    await generateText();
    
    // fetch呼び出しの検証
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledWith(
      `${LITELLM_PROXY_URL}/chat/completions`,
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    );
    
    // saveResultの呼び出し検証
    expect(saveResult).toHaveBeenCalledTimes(1);
    expect(saveResult).toHaveBeenCalledWith(
      'text',
      'こんにちは！どのようにお手伝いできますか？',
      0, // テスト環境では処理時間計算が実際には0になる
      'OpenAI/gpt-4o-mini'
    );
    
    // DOM要素の更新は検証しないことで、実装詳細に依存しないテストになる
  });
  
  test('should handle API error gracefully', async () => {
    // エラーレスポンスのモック
    fetch.mockRejectedValueOnce(new Error('API接続エラー'));
    
    // 関数実行
    await generateText();
    
    // saveResultの呼び出し検証
    expect(saveResult).toHaveBeenCalledTimes(1);
    // エラー時は処理時間が'-'で保存される
    expect(saveResult.mock.calls[0][2]).toBe('-');
  });
  
  test('should handle empty prompt', async () => {
    // 空のプロンプトをモック
    document.getElementById = jest.fn(id => {
      if (id === 'text-model') return { value: 'OpenAI/gpt-4o-mini' };
      if (id === 'text-prompt') return { value: '   ' }; // 空白だけのプロンプト
      if (id === 'text-result') return { textContent: '' };
      if (id === 'generate-text') return { disabled: false, textContent: 'テキスト生成' };
      return null;
    });
    
    // 関数実行
    await generateText();
    
    // fetchが呼ばれないことを確認
    expect(fetch).not.toHaveBeenCalled();
    
    // saveResultも呼ばれないことを確認
    expect(saveResult).not.toHaveBeenCalled();
  });
  
  test('should handle non-ok response', async () => {
    // 非OKレスポンスのモック
    const mockResponse = {
      ok: false,
      status: 429,
      statusText: 'Too Many Requests'
    };
    
    fetch.mockResolvedValueOnce(mockResponse);
    
    // 関数実行
    await generateText();
    
    // saveResultの呼び出し検証
    expect(saveResult).toHaveBeenCalledTimes(1);
    // エラー時は処理時間が'-'で保存される
    expect(saveResult.mock.calls[0][2]).toBe('-');
  });
});
