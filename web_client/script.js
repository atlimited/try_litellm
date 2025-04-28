// litellm プロキシのベース URL
const LITELLM_PROXY_URL = 'http://localhost:4000/v1';

// リクエストログを保存する配列
const requestLogs = [];
const MAX_REQUEST_LOGS = 50;  // 保存する最大リクエスト数

// XMLHttpRequest と fetch をオーバーライドしてリクエストをキャプチャする
function setupRequestInterceptor() {
    // 元のXMLHttpRequestを保存
    const originalXHR = window.XMLHttpRequest;

    // XMLHttpRequestをオーバーライド
    window.XMLHttpRequest = function() {
        const xhr = new originalXHR();
        const originalOpen = xhr.open;
        const originalSend = xhr.send;
        let requestInfo = {
            method: '',
            url: '',
            headers: {},
            body: '',
            startTime: 0,
            endTime: 0,
            status: 0,
            statusText: '',
            response: ''
        };

        // openメソッドをオーバーライド
        xhr.open = function(method, url, ...args) {
            requestInfo.method = method;
            requestInfo.url = url;
            requestInfo.startTime = Date.now();
            originalOpen.apply(xhr, [method, url, ...args]);
        };

        // sendメソッドをオーバーライド
        xhr.send = function(body) {
            if (body) {
                requestInfo.body = typeof body === 'string' ? body : JSON.stringify(body);
            }
            
            xhr.addEventListener('load', function() {
                requestInfo.endTime = Date.now();
                requestInfo.status = xhr.status;
                requestInfo.statusText = xhr.statusText;
                requestInfo.response = xhr.responseText;
                
                // リクエストをログに追加
                if (requestInfo.url.includes(LITELLM_PROXY_URL)) {
                    addRequestToLog(requestInfo);
                }
            });
            
            xhr.addEventListener('error', function() {
                requestInfo.endTime = Date.now();
                requestInfo.status = 'Error';
                requestInfo.statusText = 'Network Error';
                
                // リクエストをログに追加
                if (requestInfo.url.includes(LITELLM_PROXY_URL)) {
                    addRequestToLog(requestInfo);
                }
            });
            
            originalSend.apply(xhr, arguments);
        };
        
        // getAllResponseHeadersをパースしてヘッダーを取得
        const originalGetAllResponseHeaders = xhr.getAllResponseHeaders;
        xhr.getAllResponseHeaders = function() {
            const headers = originalGetAllResponseHeaders.apply(xhr);
            if (headers) {
                const headerLines = headers.trim().split(/[\r\n]+/);
                headerLines.forEach(line => {
                    const parts = line.split(': ');
                    const header = parts.shift();
                    const value = parts.join(': ');
                    requestInfo.headers[header] = value;
                });
            }
            return headers;
        };
        
        return xhr;
    };
    
    // 元のfetchを保存
    const originalFetch = window.fetch;
    
    // fetchをオーバーライド
    window.fetch = function(url, options = {}) {
        const requestInfo = {
            method: options.method || 'GET',
            url: typeof url === 'string' ? url : url.url,
            headers: options.headers || {},
            body: options.body || '',
            startTime: Date.now(),
            endTime: 0,
            status: 0,
            statusText: '',
            response: ''
        };
        
        // 元のfetchを呼び出し
        return originalFetch(url, options)
            .then(response => {
                requestInfo.endTime = Date.now();
                requestInfo.status = response.status;
                requestInfo.statusText = response.statusText;
                
                // レスポンスをクローンして内容を取得
                const clonedResponse = response.clone();
                
                // レスポンスヘッダーを取得
                response.headers.forEach((value, key) => {
                    requestInfo.headers[key] = value;
                });
                
                // レスポンス本文を取得
                return clonedResponse.text().then(text => {
                    requestInfo.response = text;
                    
                    // リクエストをログに追加
                    if (requestInfo.url.includes(LITELLM_PROXY_URL)) {
                        addRequestToLog(requestInfo);
                    }
                    
                    return response;
                });
            })
            .catch(error => {
                requestInfo.endTime = Date.now();
                requestInfo.status = 'Error';
                requestInfo.statusText = error.message;
                
                // リクエストをログに追加
                if (requestInfo.url.includes(LITELLM_PROXY_URL)) {
                    addRequestToLog(requestInfo);
                }
                
                throw error;
            });
    };
}

// リクエストをログに追加
function addRequestToLog(requestInfo) {
    // 古いログを削除して最大数を維持
    if (requestLogs.length >= MAX_REQUEST_LOGS) {
        requestLogs.shift();
    }
    
    // 新しいログを追加
    requestLogs.push(requestInfo);
    
    // UIを更新
    updateRequestLogUI();
}

