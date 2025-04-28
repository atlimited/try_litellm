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

// 画像をBase64エンコードする関数
async function getBase64FromFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}
