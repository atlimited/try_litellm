// image-generation.test.js
const { generateImage } = require('../js/image-generation');

// グローバル変数の定義
global.LITELLM_PROXY_URL = 'http://localhost:8000';

// saveResult関数をモック
global.saveResult = jest.fn();

// DOM要素作成のヘルパー関数
function createElementMock(attrs = {}) {
    return {
        addEventListener: jest.fn(),
        classList: {
            remove: jest.fn(),
            add: jest.fn()
        },
        style: {},
        // プロパティ更新を追跡するための仕組み
        _textContent: attrs.textContent || '',
        get textContent() {
            return this._textContent;
        },
        set textContent(value) {
            this._textContent = value;
        },
        _innerHTML: attrs.innerHTML || '',
        get innerHTML() {
            return this._innerHTML;
        },
        set innerHTML(value) {
            this._innerHTML = value;
        },
        appendChild: jest.fn(),
        ...attrs
    };
}

// ドキュメント関数のモック
document.createElement = jest.fn(tag => {
    if (tag === 'img') {
        return createElementMock({ 
            src: '',
            alt: ''
        });
    }
    if (tag === 'p') {
        return createElementMock();
    }
    return createElementMock();
});

// ドキュメントクエリ関数のモック
document.querySelector = jest.fn(() => createElementMock({ textContent: '-' }));

describe('Image Generation module', () => {
    let domElements;
    
    beforeEach(() => {
        // DOM要素の初期化
        domElements = {
            'image-model': createElementMock({ value: 'dall-e-3' }),
            'image-prompt': createElementMock({ value: '美しい富士山の風景' }),
            'image-size': createElementMock({ value: '1024x1024' }),
            'image-quality': createElementMock({ value: 'standard' }),
            'image-result': createElementMock({ 
                innerHTML: '', 
                textContent: '',
                appendChild: jest.fn()
            }),
            'image-loading': createElementMock(),
            'generate-image': createElementMock({ 
                disabled: false, 
                textContent: '画像生成' 
            })
        };
        
        // getElementById をモック化
        document.getElementById = jest.fn(id => {
            return domElements[id] || createElementMock();
        });
        
        // fetchのモック
        global.fetch = jest.fn();
        
        // パフォーマンス測定のモック
        global.performance = {
            now: jest.fn()
        };
        
        // パフォーマンスタイマーのリセット
        performance.now = jest.fn()
            .mockReturnValueOnce(1000)  // 開始時間
            .mockReturnValueOnce(5000); // 終了時間（処理時間は4000ms）
    });
    
    afterEach(() => {
        jest.clearAllMocks();
    });
    
    it('should generate image successfully', async () => {
        // 成功レスポンスをモック
        const mockImageUrl = 'https://example.com/generated-image.png';
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ 
                data: [{ url: mockImageUrl }] 
            })
        });
        
        // saveResultのモックをリセット
        saveResult.mockReset();
        
        // 関数実行
        await generateImage();
        
        // APIリクエストが正しく行われたか確認
        expect(fetch).toHaveBeenCalledWith(
            'http://localhost:8000/images/generations',
            expect.objectContaining({
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: 'dall-e-3',
                    prompt: '美しい富士山の風景',
                    n: 1,
                    size: '1024x1024',
                    quality: 'standard',
                    response_format: 'url'
                })
            })
        );
        
        // 画像要素が作成されたか確認
        expect(document.createElement).toHaveBeenCalledWith('img');
        
        // 結果表示が更新されたか確認
        const resultElement = document.getElementById('image-result');
        expect(resultElement.appendChild).toHaveBeenCalled();
        
        // URL表示用のテキスト要素が作成されたか確認
        expect(document.createElement).toHaveBeenCalledWith('p');
        
        // saveResultが呼び出されたことを確認
        expect(saveResult).toHaveBeenCalled();
        expect(saveResult.mock.calls[0][0]).toBe('image');
        expect(saveResult.mock.calls[0][3]).toBe('dall-e-3');
    });
    
    it('should handle API errors', async () => {
        // エラーレスポンスをモック
        fetch.mockResolvedValueOnce({
            ok: false,
            status: 429
        });
        
        // saveResultのモックをリセット
        saveResult.mockReset();
        
        // DOM要素のモックを更新
        const resultElement = createElementMock();
        document.getElementById = jest.fn(id => {
            if (id === 'image-result') {
                return resultElement;
            }
            return domElements[id] || createElementMock();
        });
        
        // 関数実行
        await generateImage();
        
        // エラーメッセージが表示されたか確認
        expect(resultElement.textContent).toContain('エラーが発生しました');
        
        // ボタンとローディングインジケーターが更新されたか確認
        const button = document.getElementById('generate-image');
        expect(button.disabled).toBe(false);
        expect(button.textContent).toBe('画像生成');
        
        // エラー時の処理時間表示
        const responseTimeElement = document.querySelector('.image-response-time');
        expect(responseTimeElement.textContent).toBe('-');
        
        // saveResultが呼び出されたことを確認
        expect(saveResult).toHaveBeenCalled();
        expect(saveResult.mock.calls[0][0]).toBe('image');
        expect(saveResult.mock.calls[0][2]).toBe('-');
        expect(saveResult.mock.calls[0][3]).toBe('dall-e-3');
    });
    
    it('should handle empty prompt', async () => {
        // 空のプロンプトをモック
        document.getElementById = jest.fn(id => {
            if (id === 'image-prompt') {
                return createElementMock({ value: '   ' }); // 空白のみのプロンプト
            }
            return domElements[id] || createElementMock();
        });
        
        // 関数実行
        await generateImage();
        
        // エラーメッセージが表示されたか確認
        const resultElement = document.getElementById('image-result');
        expect(resultElement.textContent).toBe('プロンプトを入力してください。');
        
        // API呼び出しが行われていないことを確認
        expect(fetch).not.toHaveBeenCalled();
    });
    
    it('should update UI elements correctly during image generation', async () => {
        // 成功レスポンスをモック
        fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ 
                data: [{ url: 'https://example.com/image.png' }] 
            })
        });
        
        // ボタンとローディング要素を取得
        const button = document.getElementById('generate-image');
        const loadingIndicator = document.getElementById('image-loading');
        
        // 関数実行
        const generatePromise = generateImage();
        
        // 非同期処理が始まった直後のUI状態を確認
        expect(button.disabled).toBe(true);
        expect(button.textContent).toBe('生成中...');
        expect(loadingIndicator.classList.remove).toHaveBeenCalledWith('hidden');
        
        // 非同期処理の完了を待つ
        await generatePromise;
        
        // 処理完了後のUI状態を確認
        expect(button.disabled).toBe(false);
        expect(button.textContent).toBe('画像生成');
        expect(loadingIndicator.classList.add).toHaveBeenCalledWith('hidden');
    });
});
