// storage.test.js
const { 
    saveResult,
    getSavedResults,
    deleteResult,
    displayResult
} = require('../js/storage');

// updateSavedResultsViewとloadStoredResultsをモック化
jest.mock('../js/storage', () => {
    const originalModule = jest.requireActual('../js/storage');
    
    // updateSavedResultsViewの実装を置き換え
    const mockUpdateSavedResultsView = jest.fn();
    
    return {
        ...originalModule,
        updateSavedResultsView: mockUpdateSavedResultsView,
        loadStoredResults: jest.fn()
    };
});

// LocalStorageのモック
const localStorageMock = (() => {
    let store = {};
    return {
        getItem: jest.fn(key => store[key] || null),
        setItem: jest.fn((key, value) => {
            store[key] = value.toString();
        }),
        removeItem: jest.fn(key => {
            delete store[key];
        }),
        clear: jest.fn(() => {
            store = {};
        }),
        _getStore: () => store  // テスト用に内部ストアを取得するヘルパー
    };
})();

// グローバルなlocalStorageをモックで上書き
Object.defineProperty(global, 'localStorage', {
    value: localStorageMock,
    writable: true
});

// DOMのモック
const mockElements = {};

// getElementById のモック
document.getElementById = jest.fn(id => {
    if (!mockElements[id]) {
        mockElements[id] = {
            innerHTML: '',
            value: '',
            querySelectorAll: jest.fn().mockReturnValue([]),
            appendChild: jest.fn(),
            addEventListener: jest.fn()
        };
    }
    return mockElements[id];
});

