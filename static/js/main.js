// Client-side JavaScript for AI Adaptive Learning Platform
document.addEventListener('DOMContentLoaded', () => {
    console.log('✨ AI Adaptive Learning Platform Engine Initialized');

    // 🌐 Load saved language or fall back to Japanese 'ja'
    const savedLang = localStorage.getItem("app_language") || "ja";
    if (typeof window.applyGlobalLanguage === 'function') {
        window.applyGlobalLanguage(savedLang);
    }

    // 👤 Sync saved username across user display elements
    if (typeof window.applyGlobalUserName === 'function') {
        window.applyGlobalUserName();
    }

    // ⏱️ Sync daily study goal setting
    if (typeof window.applyGlobalDailyStudyGoal === 'function') {
        window.applyGlobalDailyStudyGoal();
    }
});

// ==========================================
// 🌐 Multilingual i18n Translation Engine
// ==========================================
window.i18nDictionary = window.i18nDictionary || {};
Object.assign(window.i18nDictionary, {
    ja: {
        langDisplay: "日本語",
        guestUser: "ゲストユーザー",
        addFile: "ファイルを追加",
        title: "タイトル",
        lessonFile: "授業ファイル (PDFなど)",
        cancel: "キャンセル",
        addAndStartAnalysis: "追加して解析開始",
        uploadDocument: "Upload Document",
        addLearningMaterial: "Add Learning Material",
        uploadSubTitle: "PDFやテキストファイルをアップロードしてAI学習を開始しましょう",
        dragAndDropText: "ファイルをドラッグ＆ドロップ<br>またはクリックして選択",
        selectFile: "ファイルを選択",
        step: "ステップ",
        nextStep: "次へ進む →",
        understandingCheckQuestion: "理解度チェック問題",
        viewHint: "ヒントを見る",
        hint: "ヒント",
        checkAnswer: "回答を確認する",
        backToTopics: "‹ Topicsに戻る",
        generatedByAiNote: "の学習結果からAIが生成します",
        continueLearning: "Continue Learning",
        reviewDocument: "資料の確認",
        whichPartsUnderstood: "理解できている部分は<br>どこですか？",
        markSectionsDesc: "すでに知っている部分にチェックを入れると、AIが重点的に学ぶべき内容を最適化します。",
        back: "‹ 戻る",
        deleteSelected: "選択した項目を削除",
        progress: "進捗",
        aiThinking: "AIが思考中...",
        aiAnalyzing: "コンテンツを解析しています。少々お待ちください。",
        navDashboard: "ホーム",
        navSubjects: "教科一覧",
        navProfile: "プロフィール",
        continueBtn: "学習を再開",
        profile: "プロフィール",
        profilePageTitle: "プロフィール | LearnAI Platform",
        recentLearning: "最近学習中",
        progressCompleteSuffix: "% 完了",
        courseTopicCount: "コース / トピック",
        completedCourses: "完了したコース",
        completedLessons: "完了したレッスン",
        avgProgress: "平均進捗",
        totalItemsLabel: "合計 {count} 件",
        progressLabel: "進捗",
        addNewCourse: "新しいコースを追加",
        studentAccount: "学生アカウント",
        earnedScore: "獲得スコア",
        streakStudy: "連続学習",
        preferences: "環境設定",
        notificationSound: "通知音",
        studySettings: "学習設定",
        dailyGoal: "毎日の目標",
        reminderTime: "リマインダー時間",
        autoPlayAudio: "音声自動再生",
        general: "一般",
        about: "アプリについて",
        helpSupport: "ヘルプ＆サポート",
        rateApp: "アプリを評価する",
        terms: "利用規約",
        privacy: "プライバシーポリシー",
        dangerZone: "危険エリア",
        logOut: "ログアウト",
        deleteAccount: "アカウント削除",
        selectLanguage: "言語を選択",
        close: "閉じる",
        chatHistoryTitle: "チャット履歴",
        chatHistorySubtitle: "最近更新された会話を表示しています。",
        backToChatHistory: "履歴に戻る",
        chatInputPlaceholder: "質問を入力してください...",
        sendMessage: "送信",
        noChatHistory: "まだ質問履歴がありません",
        noChatHistoryDesc: "学習ページやトピック詳細から AI Assistant に質問を開始できます。",
        settings: "設定",
        darkMode: "ダークモード",
        language: "言語",
        greeting: "こんにちは！ 👋",
        recentHistory: "直近の学習履歴",
        noHistory: "まだ作成されたファイル履歴はありません",
        myCourses: "マイコース",
        viewAll: "すべて見る",
        math: "数学",
        english: "英語",
        history: "歴史",
        science: "科学",
        addSubject: "教科を追加",
        addSubjectPlaceholder: "例: 物理",
        add: "追加",
        announcementsAndTips: "お知らせ＆ヒント",
        aiTipTitle: "AIヒント: 漢字復習の間隔を空ける",
        aiTipDesc: "就寝30分前にN3漢字カードを復習すると記憶が定着しやすくなります。",
        midtermTitle: "中間試験期間",
        midtermDesc: "来週月曜日から微積分と文学の試験が始まります。日程を確認してください。",
        upcomingDeadlines: "今後の提出期限",
        quizTitle: "N3 語彙ミニクイズ",
        quizSub: "期限: 明日 23:59 • 日本語 N3",
        daysLeft: "残り1日",
        aiAssistantName: "タヌキ学習アシスタント",
        aiAssistantMsg: "「今日はどんな学習をお手伝いしましょうか？」"
    },
    en: {
        langDisplay: "English",
        guestUser: "Guest User",
        addFile: "Add File",
        title: "Title",
        lessonFile: "Lesson File (PDF, etc.)",
        cancel: "Cancel",
        addAndStartAnalysis: "Add & Start Analysis",
        uploadDocument: "Upload Document",
        addLearningMaterial: "Add Learning Material",
        uploadSubTitle: "Upload PDF or text files to start AI learning",
        dragAndDropText: "Drag & drop files here<br>or click to select",
        selectFile: "Select File",
        step: "Step",
        nextStep: "Next →",
        understandingCheckQuestion: "Understanding Check Question",
        viewHint: "View Hint",
        hint: "Hint",
        checkAnswer: "Check Answer",
        backToTopics: "‹ Back to Topics",
        generatedByAiNote: " is generated by AI based on learning results",
        continueLearning: "Continue Learning",
        reviewDocument: "Review Document",
        whichPartsUnderstood: "Which parts do you<br>already understand?",
        markSectionsDesc: "Check sections you know so AI optimizes what you need to focus on.",
        back: "‹ Back",
        deleteSelected: "Delete Selected",
        progress: "Progress",
        aiThinking: "AI is thinking...",
        aiAnalyzing: "Analyzing content. Please wait a moment.",
        navDashboard: "Home",
        navSubjects: "Subjects",
        navProfile: "Profile",
        continueBtn: "Resume learning",
        profile: "Profile",
        profilePageTitle: "Profile | LearnAI Platform",
        recentLearning: "Recently learning",
        progressCompleteSuffix: "% complete",
        courseTopicCount: "Courses / topics",
        completedCourses: "Completed courses",
        completedLessons: "Completed lessons",
        avgProgress: "Average progress",
        totalItemsLabel: "Total {count} items",
        progressLabel: "Progress",
        addNewCourse: "Add new course",
        studentAccount: "Student Account",
        earnedScore: "Earned score",
        streakStudy: "Study streak",
        preferences: "Preferences",
        notificationSound: "Notification sound",
        studySettings: "Study settings",
        dailyGoal: "Daily goal",
        reminderTime: "Reminder time",
        autoPlayAudio: "Auto play audio",
        general: "General",
        about: "About",
        helpSupport: "Help & support",
        rateApp: "Rate the app",
        terms: "Terms of service",
        privacy: "Privacy policy",
        dangerZone: "Danger zone",
        logOut: "Log out",
        deleteAccount: "Delete account",
        selectLanguage: "Select language",
        close: "Close",
        chatHistoryTitle: "Chat History",
        chatHistorySubtitle: "Showing the most recently updated conversations.",
        backToChatHistory: "Back to history",
        chatInputPlaceholder: "Type your question here...",
        sendMessage: "Send",
        noChatHistory: "No chat history yet",
        noChatHistoryDesc: "Start asking AI Assistant from the study pages or topic details.",
        settings: "Settings",
        darkMode: "Dark Mode",
        language: "Language",
        greeting: "Hello! 👋",
        recentHistory: "Recent Activity",
        noHistory: "No learning history yet",
        myCourses: "My Courses",
        viewAll: "View All",
        math: "Mathematics",
        english: "English",
        history: "History",
        science: "Science",
        addSubject: "Add Course",
        addSubjectPlaceholder: "e.g. Physics",
        add: "Add",
        announcementsAndTips: "Announcements & Tips",
        aiTipTitle: "AI Tip: Space Out Your Kanji Review",
        aiTipDesc: "Review N3 kanji cards 30 mins before sleeping to build stronger memory paths.",
        midtermTitle: "Midterm Examination Week",
        midtermDesc: "Calculus and Literature exams commence next Monday. Check schedule.",
        upcomingDeadlines: "Upcoming Deadlines",
        quizTitle: "N3 Vocabulary Mini-Quiz",
        quizSub: "Due: Tomorrow, 11:59 PM • Japanese N3",
        daysLeft: "1 day left",
        aiAssistantName: "Tanuki Study Assistant",
        aiAssistantMsg: "\"How can I help you study today?\""
    },
    vi: {
        langDisplay: "Tiếng Việt",
        guestUser: "Người dùng khách",
        addFile: "Thêm tệp",
        title: "Tiêu đề",
        lessonFile: "Tệp bài học (PDF, v.v.)",
        cancel: "Hủy",
        addAndStartAnalysis: "Thêm & Phân tích",
        uploadDocument: "Tải tệp lên",
        addLearningMaterial: "Thêm tài liệu học",
        uploadSubTitle: "Tải lên tệp PDF hoặc văn bản để bắt đầu học với AI",
        dragAndDropText: "Kéo & thả tệp vào đây<br>hoặc nhấp để chọn",
        selectFile: "Chọn tệp",
        step: "Bước",
        nextStep: "Tiếp theo →",
        understandingCheckQuestion: "Câu hỏi kiểm tra hiểu biết",
        viewHint: "Xem gợi ý",
        hint: "Gợi ý",
        checkAnswer: "Kiểm tra đáp án",
        backToTopics: "‹ Quay lại chủ đề",
        generatedByAiNote: " được AI tạo dựa trên kết quả học tập",
        continueLearning: "Tiếp tục học",
        reviewDocument: "Xác nhận tài liệu",
        whichPartsUnderstood: "Phần nào bạn đã hiểu rõ?",
        markSectionsDesc: "Đánh dấu phần bạn đã biết để AI tập trung vào kiến thức cần nâng cao.",
        back: "‹ Quay lại",
        deleteSelected: "Xóa các mục đã chọn",
        progress: "Tiến độ",
        aiThinking: "AI đang suy nghĩ...",
        aiAnalyzing: "Đang phân tích nội dung. Vui lòng chờ.",
        navDashboard: "Trang chủ",
        navSubjects: "Môn học",
        navProfile: "Hồ sơ",
        continueBtn: "Tiếp tục học",
        profile: "Hồ sơ",
        profilePageTitle: "Hồ sơ | LearnAI Platform",
        recentLearning: "Đang học gần đây",
        progressCompleteSuffix: "% hoàn thành",
        courseTopicCount: "Khóa học / Chủ đề",
        completedCourses: "Khóa học hoàn thành",
        completedLessons: "Bài học đã xong",
        avgProgress: "Tiến độ trung bình",
        totalItemsLabel: "Tổng {count} mục",
        progressLabel: "Tiến độ",
        addNewCourse: "Thêm khóa học mới",
        studentAccount: "Tài khoản học viên",
        earnedScore: "Điểm đạt được",
        streakStudy: "Chuỗi học tập",
        preferences: "Tùy chọn",
        notificationSound: "Âm báo",
        studySettings: "Cài đặt học tập",
        dailyGoal: "Mục tiêu mỗi ngày",
        reminderTime: "Giờ nhắc nhở",
        autoPlayAudio: "Tự phát âm thanh",
        general: "Chung",
        about: "Giới thiệu",
        helpSupport: "Trợ giúp & hỗ trợ",
        rateApp: "Đánh giá ứng dụng",
        terms: "Điều khoản sử dụng",
        privacy: "Chính sách quyền riêng tư",
        dangerZone: "Vùng nguy hiểm",
        logOut: "Đăng xuất",
        deleteAccount: "Xóa tài khoản",
        selectLanguage: "Chọn ngôn ngữ",
        close: "Đóng",
        chatHistoryTitle: "Lịch sử chat",
        chatHistorySubtitle: "Hiển thị các cuộc trò chuyện được cập nhật gần nhất.",
        backToChatHistory: "Quay lại lịch sử",
        chatInputPlaceholder: "Nhập câu hỏi của bạn...",
        sendMessage: "Gửi",
        noChatHistory: "Chưa có lịch sử trò chuyện",
        noChatHistoryDesc: "Bắt đầu hỏi AI Assistant từ trang học tập hoặc trang chi tiết topic.",
        settings: "Cài đặt",
        darkMode: "Chế độ tối",
        language: "Ngôn ngữ",
        greeting: "Xin chào! 👋",
        recentHistory: "Lịch sử học tập gần đây",
        noHistory: "Chưa có lịch sử học tập",
        myCourses: "Khóa học của tôi",
        viewAll: "Xem tất cả",
        math: "Toán học",
        english: "Tiếng Anh",
        history: "Lịch sử",
        science: "Khoa học",
        addSubject: "Thêm môn học",
        addSubjectPlaceholder: "Ví dụ: Vật lý",
        add: "Thêm",
        announcementsAndTips: "Thông báo & Gợi ý",
        aiTipTitle: "Gợi ý AI: Dãn cách thời gian ôn tập Kanji",
        aiTipDesc: "Ôn tập thẻ Kanji N3 30 phút trước khi ngủ để ghi nhớ tốt hơn.",
        midtermTitle: "Tuần thi giữa kỳ",
        midtermDesc: "Kỳ thi Giải tích và Ngữ văn bắt đầu vào Thứ Hai tới. Kiểm tra lịch trình.",
        upcomingDeadlines: "Hạn chót sắp tới",
        quizTitle: "Bài kiểm tra nhỏ từ vựng N3",
        quizSub: "Hạn: Ngày mai, 23:59 • Tiếng Nhật N3",
        daysLeft: "Còn 1 ngày",
        aiAssistantName: "Trợ lý học tập Tanuki",
        aiAssistantMsg: "\"Tôi có thể giúp gì cho bạn học hôm nay?\""
    }
});

