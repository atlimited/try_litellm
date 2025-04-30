// main.test.js
const { setupTabs, resetResults, LITELLM_PROXY_URL } = require('../js/main');

// グローバル変数の定義
global.localStorage = {
    clear: jest.fn(),
    removeItem: jest.fn(),
    getItem: jest.fn(),
    setItem: jest.fn()
};

// DOM要素作成のヘルパー関数
function createElementMock(attrs = {}) {
    return {
        addEventListener: jest.fn(),
        classList: {
            remove: jest.fn(),
            add: jest.fn(),
            contains: jest.fn(() => attrs.active || false)
        },
        style: {},
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
        getAttribute: jest.fn(attr => {
            if (attr === 'data-tab') {
                return attrs['data-tab'] || null;
            }
            return attrs[attr] || null;
        }),
        ...attrs
    };
}

// グローバルオブジェクトのモック
global.updateSavedResultsView = jest.fn();

describe('Main module', () => {
    // DOM構造のモック
    let tabButtons;
    let originalLocalStorage;
    
    beforeEach(() => {
        // localStorageのモックをセットアップ
        originalLocalStorage = global.localStorage;
        
        // Jest spyOnを使用してlocalStorageをモック化
        Object.defineProperty(window, 'localStorage', {
            value: {
                clear: jest.fn(),
                removeItem: jest.fn(),
                getItem: jest.fn(),
                setItem: jest.fn()
            },
            writable: true
        });
        
        // タブボタンのモックを作成
        tabButtons = [
            createElementMock({ 'data-tab': 'text' }),
            createElementMock({ 'data-tab': 'image' })
        ];
        
        // HTMLコレクションをモックするための関数
        function createHTMLCollection(elements) {
            const collection = [...elements];
            collection.item = index => elements[index] || null;
            collection.forEach = (callback) => elements.forEach(callback);
            return collection;
        }
        
        // DOMのモックをセットアップ
        const activeTabButton = createElementMock({ active: true });
        const activeTabPanel = createElementMock({ active: true });
        
        // Documentのqueryをモック
        document.querySelectorAll = jest.fn(selector => {
            if (selector === '.tab-button') {
                return createHTMLCollection(tabButtons);
            }
            if (selector === '.result-box') {
                return createHTMLCollection([
                    createElementMock({ innerHTML: 'テスト結果1' }),
                    createElementMock({ innerHTML: 'テスト結果2' })
                ]);
            }
            if (selector === '.reset-results:not([data-tab="all"])') {
                return createHTMLCollection([
                    createElementMock({ 'data-tab': 'text' }),
                    createElementMock({ 'data-tab': 'image' })
                ]);
            }
            if (selector === '.response-time-container span') {
                return createHTMLCollection([
                    createElementMock({ textContent: '1000ms' }),
                    createElementMock({ textContent: '2000ms' })
                ]);
            }
            return createHTMLCollection([]);
        });
        
        document.querySelector = jest.fn(selector => {
            if (selector === '.tab-button.active') {
                return activeTabButton;
            }
            if (selector === '.tab-pane.active') {
                return activeTabPanel;
            }
            if (selector === '.text-response-time') {
                return createElementMock({ textContent: '1000ms' });
            }
            return null;
        });
        
        document.getElementById = jest.fn(id => {
            if (id.endsWith('-tab')) {
                return createElementMock({
                    classList: { add: jest.fn(), remove: jest.fn() }
                });
            }
            if (id === 'text-result') {
                return createElementMock({ innerHTML: 'テキスト結果' });
            }
            return null;
        });
        
        // updateSavedResultsViewのモックをリセット
        updateSavedResultsView.mockClear();
    });
    
    afterEach(() => {
        // モックをリセット
        jest.clearAllMocks();
        
        // localStorageを元に戻す
        Object.defineProperty(window, 'localStorage', {
            value: originalLocalStorage,
            writable: true
        });
    });
    
    describe('setupTabs', () => {
        it('should set up tab switching functionality', () => {
            // setupTabs関数を実行
            setupTabs();
            
            // タブボタンにイベントリスナーが設定されたか確認
            expect(tabButtons[0].addEventListener).toHaveBeenCalledWith('click', expect.any(Function));
            expect(tabButtons[1].addEventListener).toHaveBeenCalledWith('click', expect.any(Function));
            
            // クリックイベントをシミュレート
            const clickHandler = tabButtons[0].addEventListener.mock.calls[0][1];
            
            // タブ切り替え前の状態を取得
            const activeTabButton = document.querySelector('.tab-button.active');
            const activeTabPanel = document.querySelector('.tab-pane.active');
            
            // クリックイベントを実行
            clickHandler();
            
            // アクティブクラスが適切に切り替わったか確認
            expect(activeTabButton.classList.remove).toHaveBeenCalledWith('active');
            expect(tabButtons[0].classList.add).toHaveBeenCalledWith('active');
            expect(activeTabPanel.classList.remove).toHaveBeenCalledWith('active');
        });
    });
    
    describe('resetResults', () => {
        it('should clear all results when reset all is clicked', () => {
            // モックを使用する場合は、関数をオーバーライドする必要がある
            const resetResults = require('../js/main').resetResults;
            
            // resetResults関数を実行（すべてのタブ）
            resetResults('all');
            
            // localStorageがクリアされたか確認
            expect(window.localStorage.clear).toHaveBeenCalled();
            
            // 保存結果一覧が更新されたか確認
            expect(updateSavedResultsView).toHaveBeenCalled();
        });
        
        it('should clear single tab results when reset for specific tab is clicked', () => {
            // resetResults関数を実行（特定のタブ）
            resetResults('text');
            
            // 特定のタブの保存結果がクリアされたか確認
            expect(window.localStorage.removeItem).toHaveBeenCalledWith('textResults');
            
            // 保存結果一覧が更新されたか確認
            expect(updateSavedResultsView).toHaveBeenCalled();
        });
    });
    
    describe('Constants', () => {
        it('should have the correct LITELLM_PROXY_URL value', () => {
            expect(LITELLM_PROXY_URL).toBe('http://localhost:4000/v1');
        });
    });
});
