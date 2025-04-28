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
    } catch (error) {
        resultElement.textContent = `エラーが発生しました: ${error.message}`;
        console.error('画像生成中にエラーが発生しました:', error);
        responseTimeElement.textContent = '-';
        
        // エラー結果も保存
        saveResult('image', resultElement.innerHTML, '-', model);
    } finally {
        // ボタンとローディングインジケーターを更新
        button.disabled = false;
        button.textContent = '画像生成';
        loadingIndicator.classList.add('hidden');
    }
}
