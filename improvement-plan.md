# URL動画台本生成システム改良計画書

## 1. 改良概要

### 1.1 改良目的
- スクレイピング情報の不足に対する解決策として、MDファイルからの台本生成ルートを追加
- より豊富で質の高いコンテンツから台本生成を可能にする
- 既存のURL入力フローを維持しつつ、新たな入力方式を提供

### 1.2 改良後のワークフロー
```
情報選択画面
├── サイトから → URL入力 → スクレイピング → AI要約 → 構造化要約 → 台本生成 → 音声設定 → 音声生成 → 字幕生成 → 完了
└── .mdファイルから → .mdファイルアップロード → 構造化要約 → 台本生成 → 音声設定 → 音声生成 → 字幕生成 → 完了
```

## 2. 影響範囲分析

### 2.1 フロントエンド（React）影響範囲

#### 2.1.1 新規コンポーネント
- **InformationSourceSelector**: 情報源選択画面
- **MarkdownUploader**: MDファイルアップロード画面
- **MarkdownPreview**: アップロードしたMDファイルのプレビュー表示

#### 2.1.2 既存コンポーネント修正
- **App.tsx**: 
  - `AppState`に`information-source-selection`と`markdown-upload`を追加
  - ワークフロー分岐ロジックの実装
  - 状態管理の追加（`inputSource`, `markdownContent`）
- **types/index.ts**:
  - 新しい型定義の追加（`InputSource`, `MarkdownData`等）

#### 2.1.3 API通信修正
- **services/api.ts**:
  - `markdownAPI`の追加
  - プロジェクト作成APIの拡張（入力ソース情報を含む）

### 2.2 バックエンド（FastAPI）影響範囲

#### 2.2.1 新規モジュール
- **modules/markdown_processor.py**: MDファイル処理専用モジュール
- **api/markdown.py**: MDファイル関連のAPIエンドポイント

#### 2.2.2 既存モジュール修正
- **models/project.py**:
  - `input_source`フィールドの追加
  - `markdown_content`フィールドの追加
- **api/project.py**:
  - プロジェクト作成ロジックの分岐対応
- **api/generation.py**:
  - 処理フローの分岐対応
- **modules/file_manager.py**:
  - MDファイル保存・読み込み機能の追加

## 3. 詳細設計

### 3.1 データモデル設計

#### 3.1.1 プロジェクトモデル拡張
```python
class Project(BaseModel):
    id: str
    url: Optional[str] = None  # URLソースの場合のみ
    title: Optional[str]
    input_source: str = "url"  # "url" | "markdown"
    markdown_filename: Optional[str] = None  # MDソースの場合のファイル名
    scenario_type: str
    status: str
    created_at: datetime
    updated_at: datetime
```

#### 3.1.2 フロントエンド型定義
```typescript
export type InputSource = 'url' | 'markdown';

export interface ProjectCreate {
  input_source: InputSource;
  url?: string;
  markdown_content?: string;
  markdown_filename?: string;
  scenario_type: string;
  options?: Record<string, any>;
}

export interface MarkdownData {
  filename: string;
  content: string;
  size: number;
  lastModified: number;
}
```

### 3.2 APIエンドポイント設計

#### 3.2.1 既存エンドポイント修正
```python
# api/project.py
@router.post("/")
async def create_project(project: ProjectCreate):
    """プロジェクト作成（入力ソース対応）"""
    # input_sourceに基づいて処理を分岐
    
# api/generation.py  
@router.post("/process")
async def process_full(project_id: str, ...):
    """フル処理実行（入力ソース対応）"""
    # プロジェクトの入力ソースを確認して処理を分岐
```

#### 3.2.2 新規エンドポイント
```python
# api/markdown.py
@router.post("/validate")
async def validate_markdown(file: UploadFile):
    """MDファイルバリデーション"""
    
@router.post("/preview")  
async def preview_markdown(file: UploadFile):
    """MDファイルプレビュー"""
```

### 3.3 フロントエンド画面設計

#### 3.3.1 情報源選択画面（InformationSourceSelector）
```typescript
interface InformationSourceSelectorProps {
  onSelect: (source: InputSource) => void;
  isLoading?: boolean;
}

// 機能:
// - サイトから/MDファイルからの選択
// - 各選択肢の説明表示
// - 視覚的に分かりやすいカード形式のUI
```

#### 3.3.2 MDファイルアップロード画面（MarkdownUploader）
```typescript
interface MarkdownUploaderProps {
  onUpload: (markdownData: MarkdownData) => void;
  onNext: (projectId: string) => void;
  onBack: () => void;
  isLoading?: boolean;
  error?: string;
}

// 機能:
// - ドラッグ&ドロップ対応
// - ファイル形式バリデーション（.md, .markdown）
// - ファイルサイズ制限チェック
// - プレビュー表示
// - プロジェクト自動作成
```

## 4. 実装計画

### 4.1 Phase 1: バックエンド基盤実装（1週間）

#### 4.1.1 Day 1-2: データモデル拡張
- [ ] `models/project.py`の`input_source`フィールド追加
- [ ] `ProjectCreate`モデルの拡張
- [ ] データベーススキーマ更新（必要に応じて）

#### 4.1.2 Day 3-4: MDファイル処理モジュール
- [ ] `modules/markdown_processor.py`作成
  ```python
  class MarkdownProcessor:
      async def validate_markdown(self, content: str) -> bool
      async def extract_metadata(self, content: str) -> Dict
      async def process_content(self, content: str) -> str
      def estimate_content_quality(self, content: str) -> float
  ```

#### 4.1.3 Day 5-7: API拡張
- [ ] `api/markdown.py`作成
- [ ] `api/project.py`のプロジェクト作成ロジック分岐対応
- [ ] `api/generation.py`の処理フロー分岐対応