// ==========================================
// ⏱️ Daily Study Goal Sync Engine
// ==========================================
window.applyGlobalDailyStudyGoal = function() {
    const savedGoal = localStorage.getItem("daily_study_goal") || "30";
    const goalNum = parseInt(savedGoal, 10) || 30;

    document.querySelectorAll(".daily-goal-display, .daily-goal-target, #dailyGoalDisplay").forEach(el => {
        const format = el.dataset.format;
        if (format === "text") {
            el.textContent = `${goalNum}分`;
        } else if (format === "m") {
            el.textContent = `${goalNum}m`;
        } else if (format === "raw") {
            el.textContent = goalNum;
        } else {
            el.textContent = `目標: ${goalNum}分`;
        }
    });
};

window.saveDailyStudyGoal = function(minutes) {
    if (minutes !== undefined && minutes !== null && minutes !== "") {
        localStorage.setItem("daily_study_goal", String(minutes));
        window.applyGlobalDailyStudyGoal();
    }
};

// ==========================================
// 👤 Global Username Sync Engine
// ==========================================
window.applyGlobalUserName = function() {
    const savedName = localStorage.getItem("user_name");
    const lang = localStorage.getItem("app_language") || "ja";
    const dict = (window.i18nDictionary && window.i18nDictionary[lang]) ? window.i18nDictionary[lang] : { guestUser: "ゲストユーザー" };

    const displayName = (savedName && savedName.trim() !== "") ? savedName : dict.guestUser;

    document.querySelectorAll(".user-name-display").forEach(el => {
        el.textContent = displayName;
    });
};

