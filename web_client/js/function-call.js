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
