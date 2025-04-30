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
    } catch (error) {
        resultElement.textContent = `エラーが発生しました: ${error.message}`;
        console.error('テキスト生成中にエラーが発生しました:', error);
        responseTimeElement.textContent = '-';
        
        // エラー結果も保存
        saveResult('text', resultElement.innerHTML, '-', model);
    } finally {
        // ボタンを再有効化
        button.disabled = false;
        button.textContent = 'テキスト生成';
    }
}

// Node.js環境とブラウザ環境の両方で動作するように、モジュールエクスポートを追加
// テスト用にエクスポート
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        generateText
    };
}
