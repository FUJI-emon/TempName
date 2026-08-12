// Client-side JavaScript for AI Adaptive Learning App
document.addEventListener('DOMContentLoaded', () => {
    console.log('AIとともに学習するクイズアプリ — Phase 1 Initialized');
});

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