// リクエストログUIを更新
function updateRequestLogUI() {
    const logContainer = document.getElementById('request-log');
    
    // コンテナをクリア
    logContainer.innerHTML = '';
    
    if (requestLogs.length === 0) {
        logContainer.innerHTML = '<div class="no-requests">リクエストログはありません</div>';
        return;
    }
    
    // 最新のリクエストから表示
    for (let i = requestLogs.length - 1; i >= 0; i--) {
        const log = requestLogs[i];
        const requestItem = document.createElement('div');
        requestItem.className = 'request-item';
        
        // 時間を日本語フォーマットに
        const date = new Date(log.startTime);
        const timeStr = `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}.${date.getMilliseconds().toString().padStart(3, '0')}`;
        
        // API パスを抽出
        const urlObj = new URL(log.url);
        const path = urlObj.pathname + urlObj.search;
        
        // メソッドに応じたクラス
        const methodClass = log.method.toLowerCase();
        
        // 処理時間
        const processingTime = log.endTime - log.startTime;
        
        // ステータスに応じたクラス
        const statusClass = (log.status >= 200 && log.status < 300) ? 'success' : 'error';
        
        // リクエスト詳細
        let requestDetails = '';
        if (log.body) {
            try {
                // JSONの場合はフォーマット
                const jsonBody = JSON.parse(log.body);
                requestDetails += `リクエスト本文:\n${JSON.stringify(jsonBody, null, 2)}\n\n`;
            } catch (e) {
                requestDetails += `リクエスト本文:\n${log.body}\n\n`;
            }
        }
        
        // レスポンス詳細
        if (log.response) {
            try {
                // JSONの場合はフォーマット
                const jsonResponse = JSON.parse(log.response);
                requestDetails += `レスポンス本文:\n${JSON.stringify(jsonResponse, null, 2)}`;
            } catch (e) {
                requestDetails += `レスポンス本文:\n${log.response}`;
            }
        }
        
        requestItem.innerHTML = `
            <div class="request-time">${timeStr}</div>
            <div>
                <span class="request-method ${methodClass}">${log.method}</span>
                <span class="request-path">${path}</span>
            </div>
            <div class="request-status ${statusClass}">
                ステータス: ${log.status} ${log.statusText} (${processingTime}ms)
            </div>
            ${requestDetails ? `<div class="request-details">${requestDetails}</div>` : ''}
        `;
        
        logContainer.appendChild(requestItem);
    }
}

// ログをクリア
function clearRequestLog() {
    requestLogs.length = 0;
    updateRequestLogUI();
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', () => {
    // リクエストインターセプターを設定
    setupRequestInterceptor();
    
    // タブ切り替え機能
    setupTabs();
    
    // 各ボタンにイベントリスナーを設定
    document.getElementById('generate-text').addEventListener('click', generateText);
    document.getElementById('generate-image').addEventListener('click', generateImage);
    document.getElementById('generate-tts').addEventListener('click', generateTTS);
    document.getElementById('analyze-image').addEventListener('click', analyzeImage);
    document.getElementById('transcribe-audio').addEventListener('click', transcribeAudio);
    
    // リセットボタンにイベントリスナーを設定
    document.querySelectorAll('.reset-results').forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            resetResults(tabId);
            updateSavedResultsView(); // 保存結果表示を更新
        });
    });
    
    // ログクリアボタンにイベントリスナーを設定
    document.getElementById('clear-request-log').addEventListener('click', clearRequestLog);
    
    // 画像認識の画像ファイル入力とURLの設定
    setupVisionImageInput();
    
    // 音声認識の音声ファイル入力と録音機能の設定
    setupSpeechAudioInput();
    setupAudioRecording();
    
    // 保存されている結果を読み込む
    loadStoredResults();
    
    // 保存結果一覧を表示
    updateSavedResultsView();
});

// 結果を保存
function saveResult(tabId, result, processingTime, model) {
    // 既存の結果リストを取得
    let resultsList = JSON.parse(localStorage.getItem(`${tabId}Results`) || '[]');
    
    // 新しい結果を追加
    resultsList.push({
        result: result,
        processingTime: processingTime,
        model: model,
        date: new Date().toISOString()
    });
    
    // ローカルストレージに保存
    localStorage.setItem(`${tabId}Results`, JSON.stringify(resultsList));
}

