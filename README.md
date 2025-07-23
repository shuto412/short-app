# URL動画台本生成システム

URLから自動的にコンテンツを取得し、AI（Claude）を活用して動画台本を生成、音声と字幕ファイルを作成するシステムです。

## 🎯 システム概要

- **URL入力**: ウェブページのURLを入力
- **コンテンツ取得**: 自動でページ内容をスクレイピング
- **AI要約**: Claude APIでコンテンツを要約
- **台本生成**: シナリオテンプレートに基づいて動画台本を生成
- **音声生成**: Nijivoice APIで高品質な音声ファイルを作成
- **字幕生成**: SRT/VTT形式の字幕ファイルを自動生成

## 🛠️ 技術スタック

### バックエンド
- **Python 3.9+** + FastAPI
- **AI**: Claude API (Anthropic)
- **音声生成**: Nijivoice API
- **スクレイピング**: BeautifulSoup + Selenium

### フロントエンド
- **React 18** + TypeScript
- **Material-UI v7**
- **状態管理**: React Query (TanStack Query)

## 📋 前提条件

- Python 3.9以上
- Node.js 16以上
- Chrome/Chromium (Selenium用)

## 🚀 セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd url-video-script-generator
```

### 2. バックエンドのセットアップ

```bash
# バックエンドディレクトリに移動
cd backend

# Python仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

#### 環境変数設定 (.env)

```bash
# APIキー (必須)
CLAUDE_API_KEY=your_claude_api_key_here
NIJIVOICE_API_KEY=your_nijivoice_api_key_here

# サーバー設定
BACKEND_PORT=8080
DATA_DIR=../DATA

# ファイル設定
MAX_FILE_SIZE=100MB

# レート制限
CLAUDE_RPM=50
NIJIVOICE_RPM=100
```

### 3. フロントエンドのセットアップ

```bash
# フロントエンドディレクトリに移動
cd ../frontend

# 依存関係のインストール
npm install

# 開発用ビルド（確認）
npm run build
```

## 🎮 起動コマンド

### 開発環境での起動

#### バックエンド起動

```bash
# バックエンドディレクトリで実行
cd backend
source venv/bin/activate  # 仮想環境有効化
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

起動確認: http://localhost:8080 でAPIドキュメントが表示されます

#### フロントエンド起動

```bash
# フロントエンドディレクトリで実行（新しいターミナル）
cd frontend
npm start
```

起動確認: http://localhost:3000 でアプリケーションが表示されます

### 本番環境での起動

#### バックエンド（本番）

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

#### フロントエンド（本番）

```bash
cd frontend
npm run build
npm install -g serve
serve -s build -l 3000
```

## 📝 使用方法

### 1. 基本的な使用フロー

1. **URL入力**: 動画にしたいコンテンツのURLを入力
2. **シナリオ選択**: 生成したい動画のタイプを選択
   - 製品紹介 (60-90秒)
   - チュートリアル (2-5分)
   - 機能説明 (1-3分)
3. **処理開始**: 自動でコンテンツ処理が開始
4. **結果確認**: 生成されたファイルをダウンロード

### 2. 生成されるファイル

- **台本ファイル (YAML)**: 動画制作ソフトで使用
- **音声ファイル (WAV)**: 高品質な音声データ
- **字幕ファイル (SRT)**: 動画プレイヤーで表示可能
- **要約ファイル (TXT)**: 元コンテンツの要約

### 3. 対応サイト

- 一般的なウェブページ
- ブログ記事
- 製品ページ
- ドキュメントサイト
- ニュース記事

## 🏗️ プロジェクト構造

```
url-video-script-generator/
├── frontend/                    # Reactフロントエンド
│   ├── public/
│   ├── src/
│   │   ├── components/         # UIコンポーネント
│   │   ├── services/           # API通信
│   │   ├── App.tsx            # メインアプリ
│   │   └── index.tsx
│   ├── package.json
│   └── tsconfig.json
├── backend/                     # Pythonバックエンド
│   ├── app/
│   │   ├── main.py            # FastAPIメイン
│   │   ├── config.py          # 設定
│   │   ├── models/            # データモデル
│   │   ├── modules/           # 機能モジュール
│   │   ├── api/               # APIエンドポイント
│   │   └── templates/         # シナリオテンプレート
│   ├── requirements.txt
│   └── .env
├── DATA/                        # 生成データ保存先
└── README.md
```

## 🔧 トラブルシューティング

### よくある問題

#### バックエンドが起動しない

```bash
# ポートが使用されている場合
lsof -ti:8080 | xargs kill -9

# 仮想環境の再作成
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### フロントエンドがビルドできない

```bash
# node_modulesの再インストール
rm -rf node_modules package-lock.json
npm install

# キャッシュクリア
npm start -- --reset-cache
```

#### APIキーエラー

1. `.env`ファイルの存在確認
2. APIキーの有効性確認
3. レート制限の確認

### Chrome/Seleniumの問題

```bash
# Chromeドライバーの更新
pip install --upgrade selenium
```

### ログの確認

```bash
# バックエンドログ
tail -f backend/logs/app.log

# フロントエンドログ
# ブラウザの開発者ツール > Console
```

## 🧪 テスト実行

### バックエンドテスト

```bash
cd backend
python -m pytest tests/
```

### フロントエンドテスト

```bash
cd frontend
npm test
```

### 統合テスト

```bash
# バックエンド起動後
cd frontend
npm run test:integration
```

## 📚 API仕様

### 主要エンドポイント

- `POST /api/projects` - プロジェクト作成
- `GET /api/projects/{id}` - プロジェクト情報取得
- `GET /api/projects/{id}/status` - 処理状況取得
- `GET /api/generate/scenarios` - シナリオ一覧
- `POST /api/generate/process` - 処理開始
- `GET /api/generate/download/{id}/{type}` - ファイルダウンロード

詳細な仕様: http://localhost:8080/docs

## 🔒 セキュリティ

- APIキーは環境変数で管理
- CORS設定でアクセス制御
- ファイルサイズ制限
- レート制限

## 📄 ライセンス

MIT License

## 🤝 貢献

1. Forkしてください
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

問題がある場合は、以下を確認してください：

1. [トラブルシューティング](#-トラブルシューティング)
2. [Issues](https://github.com/your-repo/issues)
3. [Discussions](https://github.com/your-repo/discussions)

---

## 🚀 クイックスタート

```bash
# 1. バックエンド起動
cd url-video-script-generator/backend && source venv/bin/activate && uvicorn app.main:app --reload

# 2. フロントエンド起動（新しいターミナル）
cd url-video-script-generator/frontend && npm start

# 3. ブラウザでアクセス
open http://localhost:3000
```

**🎉 これで URL動画台本生成システムが利用可能です！** 