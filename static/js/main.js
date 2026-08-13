// Client-side JavaScript for AI Adaptive Learning App
document.addEventListener('DOMContentLoaded', () => {
    console.log('AIとともに学習するクイズアプリ — Phase 1 Initialized');
});

/**
 * 1. 新しいファイルを作成した際に履歴へ追加する関数
 * @param {string|null} id - ファイルID (未指定時は自動生成)
 * @param {string} fileName - ファイル名
 * @param {string} theme - テーマカラー ('blue', 'purple', 'amber', 'emerald')
 * @param {string} url - 遷移先のURL
 */
window.addCreatedFile = function(id, fileName, theme, url) {
    let files = JSON.parse(localStorage.getItem("user_created_files_history") || "[]");
    let activeIds = JSON.parse(localStorage.getItem("user_active_file_ids") || "[]");

    // IDが未指定の場合はユニークなIDを発行
    const fileId = id ? id : ('file_' + Date.now() + '_' + Math.floor(Math.random() * 1000));
    const today = new Date();
    const dateStr = `${today.getDate()}/${today.getMonth() + 1}`;

    // 重複を防止
    files = files.filter(f => f.id !== fileId);

    // 有効ファイルIDリストへ追加
    if (!activeIds.includes(fileId)) {
        activeIds.push(fileId);
        localStorage.setItem("user_active_file_ids", JSON.stringify(activeIds));
    }

    // 最新（先頭）にファイル情報を追加
    files.unshift({
        id: fileId,
        name: fileName || 'no title',
        theme: theme || 'blue',
        made: dateStr,
        recent: dateStr,
        url: url || '#'
    });

    localStorage.setItem("user_created_files_history", JSON.stringify(files));

    // 画面上に履歴表示関数があれば即座に再描画
    if (typeof window.renderRecentHistory === 'function') {
        window.renderRecentHistory();
    }
};

/**
 * 2. ファイルを削除した際に履歴からも消去する関数
 * @param {string} fileId - 削除するファイルのID
 */
window.removeCreatedFile = function(fileId) {
    let files = JSON.parse(localStorage.getItem("user_created_files_history") || "[]");
    let activeIds = JSON.parse(localStorage.getItem("user_active_file_ids") || "[]");

    files = files.filter(f => f.id !== fileId);
    activeIds = activeIds.filter(id => id !== fileId);

    localStorage.setItem("user_created_files_history", JSON.stringify(files));
    localStorage.setItem("user_active_file_ids", JSON.stringify(activeIds));

    if (typeof window.renderRecentHistory === 'function') {
        window.renderRecentHistory();
    }
};

/**
 * 3. 履歴をすべて消去して0件（初期状態）に戻す関数
 */
window.clearAllHistory = function() {
    if (confirm("学習履歴をすべて削除して0件に戻しますか？")) {
        localStorage.removeItem("user_created_files_history");
        localStorage.removeItem("user_active_file_ids");
        location.reload();
    }
};

/**
 * 4. ファイル作成・保存成功時に呼び出すサンプル関数
 * @param {string} fileName - 作成されたファイル名
 * @param {string} fileUrl - そのファイルのURL
 * @param {string|null} fileId - ファイルID（オプション）
 */
window.onSaveFileSuccess = function(fileName, fileUrl, fileId) {
    const title = fileName || "新しいファイル";
    const url = fileUrl || "#";

    // 履歴へ保存を実行（テーマはデフォルトで 'blue'）
    window.addCreatedFile(fileId || null, title, 'blue', url);
};