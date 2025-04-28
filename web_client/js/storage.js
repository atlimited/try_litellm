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
    
    // 保存結果一覧を更新
    updateSavedResultsView();
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
            case 'tools': tabName = '関数呼び出し'; break;
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
    const tabs = ['text', 'image', 'tts', 'vision', 'speech', 'tools'];
    
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
    const tabs = ['text', 'image', 'tts', 'vision', 'speech', 'tools'];
    
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
    
    // 保存結果一覧を表示
    updateSavedResultsView();
}
