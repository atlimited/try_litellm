// __tests__/function-call.test.js
const path = require('path');

// function-call.jsからモジュールをインポート
const {
  getCurrentWeather,
  escapeHtml,
  tools,
  executeFunctionCall
} = require('../js/function-call.js');

// グローバル変数とDOM要素のモック
global.document = {
  getElementById: jest.fn().mockReturnValue({}),
  addEventListener: jest.fn(),
  querySelectorAll: jest.fn().mockReturnValue([]),
};

global.window = {
  hljs: {
    highlightElement: jest.fn(),
  },
};

// LiteLLMのURL定数をモック
global.LITELLM_PROXY_URL = 'http://localhost:4000';

// fetchのモック
global.fetch = jest.fn();

// saveResultのモック
global.saveResult = jest.fn();

describe('getCurrentWeather', () => {
  test('should return Tokyo weather correctly', () => {
    const result = JSON.parse(getCurrentWeather('tokyo'));
    expect(result.location).toBe('Tokyo');
    expect(result.temperature).toBe('10');
    expect(result.unit).toBe('celsius');
  });

  test('should return San Francisco weather correctly', () => {
    const result = JSON.parse(getCurrentWeather('san francisco'));
    expect(result.location).toBe('San Francisco');
    expect(result.temperature).toBe('72');
    expect(result.unit).toBe('fahrenheit');
  });

  test('should return undefined for unknown locations', () => {
    const result = JSON.parse(getCurrentWeather('unknown'));
    expect(result.temperature).toBe('undefined');
  });
});

describe('escapeHtml', () => {
  test('should escape HTML characters', () => {
    const input = '<script>alert("XSS")</script>';
    const expected = '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;';
    expect(escapeHtml(input)).toBe(expected);
  });
});

describe('executeFunctionCall', () => {
  // テスト前にDOM要素をセットアップ
  beforeEach(() => {
    // DOMモックをリセット
    jest.clearAllMocks();
    
    // 結果表示エリアのモック
    const resultBox = { 
      innerHTML: '',
      id: 'tools-result'
    };
    
    const functionCallsLog = {
      innerHTML: '',
      id: 'function-calls-log'
    };
    
    const loadingIndicator = {
      id: 'tools-loading',
      classList: {
        remove: jest.fn(),
        add: jest.fn()
      }
    };
    
    const responseTimeElement = {
      textContent: '',
      classList: {
        add: jest.fn()
      }
    };
    
    // getElementById関数自体をモック
    document.getElementById = jest.fn(id => {
      if (id === 'tools-model') return { value: 'OpenAI/gpt-4o-mini' };
      if (id === 'tools-prompt') return { value: 'tokyoの天気を教えて' };
      if (id === 'tools-system-prompt') return { value: 'あなたは優秀なアシスタントです' };
      if (id === 'tools-result') return resultBox;
      if (id === 'function-calls-log') return functionCallsLog;
      if (id === 'tools-loading') return loadingIndicator;
      if (id === 'available-functions') return { innerHTML: '' };
      if (id === 'tool-definitions') return { innerHTML: '' };
      return null;
    });
    
    // querySelectorのモック
    document.querySelector = jest.fn(selector => {
      if (selector === '.tools-response-time') return responseTimeElement;
      return null;
    });
  });
  
  test('should handle API response with function call successfully', async () => {
    // 最初のfetchレスポンスのモック (関数呼び出しあり)
    const firstResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        id: 'chatcmpl-123',
        choices: [{
          message: {
            role: 'assistant',
            content: null,
            tool_calls: [{
              id: 'call_123',
              type: 'function',
              function: {
                name: 'get_current_weather',
                arguments: JSON.stringify({ location: 'tokyo' })
              }
            }]
          },
          index: 0,
          finish_reason: 'tool_calls'
        }]
      })
    };
    
    // 2回目のfetchレスポンスのモック
    const secondResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        id: 'chatcmpl-456',
        choices: [{
          message: {
            role: 'assistant',
            content: '東京の天気は晴れで、気温は10度(摂氏)です。'
          },
          index: 0,
          finish_reason: 'stop'
        }]
      })
    };
    
    // fetchのモック実装
    fetch.mockResolvedValueOnce(firstResponse).mockResolvedValueOnce(secondResponse);
    
    // 関数実行
    await executeFunctionCall();
    
    // 検証
    // fetchが2回呼ばれたことを確認
    expect(fetch).toHaveBeenCalledTimes(2);
    
    // システムプロンプトが含まれていることを確認
    const firstCall = fetch.mock.calls[0][1];
    expect(JSON.parse(firstCall.body).messages).toContainEqual({
      role: 'system',
      content: 'あなたは優秀なアシスタントです'
    });
    
    // ローディングインジケータが正しく制御されたことを確認
    const loadingIndicator = document.getElementById('tools-loading');
    expect(loadingIndicator.classList.remove).toHaveBeenCalledWith('hidden');
    expect(loadingIndicator.classList.add).toHaveBeenCalledWith('hidden');
    
    // resultBoxに結果が表示されたことを確認
    const resultBox = document.getElementById('tools-result');
    expect(resultBox.innerHTML).toContain('東京の天気は晴れで');
  });
  
  test('should handle API error gracefully', async () => {
    // エラーレスポンスのモック
    fetch.mockRejectedValueOnce(new Error('API接続エラー'));
    
    // 関数実行
    await executeFunctionCall();
    
    // エラーが表示されることを確認
    const resultBox = document.getElementById('tools-result');
    expect(resultBox.innerHTML).toContain('エラーが発生しました');
    expect(resultBox.innerHTML).toContain('API接続エラー');
    
    // ローディングインジケータが非表示になることを確認
    const loadingIndicator = document.getElementById('tools-loading');
    expect(loadingIndicator.classList.add).toHaveBeenCalledWith('hidden');
  });
  
  test('should handle direct response without function call', async () => {
    // 関数呼び出しなしのレスポンスをモック
    const response = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        id: 'chatcmpl-789',
        choices: [{
          message: {
            role: 'assistant',
            content: 'お手伝いできることはありますか？'
          },
          index: 0,
          finish_reason: 'stop'
        }]
      })
    };
    
    fetch.mockResolvedValueOnce(response);
    
    // 関数実行
    await executeFunctionCall();
    
    // 検証
    // fetchが1回だけ呼ばれたことを確認
    expect(fetch).toHaveBeenCalledTimes(1);
    
    // 結果が直接表示されることを確認
    const resultBox = document.getElementById('tools-result');
    expect(resultBox.innerHTML).toContain('お手伝いできることはありますか？');
  });
});
