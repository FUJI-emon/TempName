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
document.addEventListener('DOMContentLoaded', () => {
    // 使う要素（HTMLのパーツ）を取得
    const nameEditBtn = document.getElementById('nameEditBtn');
    const nameModalOverlay = document.getElementById('nameModalOverlay');
    const cancelNameBtn = document.getElementById('cancelNameBtn');
    const saveNameBtn = document.getElementById('saveNameBtn');
    const nameInput = document.getElementById('nameInput');

    // 1. バッジをクリックしたらポップアップを表示
    if (nameEditBtn && nameModalOverlay) {
        nameEditBtn.addEventListener('click', () => {
            nameModalOverlay.classList.remove('hidden');
            nameInput.focus(); // 自動的に入力欄にカーソルを合わせる
        });

        // 2. キャンセルボタンを押したら隠す
        cancelNameBtn.addEventListener('click', () => {
            nameModalOverlay.classList.add('hidden');
        });

        // 3. 保存ボタンを押したらCookieに記録して画面を更新
        saveNameBtn.addEventListener('click', () => {
            const newName = nameInput.value.trim(); // 入力された文字を取得
            if (newName) {
                // 名前をCookieに30日間保存
                document.cookie = `user_name=${newName}; path=/; max-age=2592000;`;
                location.reload(); // 画面を更新してヘッダーに名前を反映させる
            }
        });
    }
});

// ==========================================
    // クッキー同意バナーの処理
    // ==========================================
    const cookieBanner = document.getElementById('cookieBanner');
    const acceptCookieBtn = document.getElementById('acceptCookieBtn');
    const rejectCookieBtn = document.getElementById('rejectCookieBtn');

    if (cookieBanner) {
        // 1. ページを開いたとき、すでに「同意(true)」か「拒否(false)」のCookieがあればバナーを隠す
        if (document.cookie.includes('cookie_consent=true') || document.cookie.includes('cookie_consent=false')) {
            cookieBanner.style.display = 'none';
        }

        // 2. 「同意する」ボタンを押したときの処理
        if (acceptCookieBtn) {
            acceptCookieBtn.addEventListener('click', () => {
                // cookie_consent=true という記録を30日間保存
                document.cookie = "cookie_consent=true; path=/; max-age=2592000;";
                // バナーを画面から消す
                cookieBanner.style.display = 'none';
            });
        }

        // 3. 「拒否する」ボタンを押したときの処理
        if (rejectCookieBtn) {
            rejectCookieBtn.addEventListener('click', () => {
                // cookie_consent=false という記録を30日間保存
                document.cookie = "cookie_consent=false; path=/; max-age=2592000;";
                // バナーを画面から消す
                cookieBanner.style.display = 'none';
            });
        }
    }