// 保存結果一覧を表示
function updateSavedResultsView() {
    const container = document.getElementById('saved-results-container');
    container.innerHTML = ''; // 既存のコンテンツをクリア
    
    const savedResults = getSavedResults();
    
    if (Object.keys(savedResults).length === 0) {
        container.innerHTML = '<div class="no-saved-results">保存された結果はありません</div>';
        return;
    }
    
    // すべての結果をフラット化して日付でソート
    let allResults = [];
    for (const [tabId, resultsList] of Object.entries(savedResults)) {
        resultsList.forEach(data => {
            allResults.push({
                tabId,
                ...data
            });
        });
    }
    
    // 日付の新しい順にソート
    allResults.sort((a, b) => new Date(b.date) - new Date(a.date));
    
    // 表示
    allResults.forEach(data => {
        const card = document.createElement('div');
        card.className = 'saved-result-card';
        
        // タブ名を表示用の名前に変換
        let tabName;
        switch(data.tabId) {
            case 'text': tabName = 'テキスト生成'; break;
            case 'image': tabName = '画像生成'; break;
            case 'tts': tabName = '音声生成'; break;
            case 'vision': tabName = '画像認識'; break;
            case 'speech': tabName = '音声認識'; break;
            default: tabName = data.tabId;
        }
        
        // 最大100文字までの内容を表示
        let content = data.result || "";
        if (content.length > 100) {
            content = content.substring(0, 100) + '...';
        }
        // HTMLタグを除去（ただし基本的なフォーマットは保持）
        content = content.replace(/<(?!br\s*\/?)[^>]+>/g, '');
        
        // 日時を日本語フォーマットに
        const date = data.date ? new Date(data.date) : new Date();
        const dateStr = `${date.getFullYear()}年${date.getMonth()+1}月${date.getDate()}日 ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
        
        card.innerHTML = `
            <h3>${tabName}</h3>
            <div class="saved-result-info">
                <p>モデル: <span>${data.model || '不明'}</span></p>
                <p>処理時間: <span>${data.processingTime || '-'} ms</span></p>
                <p>保存日時: <span>${dateStr}</span></p>
            </div>
            <div class="saved-result-content">${content}</div>
            <div class="saved-result-actions">
                <button class="view-result" data-tab="${data.tabId}" data-index="${data.index}">表示</button>
                <button class="delete-result" data-tab="${data.tabId}" data-index="${data.index}">削除</button>
            </div>
        `;
        
        container.appendChild(card);
    });
    
    // ボタンのイベントリスナーを設定
    container.querySelectorAll('.view-result').forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            const index = this.getAttribute('data-index');
            // 対応するタブを表示
            document.querySelector(`.tab-button[data-tab="${tabId}"]`).click();
            
            // 該当する結果を表示
            displayResult(tabId, index);
        });
    });
    
    container.querySelectorAll('.delete-result').forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            const index = this.getAttribute('data-index');
            
            // 特定の結果を削除
            deleteResult(tabId, index);
            updateSavedResultsView(); // 削除後に表示を更新
        });
    });
}

// 特定のタブの特定のインデックスの結果を削除
function deleteResult(tabId, index) {
    let resultsList = JSON.parse(localStorage.getItem(`${tabId}Results`) || '[]');
    if (index && index < resultsList.length) {
        resultsList.splice(index, 1);
        localStorage.setItem(`${tabId}Results`, JSON.stringify(resultsList));
    }
}

// 特定のタブの特定のインデックスの結果を表示
function displayResult(tabId, index) {
    if (!index) return;
    
    let resultsList = JSON.parse(localStorage.getItem(`${tabId}Results`) || '[]');
    if (index < resultsList.length) {
        const data = resultsList[index];
        
        // 該当するタブの結果表示領域に表示
        document.getElementById(`${tabId}-result`).innerHTML = data.result;
        document.querySelector(`.${tabId}-response-time`).textContent = data.processingTime || '-';
        
        // モデル選択を更新（存在する場合）
        const modelSelector = document.getElementById(`${tabId}-model`);
        if (modelSelector && data.model) {
            modelSelector.value = data.model;
        }
    }
}

// 保存されているすべての結果を取得
function getSavedResults() {
    const savedResults = {};
    
    // 各タブの結果リストを取得
    const tabs = ['text', 'image', 'tts', 'vision', 'speech'];
    
    tabs.forEach(tabId => {
        const resultsList = JSON.parse(localStorage.getItem(`${tabId}Results`) || '[]');
        if (resultsList.length > 0) {
            // 各結果にインデックスを追加
            savedResults[tabId] = resultsList.map((result, index) => ({
                ...result,
                index
            }));
        }
    });
    
    return savedResults;
}

// 保存された結果を読み込む
function loadStoredResults() {
    // 以前の単一の結果も読み込んで新形式に変換（一度だけの移行用）
    const tabs = ['text', 'image', 'tts', 'vision', 'speech'];
    
    tabs.forEach(tabId => {
        // 新形式のデータがまだなく、旧形式のデータがある場合
        if (!localStorage.getItem(`${tabId}Results`) && localStorage.getItem(`${tabId}Result`)) {
            const oldResult = localStorage.getItem(`${tabId}Result`);
            const oldTime = localStorage.getItem(`${tabId}ResponseTime`);
            const oldModel = localStorage.getItem(`${tabId}Model`);
            const oldDate = localStorage.getItem(`${tabId}Date`) || new Date().toISOString();
            
            // 新形式に変換
            const newResults = [{
                result: oldResult,
                processingTime: oldTime,
                model: oldModel,
                date: oldDate
            }];
            
            // 保存
            localStorage.setItem(`${tabId}Results`, JSON.stringify(newResults));
            
            // 旧形式のデータをクリア
            localStorage.removeItem(`${tabId}Result`);
            localStorage.removeItem(`${tabId}ResponseTime`);
            localStorage.removeItem(`${tabId}Model`);
            localStorage.removeItem(`${tabId}Date`);
        }
        
        // 結果を表示
        const resultsList = JSON.parse(localStorage.getItem(`${tabId}Results`) || '[]');
        if (resultsList.length > 0) {
            // 最新の結果を表示
            const latestResult = resultsList[resultsList.length - 1];
            document.getElementById(`${tabId}-result`).innerHTML = latestResult.result;
            document.querySelector(`.${tabId}-response-time`).textContent = latestResult.processingTime || '-';
            
            // モデル選択を更新（存在する場合）
            const modelSelector = document.getElementById(`${tabId}-model`);
            if (modelSelector && latestResult.model) {
                modelSelector.value = latestResult.model;
            }
        }
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
}

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

// テキスト生成機能
async function generateText() {
    const model = document.getElementById('text-model').value;
    const prompt = document.getElementById('text-prompt').value;
    const resultElement = document.getElementById('text-result');
    const responseTimeElement = document.querySelector('.text-response-time');
    
    if (!prompt.trim()) {
        resultElement.textContent = 'プロンプトを入力してください。';
        return;
    }
    
    // ボタンを無効化
    const button = document.getElementById('generate-text');
    button.disabled = true;
    button.textContent = '生成中...';
    
    resultElement.textContent = '生成中...';
    responseTimeElement.textContent = '-';
    
    // 処理開始時間を記録
    const startTime = performance.now();
    
    try {
        const response = await fetch(`${LITELLM_PROXY_URL}/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model,
                messages: [
                    {
                        role: 'user',
                        content: [
                            {
                                type: 'text',
                                text: prompt
                            }
                        ]
                    }
                ]
            })
        });
        
        if (!response.ok) {
            throw new Error(`API エラー: ${response.status}`);
        }
        
        const data = await response.json();
        resultElement.innerHTML = data.choices[0].message.content.replace(/\n/g, '<br>');
        
        // 処理終了時間を記録し、処理時間を計算して表示
        const endTime = performance.now();
        const processingTime = Math.round(endTime - startTime);
        responseTimeElement.textContent = processingTime;
        
        // 結果を保存
        saveResult('text', resultElement.innerHTML, processingTime, model);
        
        // 保存結果一覧を更新
        updateSavedResultsView();
    } catch (error) {
        resultElement.textContent = `エラーが発生しました: ${error.message}`;
        console.error('テキスト生成中にエラーが発生しました:', error);
        responseTimeElement.textContent = '-';
        
        // エラー結果も保存
        saveResult('text', resultElement.innerHTML, '-', model);
        
        // 保存結果一覧を更新
        updateSavedResultsView();
    } finally {
        // ボタンを再有効化
        button.disabled = false;
        button.textContent = 'テキスト生成';
    }
}

