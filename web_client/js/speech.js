// 音声録音機能
let mediaRecorder;
let audioChunks = [];
let audioBlob;
let audioUrl;

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

// 音声録音機能の設定
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
    } catch (error) {
        resultElement.textContent = `エラーが発生しました: ${error.message}`;
        console.error('音声文字起こし中にエラーが発生しました:', error);
        responseTimeElement.textContent = '-';
        
        // エラー結果も保存
        saveResult('speech', resultElement.innerHTML, '-', model);
    } finally {
        // ボタンとローディングインジケーターを更新
        button.disabled = false;
        button.textContent = '音声文字起こし';
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
    } catch (error) {
        resultElement.textContent = `エラーが発生しました: ${error.message}`;
        console.error('音声生成中にエラーが発生しました:', error);
        responseTimeElement.textContent = '-';
        
        // エラー結果も保存
        saveResult('tts', resultElement.innerHTML, '-', model);
    } finally {
        // ボタンとローディングインジケーターを更新
        button.disabled = false;
        button.textContent = '音声生成';
        loadingIndicator.classList.add('hidden');
    }
}

// テスト用にエクスポート
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        setupSpeechAudioInput,
        setupAudioRecording,
        transcribeAudio,
        generateTTS
    };
}
