// litellm プロキシのベース URL
const LITELLM_PROXY_URL = 'http://localhost:4000/v1';

// DOMContentLoadedイベントリスナー - 初期化処理
document.addEventListener('DOMContentLoaded', () => {
    // リクエストインターセプターを設定
    setupRequestInterceptor();
    
    // タブ切り替え機能の設定
    setupTabs();
    
    // 保存された結果を読み込む
    loadStoredResults();
    
    // リクエストログクリアボタン
    const clearLogButton = document.getElementById('clear-request-log');
    clearLogButton.addEventListener('click', clearRequestLog);
    
    // 全タブのリセットボタン
    const resetAllButton = document.querySelector('.reset-results[data-tab="all"]');
    resetAllButton.addEventListener('click', () => resetResults('all'));
    
    // 個別タブのリセットボタン
    const resetButtons = document.querySelectorAll('.reset-results:not([data-tab="all"])');
    resetButtons.forEach(button => {
        const tabId = button.getAttribute('data-tab');
        button.addEventListener('click', () => resetResults(tabId));
    });
    
    // テキスト生成ボタン
    const generateTextButton = document.getElementById('generate-text');
    generateTextButton.addEventListener('click', generateText);
    
    // 画像生成ボタン
    const generateImageButton = document.getElementById('generate-image');
    generateImageButton.addEventListener('click', generateImage);
    
    // 音声生成ボタン
    const generateTTSButton = document.getElementById('generate-tts');
    generateTTSButton.addEventListener('click', generateTTS);
    
    // 画像分析ボタン
    const analyzeImageButton = document.getElementById('analyze-image');
    analyzeImageButton.addEventListener('click', analyzeImage);
    
    // 音声認識ボタン
    const transcribeAudioButton = document.getElementById('transcribe-audio');
    transcribeAudioButton.addEventListener('click', transcribeAudio);
    
    // 関数呼び出しボタン
    const executeFunctionCallButton = document.getElementById('execute-function-call');
    executeFunctionCallButton.addEventListener('click', executeFunctionCall);
    
    // 画像ファイル入力の設定
    setupVisionImageInput();
    
    // 音声ファイル入力の設定
    setupSpeechAudioInput();
    
    // 音声録音機能の設定
    setupAudioRecording();
});

// タブ切り替え機能の設定
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // アクティブなタブを更新
            document.querySelector('.tab-button.active').classList.remove('active');
            button.classList.add('active');
            
            // タブコンテンツを切り替え
            const tabId = button.getAttribute('data-tab');
            document.querySelector('.tab-pane.active').classList.remove('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
}

// リセット機能
function resetResults(tabId) {
    if (tabId === 'all') {
        localStorage.clear();
        document.querySelectorAll('.result-box').forEach(el => el.innerHTML = '');
        document.querySelectorAll('.response-time-container span').forEach(el => el.textContent = '-');
    } else {
        localStorage.removeItem(`${tabId}Results`);
        document.getElementById(`${tabId}-result`).innerHTML = '';
        document.querySelector(`.${tabId}-response-time`).textContent = '-';
    }
    
    // 保存結果一覧を更新
    updateSavedResultsView();
}

// テスト用にエクスポート
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        setupTabs,
        resetResults,
        LITELLM_PROXY_URL
    };
}
