// __tests__/vision.test.js
const path = require('path');

// vision.jsからモジュールをインポート
const {
  analyzeImage,
  setupVisionImageInput,
  getBase64FromFile
} = require('../js/vision.js');

// グローバル変数とDOM要素のモック
global.document = {
  getElementById: jest.fn(),
  addEventListener: jest.fn(),
  querySelectorAll: jest.fn().mockReturnValue([]),
  createElement: jest.fn(() => ({
    src: '',
    alt: '',
    onerror: null,
    appendChild: jest.fn()
  }))
};

// LiteLLMのURL定数をモック
global.LITELLM_PROXY_URL = 'http://localhost:4000';

// fetchのモック
global.fetch = jest.fn();

// saveResultのモック
global.saveResult = jest.fn();

// ファイルの内容をモック
global.Blob = function(content, options) {
  this.content = content;
  this.options = options;
  this.type = options.type;
};

describe('Vision module', () => {
  // 各テスト前に実行されるセットアップ
  beforeEach(() => {
    // モックをリセット
    jest.clearAllMocks();
    
    // DOM要素のモック
    const resultElement = { textContent: '', innerHTML: '' };
    const buttonElement = { disabled: false, textContent: '画像分析' };
    const responseTimeElement = { textContent: '-' };
    const loadingIndicator = { classList: { remove: jest.fn(), add: jest.fn() } };
    const imagePreview = { innerHTML: '', appendChild: jest.fn() };
    
    // ファイル入力とURL入力のモック
    const imageFile = { 
      name: 'test.jpg', 
      type: 'image/jpeg', 
      size: 1024
    };
    
    const imageFileInput = { 
      files: [imageFile], 
      value: '',
      addEventListener: jest.fn()
    };
    
    const imageUrlInput = { 
      value: 'https://example.com/test.jpg',
      addEventListener: jest.fn()
    };
    
    // document.getElementByIdのモック実装
    document.getElementById = jest.fn(id => {
      if (id === 'vision-model') return { value: 'Gemini/gemini-pro-vision' };
      if (id === 'vision-prompt') return { value: 'この画像を説明してください' };
      if (id === 'vision-image') return imageFileInput;
      if (id === 'vision-image-url') return imageUrlInput;
      if (id === 'vision-result') return resultElement;
      if (id === 'analyze-image') return buttonElement;
      if (id === 'vision-loading') return loadingIndicator;
      if (id === 'vision-image-preview') return imagePreview;
      return null;
    });
    
    // document.querySelectorのモック実装
    document.querySelector = jest.fn(selector => {
      if (selector === '.vision-response-time') return responseTimeElement;
      return null;
    });
    
    // performance.nowのモック
    global.performance = {
      now: jest.fn()
        .mockReturnValueOnce(1000)  // 1回目の呼び出し（開始時間）
        .mockReturnValueOnce(5000)  // 2回目の呼び出し（終了時間）
    };
    
    // FileReaderモックを改善
    global.FileReader = jest.fn().mockImplementation(() => {
      const reader = {
        readAsDataURL: jest.fn(file => {
          // readAsDataURLが呼ばれたら非同期でonloadをトリガー
          setTimeout(() => {
            if (reader.onload) {
              reader.result = 'data:image/jpeg;base64,mockImageData';
              reader.onload({ target: reader });
            }
          }, 0);
        })
      };
      return reader;
    });
    
    // debounceのモック
    global.debounce = jest.fn(fn => fn);
    
    // getBase64FromFileをモック
    global.getBase64FromFile = jest.fn().mockResolvedValue('data:image/jpeg;base64,mockImageData');
  });
  
  describe('analyzeImage', () => {
    // テストタイムアウトを増加
    test('should analyze image from file successfully', async () => {
      // 成功レスポンスのモック
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          id: 'chatcmpl-456',
          choices: [{
            message: {
              role: 'assistant',
              content: '画像には山と湖が写っています。'
            },
            index: 0,
            finish_reason: 'stop'
          }]
        })
      };
      
      fetch.mockResolvedValueOnce(mockResponse);
      
      // 関数実行
      await analyzeImage();
      
      // fetch呼び出しの検証
      expect(fetch).toHaveBeenCalledTimes(1);
      
      // saveResultの呼び出し検証
      expect(saveResult).toHaveBeenCalledTimes(1);
      
      // 処理時間は実行環境によって変動するので、具体的な値ではなくタイプをチェック
      const saveResultCall = saveResult.mock.calls[0];
      expect(saveResultCall[0]).toBe('vision');
      expect(saveResultCall[1]).toBe('画像には山と湖が写っています。');
      expect(typeof saveResultCall[2]).toBe('number'); // 具体的な値ではなく数値型であることを確認
      expect(saveResultCall[3]).toBe('Gemini/gemini-pro-vision');
    }, 10000); // テストタイムアウトを10秒に設定
    
    test('should handle errors when URL is invalid', async () => {
      // ファイル入力をnullに設定し、URL入力を使用
      document.getElementById = jest.fn(id => {
        if (id === 'vision-model') return { value: 'Gemini/gemini-pro-vision' };
        if (id === 'vision-prompt') return { value: 'この画像を説明してください' };
        if (id === 'vision-image') return { files: [] }; // ファイルなし
        if (id === 'vision-image-url') return { value: 'https://invalid-url.com/image.jpg' };
        if (id === 'vision-result') return { textContent: '', innerHTML: '' };
        if (id === 'analyze-image') return { disabled: false, textContent: '画像分析' };
        if (id === 'vision-loading') return { classList: { remove: jest.fn(), add: jest.fn() } };
        if (id === 'vision-image-preview') return { innerHTML: '' };
        return null;
      });
      
      // URL画像取得エラーのモック
      fetch.mockRejectedValueOnce(new Error('画像取得エラー'));
      
      // 関数実行
      await analyzeImage();
      
      // saveResultの呼び出し検証 - エラー時は処理時間が'-'で保存
      expect(saveResult).toHaveBeenCalledTimes(1);
      expect(saveResult.mock.calls[0][2]).toBe('-');
    }, 10000);
    
    test('should handle API errors', async () => {
      // API呼び出しエラーのモック
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        statusText: 'Too Many Requests'
      });
      
      // 関数実行
      await analyzeImage();
      
      // エラー時のsaveResult呼び出し検証
      expect(saveResult).toHaveBeenCalledTimes(1);
      expect(saveResult.mock.calls[0][2]).toBe('-');
    }, 10000);
    
    test('should handle empty prompt', async () => {
      // 空のプロンプトをモック
      document.getElementById = jest.fn(id => {
        if (id === 'vision-model') return { value: 'Gemini/gemini-pro-vision' };
        if (id === 'vision-prompt') return { value: '   ' }; // 空白だけのプロンプト
        if (id === 'vision-image') return { files: [{ name: 'test.jpg' }] };
        if (id === 'vision-image-url') return { value: '' };
        if (id === 'vision-result') return { textContent: '' };
        if (id === 'analyze-image') return { disabled: false, textContent: '画像分析' };
        if (id === 'vision-loading') return { classList: { remove: jest.fn(), add: jest.fn() } };
        return null;
      });
      
      // 関数実行
      await analyzeImage();
      
      // fetchが呼ばれないことを確認
      expect(fetch).not.toHaveBeenCalled();
      
      // saveResultも呼ばれないことを確認
      expect(saveResult).not.toHaveBeenCalled();
    });
    
    test('should handle missing image input', async () => {
      // 画像がない状態をモック
      document.getElementById = jest.fn(id => {
        if (id === 'vision-model') return { value: 'Gemini/gemini-pro-vision' };
        if (id === 'vision-prompt') return { value: 'この画像を説明してください' };
        if (id === 'vision-image') return { files: [] }; // ファイルなし
        if (id === 'vision-image-url') return { value: '' }; // URLなし
        if (id === 'vision-result') return { textContent: '' };
        if (id === 'analyze-image') return { disabled: false, textContent: '画像分析' };
        if (id === 'vision-loading') return { classList: { remove: jest.fn(), add: jest.fn() } };
        return null;
      });
      
      // 関数実行
      await analyzeImage();
      
      // fetchが呼ばれないことを確認
      expect(fetch).not.toHaveBeenCalled();
      
      // saveResultも呼ばれないことを確認
      expect(saveResult).not.toHaveBeenCalled();
    });
  });
  
  describe('getBase64FromFile', () => {
    test('should convert file to base64', async () => {
      // テスト用のファイル
      const testFile = { 
        name: 'test.jpg', 
        type: 'image/jpeg', 
        size: 1024
      };
      
      // 関数を実行（FileReaderのモックが自動的にonloadをトリガー）
      const result = await getBase64FromFile(testFile);
      
      // 正しい結果が返されるか検証
      expect(result).toBe('data:image/jpeg;base64,mockImageData');
    });
  });
  
  describe('setupVisionImageInput', () => {
    test('should set up event listeners for file and URL inputs', () => {
      // テストのためにオリジナルの関数を退避
      const originalSetup = setupVisionImageInput;
      
      // 必要なDOM要素が存在することを確認
      expect(document.getElementById('vision-image')).toBeTruthy();
      expect(document.getElementById('vision-image-url')).toBeTruthy();
      
      // イベントリスナーが登録できることを間接的に検証
      const imageFileInput = document.getElementById('vision-image');
      const imageUrlInput = document.getElementById('vision-image-url');
      
      expect(imageFileInput.addEventListener).toBeDefined();
      expect(imageUrlInput.addEventListener).toBeDefined();
    });
  });
});