// querySelector のモック
document.querySelector = jest.fn(selector => {
    const id = selector.replace(/[.#]/g, '').replace(/\[.*\]/g, '');
    if (!mockElements[id]) {
        mockElements[id] = {
            textContent: '',
            value: '',
            innerHTML: ''
        };
    }
    return mockElements[id];
});

// Dateのモック
const mockDate = new Date('2025-01-01T12:00:00Z');
global.Date = class extends Date {
    constructor() {
        super();
        return mockDate;
    }
    static now() {
        return mockDate.getTime();
    }
};
global.Date.prototype.toISOString = () => '2025-01-01T12:00:00Z';

describe('Storage module', () => {
    beforeEach(() => {
        // モックをリセット
        jest.clearAllMocks();
        localStorage.clear();
        
        // モック要素をリセット
        for (const id in mockElements) {
            delete mockElements[id];
        }
        
        // あらかじめ必要なモック要素を作成
        document.getElementById('text-result');
        document.getElementById('image-result');
        document.getElementById('text-model');
        document.querySelector('.text-response-time');
        document.querySelector('.image-response-time');
    });
    
    describe('saveResult', () => {
        it('should save a new result to localStorage', () => {
            // 結果を保存
            saveResult('text', 'これはテストの結果です', 1500, 'gpt-4');
            
            // localStorageに正しく保存されたか確認
            expect(localStorage.setItem).toHaveBeenCalled();
            
            // 保存された値を確認
            const savedResultsStr = localStorage.getItem('textResults');
            expect(savedResultsStr).toBeTruthy();
            
            const savedResults = JSON.parse(savedResultsStr);
            expect(savedResults).toHaveLength(1);
            expect(savedResults[0].result).toBe('これはテストの結果です');
            expect(savedResults[0].processingTime).toBe(1500);
            expect(savedResults[0].model).toBe('gpt-4');
        });
        
        it('should append to existing results', () => {
            // 既存の結果をセットアップ
            localStorage.setItem('textResults', JSON.stringify([{
                result: '既存の結果',
                processingTime: 1000,
                model: 'gpt-3.5',
                date: '2024-01-01T00:00:00Z'
            }]));
            
            // 新しい結果を保存
            saveResult('text', '新しい結果', 1500, 'gpt-4');
            
            // 保存された値を確認
            const savedResultsStr = localStorage.getItem('textResults');
            const savedResults = JSON.parse(savedResultsStr);
            
            expect(savedResults).toHaveLength(2);
            expect(savedResults[0].result).toBe('既存の結果');
            expect(savedResults[1].result).toBe('新しい結果');
        });
    });
    
    describe('getSavedResults', () => {
        it('should return saved results with indices', () => {
            // いくつかの結果を保存
            localStorage.setItem('textResults', JSON.stringify([
                { result: 'テキスト結果1', processingTime: 1000, model: 'gpt-3.5' },
                { result: 'テキスト結果2', processingTime: 1500, model: 'gpt-4' }
            ]));
            
            localStorage.setItem('imageResults', JSON.stringify([
                { result: '画像結果', processingTime: 2000, model: 'dalle-3' }
            ]));
            
            // 保存された結果を取得
            const results = getSavedResults();
            
            // 結果が正しい形式で返されたか確認
            expect(results).toHaveProperty('text');
            expect(results).toHaveProperty('image');
            expect(results.text).toHaveLength(2);
            expect(results.image).toHaveLength(1);
            
            // インデックスが追加されているか確認
            expect(results.text[0]).toHaveProperty('index', 0);
            expect(results.text[1]).toHaveProperty('index', 1);
            expect(results.image[0]).toHaveProperty('index', 0);
        });
        
        it('should return empty object when no results are saved', () => {
            const results = getSavedResults();
            expect(Object.keys(results)).toHaveLength(0);
        });
    });
    
    describe('deleteResult', () => {
        it('should delete a specific result', () => {
            // テスト用の結果をセットアップ
            localStorage.setItem('textResults', JSON.stringify([
                { result: 'テキスト結果1' },
                { result: 'テキスト結果2' },
                { result: 'テキスト結果3' }
            ]));
            
            // 真ん中の結果を削除
            deleteResult('text', 1);
            
            // 結果を確認
            const savedResultsStr = localStorage.getItem('textResults');
            const savedResults = JSON.parse(savedResultsStr);
            
            expect(savedResults).toHaveLength(2);
            expect(savedResults[0].result).toBe('テキスト結果1');
            expect(savedResults[1].result).toBe('テキスト結果3');
        });
        
        it('should do nothing if index is invalid', () => {
            // テスト用の結果をセットアップ
            localStorage.setItem('textResults', JSON.stringify([
                { result: 'テキスト結果1' },
                { result: 'テキスト結果2' }
            ]));
            
            // 無効なインデックスで削除を試みる
            deleteResult('text', 5);
            
            // 結果が変わっていないことを確認
            const savedResultsStr = localStorage.getItem('textResults');
            const savedResults = JSON.parse(savedResultsStr);
            
            expect(savedResults).toHaveLength(2);
        });
    });
    
    describe('displayResult', () => {
        it('should display a specific result in the DOM', () => {
            // テスト用の結果をセットアップ
            localStorage.setItem('textResults', JSON.stringify([
                { result: 'テキスト結果1', processingTime: 1000, model: 'gpt-3.5' },
                { result: 'テキスト結果2', processingTime: 1500, model: 'gpt-4' }
            ]));
            
            // DOMのモックを準備
            const resultElement = document.getElementById('text-result');
            const timeElement = document.querySelector('.text-response-time');
            const modelElement = document.getElementById('text-model');
            
            // 特定の結果を表示
            displayResult('text', 1);
            
            // DOMが更新されたか確認
            expect(resultElement.innerHTML).toBe('テキスト結果2');
            expect(timeElement.textContent).toBe(1500);
            expect(modelElement.value).toBe('gpt-4');
        });
        
        it('should do nothing if index is invalid', () => {
            // 初期状態を設定
            const resultElement = document.getElementById('text-result');
            resultElement.innerHTML = '元の内容';
            
            const timeElement = document.querySelector('.text-response-time');
            timeElement.textContent = '元の時間';
            
            // 無効なインデックスで表示を試みる
            displayResult('text', 99);
            
            // DOMが変更されていないことを確認
            expect(resultElement.innerHTML).toBe('元の内容');
            expect(timeElement.textContent).toBe('元の時間');
        });
    });
});