### 4.2 Phase 2: フロントエンド基盤実装（1週間）

#### 4.2.1 Day 1-2: 型定義と状態管理
- [ ] `types/index.ts`に新しい型定義追加
- [ ] `App.tsx`の状態管理拡張

#### 4.2.2 Day 3-5: 新規コンポーネント
- [ ] `InformationSourceSelector`コンポーネント
- [ ] `MarkdownUploader`コンポーネント
- [ ] `MarkdownPreview`コンポーネント

#### 4.2.3 Day 6-7: API通信とフロー統合
- [ ] `services/api.ts`にMD関連API追加
- [ ] `App.tsx`のワークフロー統合

### 4.3 Phase 3: 統合テスト・調整（3日間）

#### 4.3.1 Day 1: 単体テスト
- [ ] MDファイル処理の各機能テスト
- [ ] API エンドポイントテスト
- [ ] フロントエンドコンポーネントテスト

#### 4.3.2 Day 2: 統合テスト
- [ ] URL→MD両フローの動作確認
- [ ] エラーハンドリングテスト
- [ ] ファイルアップロード・処理テスト

#### 4.3.3 Day 3: UI/UX調整
- [ ] レスポンシブデザイン調整
- [ ] エラーメッセージ・ガイダンス改善
- [ ] パフォーマンス最適化

## 5. 技術仕様

### 5.1 MDファイル処理仕様

#### 5.1.1 サポートファイル形式
- `.md`, `.markdown`拡張子
- UTF-8エンコーディング
- 最大ファイルサイズ: 10MB

#### 5.1.2 メタデータ抽出
```markdown
---
title: "製品タイトル"
description: "製品説明"
category: "製品カテゴリ"
tags: ["tag1", "tag2"]
---

# メインコンテンツ
...
```

#### 5.1.3 コンテンツ品質評価
- 文字数（最低500文字推奨）
- 構造化度（見出しの使用状況）
- メタデータの充実度
- 品質スコア算出（0-100）

### 5.2 セキュリティ考慮事項

#### 5.2.1 ファイルアップロード
- ファイル形式厳格チェック
- ウイルススキャン（将来実装）
- アップロードサイズ制限
- 一時ファイルの自動削除

#### 5.2.2 入力データ検証
- MDコンテンツのサニタイゼーション
- XSS攻撃対策
- インジェクション攻撃対策

## 6. 期待効果

### 6.1 機能面の改善
- **情報の質向上**: 事前準備されたMDファイルにより、より詳細で構造化された情報から台本生成
- **処理成功率向上**: スクレイピング失敗リスクの回避
- **カスタマイズ性向上**: ユーザーが情報を事前に整理・編集可能

### 6.2 ユーザビリティ改善
- **選択の自由度**: 状況に応じた最適な入力方法選択
- **処理時間短縮**: スクレイピング工程のスキップによる高速化
- **成功率向上**: 情報不足による失敗の回避
- **ファイル管理の簡素化**: ブラウザから直接MDフォルダにアクセス
- **プレビュー機能**: ファイル選択前の内容確認が可能

### 6.3 システム安定性向上
- **外部依存削減**: スクレイピング対象サイトの制約回避
- **エラー要因削減**: ネットワーク問題・サイト構造変更の影響回避
- **処理品質向上**: より予測可能な入力データによる安定した出力

## 7. リスク分析と対策

### 7.1 技術的リスク
| リスク | 影響度 | 発生確率 | 対策 |
|-------|-------|---------|------|
| MDファイル解析失敗 | 中 | 低 | 詳細なバリデーション実装 |
| ファイルアップロード不具合 | 高 | 中 | 段階的テスト・エラーハンドリング強化 |
| 既存フロー影響 | 高 | 低 | 既存コード影響最小化・十分なテスト |

### 7.2 運用リスク
| リスク | 影響度 | 発生確率 | 対策 |
|-------|-------|---------|------|
| ユーザー混乱 | 中 | 中 | 明確なUI・ガイダンス提供 |
| ファイル容量問題 | 中 | 中 | 適切なサイズ制限・定期清掃 |
| 不正ファイル投稿 | 高 | 低 | 厳格なバリデーション・監視 |

## 8. 成功指標（KPI）

### 8.1 機能指標
- MDファイルからの台本生成成功率: 95%以上
- 処理時間（MDルート）: 平均30秒以内
- ファイルアップロード成功率: 98%以上

### 8.2 品質指標  
- システムエラー発生率: 2%以下
- ユーザー操作エラー率: 5%以下
- 生成された台本の品質スコア: 平均80点以上

### 8.3 ユーザビリティ指標
- 情報源選択画面の完了率: 95%以上
- MDアップロード完了率: 90%以上
- ユーザーサポート問い合わせ増加率: 10%以下

## 9. 今後の拡張計画

### 9.1 短期拡張（3ヶ月以内）
- テキストファイル（.txt）対応
- PDFファイル対応
- 複数ファイル同時アップロード

### 9.2 中期拡張（6ヶ月以内）
- MDファイルのリアルタイムプレビュー編集
- テンプレートMDファイル提供
- ファイル履歴管理機能

### 9.3 長期拡張（1年以内）
- Googleドライブ・Dropbox連携
- MDファイル自動品質改善提案
- 協業編集機能

## 10. まとめ

本改良により、URL動画台本生成システムはより柔軟で信頼性の高いシステムに進化します。既存のURL入力フローを維持しつつ、MDファイルからの高品質な台本生成ルートを追加することで、ユーザーのニーズに幅広く対応し、システムの実用性と成功率を大幅に向上させることができます。

段階的な実装により、リスクを最小限に抑えながら確実に機能拡張を実現し、将来的なさらなる機能拡張への基盤も整備されます。