window.saveUserNameOnLogin = function(inputElementOrString) {
    let username = "";
    if (typeof inputElementOrString === "string") {
        username = inputElementOrString;
    } else if (inputElementOrString && inputElementOrString.value) {
        username = inputElementOrString.value;
    }

    if (username.trim() !== "") {
        localStorage.setItem("user_name", username.trim());
        window.applyGlobalUserName();
    }
};

// ==========================================
// 🖐️ Card Swipe Gesture Utility Engine
// ==========================================
window.setupSwipeableCard = function(cardElement, onSwipeLeft, onSwipeRight) {
    if (!cardElement) return;

    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    let isDragging = false;

    const handleTouchStart = (e) => {
        const touch = e.touches ? e.touches[0] : e;
        startX = touch.clientX;
        startY = touch.clientY;
        isDragging = true;
        cardElement.classList.add('swiping');
    };

    const handleTouchMove = (e) => {
        if (!isDragging) return;
        const touch = e.touches ? e.touches[0] : e;
        currentX = touch.clientX - startX;
        currentY = touch.clientY - startY;

        // Only rotate and transform if horizontal swipe is dominant
        if (Math.abs(currentX) > Math.abs(currentY)) {
            const rotate = currentX * 0.05;
            cardElement.style.transform = `translateX(${currentX}px) rotate(${rotate}deg)`;
            cardElement.style.opacity = Math.max(0.4, 1 - Math.abs(currentX) / 400);
        }
    };

    const handleTouchEnd = () => {
        if (!isDragging) return;
        isDragging = false;
        cardElement.classList.remove('swiping');

        const threshold = 100;
        if (currentX < -threshold) {
            cardElement.style.transform = '';
            cardElement.style.opacity = '';
            if (typeof onSwipeLeft === 'function') onSwipeLeft();
        } else if (currentX > threshold) {
            cardElement.style.transform = '';
            cardElement.style.opacity = '';
            if (typeof onSwipeRight === 'function') onSwipeRight();
        } else {
            cardElement.style.transform = '';
            cardElement.style.opacity = '';
        }

        startX = 0;
        startY = 0;
        currentX = 0;
        currentY = 0;
    };

    cardElement.addEventListener('touchstart', handleTouchStart, { passive: true });
    cardElement.addEventListener('touchmove', handleTouchMove, { passive: true });
    cardElement.addEventListener('touchend', handleTouchEnd);

    cardElement.addEventListener('mousedown', handleTouchStart);
    window.addEventListener('mousemove', handleTouchMove);
    window.addEventListener('mouseup', handleTouchEnd);
};
