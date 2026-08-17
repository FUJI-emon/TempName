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
    en: {
      "Lumina Learning": "TempName Learning",
      "Lumina AI": "TempName AI",
      "Lịch Sử Chat": "Chat History",
      "Đoạn chat mới": "New Chat",
      "Các cuộc trò chuyện gần đây": "Recent Conversations",
      "Đang tải lịch sử chat...": "Loading chat history...",
      "Đang tải lịch sử...": "Loading history...",
      "Chưa có lịch sử đoạn chat nào.": "No chat history found.",
      "Không thể tải danh sách cuộc trò chuyện.": "Failed to load chat conversations.",
      "Không thể tạo hoặc tải chat thread từ server.": "Unable to create or load chat thread from server.",
      "Lỗi kết nối backend AI Chat. Vui lòng thử lại.": "AI Chat connection error. Please try again.",
      "Không thể tải tin nhắn của đoạn chat này.": "Unable to load messages for this conversation.",
      "Không thể khởi tạo đoạn chat mới.": "Unable to start a new chat.",
      "TempName AI đang suy nghĩ...": "TempName AI is thinking...",
      "Lumina AI đang suy nghĩ...": "TempName AI is thinking...",
      "Đã xảy ra lỗi khi gửi tin nhắn.": "An error occurred while sending message.",
      "Đóng": "Close",
      "Nhập câu hỏi cho AI Tutor...": "Ask AI Tutor a question...",
      "Học cùng TempName AI Tutor": "Learn with TempName AI Tutor",
      "Học cùng Lumina AI Tutor": "Learn with TempName AI Tutor",
      "Bạn có thể hỏi bất kỳ thắc mắc nào về bài học, khái niệm hoặc hỏi \"Tại sao bước này lại làm như vậy?\"." : "You can ask any questions about lessons, concepts, or why a step was done this way.",
      "Xóa khóa học": "Delete Course",
      "Xin chào! Bạn muốn học về chủ đề gì hôm nay?": "Hello! What topic would you like to learn today?",
      "Hãy trò chuyện với AI Tutor về chủ đề hoặc mục tiêu học tập của bạn, hoặc tải ngay tài liệu bài học lên để AI phân tích và tạo lộ trình cá nhân hóa!": "Chat with AI Tutor about your learning topic or goal, or upload lesson materials for AI to analyze and create a personalized path!",
      "Upload tài liệu ngay": "Upload document now",
      "Trò chuyện về chủ đề": "Chat about topic"
    },
    vi: {
      "Lumina Learning": "TempName Learning",
      "TempName Learning": "TempName Learning",
      "Lumina AI": "TempName AI",
      "TempName AI": "TempName AI",
      "Lịch Sử Chat": "Lịch Sử Chat",
      "Chat History": "Lịch Sử Chat",
      "Đoạn chat mới": "Đoạn chat mới",
      "New Chat": "Đoạn chat mới",
      "Các cuộc trò chuyện gần đây": "Các cuộc trò chuyện gần đây",
      "Recent Conversations": "Các cuộc trò chuyện gần đây",
      "Đang tải lịch sử chat...": "Đang tải lịch sử chat...",
      "Loading chat history...": "Đang tải lịch sử chat...",
      "Đang tải lịch sử...": "Đang tải lịch sử...",
      "Loading history...": "Đang tải lịch sử...",
      "Chưa có lịch sử đoạn chat nào.": "Chưa có lịch sử đoạn chat nào.",
      "No chat history found.": "Chưa có lịch sử đoạn chat nào.",
      "Không thể tải danh sách cuộc trò chuyện.": "Không thể tải danh sách cuộc trò chuyện.",
      "Failed to load chat conversations.": "Không thể tải danh sách cuộc trò chuyện.",
      "Không thể tạo hoặc tải chat thread từ server.": "Không thể tạo hoặc tải chat thread từ server.",
      "Unable to create or load chat thread from server.": "Không thể tạo hoặc tải chat thread từ server.",
      "Lỗi kết nối backend AI Chat. Vui lòng thử lại.": "Lỗi kết nối backend AI Chat. Vui lòng thử lại.",
      "AI Chat connection error. Please try again.": "Lỗi kết nối backend AI Chat. Vui lòng thử lại.",
      "Không thể tải tin nhắn của đoạn chat này.": "Không thể tải tin nhắn của đoạn chat này.",
      "Unable to load messages for this conversation.": "Không thể tải tin nhắn của đoạn chat này.",
      "Không thể khởi tạo đoạn chat mới.": "Không thể khởi tạo đoạn chat mới.",
      "Unable to start a new chat.": "Không thể khởi tạo đoạn chat mới.",
      "TempName AI đang suy nghĩ...": "TempName AI đang suy nghĩ...",
      "TempName AI is thinking...": "TempName AI đang suy nghĩ...",
      "Lumina AI đang suy nghĩ...": "TempName AI đang suy nghĩ...",
      "Đã xảy ra lỗi khi gửi tin nhắn.": "Đã xảy ra lỗi khi gửi tin nhắn.",
      "An error occurred while sending message.": "Đã xảy ra lỗi khi gửi tin nhắn.",
      "Đóng": "Đóng",
      "Close": "Đóng",
      "Nhập câu hỏi cho AI Tutor...": "Nhập câu hỏi cho AI Tutor...",
      "Ask AI Tutor a question...": "Nhập câu hỏi cho AI Tutor...",
      "Học cùng TempName AI Tutor": "Học cùng TempName AI Tutor",
      "Learn with TempName AI Tutor": "Học cùng TempName AI Tutor",
      "Học cùng Lumina AI Tutor": "Học cùng TempName AI Tutor",
      "Bạn có thể hỏi bất kỳ thắc mắc nào về bài học, khái niệm hoặc hỏi \"Tại sao bước này lại làm như vậy?\".": "Bạn có thể hỏi bất kỳ thắc mắc nào về bài học, khái niệm hoặc hỏi \"Tại sao bước này lại làm như vậy?\".",
      "You can ask any questions about lessons, concepts, or why a step was done this way.": "Bạn có thể hỏi bất kỳ thắc mắc nào về bài học, khái niệm hoặc hỏi \"Tại sao bước này lại làm như vậy?\".",
      "TempName AI can make mistakes. Verify important information.": "TempName AI có thể mắc sai sót. Vui lòng kiểm tra lại thông tin quan trọng.",
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
      "Japanese (日本語)": "Tiếng Nhật",
      "No Active Courses Found": "Chưa có khóa học nào đang hoạt động",
      "Upload a study material or topic to get started with your personalized AI learning journey!": "Tải lên tài liệu học tập hoặc chủ đề để bắt đầu lộ trình học tập cá nhân hóa cùng AI!",
      "Start New Course": "Bắt đầu khóa học mới",
      "Expand Your Horizons": "Mở rộng tri thức",
      "Discover new subjects tailored to your learning style.": "Khám phá các chủ đề mới được thiết kế riêng cho phong cách học của bạn.",
      "Start New Topic": "Bắt đầu chủ đề mới",
      "Upload new study material": "Tải lên tài liệu học tập mới",
      "Upload PDF or Word documents for AI to analyze and generate a learning path": "Tải lên PDF/Word để AI phân tích và tạo lộ trình học tập",
      "Chat with AI Tutor": "Trò chuyện với AI Tutor",
      "Discuss learning topics you want to explore": "Thảo luận về chủ đề học tập bạn mong muốn khám phá",
      "AI Path Suggestion": "Gợi ý lộ trình AI",
      "Upload study materials or chat with AI Tutor to receive a personalized learning path!": "Hãy tải lên tài liệu học tập hoặc thảo luận với AI Tutor để nhận gợi ý lộ trình cá nhân hóa!",
      "Learning Path Analysis": "Phân tích lộ trình học tập",
      "Just updated": "Vừa cập nhật",
      "AI Tutor Tip": "Gợi ý từ AI Tutor",
      "Spend 15 minutes daily reviewing core concepts for long-term retention!": "Hãy dành 15 phút mỗi ngày để xem lại các khái niệm quan trọng giúp tăng khả năng ghi nhớ dài hạn!",
      "Review Now": "Xem lộ trình ngay",
      "Completed": "Đã hoàn thành",
      "Avg Progress": "Tiến độ TB",
      "Ready to continue your enlightened learning journey?": "Sẵn sàng tiếp tục hành trình học tập thông minh của bạn?",
      "Welcome back,": "Chào mừng bạn trở lại,",
      "Which parts have you understood?": "Bạn đã hiểu những phần nào?",
      "Mark the sections you already know so AI can focus on what you need to learn": "Đánh dấu những mục bạn đã biết để AI tập trung vào nội dung bạn cần học",
      "Submit and Generate Path": "Xác nhận và tạo lộ trình học",
      "Submit and Learn": "Xác nhận và tạo lộ trình học",
      "Skip (Learn All Concepts)": "Bỏ qua (Học tất cả các khái niệm)",
      "Skip, show everything": "Bỏ qua (Học tất cả các khái niệm)",
      "Calling AI Engine to design custom learning path steps...": "Đang gọi AI Engine để thiết kế các bước lộ trình học tập...",
      "AI is generating your learning path...": "AI đang khởi tạo lộ trình học tập của bạn...",
      "Learning path generated successfully!": "Tạo lộ trình học tập thành công!",
      "Uploaded Material": "Tài liệu đã tải lên",
      "Check if you already know this": "Tích chọn nếu bạn đã nắm rõ",
      "Loading material...": "Đang tải tài liệu...",
      "Loading concepts from AI Engine...": "Đang tải các khái niệm từ AI Engine...",
      "Analyzing document with AI...": "Đang phân tích tài liệu bằng AI...",
      "Sending document to AI Engine to extract concepts...": "Đang gửi tài liệu tới AI Engine để trích xuất khái niệm...",
      "Document created & concepts analyzed successfully!": "Tạo tài liệu & phân tích khái niệm thành công!",
      "Please select a document file or enter a learning topic.": "Vui lòng chọn một file tài liệu hoặc nhập chủ đề học tập.",
      "No documents uploaded yet.": "Chưa có tài liệu nào được tải lên.",
      "Failed to load document history.": "Không thể tải lịch sử tài liệu.",
      "AI API Limit Reached": "Đạt giới hạn gọi AI / Hết Quota",
      "AI System (OpenRouter) has reached the API rate limit or ran out of token quota. Please wait a few minutes and try again.": "Hệ thống AI (OpenRouter) hiện đã đạt giới hạn số lượt gọi API hoặc hết Quota token. Vui lòng chờ ít phút rồi thử lại.",
      "Got it": "Đã hiểu",
      "Are you sure you want to delete this course?": "Bạn có chắc chắn muốn xóa khóa học này?",
      "This action will remove all learning progress and AI materials. This cannot be undone.": "Thao tác này sẽ làm mất toàn bộ tiến trình học tập và dữ liệu bài giảng AI tương ứng. Bạn không thể hoàn tác sau khi xác nhận.",
      "Cancel": "Hủy bỏ",
      "Confirm Delete": "Xác nhận xóa"
    },
    ja: {
      "Lumina Learning": "TempName Learning",
      "TempName Learning": "TempName Learning",
      "Lumina AI": "TempName AI",
      "TempName AI": "TempName AI",
      "AI API Limit Reached": "AI API制限に達しました",
      "AI System (OpenRouter) has reached the API rate limit or ran out of token quota. Please wait a few minutes and try again.": "AIシステム（OpenRouter）がAPIレート制限に達したか、トークンQuotaが終了しました。しばらく待ってから再試行してください。",
      "Got it": "了解",
      "Are you sure you want to delete this course?": "このコースを削除してもよろしいですか？",
      "This action will remove all learning progress and AI materials. This cannot be undone.": "この操作により、すべての学習の進捗状況とAI教材が削除されます。この操作は取り消せません。",
      "Confirm Delete": "削除を確認",
      "Lịch Sử Chat": "チャット履歴",
      "Chat History": "チャット履歴",
      "Đoạn chat mới": "新しいチャット",
      "New Chat": "新しいチャット",
      "Các cuộc trò chuyện gần đây": "最近の会話",
      "Recent Conversations": "最近の会話",
      "Đang tải lịch sử chat...": "チャット履歴を読み込み中...",
      "Loading chat history...": "チャット履歴を読み込み中...",
      "Đang tải lịch sử...": "履歴を読み込み中...",
      "Loading history...": "履歴を読み込み中...",
      "Chưa có lịch sử đoạn chat nào.": "チャット履歴がありません。",
      "No chat history found.": "チャット履歴がありません。",
      "Không thể tải danh sách cuộc trò chuyện.": "会話一覧を取得できませんでした。",
      "Failed to load chat conversations.": "会話一覧を取得できませんでした。",
      "Không thể tạo hoặc tải chat thread từ server.": "サーバーからチャットを作成できませんでした。",
      "Unable to create or load chat thread từ server.": "サーバーからチャットを作成できませんでした。",
      "Lỗi kết nối backend AI Chat. Vui lòng thử lại.": "AIチャット接続エラーが発生しました。再試行してください。",
      "AI Chat connection error. Please try again.": "AIチャット接続エラーが発生しました。再試行してください。",
      "Không thể tải tin nhắn của đoạn chat này.": "このチャットのメッセージを取得できませんでした。",
      "Unable to load messages for this conversation.": "このチャットのメッセージを取得できませんでした。",
      "Không thể khởi tạo đoạn chat mới.": "新しいチャットを開始できませんでした。",
      "Unable to start a new chat.": "新しいチャットを開始できませんでした。",
      "TempName AI đang suy nghĩ...": "TempName AIが考え中...",
      "TempName AI is thinking...": "TempName AIが考え中...",
      "Lumina AI đang suy nghĩ...": "TempName AI가考え中...",
      "Đã xảy ra lỗi khi gửi tin nhắn.": "メッセージの送信中にエラーが発生しました。",
      "An error occurred while sending message.": "メッセージの送信中にエラーが発生しました。",
      "Đóng": "閉じる",
      "Close": "閉じる",
      "Nhập câu hỏi cho AI Tutor...": "AIチューターに質問を入力...",
      "Ask AI Tutor a question...": "AIチューターに質問を入力...",
      "Học cùng TempName AI Tutor": "TempName AIチューターと学ぶ",
      "Learn with TempName AI Tutor": "TempName AIチューターと学ぶ",
      "Học cùng Lumina AI Tutor": "TempName AIチューターと学ぶ",
      "Bạn có thể hỏi bất kỳ thắc mắc nào về bài học, khái niệm hoặc hỏi \"Tại sao bước này lại làm như vậy?\".": "レッスンや概念について質問したり、手順の理由を聞くことができます。",
      "You can ask any questions about lessons, concepts, or why a step was done this way.": "レッスンや概念について質問したり、手順の理由を聞くことができます。",
      "TempName AI can make mistakes. Verify important information.": "TempName AIは間違いを犯す可能性があります。重要な情報を確認してください。",
      "Upload study materials": "学習資料をアップロード",
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
      "Japanese (日本語)": "日本語",
      "Ready to continue your enlightened learning journey?": "賢い学習の旅を続ける準備はできていますか？",
      "Completed": "完了済み",
      "Avg Progress": "平均進捗",
      "No Active Courses Found": "アクティブなコースが見つかりません",
      "Upload a study material or topic to get started with your personalized AI learning journey!": "学習資料やトピックをアップロードして、パーソナライズされたAI学習を開始しましょう！",
      "Start New Course": "新しいコースを開始",
      "Language": "言語",
      "Intermediate": "中級",
      "Progress": "進捗",
      "Personalized Learning Path": "パーソナライズ学習ロードマップ",
      "Custom AI-designed step-by-step path based on your concept review.": "あなたの概念理解に基づいてAIが設計したステップバイステップの学習パス。",
      "Xóa khóa học": "コースを削除",
      "Delete Course": "コースを削除",
      "Loading your personalized learning steps...": "パーソナライズされた学習ステップを読み込み中...",
      "Module Progress": "モジュール進捗",
      "Accuracy": "正解率",
      "Remaining Steps": "残りのステップ",
      "Document": "ドキュメント",
      "optimize the learning path": "学習ロードマップの最適化",
      "Would you like to upload documents so the AI can design a more personalized and suitable learning path?": "AIがよりパーソナライズされた最適な学習パスを設計するためにドキュメントをアップロードしますか？",
      "Document history": "ドキュメント履歴",
      "Loading uploaded document history...": "アップロード済みドキュメントの履歴を読み込み中...",
      "click or drag to upload file": "クリックまたはドラッグ＆ドロップでファイルをアップロード",
      "PDF, Word, PowerPoint, TXT (maximum 10MB)": "PDF, Word, PowerPoint, TXT（最大10MB）",
      "Learning Goal / Topic (Optional)": "学習目標 / トピック（任意）",
      "e.g. Embedded Systems Firmware Architecture": "例：組み込みシステムファームウェアアーキテクチャ",
      "upload and analyze": "アップロードして分析",
      "Manage your account preferences and application settings.": "アカウント設定およびアプリケーション設定を管理します。",
      "Last changed 3 months ago": "3ヶ月前に変更済み",
      "Update": "更新",
      "Manage connections for quick login": "クイックログインのための連携を管理",
      "Manage": "管理",
      "Add an extra layer of security to your account": "アカウントに追加のセキュリティ層を設定",
      "Study Reminders": "学習リマインダー",
      "In-app & push alerts": "アプリ内＆プッシュ通知",
      "New Lesson Updates": "新しいレッスン更新",
      "AI Tutor course additions": "AIチューターコースの追加",
      "Email Digest": "メールダイジェスト",
      "Weekly progress reports": "週次進捗レポート",
      "Edit Profile": "プロフィール編集",
      "Display Name": "表示名",
      "Email Address": "メールアドレス",
      "Cancel": "キャンセル",
      "Save Changes": "変更を保存",
      "Xin chào! Bạn muốn học về chủ đề gì hôm nay?": "こんにちは！今日はどんなトピックについて学びたいですか？",
      "Hãy trò chuyện với AI Tutor về chủ đề hoặc mục tiêu học tập của bạn, hoặc tải ngay tài liệu bài học lên để AI phân tích và tạo lộ trình cá nhân hóa!": "学習トピックや目標についてAIチューターとチャットするか、資料を直接アップロードしてAIに分析・カスタムロードマップ作成を依頼しましょう！",
      "Upload tài liệu ngay": "今すぐ資料をアップロード",
      "Trò chuyện về chủ đề": "トピックについてチャット",
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
      "TempName Learning - AI Tutor": "TempName Learning - Gia sư AI",
      "TempName Learning - Login": "TempName Learning - Đăng nhập",
      "TempName Learning - Student Dashboard": "TempName Learning - Bảng điều khiển",
      "Optimize Learning Path - Document Upload": "Tối ưu lộ trình học - Tải tài liệu",
      "TempName Learning - Review Document": "TempName Learning - Xem lại tài liệu",
      "TempName Learning - Learning Path": "TempName Learning - Lộ trình học",
      "TempName Learning - Linear Regression": "TempName Learning - Hồi quy tuyến tính",
      "TempName AI - AI Tutor Chat": "TempName AI - Chat gia sư AI",
      "Settings - TempName AI": "Cài đặt - TempName AI",
      "Course History - TempName AI": "Lịch sử khóa học - TempName AI",
      "TempName Learning - Concept Test": "TempName Learning - Bài kiểm tra khái niệm",
      "TempName Learning - Final Test Result": "TempName Learning - Kết quả bài kiểm tra cuối",
      "AI Tutor Conversation": "Cuộc trò chuyện với AI Tutor"
    },
    ja: {
      "TempName Learning - AI Tutor": "TempName Learning - AIチューター",
      "TempName Learning - Login": "TempName Learning - ログイン",
      "TempName Learning - Student Dashboard": "TempName Learning - ダッシュボード",
      "Optimize Learning Path - Document Upload": "学習パスを最適化 - 資料アップロード",
      "TempName Learning - Review Document": "TempName Learning - 資料レビュー",
      "TempName Learning - Learning Path": "TempName Learning - 学習パス",
      "TempName Learning - Linear Regression": "TempName Learning - 線形回帰",
      "TempName AI - AI Tutor Chat": "TempName AI - AIチューターチャット",
      "Settings - TempName AI": "設定 - TempName AI",
      "Course History - TempName AI": "コース履歴 - TempName AI",
      "TempName Learning - Concept Test": "TempName Learning - 概念テスト",
      "TempName Learning - Final Test Result": "TempName Learning - 最終テスト結果",
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
      if (element.dataset.themeOption || element.dataset.noNav === "true" || element.closest("#edit-profile-modal") || element.id === "edit-profile-btn" || element.id === "close-modal-btn" || element.id === "toggle-mode-btn" || element.id === "toggle-password" || element.id === "submit-btn" || element.type === "submit") {
        return;
      }
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

    let destination = target;
    if (target === ROUTES.newCourse && !target.includes("?")) {
      const urlParams = new URLSearchParams(window.location.search);
      const matId = urlParams.get("material_id") || window.API?.storage?.getLastMaterialId();
      const goalId = urlParams.get("goal_id");
      const conceptId = urlParams.get("concept_id");
      const lessonId = urlParams.get("lesson_id") || urlParams.get("step_id");

      const params = new URLSearchParams();
      if (goalId) params.set("goal_id", goalId);
      if (matId) params.set("material_id", matId);
      if (conceptId) params.set("concept_id", conceptId);
      if (lessonId) params.set("lesson_id", lessonId);

      const queryString = params.toString();
      if (queryString) {
        destination = `${target}?${queryString}`;
      }
    }

    const body = document.body;
    if (!body) {
      window.location.href = destination;
      return;
    }

    if (body.dataset.transitioning === "true") return;
    body.dataset.transitioning = "true";
    body.classList.remove("lumina-page-enter");
    body.classList.add("lumina-page-exit");

    window.setTimeout(() => {
      window.location.href = destination;
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
    { match: /tempname learning|tempname ai|lumina learning|lumina ai/i, target: currentPage === ROUTES.landing ? ROUTES.landing : ROUTES.dashboard },
    { match: /dashboard|bảng điều khiển|trang chủ|ダッシュボード/i, target: ROUTES.dashboard },
    { match: /my courses|courses|khóa học|khóa học của tôi|マイコース|コース/i, target: ROUTES.courses },
    { match: /ai tutor|gia sư ai|aiチューター/i, target: ROUTES.newCourse },
    { match: /settings|cài đặt|người dùng|thiết lập|設定/i, target: ROUTES.settings },
    { match: /history|lịch sử|nhật ký|履歴/i, target: ROUTES.history },
    { match: /help center|help|trợ giúp/i, target: ROUTES.dashboard },
    { match: /logout|đăng xuất|ログアウト/i, target: ROUTES.landing }
  ];

  const pageRules = {
    [ROUTES.landing]: [
      { match: /login/i, target: ROUTES.login },
      { match: /get started/i, target: ROUTES.login },
      { match: /start learning free/i, target: ROUTES.login }
    ],
    [ROUTES.login]: [
      { match: /google/i, target: ROUTES.dashboard },
      { match: /apple/i, target: ROUTES.dashboard }
    ],
    [ROUTES.dashboard]: [
      { match: /new study session|start new course|add new course|buổi học mới|bắt đầu khóa học mới/i, target: ROUTES.newCourse },
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

    // Translate input & textarea placeholders
    const inputs = document.querySelectorAll("input[placeholder], textarea[placeholder]");
    inputs.forEach((el) => {
      if (!el.__luminaOriginalPlaceholder) {
        el.__luminaOriginalPlaceholder = el.placeholder;
      }
      const source = el.__luminaOriginalPlaceholder;
      const normalized = source.replace(/\s+/g, " ").trim();
      const translated = map[normalized];
      el.placeholder = translated ? source.replace(normalized, translated) : source;
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
      button.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        applyTheme(button.dataset.themeOption);
      });
    });

    const languageSelect = document.querySelector("#language-select");
    if (languageSelect && languageSelect.dataset.boundLanguage !== "true") {
      languageSelect.dataset.boundLanguage = "true";
      languageSelect.addEventListener("change", (e) => {
        applyLanguage(languageSelect.value);
      });
    }
  }

  function updateUserProfileUI(user) {
    if (!user) return;
    const displayName = user.display_name || user.username || "Learner";
    const email = user.email || `${user.username || "user"}@example.com`;
    const usernameHandle = `@${user.username || "user"}`;
    const initials = (displayName.split(" ").map((n) => n[0]).join("") || "U").toUpperCase().slice(0, 2);

    const nameEls = document.querySelectorAll("#sidebar-user-name, #settings-profile-name, [data-user-display-name]");
    nameEls.forEach((el) => {
      el.textContent = displayName;
      el.title = displayName;
    });

    const emailEls = document.querySelectorAll("#sidebar-user-email, #settings-profile-email, [data-user-email]");
    emailEls.forEach((el) => {
      el.textContent = email;
      el.title = email;
    });

    const handleEls = document.querySelectorAll("#settings-profile-handle, [data-user-handle]");
    handleEls.forEach((el) => {
      el.textContent = usernameHandle;
      el.title = usernameHandle;
    });

    const initialEls = document.querySelectorAll("[data-user-initials]");
    initialEls.forEach((el) => { el.textContent = initials; });
  }

  async function initAuthAndSessionGuard() {
    // Bind all logout triggers across the page
    const logoutElements = document.querySelectorAll("#logout-btn, [data-action='logout'], a[href*='logout']");
    logoutElements.forEach((el) => {
      if (el.dataset.boundLogout === "true") return;
      el.dataset.boundLogout = "true";
      el.addEventListener("click", async (e) => {
        e.preventDefault();
        if (window.API?.auth?.logout) {
          await window.API.auth.logout();
        }
      });
    });

    const publicPages = [ROUTES.landing, ROUTES.login];
    const isPublicPage = publicPages.includes(currentPage);

    if (!window.API?.auth?.me) return;

    const cachedUser = window.API?.storage?.getUser();
    if (cachedUser) {
      updateUserProfileUI(cachedUser);
    }

    try {
      const user = await window.API.auth.me();
      if (user) {
        updateUserProfileUI(user);

        if (currentPage === ROUTES.login) {
          window.location.href = ROUTES.dashboard;
        }
      } else {
        if (!isPublicPage) {
          window.location.href = ROUTES.login;
        }
      }
    } catch (err) {
      if (!isPublicPage) {
        window.location.href = ROUTES.login;
      }
    }
  }

  function bindNavigation() {
    applyRules(sharedRules, "a, button");
    const rules = pageRules[currentPage] || [];
    applyRules(rules, "a, button");
  }

  bindNavigation();
  applyTheme(getTheme());
  applyLanguage(getLanguage());
  bindSettingsControls();
  initAuthAndSessionGuard();

  window.LuminaNav = {
    applyLanguage,
    getLanguage,
    translatePage: () => translateTextNodes(getLanguage())
  };

  window.requestAnimationFrame(() => {
    document.body?.classList.add("lumina-page-enter");
  });
})();
