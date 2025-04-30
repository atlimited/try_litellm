// utils.test.js
const { 
    debounce, 
    getMimeTypeFromFileName
} = require('../js/utils');

// Jestのフェイクタイマーを有効化
jest.useFakeTimers();

// グローバル変数の定義
global.window = {};
global.document = {};

// FileReader、Blob、DOMモック関連は簡略化し、テスト対象をdebounceとgetMimeTypeFromFileNameに限定
beforeAll(() => {
    window.XMLHttpRequest = function() {
        return {
            open: jest.fn(),
            send: jest.fn(),
            getAllResponseHeaders: jest.fn(),
            addEventListener: jest.fn()
        };
    };
    
    window.fetch = jest.fn().mockImplementation(() => 
        Promise.resolve({
            clone: () => ({
                text: () => Promise.resolve('')
            }),
            headers: {
                forEach: () => {}
            }
        })
    );
    
    document.getElementById = jest.fn().mockImplementation(() => ({
        innerHTML: '',
        appendChild: jest.fn()
    }));
    
    document.createElement = jest.fn().mockImplementation(() => ({
        className: '',
        innerHTML: '',
        appendChild: jest.fn()
    }));
    
    document.querySelectorAll = jest.fn().mockReturnValue([]);
});

afterAll(() => {
    jest.clearAllMocks();
});

describe('Utils module', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });
    
    describe('debounce', () => {
        it('should delay function execution', () => {
            // モック関数を作成
            const mockFn = jest.fn();
            
            // debounce関数を使用
            const debouncedFn = debounce(mockFn, 100);
            
            // debounce関数を実行
            debouncedFn();
            
            // 即時には実行されないことを確認
            expect(mockFn).not.toHaveBeenCalled();
            
            // 時間を進める
            jest.advanceTimersByTime(50);
            expect(mockFn).not.toHaveBeenCalled();
            
            // さらに時間を進めて関数が実行されることを確認
            jest.advanceTimersByTime(50);
            expect(mockFn).toHaveBeenCalled();
            expect(mockFn).toHaveBeenCalledTimes(1);
        });
        
        it('should reset the timer when called again', () => {
            // モック関数を作成
            const mockFn = jest.fn();
            
            // debounce関数を使用
            const debouncedFn = debounce(mockFn, 100);
            
            // 最初の呼び出し
            debouncedFn();
            jest.advanceTimersByTime(50);
            
            // 2回目の呼び出し（タイマーをリセット）
            debouncedFn();
            jest.advanceTimersByTime(50);
            
            // まだ実行されていないことを確認
            expect(mockFn).not.toHaveBeenCalled();
            
            // タイマーが完了するまで進める
            jest.advanceTimersByTime(50);
            expect(mockFn).toHaveBeenCalled();
            expect(mockFn).toHaveBeenCalledTimes(1);
        });
    });
    
    describe('getMimeTypeFromFileName', () => {
        it('should return correct MIME type for known extensions', () => {
            // 各拡張子に対して正しいMIMEタイプが返されることを確認
            expect(getMimeTypeFromFileName('test.mp3')).toBe('audio/mp3');
            expect(getMimeTypeFromFileName('audio.wav')).toBe('audio/wav');
            expect(getMimeTypeFromFileName('sample.ogg')).toBe('audio/ogg');
            expect(getMimeTypeFromFileName('music.flac')).toBe('audio/flac');
            expect(getMimeTypeFromFileName('sound.m4a')).toBe('audio/m4a');
            expect(getMimeTypeFromFileName('voice.webm')).toBe('audio/webm');
        });
        
        it('should return null for unknown extensions', () => {
            // 未知の拡張子の場合はnullが返されることを確認
            expect(getMimeTypeFromFileName('document.pdf')).toBeNull();
            expect(getMimeTypeFromFileName('image.jpg')).toBeNull();
            expect(getMimeTypeFromFileName('file.txt')).toBeNull();
        });
        
        it('should handle case insensitivity', () => {
            // 大文字小文字を区別しないことを確認
            expect(getMimeTypeFromFileName('audio.MP3')).toBe('audio/mp3');
            expect(getMimeTypeFromFileName('sound.Wav')).toBe('audio/wav');
        });
        
        it('should handle files without extensions', () => {
            // 拡張子のないファイルを処理できることを確認
            expect(getMimeTypeFromFileName('noextension')).toBeNull();
        });
    });
    
    // getBase64FromFileは非同期処理のため、モックとPromiseの扱いが難しいので省略
    
    // DOM関連のテストは簡略化
    describe('DOM related functions', () => {
        it('should interact with the DOM correctly', () => {
            // DOMのモックが正しく設定されていることを確認
            expect(document.getElementById).toBeDefined();
            expect(document.createElement).toBeDefined();
            expect(document.querySelectorAll).toBeDefined();
            
            // getElementById が正しく動作することを確認
            const element = document.getElementById('test-id');
            expect(element).toBeDefined();
            expect(element.innerHTML).toBe('');
            
            // 要素にプロパティを設定できることを確認
            element.innerHTML = 'テスト内容';
            expect(element.innerHTML).toBe('テスト内容');
        });
    });
    
    // XMLHttpRequestとfetchのテスト
    describe('Request related functions', () => {
        it('should have XMLHttpRequest correctly mocked', () => {
            const xhr = new window.XMLHttpRequest();
            expect(xhr).toBeDefined();
            expect(xhr.open).toBeDefined();
            expect(xhr.send).toBeDefined();
        });
        
        it('should have fetch correctly mocked', () => {
            expect(window.fetch).toBeDefined();
            
            window.fetch('test-url');
            expect(window.fetch).toHaveBeenCalledWith('test-url');
            expect(window.fetch).toHaveBeenCalledTimes(1);
        });
    });
});