// 画像生成機能
async function generateImage() {
    const model = document.getElementById('image-model').value;
    const prompt = document.getElementById('image-prompt').value;
    const size = document.getElementById('image-size').value;
    const quality = document.getElementById('image-quality').value;
    const resultElement = document.getElementById('image-result');
    const loadingIndicator = document.getElementById('image-loading');
    const responseTimeElement = document.querySelector('.image-response-time');
    
    if (!prompt.trim()) {
        resultElement.textContent = 'プロンプトを入力してください。';
        return;
    }
    
    // ボタンとローディングインジケーターの表示を更新
    const button = document.getElementById('generate-image');
    button.disabled = true;
    button.textContent = '生成中...';
    loadingIndicator.classList.remove('hidden');
    resultElement.innerHTML = '';
    responseTimeElement.textContent = '-';
    
    // 処理開始時間を記録
    const startTime = performance.now();
    
    try {
        const response = await fetch(`${LITELLM_PROXY_URL}/images/generations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model,
                prompt: prompt,
                n: 1,
                size: size,
                quality: quality,
                response_format: 'url'
            })
        });
        
        if (!response.ok) {
            throw new Error(`API エラー: ${response.status}`);
        }
        
        const data = await response.json();
        const imageUrl = data.data[0].url;
        
        // 画像を表示
        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = 'Generated image';
        
        resultElement.innerHTML = '';
        resultElement.appendChild(img);
        
        // 画像URLも表示
        const urlText = document.createElement('p');
        urlText.textContent = `画像 URL: ${imageUrl}`;
        urlText.style.marginTop = '10px';
        urlText.style.fontSize = '12px';
        urlText.style.wordBreak = 'break-all';
        resultElement.appendChild(urlText);
        
        // 処理終了時間を記録し、処理時間を計算して表示
        const endTime = performance.now();
        const processingTime = Math.round(endTime - startTime);
        responseTimeElement.textContent = processingTime;
        
        // 結果を保存
        saveResult('image', resultElement.innerHTML, processingTime, model);
        
        // 保存結果一覧を更新
        updateSavedResultsView();
    } catch (error) {
        resultElement.textContent = `エラーが発生しました: ${error.message}`;
        console.error('画像生成中にエラーが発生しました:', error);
        responseTimeElement.textContent = '-';
        
        // エラー結果も保存
        saveResult('image', resultElement.innerHTML, '-', model);
        
        // 保存結果一覧を更新
        updateSavedResultsView();
    } finally {
        // ボタンとローディングインジケーターを更新
        button.disabled = false;
        button.textContent = '画像生成';
        loadingIndicator.classList.add('hidden');
    }
}

// 音声生成機能
async function generateTTS() {
    const model = document.getElementById('tts-model').value;
    const voice = document.getElementById('tts-voice').value;
    const text = document.getElementById('tts-text').value;
    const resultElement = document.getElementById('tts-result');
    const loadingIndicator = document.getElementById('tts-loading');
    const responseTimeElement = document.querySelector('.tts-response-time');
    
    if (!text.trim()) {
        resultElement.textContent = 'テキストを入力してください。';
        return;
    }
    
    // ボタンとローディングインジケーターの表示を更新
    const button = document.getElementById('generate-tts');
    button.disabled = true;
    button.textContent = '生成中...';
    loadingIndicator.classList.remove('hidden');
    resultElement.innerHTML = '';
    responseTimeElement.textContent = '-';
    
    // 処理開始時間を記録
    const startTime = performance.now();
    
    try {
        const response = await fetch(`${LITELLM_PROXY_URL}/audio/speech`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model,
                input: text,
                voice: voice,
                response_format: 'mp3'
            })
        });
        
        if (!response.ok) {
            throw new Error(`API エラー: ${response.status}`);
        }
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // 音声プレーヤーを作成
        const audioPlayer = document.createElement('audio');
        audioPlayer.controls = true;
        audioPlayer.src = audioUrl;
        audioPlayer.style.width = '100%';
        resultElement.appendChild(audioPlayer);
        
        // ダウンロードリンクを作成
        const downloadLink = document.createElement('a');
        downloadLink.href = audioUrl;
        downloadLink.download = 'generated_audio.mp3';
        downloadLink.textContent = 'ダウンロード';
        downloadLink.className = 'download-link';
        resultElement.appendChild(downloadLink);
        
        // 処理終了時間を記録し、処理時間を計算して表示
        const endTime = performance.now();
        const processingTime = Math.round(endTime - startTime);
        responseTimeElement.textContent = processingTime;
        
        // 結果を保存
        saveResult('tts', resultElement.innerHTML, processingTime, model);
        
        // 保存結果一覧を更新
        updateSavedResultsView();
    } catch (error) {
        resultElement.textContent = `エラーが発生しました: ${error.message}`;
        console.error('音声生成中にエラーが発生しました:', error);
        responseTimeElement.textContent = '-';
        
        // エラー結果も保存
        saveResult('tts', resultElement.innerHTML, '-', model);
        
        // 保存結果一覧を更新
        updateSavedResultsView();
    } finally {
        // ボタンとローディングインジケーターを更新
        button.disabled = false;
        button.textContent = '音声生成';
        loadingIndicator.classList.add('hidden');
    }
}

// 画像分析機能
async function analyzeImage() {
    const model = document.getElementById('vision-model').value;
    const prompt = document.getElementById('vision-prompt').value;
    const imageFile = document.getElementById('vision-image').files[0];
    const imageUrl = document.getElementById('vision-image-url').value.trim();
    const resultElement = document.getElementById('vision-result');
    const loadingIndicator = document.getElementById('vision-loading');
    const responseTimeElement = document.querySelector('.vision-response-time');
    
    if (!prompt.trim()) {
        resultElement.textContent = 'プロンプトを入力してください。';
        return;
    }
    
    if (!imageFile && !imageUrl) {
        resultElement.textContent = '画像をアップロードするか、画像URLを入力してください。';
        return;
    }
    
    // ボタンとローディングインジケーターの表示を更新
    const button = document.getElementById('analyze-image');
    button.disabled = true;
    button.textContent = '分析中...';
    loadingIndicator.classList.remove('hidden');
    resultElement.innerHTML = '';
    responseTimeElement.textContent = '-';
    
    // 処理開始時間を記録
    const startTime = performance.now();
    
    try {
        // 画像データの準備
        let imageContent;
        if (imageFile) {
            // ファイルからBase64エンコード
            imageContent = await getBase64FromFile(imageFile);
        } else {
            // URLから画像を取得してBase64エンコード
            try {
                const response = await fetch(imageUrl);
                if (!response.ok) {
                    throw new Error(`画像の取得に失敗しました: ${response.status}`);
                }
                
                const blob = await response.blob();
                const reader = new FileReader();
                imageContent = await new Promise((resolve, reject) => {
                    reader.onload = () => resolve(reader.result);
                    reader.onerror = reject;
                    reader.readAsDataURL(blob);
                });
            } catch (error) {
                resultElement.textContent = `画像の取得に失敗しました: ${error.message}`;
                throw error;
            }
        }
        
        // APIリクエスト
        const response = await fetch(`${LITELLM_PROXY_URL}/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model,
                messages: [
                    {
                        role: 'user',
                        content: [
                            {
                                type: 'text',
                                text: prompt
                            },
                            {
                                type: 'image_url',
                                image_url: {
                                    url: imageContent
                                }
                            }
                        ]
                    }
                ]
            })
        });
        
        if (!response.ok) {
            throw new Error(`API エラー: ${response.status}`);
        }
        
        const data = await response.json();
        resultElement.innerHTML = data.choices[0].message.content.replace(/\n/g, '<br>');
        
        // 処理終了時間を記録し、処理時間を計算して表示
        const endTime = performance.now();
        const processingTime = Math.round(endTime - startTime);
        responseTimeElement.textContent = processingTime;
        
        // 結果を保存
        saveResult('vision', resultElement.innerHTML, processingTime, model);
        
        // 保存結果一覧を更新
        updateSavedResultsView();
    } catch (error) {
        resultElement.textContent = `エラーが発生しました: ${error.message}`;
        console.error('画像分析中にエラーが発生しました:', error);
        responseTimeElement.textContent = '-';
        
        // エラー結果も保存
        saveResult('vision', resultElement.innerHTML, '-', model);
        
        // 保存結果一覧を更新
        updateSavedResultsView();
    } finally {
        // ボタンとローディングインジケーターを更新
        button.disabled = false;
        button.textContent = '画像分析';
        loadingIndicator.classList.add('hidden');
    }
}

