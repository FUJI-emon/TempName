(function () {
  const ROUTES = {
    landing: "lumina_learning_landing_page.html",
    login: "lumina_learning_login_screen.html",
    dashboard: "student_dashboard_overview.html",
    upload: "lumina_learning_upload_document_desktop.html",
    reviewDocument: "review_document_content_selection.html",
    courses: "personalized_learning_path.html",
    lesson: "interactive_lesson_linear_regression_with_sidebar.html",
    newCourse: "new_course_ai_topic_discussion.html",
    settings: "settings_user_account_preferences.html",
    history: "course_history_my_learning_journeys_1.html",
    test: "final_test_full_screen_question_review.html",
    result: "final_test_result_summary_review.html",
    aiReview: "final_test_ai_review_conversation.html"
  };

  const STORAGE = {
    theme: "lumina.theme",
    language: "lumina.language"
  };

  const SUPPORTED_LANGS = ["en", "vi", "ja"];
  const currentPage = (document.body?.dataset.page || decodeURIComponent(window.location.pathname.split("/").pop() || "")).toLowerCase();
  const originalTitle = document.title;

  const TEXT_MAP = {
    en: {},
    vi: {
      "Lumina Learning": "Lumina Learning",
      "Lumina AI": "Lumina AI",
      "Dashboard": "Bảng điều khiển",
      "My Courses": "Khóa học của tôi",
      "Courses": "Khóa học",
      "AI Tutor": "Gia sư AI",
      "Settings": "Cài đặt",
      "Help": "Trợ giúp",
      "Help Center": "Trung tâm trợ giúp",
      "Logout": "Đăng xuất",
      "Login": "Đăng nhập",
      "Get Started": "Bắt đầu",
      "Start Learning Free": "Bắt đầu học miễn phí",
      "Features": "Tính năng",
      "Pricing": "Bảng giá",
      "About": "Giới thiệu",
      "Welcome back": "Chào mừng bạn trở lại",
      "Sign in to continue your learning journey": "Đăng nhập để tiếp tục hành trình học tập",
      "Forgot password?": "Quên mật khẩu?",
      "Don't have an account?": "Chưa có tài khoản?",
      "Sign up": "Đăng ký",
      "New Study Session": "Buổi học mới",
      "Continue Learning": "Tiếp tục học",
      "Continue Lesson": "Tiếp tục bài học",
      "Upcoming Lessons": "Bài học sắp tới",
      "AI Insights": "Gợi ý từ AI",
      "View all": "Xem tất cả",
      "Start New Topic": "Bắt đầu chủ đề mới",
      "Review Now": "Ôn lại ngay",
      "Upload study materials": "Tải tài liệu học tập lên",
      "Submit and Learn": "Gửi và học",
      "Skip, show everything": "Bỏ qua, hiển thị tất cả",
      "Previous": "Trước đó",
      "Next": "Tiếp theo",
      "Need help?": "Cần trợ giúp?",
      "Exit Test": "Thoát bài kiểm tra",
      "Submit Answer": "Nộp câu trả lời",
      "Continue to Next Lesson": "Tiếp tục sang bài tiếp theo",
      "Review Mistakes": "Xem lại lỗi sai",
      "Hear AI Explanation": "Nghe giải thích từ AI",
      "Ask AI about this": "Hỏi AI về nội dung này",
      "Question Review": "Xem lại câu hỏi",
      "Correct": "Đúng",
      "Incorrect": "Sai",
      "Lesson Complete": "Hoàn thành bài học",
      "Profile Settings": "Cài đặt hồ sơ",
      "Account & Security": "Tài khoản và bảo mật",
      "Password": "Mật khẩu",
      "Linked Accounts": "Tài khoản liên kết",
      "Two-Factor Authentication": "Xác thực hai lớp",
      "App Preferences": "Tùy chọn ứng dụng",
      "Appearance Theme": "Giao diện",
      "Primary Language": "Ngôn ngữ chính",
      "Notifications": "Thông báo",
      "Light": "Sáng",
      "Dark": "Tối",
      "English (US)": "Tiếng Anh",
      "Vietnamese (Tiếng Việt)": "Tiếng Việt",
      "Japanese (日本語)": "Tiếng Nhật"
    },
    ja: {
      "Lumina Learning": "Lumina Learning",
      "Lumina AI": "Lumina AI",
      "Dashboard": "ダッシュボード",
      "My Courses": "マイコース",
      "Courses": "コース",
      "AI Tutor": "AIチューター",
      "Settings": "設定",
      "Help": "ヘルプ",
      "Help Center": "ヘルプセンター",
      "Logout": "ログアウト",
      "Login": "ログイン",
      "Get Started": "始める",
      "Start Learning Free": "無料で学習を始める",
      "Features": "機能",
      "Pricing": "料金",
      "About": "概要",
      "Welcome back": "お帰りなさい",
      "Sign in to continue your learning journey": "学習を続けるにはサインインしてください",
      "Forgot password?": "パスワードをお忘れですか？",
      "Don't have an account?": "アカウントをお持ちでないですか？",
      "Sign up": "登録",
      "New Study Session": "新しい学習セッション",
      "Continue Learning": "学習を続ける",
      "Continue Lesson": "レッスンを続ける",
      "Upcoming Lessons": "今後のレッスン",
      "AI Insights": "AIのヒント",
      "View all": "すべて表示",
      "Start New Topic": "新しいトピックを開始",
      "Review Now": "今すぐ復習",
      "Upload study materials": "学習資料をアップロード",
      "Submit and Learn": "送信して学ぶ",
      "Skip, show everything": "スキップして全て表示",
      "Previous": "前へ",
      "Next": "次へ",
      "Need help?": "ヘルプが必要ですか？",
      "Exit Test": "テストを終了",
      "Submit Answer": "回答を送信",
      "Continue to Next Lesson": "次のレッスンへ進む",
      "Review Mistakes": "間違いを確認",
      "Hear AI Explanation": "AIの説明を聞く",
      "Ask AI about this": "これについてAIに質問",
      "Question Review": "問題レビュー",
      "Correct": "正解",
      "Incorrect": "不正解",
      "Lesson Complete": "レッスン完了",
      "Profile Settings": "プロフィール設定",
      "Account & Security": "アカウントとセキュリティ",
      "Password": "パスワード",
      "Linked Accounts": "連携アカウント",
      "Two-Factor Authentication": "二要素認証",
      "App Preferences": "アプリ設定",
      "Appearance Theme": "外観テーマ",
      "Primary Language": "表示言語",
      "Notifications": "通知",
      "Light": "ライト",
      "Dark": "ダーク",
      "English (US)": "英語",
      "Vietnamese (Tiếng Việt)": "ベトナム語",
      "Japanese (日本語)": "日本語"
    }
  };

  const TITLE_MAP = {
    vi: {
      "Lumina Learning - AI Tutor": "Lumina Learning - Gia sư AI",
      "Lumina Learning - Login": "Lumina Learning - Đăng nhập",
      "Lumina Learning - Student Dashboard": "Lumina Learning - Bảng điều khiển",
      "Optimize Learning Path - Document Upload": "Tối ưu lộ trình học - Tải tài liệu",
      "Lumina Learning - Review Document": "Lumina Learning - Xem lại tài liệu",
      "Lumina Learning - Learning Path": "Lumina Learning - Lộ trình học",
      "Lumina Learning - Linear Regression": "Lumina Learning - Hồi quy tuyến tính",
      "Lumina AI - AI Tutor Chat": "Lumina AI - Chat gia sư AI",
      "Settings - Lumina AI": "Cài đặt - Lumina AI",
      "Course History - Lumina AI": "Lịch sử khóa học - Lumina AI",
      "Lumina Learning - Concept Test": "Lumina Learning - Bài kiểm tra khái niệm",
      "Lumina Learning - Final Test Result": "Lumina Learning - Kết quả bài kiểm tra cuối",
      "AI Tutor Conversation": "Cuộc trò chuyện với AI Tutor"
    },
    ja: {
      "Lumina Learning - AI Tutor": "Lumina Learning - AIチューター",
      "Lumina Learning - Login": "Lumina Learning - ログイン",
      "Lumina Learning - Student Dashboard": "Lumina Learning - ダッシュボード",
      "Optimize Learning Path - Document Upload": "学習パスを最適化 - 資料アップロード",
      "Lumina Learning - Review Document": "Lumina Learning - 資料レビュー",
      "Lumina Learning - Learning Path": "Lumina Learning - 学習パス",
      "Lumina Learning - Linear Regression": "Lumina Learning - 線形回帰",
      "Lumina AI - AI Tutor Chat": "Lumina AI - AIチューターチャット",
      "Settings - Lumina AI": "設定 - Lumina AI",
      "Course History - Lumina AI": "コース履歴 - Lumina AI",
      "Lumina Learning - Concept Test": "Lumina Learning - 概念テスト",
      "Lumina Learning - Final Test Result": "Lumina Learning - 最終テスト結果",
      "AI Tutor Conversation": "AIチューター会話"
    }
  };

  function storageGet(key) {
    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  }

  function storageSet(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch {
      return;
    }
  }

  function ensureThemeStyle() {
    if (document.getElementById("lumina-theme-overrides")) return;
    const style = document.createElement("style");
    style.id = "lumina-theme-overrides";
    style.textContent = `
      html {
        background: #0b0d12;
      }
      body {
        transform-origin: 50% 30%;
      }
      body.lumina-page-enter {
        animation: luminaPageEnter 340ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
      }
      body.lumina-page-exit {
        animation: luminaPageExit 180ms cubic-bezier(0.4, 0, 0.2, 1) both;
      }
      @keyframes luminaPageEnter {
        from {
          opacity: 0;
          transform: translateY(14px) scale(0.985) rotateX(1deg);
          filter: blur(6px);
        }
        to {
          opacity: 1;
          transform: translateY(0) scale(1) rotateX(0deg);
          filter: blur(0);
        }
      }
      @keyframes luminaPageExit {
        from {
          opacity: 1;
          transform: translateY(0) scale(1) rotateX(0deg);
          filter: blur(0);
        }
        to {
          opacity: 0;
          transform: translateY(-10px) scale(0.992) rotateX(1.5deg);
          filter: blur(4px);
        }
      }
      html[data-theme="dark"] {
        color-scheme: dark;
        background: #0b0d12;
      }
      html[data-theme="dark"] body {
        background: #0b0d12 !important;
        color: #e8eaf0 !important;
      }
      html[data-theme="dark"] body,
      html[data-theme="dark"] main,
      html[data-theme="dark"] header,
      html[data-theme="dark"] footer,
      html[data-theme="dark"] nav,
      html[data-theme="dark"] aside,
      html[data-theme="dark"] section,
      html[data-theme="dark"] article,
      html[data-theme="dark"] .glass-panel,
      html[data-theme="dark"] .glass,
      html[data-theme="dark"] .glass-panel * {
        color-scheme: dark;
      }
      html[data-theme="dark"] .bg-background,
      html[data-theme="dark"] .bg-page {
        background-color: #0b0d12 !important;
      }
      html[data-theme="dark"] .bg-surface-container-lowest,
      html[data-theme="dark"] .glass-panel,
      html[data-theme="dark"] .glass {
        background-color: #171e2b !important;
        border-color: #2a3140 !important;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.28) !important;
      }
      html[data-theme="dark"] .bg-surface-container-low,
      html[data-theme="dark"] .bg-surface-bright,
      html[data-theme="dark"] .bg-surface-container,
      html[data-theme="dark"] .chat-ai-bg {
        background-color: #1b2332 !important;
        border-color: #2c3546 !important;
      }
      html[data-theme="dark"] .bg-surface-container-high,
      html[data-theme="dark"] .bg-surface-container-highest,
      html[data-theme="dark"] .bg-surface-dim,
      html[data-theme="dark"] .bg-surface-variant {
        background-color: #212c3c !important;
      }
      html[data-theme="dark"] .bg-surface,
      html[data-theme="dark"] .bg-surface-container-lowest\/80,
      html[data-theme="dark"] .bg-surface\/80,
      html[data-theme="dark"] .checkbox-container:has(input:checked),
      html[data-theme="dark"] .dark\:bg-inverse-surface,
      html[data-theme="dark"] .dark\:bg-background\/80 {
        background-color: #151c27 !important;
      }
      html[data-theme="dark"] .bg-surface-container-lowest\/0,
      html[data-theme="dark"] .bg-surface-container-lowest\/5,
      html[data-theme="dark"] .bg-surface-container-lowest\/10 {
        background-color: transparent !important;
      }
      html[data-theme="dark"] .border-outline-variant,
      html[data-theme="dark"] .border-surface-variant,
      html[data-theme="dark"] .border-surface-container-highest,
      html[data-theme="dark"] .border-surface-container-high,
      html[data-theme="dark"] .border-surface-container {
        border-color: #2a3140 !important;
      }
      html[data-theme="dark"] .text-on-surface,
      html[data-theme="dark"] .text-on-background {
        color: #eef1f7 !important;
      }
      html[data-theme="dark"] .text-on-surface-variant,
      html[data-theme="dark"] .text-outline,
      html[data-theme="dark"] .text-outline-variant {
        color: #aab2c5 !important;
      }
      html[data-theme="dark"] .text-primary,
      html[data-theme="dark"] .text-primary-fixed-dim,
      html[data-theme="dark"] .text-inverse-primary {
        color: #b9b7ff !important;
      }
      html[data-theme="dark"] .material-symbols-outlined,
      html[data-theme="dark"] svg,
      html[data-theme="dark"] svg * {
        color: #d8ddeb !important;
        fill: currentColor !important;
        stroke: currentColor !important;
      }
      html[data-theme="dark"] .text-xs,
      html[data-theme="dark"] .font-label-sm,
      html[data-theme="dark"] .text-label-sm,
      html[data-theme="dark"] .text-sm {
        color: #b4bfd1 !important;
      }
      html[data-theme="dark"] .bg-primary-container,
      html[data-theme="dark"] .bg-primary-fixed,
      html[data-theme="dark"] .bg-primary-fixed-dim {
        background-color: #2d3272 !important;
      }
      html[data-theme="dark"] .bg-secondary-container {
        background-color: #4b2b61 !important;
      }
      html[data-theme="dark"] .bg-tertiary-container {
        background-color: #163f74 !important;
      }
      html[data-theme="dark"] .bg-primary {
        background-color: #7c79ff !important;
      }
      html[data-theme="dark"] input,
      html[data-theme="dark"] select,
      html[data-theme="dark"] textarea {
        background-color: #0f141c !important;
        color: #eef1f7 !important;
        border-color: #2a3140 !important;
      }
      html[data-theme="dark"] option {
        background-color: #0f141c !important;
        color: #eef1f7 !important;
      }
      html[data-theme="dark"] .shadow-sm,
      html[data-theme="dark"] .shadow-md,
      html[data-theme="dark"] .shadow-lg,
      html[data-theme="dark"] .shadow-xl {
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.32) !important;
      }
      html[data-theme="dark"] ::placeholder {
        color: #74809a !important;
      }
      html[data-theme="dark"] a:hover,
      html[data-theme="dark"] button:hover {
        filter: brightness(1.06);
      }
    `;
    document.head.appendChild(style);
  }

  function textOf(element) {
    return (element.textContent || "").replace(/\s+/g, " ").trim();
  }

  function setNavigation(element, target) {
    if (!target || !element) return;

    if (element.tagName === "A") {
      element.href = target;
      if (element.dataset.navBound === "true") return;
      element.dataset.navBound = "true";
      element.addEventListener("click", (event) => {
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) {
          return;
        }
        event.preventDefault();
        navigateWithTransition(target);
      });
      return;
    }

    if (element.tagName === "BUTTON") {
      element.type = "button";
      if (element.dataset.navBound === "true") return;
      element.dataset.navBound = "true";
      element.addEventListener("click", (event) => {
        event.preventDefault();
        navigateWithTransition(target);
      });
      element.style.cursor = "pointer";
    }
  }

  function navigateWithTransition(target) {
    if (target === ROUTES.landing && window.API?.auth) {
      window.API.auth.logout();
    }
    const body = document.body;
    if (!body) {
      window.location.href = target;
      return;
    }

    if (body.dataset.transitioning === "true") return;
    body.dataset.transitioning = "true";
    body.classList.remove("lumina-page-enter");
    body.classList.add("lumina-page-exit");

    window.setTimeout(() => {
      window.location.href = target;
    }, 180);
  }

  function applyRules(rules, selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach((element) => {
      const label = textOf(element);
      if (!label) return;

      for (const rule of rules) {
        if (rule.match.test(label)) {
          setNavigation(element, rule.target);
          break;
        }
      }
    });
  }

  const sharedRules = [
    { match: /lumina learning|lumina ai/i, target: currentPage === ROUTES.landing ? ROUTES.landing : ROUTES.dashboard },
    { match: /dashboard/i, target: ROUTES.dashboard },
    { match: /(my courses|courses)/i, target: ROUTES.courses },
    { match: /ai tutor/i, target: ROUTES.newCourse },
    { match: /settings/i, target: ROUTES.settings },
    { match: /history/i, target: ROUTES.history },
    { match: /help center|help\b/i, target: ROUTES.dashboard },
    { match: /logout/i, target: ROUTES.landing }
  ];

  const pageRules = {
    [ROUTES.landing]: [
      { match: /login/i, target: ROUTES.login },
      { match: /get started/i, target: ROUTES.login },
      { match: /start learning free/i, target: ROUTES.login }
    ],
    [ROUTES.login]: [
      { match: /forgot password/i, target: ROUTES.landing },
      { match: /sign up/i, target: ROUTES.landing },
      { match: /google/i, target: ROUTES.dashboard },
      { match: /apple/i, target: ROUTES.dashboard }
    ],
    [ROUTES.dashboard]: [
      { match: /new study session/i, target: ROUTES.upload },
      { match: /add new course/i, target: ROUTES.upload },
      { match: /view all/i, target: ROUTES.courses },
      { match: /continue lesson/i, target: ROUTES.lesson },
      { match: /start new topic/i, target: ROUTES.newCourse },
      { match: /review now/i, target: ROUTES.reviewDocument }
    ],
    [ROUTES.upload]: [
      { match: /chevron_left|arrow_back/i, target: ROUTES.dashboard }
    ],
    [ROUTES.reviewDocument]: [
      { match: /arrow_back|chevron_left/i, target: ROUTES.upload },
      { match: /submit and learn/i, target: ROUTES.courses },
      { match: /skip, show everything/i, target: ROUTES.courses },
      { match: /new study session/i, target: ROUTES.upload }
    ],
    [ROUTES.courses]: [
      { match: /continue learning/i, target: ROUTES.lesson }
    ],
    [ROUTES.newCourse]: [
      { match: /resources/i, target: ROUTES.upload },
      { match: /upload study materials/i, target: ROUTES.upload }
    ],
    [ROUTES.lesson]: [
      { match: /previous/i, target: ROUTES.courses },
      { match: /\bnext\b/i, target: ROUTES.test },
      { match: /need help/i, target: ROUTES.newCourse }
    ],
    [ROUTES.test]: [
      { match: /exit test/i, target: ROUTES.lesson },
      { match: /submit answer/i, target: ROUTES.result }
    ],
    [ROUTES.result]: [
      { match: /continue to next lesson/i, target: ROUTES.courses },
      { match: /review mistakes/i, target: ROUTES.test },
      { match: /hear ai explanation|ask ai about this/i, target: ROUTES.aiReview },
      { match: /^question \d+/i, target: ROUTES.test }
    ],
    [ROUTES.aiReview]: [
      { match: /close/i, target: ROUTES.result },
      { match: /next question/i, target: ROUTES.test }
    ],
    [ROUTES.history]: [
      { match: /add new course/i, target: ROUTES.upload },
      { match: /continue lesson/i, target: ROUTES.lesson },
      { match: /review material/i, target: ROUTES.reviewDocument },
      { match: /resume masterclass/i, target: ROUTES.lesson }
    ]
  };

  function getLanguage() {
    const saved = storageGet(STORAGE.language);
    if (saved && SUPPORTED_LANGS.includes(saved)) return saved;
    const browser = (navigator.language || "").toLowerCase();
    if (browser.startsWith("ja")) return "ja";
    if (browser.startsWith("vi")) return "vi";
    return "en";
  }

  function getTheme() {
    const saved = storageGet(STORAGE.theme);
    if (saved === "dark" || saved === "light") return saved;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function syncThemeControls(theme) {
    const controls = document.querySelectorAll("[data-theme-option]");
    controls.forEach((control) => {
      const selected = control.dataset.themeOption === theme;
      control.setAttribute("aria-pressed", selected ? "true" : "false");
      control.classList.toggle("bg-surface-container-lowest", selected);
      control.classList.toggle("shadow-sm", selected);
      control.classList.toggle("text-primary", selected);
      control.classList.toggle("text-on-surface-variant", !selected);
    });
  }

  function applyTheme(theme) {
    ensureThemeStyle();
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    root.classList.toggle("light", theme !== "dark");
    root.dataset.theme = theme;
    storageSet(STORAGE.theme, theme);
    syncThemeControls(theme);
  }

  function translateTextNodes(lang) {
    const map = TEXT_MAP[lang] || TEXT_MAP.en;
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (["SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE"].includes(parent.tagName)) return NodeFilter.FILTER_REJECT;
        if (!node.nodeValue || !node.nodeValue.replace(/\s+/g, " ").trim()) return NodeFilter.FILTER_SKIP;
        return NodeFilter.FILTER_ACCEPT;
      }
    });

    const nodes = [];
    while (walker.nextNode()) {
      nodes.push(walker.currentNode);
    }

    nodes.forEach((node) => {
      if (!node.__luminaOriginalText) {
        node.__luminaOriginalText = node.nodeValue;
      }
      const source = node.__luminaOriginalText;
      const normalized = source.replace(/\s+/g, " ").trim();
      const translated = map[normalized];
      node.nodeValue = translated ? source.replace(normalized, translated) : source;
    });
  }

  function syncLanguageControls(lang) {
    const select = document.querySelector("#language-select");
    if (select) {
      select.value = lang;
    }
  }

  function applyLanguage(lang) {
    const normalized = SUPPORTED_LANGS.includes(lang) ? lang : "en";
    const root = document.documentElement;
    root.lang = normalized;
    root.dataset.language = normalized;
    storageSet(STORAGE.language, normalized);
    translateTextNodes(normalized);
    syncLanguageControls(normalized);

    const titleMap = TITLE_MAP[normalized] || {};
    document.title = titleMap[originalTitle] || originalTitle;
  }

  function bindSettingsControls() {
    const themeButtons = document.querySelectorAll("[data-theme-option]");
    themeButtons.forEach((button) => {
      if (button.dataset.boundTheme === "true") return;
      button.dataset.boundTheme = "true";
      button.addEventListener("click", () => applyTheme(button.dataset.themeOption));
    });

    const languageSelect = document.querySelector("#language-select");
    if (languageSelect && languageSelect.dataset.boundLanguage !== "true") {
      languageSelect.dataset.boundLanguage = "true";
      languageSelect.addEventListener("change", () => applyLanguage(languageSelect.value));
    }
  }

  function bindNavigation() {
    applyRules(sharedRules, "a, button");
    const rulesForPage = pageRules[currentPage];
    if (rulesForPage) {
      applyRules(rulesForPage, "a, button");
    }
  }

  bindNavigation();
  applyTheme(getTheme());
  applyLanguage(getLanguage());
  bindSettingsControls();

  window.requestAnimationFrame(() => {
    document.body?.classList.add("lumina-page-enter");
  });
})();
