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
    } catch (error) {
        resultElement.textContent = `エラーが発生しました: ${error.message}`;
        console.error('画像分析中にエラーが発生しました:', error);
        responseTimeElement.textContent = '-';
        
        // エラー結果も保存
        saveResult('vision', resultElement.innerHTML, '-', model);
    } finally {
        // ボタンとローディングインジケーターを更新
        button.disabled = false;
        button.textContent = '画像分析';
        loadingIndicator.classList.add('hidden');
    }
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