// 音声認識: 音声ファイル入力の設定
function setupSpeechAudioInput() {
    const audioFileInput = document.getElementById('speech-audio');
    const audioPreview = document.getElementById('audio-preview');
    const audioPlayer = document.getElementById('audio-player');
    
    audioFileInput.addEventListener('change', (event) => {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            const audioUrl = URL.createObjectURL(file);
            
            // オーディオプレーヤーを表示
            audioPlayer.src = audioUrl;
            audioPreview.classList.remove('hidden');
        }
    });
}

// 音声録音機能
let mediaRecorder;
let audioChunks = [];
let audioBlob;
let audioUrl;

function setupAudioRecording() {
    const recordStartButton = document.getElementById('record-start');
    const recordStopButton = document.getElementById('record-stop');
    const recordingStatus = document.getElementById('recording-status');
    const audioPreview = document.getElementById('audio-preview');
    const audioPlayer = document.getElementById('audio-player');
    
    // 録音開始ボタン
    recordStartButton.addEventListener('click', async () => {
        try {
            // マイクへのアクセス許可を取得
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // 録音準備
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            // データ取得時の処理
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            // 録音停止時の処理
            mediaRecorder.onstop = () => {
                audioBlob = new Blob(audioChunks, { type: 'audio/mpeg' });
                audioUrl = URL.createObjectURL(audioBlob);
                
                // オーディオプレーヤーを設定
                audioPlayer.src = audioUrl;
                audioPreview.classList.remove('hidden');
                
                // ボタンと状態を更新
                recordStartButton.disabled = false;
                recordStopButton.disabled = true;
                recordingStatus.textContent = '録音完了';
                
                // ストリームの全トラックを停止
                stream.getTracks().forEach(track => track.stop());
            };
            
            // 録音開始
            mediaRecorder.start();
            
            // ボタンと状態を更新
            recordStartButton.disabled = true;
            recordStopButton.disabled = false;
            recordingStatus.textContent = '録音中...';
        } catch (error) {
            console.error('録音の開始中にエラーが発生しました:', error);
            recordingStatus.textContent = `エラー: ${error.message}`;
        }
    });
    
    // 録音停止ボタン
    recordStopButton.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
    });
}

