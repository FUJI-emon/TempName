# AIとともに学習するクイズアプリ (AI-assisted Adaptive Learning Quiz App)

「単にAIが問題を自動生成して答えを教える」アプリではなく、**「生徒が、先生が望む成果（学習目標）を出せるようになること」**を目的とした段階的・適応型の学習支援プラットフォームです。

Duolingoのようなプログレッシブ学習モデルを参考にしつつ、答えをすぐに提示するのではなく、生徒の思考プロセスと本質的な理解を促すヒント提供メカニズムを提供します。

---

## 🛠 テクノロジースタック

- **言語**: Python 3.12+
- **フレームワーク**: Django 5.2+
- **データベース**: SQLite3（開発初期。将来的にPostgreSQLへ移行可能な設計）
- **フロントエンド**: Django Templates, HTML5, CSS3 (CSS Variables, Flexbox/Grid), JavaScript (ES6+)
- **環境設定**: `python-dotenv`

---

## 📁 プロジェクト構造 (Phase 1)

初学者にもわかりやすく、将来の拡張に耐えうるように **`config/`（全体設定）** と **`apps/`（ドメインアプリケーション）** を分離したディレクトリ設計を採用しています。

```text
ai_learning/
├── manage.py                # Django管理コマンドスクリプト
├── requirements.txt         # 依存ライブラリ一覧
├── .env.example             # 環境変数設定サンプル
├── .gitignore               # Git除外設定
├── README.md                # 本プロジェクトドキュメント
├── config/                  # プロジェクト全体設定パッケージ
│   ├── __init__.py
│   ├── settings.py          # Django設定（アプリ登録、DB、静的ファイル等）
│   ├── urls.py              # ルートURLルーティング
│   ├── asgi.py              # 非同期Webサーバーインターフェース
│   └── wsgi.py              # 同期Webサーバーインターフェース
├── apps/                    # 機能別アプリケーション格納ディレクトリ
│   └── learning/            # 学習コンテンツ管理アプリ (Phase 1)
│       ├── __init__.py
│       ├── admin.py          # Django Admin設定（教材・学習目標の管理）
│       ├── apps.py           # アプリケーション設定情報 (`apps.learning`)
│       ├── models.py         # LearningMaterial, LearningGoal モデル定義
│       ├── urls.py           # アプリ個別のURLルーティング
│       ├── views.py          # リクエスト処理ビュー（index表示）
│       ├── tests.py          # 自動ユニットテスト
│       └── migrations/       # DBマイグレーションファイル
├── templates/               # グローバルHTMLテンプレート
│   ├── base.html            # 共通親テンプレート（ヘッダー・フッター・スタイル）
│   └── learning/
│       └── index.html       # ホームページ・教材一覧表示
├── static/                  # 静的ファイル (CSS / JS / 画像)
│   ├── css/
│   │   └── style.css        # モダンデザインスタイルシート
│   └── js/
│       └── main.js          # フロントエンドJS処理
└── media/                   # ユーザーアップロードファイル用ディレクトリ
```

---

## 🚀 起動・開発手順

### 1. 仮想環境の作成と有効化

```bash
# 仮想環境を作成
python -m venv .venv

# 仮想環境を有効化 (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# (macOS / Linux の場合)
# source .venv/bin/activate
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定 (任意)

`.env.example` をコピーして `.env` を作成します。

```bash
cp .env.example .env
```

### 4. マイグレーションの実行

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. ユニットテストの実行

```bash
python manage.py test
```

### 6. 管理者アカウントの作成 (Django Admin用)

```bash
python manage.py createsuperuser
```

### 7. 開発サーバーの起動

```bash
python manage.py runserver 8000
```

ブラウザで `http://127.0.0.1:8000/` にアクセスしてください。  
管理画面は `http://127.0.0.1:8000/admin/` で確認できます。

---

## 📌 概念設計と段階的拡張計画

### 1. 現在のスコープ (Phase 1)
- Django の基本 MVT (Model-View-Template) パターンの学習と確立。
- `LearningMaterial`（学習教材・課題）と `LearningGoal`（学習目標）のデータモデル定義。
- Django Admin によるデータ登録・編集機能。
- テンプレート継承 (`base.html`) と静的ファイル管理 (`static/`) の基礎。

### 2. 今後追加予定のアプリケーション (Phase 2〜)

`apps/` ディレクトリ配下に、以下の役割別に分割したアプリを順次作成します。

- **`apps/users/`**: ユーザー登録・ログイン・生徒/先生権限管理
- **`apps/assessment/`**: 診断テスト・理解度評価機能
- **`apps/quiz/`**: クイズ・問題演習・ヒント生成表示機能
- **`apps/progress/`**: スキルプロファイル・進捗度・間隔反復メタデータ管理
- **`apps/ai/`**: Prompt管理・AI連携サービスレイヤー

### 3. AIサービスレイヤーの設計思想

Django のビジネスロジックやビューに AI 依存コードを直接記述せず、以下のような疎結合アーキテクチャを採用します。

```text
Django Views / Business Logic
            │
            ▼
   apps/ai/services/ (LLMService インターフェース)
            │
            ▼
   apps/ai/adapters/ (OpenRouterAdapter / GeminiAdapter)
            │
            ▼
     外部 AI API (OpenRouter / Google Gemini)
```

これにより、将来 AI プロバイダーを変更・追加する場合でも、アダプターを差し替えるだけで既存の学習ロジックに影響を与えない設計となっています。