// 音声文字起こし機能
async function transcribeAudio() {
    const model = document.getElementById('speech-model').value;
    const language = document.getElementById('speech-language').value;
    const audioFile = document.getElementById('speech-audio').files[0];
    const audioPath = document.getElementById('speech-audio-path').value;
    const resultElement = document.getElementById('speech-result');
    const loadingIndicator = document.getElementById('speech-loading');
    const responseTimeElement = document.querySelector('.speech-response-time');
    
    // 録音されたオーディオまたはアップロードされたファイルを使用
    let audioData;
    if (audioBlob) {
        // 録音されたオーディオを使用
        audioData = new File([audioBlob], 'recorded_audio.webm', { type: audioBlob.type });
    } else if (audioFile) {
        // アップロードされたファイルを使用
        audioData = audioFile;
    } else if (audioPath) {
        // パスから音声ファイルを取得
        try {
            const response = await fetch(audioPath);
            if (!response.ok) {
                throw new Error(`ファイルの取得に失敗しました: ${response.status}`);
            }
            const blob = await response.blob();
            // ファイル名を取得
            const fileName = audioPath.split('/').pop();
            // MIMEタイプを推測
            const mimeType = getMimeTypeFromFileName(fileName) || 'audio/mp3';
            audioData = new File([blob], fileName, { type: mimeType });
        } catch (error) {
            resultElement.textContent = `ファイルの読み込みに失敗しました: ${error.message}`;
            return;
        }
    } else {
        resultElement.textContent = '音声ファイルをアップロードするか、録音してください。';
        return;
    }
    
    // ボタンとローディングインジケーターの表示を更新
    const button = document.getElementById('transcribe-audio');
    button.disabled = true;
    button.textContent = '文字起こし中...';
    loadingIndicator.classList.remove('hidden');
    resultElement.innerHTML = '';
    responseTimeElement.textContent = '-';
    
    // 処理開始時間を記録
    const startTime = performance.now();
    
    try {
        let response;
        
        // Sambanovaモデルかどうかを確認
        if (model.includes('sambanova') || model.includes('qwen2-audio')) {
            // Sambanovaモデルの場合、チャット完了エンドポイントを使用
            // Base64エンコードされた音声ファイルが必要
            const reader = new FileReader();
            const audioBase64Promise = new Promise((resolve, reject) => {
                reader.onload = () => {
                    // ArrayBufferをBase64に変換
                    const base64 = btoa(
                        new Uint8Array(reader.result)
                            .reduce((data, byte) => data + String.fromCharCode(byte), '')
                    );
                    resolve(base64);
                };
                reader.onerror = reject;
                reader.readAsArrayBuffer(audioData);
            });
            
            const audioBase64 = await audioBase64Promise;
            
            // 言語に基づいたプロンプトの作成
            let promptText = "この録音には何が含まれていますか？";
            if (language !== 'auto') {
                // 言語のマッピング
                const languageNames = {
                    'ja': '日本語',
                    'en': '英語',
                    'zh': '中国語',
                    'ko': '韓国語',
                    'fr': 'フランス語',
                    'de': 'ドイツ語',
                    'es': 'スペイン語',
                    'ru': 'ロシア語'
                };
                const languageName = languageNames[language] || language;
                promptText = `これは${languageName}の音声です。この録音の内容を文字起こししてください。`;
            }
            
            response = await fetch(`${LITELLM_PROXY_URL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: model,
                    messages: [
                        {
                            role: 'user',
                            content: [
                                {
                                    type: 'text',
                                    text: promptText
                                },
                                {
                                    type: 'input_audio',
                                    input_audio: {
                                        data: audioBase64,
                                        format: audioData.type.split('/')[1] || 'wav'
                                    }
                                }
                            ]
                        }
                    ],
                    language: language !== 'auto' ? language : undefined
                })
            });
            
            if (!response.ok) {
                throw new Error(`API エラー: ${response.status}`);
            }
            
            const data = await response.json();
            resultElement.innerHTML = data.choices[0].message.content.replace(/\n/g, '<br>');
        } else {
            // Whisperモデルなど標準の文字起こしエンドポイントを使用するモデルの場合
            // FormDataの作成
            const formData = new FormData();
            formData.append('file', audioData);
            formData.append('model', model);
            
            // 言語が「auto」でない場合のみ言語パラメータを追加
            if (language !== 'auto') {
                formData.append('language', language);
            }
            
            // APIリクエスト
            response = await fetch(`${LITELLM_PROXY_URL}/audio/transcriptions`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`API エラー: ${response.status}`);
            }
            
            const data = await response.json();
            resultElement.textContent = data.text;
        }
        
        // 処理終了時間を記録し、処理時間を計算して表示
        const endTime = performance.now();
        const processingTime = Math.round(endTime - startTime);
        responseTimeElement.textContent = processingTime;
        
        // 結果を保存
        saveResult('speech', resultElement.innerHTML, processingTime, model);
        
        // 保存結果一覧を更新
        updateSavedResultsView();
    } catch (error) {
        resultElement.textContent = `エラーが発生しました: ${error.message}`;
        console.error('音声文字起こし中にエラーが発生しました:', error);
        responseTimeElement.textContent = '-';
        
        // エラー結果も保存
        saveResult('speech', resultElement.innerHTML, '-', model);
        
        // 保存結果一覧を更新
        updateSavedResultsView();
    } finally {
        // ボタンとローディングインジケーターを更新
        button.disabled = false;
        button.textContent = '音声文字起こし';
        loadingIndicator.classList.add('hidden');
    }
}

// 画像をBase64エンコードする関数
async function getBase64FromFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

// Vision機能: 画像ファイル入力の設定
function setupVisionImageInput() {
    const imageFileInput = document.getElementById('vision-image');
    const imageUrlInput = document.getElementById('vision-image-url');
    const imagePreview = document.getElementById('vision-image-preview');
    
    // ファイル選択時のプレビュー表示
    imageFileInput.addEventListener('change', (event) => {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            const reader = new FileReader();
            
            reader.onload = (e) => {
                // 画像プレビューを表示
                imagePreview.innerHTML = '';
                const img = document.createElement('img');
                img.src = e.target.result;
                img.alt = 'Selected image';
                imagePreview.appendChild(img);
                
                // URL入力欄をクリア（ファイルが優先）
                imageUrlInput.value = '';
            };
            
            reader.readAsDataURL(file);
        }
    });
    
    // URL入力時のプレビュー表示
    imageUrlInput.addEventListener('input', debounce(async (event) => {
        const url = event.target.value.trim();
        if (url) {
            try {
                // 画像プレビューを表示
                imagePreview.innerHTML = '';
                const img = document.createElement('img');
                img.src = url;
                img.alt = 'Image from URL';
                img.onerror = () => {
                    imagePreview.innerHTML = '<p style="color: red;">画像を読み込めませんでした。有効なURLを入力してください。</p>';
                };
                imagePreview.appendChild(img);
                
                // ファイル入力をクリア
                imageFileInput.value = '';
            } catch (error) {
                imagePreview.innerHTML = '<p style="color: red;">画像の読み込み中にエラーが発生しました。</p>';
            }
        }
    }, 500));
}

// 入力のdebounce処理
function debounce(func, delay) {
    let debounceTimer;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => func.apply(context, args), delay);
    };
}

// ファイル名からMIMEタイプを推測する関数
function getMimeTypeFromFileName(fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    const mimeTypes = {
        'mp3': 'audio/mp3',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
        'flac': 'audio/flac',
        'm4a': 'audio/m4a',
        'webm': 'audio/webm'
    };
    return mimeTypes[extension] || null;
}

// 関数呼び出し用の天気情報取得関数
function getCurrentWeather(location, unit = "fahrenheit") {
    console.log(`天気情報取得リクエスト: 場所=${location}, 単位=${unit}`);
    
    if (location.toLowerCase().includes("tokyo")) {
        return JSON.stringify({"location": "Tokyo", "temperature": "10", "unit": "celsius"});
    } else if (location.toLowerCase().includes("san francisco")) {
        return JSON.stringify({"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"});
    } else if (location.toLowerCase().includes("paris")) {
        return JSON.stringify({"location": "Paris", "temperature": "22", "unit": "celsius"});
    } else {
        return JSON.stringify({"location": location, "temperature": "unknown"});
    }
}

// 関数呼び出し処理
async function executeFunctionCall() {
    const model = document.getElementById('tools-model').value;
    const prompt = document.getElementById('tools-prompt').value;
    const resultBox = document.getElementById('tools-result');
    const functionCallsLog = document.getElementById('function-calls-log');
    const loadingIndicator = document.getElementById('tools-loading');
    const responseTimeElement = document.querySelector('.tools-response-time');
    
    // 結果表示エリアをクリア
    resultBox.innerHTML = '';
    functionCallsLog.innerHTML = '';
    responseTimeElement.textContent = '-';
    
    // ローディングインジケータを表示
    loadingIndicator.classList.remove('hidden');
    
    const startTime = Date.now();
    
    try {
        // ツール定義
        const tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            },
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["location"],
                    },
                },
            }
        ];
        
        // メッセージの準備
        const messages = [{"role": "user", "content": prompt}];
        
        // リクエストペイロード
        const payload = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        };
        
        // リクエストを実行
        functionCallsLog.innerHTML += `<div class="log-entry">🚀 ${model}にリクエストを送信中...</div>`;
        
        // LiteLLM APIにリクエストを送信
        const response = await fetch(`${LITELLM_PROXY_URL}/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        const responseMessage = result.choices[0].message;
        
        functionCallsLog.innerHTML += `<div class="log-entry">🤖 LLMレスポンスを受信しました</div>`;
        
        // ツール呼び出しがあるか確認
        if (responseMessage.tool_calls) {
            const toolCalls = responseMessage.tool_calls;
            functionCallsLog.innerHTML += `<div class="log-entry">🔧 ツール呼び出しが検出されました: ${toolCalls.length}個</div>`;
            
            // 各ツール呼び出しを処理
            for (const toolCall of toolCalls) {
                const functionName = toolCall.function.name;
                const functionArgs = JSON.parse(toolCall.function.arguments);
                
                functionCallsLog.innerHTML += `<div class="log-entry">📝 関数 '${functionName}' を呼び出します。引数: ${JSON.stringify(functionArgs)}</div>`;
                
                // 関数を実行
                let functionResponse;
                if (functionName === "get_current_weather") {
                    functionResponse = getCurrentWeather(
                        functionArgs.location,
                        functionArgs.unit || "fahrenheit"
                    );
                    
                    functionCallsLog.innerHTML += `<div class="log-entry">🌤 天気情報: ${functionResponse}</div>`;
                }
                
                // 関数の結果をメッセージに追加
                messages.push(responseMessage);
                messages.push({
                    "role": "tool",
                    "tool_call_id": toolCall.id,
                    "name": functionName,
                    "content": functionResponse,
                });
            }
            
            // 関数結果を含めて再度リクエスト
            const secondPayload = {
                "model": model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            };
            
            functionCallsLog.innerHTML += `<div class="log-entry">🔄 関数の結果を含めて再度リクエストを送信中...</div>`;
            
            const secondResponse = await fetch(`${LITELLM_PROXY_URL}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(secondPayload),
            });
            
            if (!secondResponse.ok) {
                throw new Error(`HTTP error! status: ${secondResponse.status}`);
            }
            
            const secondResult = await secondResponse.json();
            functionCallsLog.innerHTML += `<div class="log-entry">🤖 最終レスポンスを受信しました</div>`;
            
            const finalMessage = secondResult.choices[0].message.content;
            
            // マークダウンパーサーでレンダリング
            resultBox.innerHTML = `<div class="markdown-content">${finalMessage.replace(/\n/g, '<br>')}</div>`;
        } else {
            // ツール呼び出しがない場合は直接メッセージを表示
            const content = responseMessage.content;
            resultBox.innerHTML = `<div class="markdown-content">${content.replace(/\n/g, '<br>')}</div>`;
        }
        
        // 処理時間を表示
        const endTime = Date.now();
        const processingTime = endTime - startTime;
        responseTimeElement.textContent = processingTime;
        
        // 結果を保存
        saveResult('tools', resultBox.innerHTML, processingTime, model);
        
    } catch (error) {
        console.error('エラー:', error);
        resultBox.innerHTML = `<div class="error">エラーが発生しました: ${error.message}</div>`;
    } finally {
        // ローディングインジケータを非表示
        loadingIndicator.classList.add('hidden');
    }
}

// DOMContentLoadedイベントリスナーに関数呼び出しボタンのリスナーを追加
document.addEventListener('DOMContentLoaded', () => {
    // 既存のイベントリスナーはそのまま

    // 関数呼び出しボタン
    const executeFunctionCallButton = document.getElementById('execute-function-call');
    if (executeFunctionCallButton) {
        executeFunctionCallButton.addEventListener('click', executeFunctionCall);
    }
});