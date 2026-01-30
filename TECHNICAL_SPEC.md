# ChainFlowFiler Technical Specification & Design Philosophy

## 1. 設計思想 (Design Philosophy)

**ChainFlowFiler** は、既存のエクスプローラーや一般的な2画面ファイラの限界を超えるために設計された、パワーユーザー向けのファイル管理ツールです。

### 1.1. Chain Flow Concept (連鎖的フロー)
Miller Columns (カラム表示) の「階層を深く潜る」利便性と、複数ウィンドウを開いて作業する「並列性」を融合させました。
*   **Flow Lane (横軸)**: 1つのタスクや思考の流れを表すファイルパスの連鎖（親→子→孫）。
*   **Multi-Lane (縦軸)**: 複数の異なるタスク（例: 左側で素材探し、右側で成果物保存）を同時に並列表示し、ドラッグ＆ドロップで連携可能にします。
*   **Flexible Layout**: ユーザーの思考に合わせて、ペイン（枠）を自由に追加・分割・リサイズできます。

### 1.2. Keyboard Centric & Efficiency (操作効率)
*   **Mouse-less Option**: ほぼ全ての操作（移動、選択、コピー、リネーム、プレビュー、ペイン追加/削除）をキーボードショートカットで完結可能に設計しています。
*   **Vim-like / WASD**: ゲーマーやエンジニアに馴染みのあるキーバインド（WASD, Vim風移動）を一部採用し、直感的な操作を実現。

### 1.3. Visual Immersion (没入感)
*   **Dark Theme**: 長時間の作業でも目が疲れないダークモードを標準採用。VSCodeライクな配色で、エンジニアにとっての「いつもの場所」のような安心感を提供します。
*   **Custom UI Components**: OS標準の無機質なスクロールバー等を排除し、視認性とデザイン性を両立させたカスタムコンポーネント（Accent Rounded Scrollbarなど）を使用。

### 1.4. Portability (完全な可搬性)
*   **No Registry**: Windowsレジストリを使用せず、設定ファイル（JSON）は全て実行ファイルと同階層に保存されます。
*   **Single Binary**: PyInstallerにより単一のEXEファイルとして提供され、USBメモリに入れて持ち運ぶだけで、どのPCでも同じ環境を再現できます。

---

## 2. 技術スタック (Technology Stack)

*   **Core Language**: Python 3.11+
    *   開発効率とライブラリの豊富さを重視。
*   **GUI Framework**: PySide6 (Qt for Python 6.x)
    *   高速なレンダリング、強力なウィジェットシステム、クロスプラットフォーム性（将来的なMac/Linux対応も視野）のため採用。
    *   `QFileSystemModel` によるOSネイティブファイルシステムの非同期監視能力を活用。
*   **Build Tool**: PyInstaller
    *   `--onefile` モードにより依存関係を全て1つにパッケージング。
    *   実行時に一時リソース (`sys._MEIPASS`) を展開する仕組みを利用。

---

## 3. アーキテクチャ概要 (Architecture Overview)

アプリケーションはコンポーネント指向で構築されており、親から子への明確な所有権構造を持っています。

### 3.1. 階層構造 (Component Hierarchy)

```mermaid
graph TD
    App[Main Window (ChainFlowFiler)] --> Nav[Navigation Pane (Left Sidebar)]
    App --> Tabs[QTabWidget]
    
    Tabs --> Area[Flow Aera (Tab Content)]
    Area --> VSplit[Vertical Splitter]
    
    VSplit --> Lane[Flow Lane (Horizontal Container)]
    Lane --> HSplit[Horizontal Splitter]
    
    HSplit --> Pane[File Pane]
    
    Pane --> Header[Header / Search Bar]
    Pane --> View[QTreeView]
    Pane --> Proxy[SmartSortFilterProxyModel]
    Proxy --> FSModel[QFileSystemModel]
```

### 3.2. 主要コンポーネントの役割

#### **Main Window (`widgets/main_window.py`)**
*   **Application Root**: アプリ全体のライフサイクル管理。
*   **Session Management**: `closeEvent` でウィンドウ状態や開いているパスを `session.json` に保存し、起動時に復元する。
*   **Effect Manager**: アプリケーションアイコンの設定（タスクバーID管理含む）や全体ショートカットのディスパッチを行う。

#### **Flow Area (`widgets/flow_area.py`)**
*   **Vertical Coordinator**: 縦方向に並ぶ `Flow Lane` を管理する。
*   **Tab Interface**: 1つのタブの中身として機能し、作業スペース（Workspace）を提供する。

#### **Flow Lane (`widgets/flow_lane.py`)**
*   **Horizontal Coordinator**: 横方向に並ぶ `File Pane` の連鎖を管理する。
*   **Downstream Logic**: 左側のペイン（親）でフォルダが選択された際、右側のペイン（子）を更新するロジックを持つ。
    *   **v9.1 Update**: 既存の子孫ペインの「選択状態」を監視し、選択が維持されている場合は単純なクリアを行わず、再帰的に表示更新を行う（Selection Persistence）。

#### **File Pane (`widgets/file_pane.py`)**
*   **The Atom**: ファイル操作の最小単位。
*   **Event Handling**: キーボードイベント（`QShortcut`）、マウスイベント（右クリックメニュー、ホイールリサイズ）を集中的に処理する。
*   **Resizing Logic (v9.0)**: `eventFilter` を使用し、自身の領域だけでなく子ウィジェット（スクロールエリア等）のホイールイベントもフックして、リサイズ操作へと変換する。

#### **Data Models**
*   **`QFileSystemModel`**: OSのファイルシステムを別スレッドで非同期に監視・読み込みを行うQt標準モデル。UIブロックを防ぐ要。
*   **`SmartSortFilterProxyModel` (`models/proxy_model.py`)**:
    *   **Filtering**: リアルタイム検索、表示モード切替（All/Files/Dirs）、隠しファイル制御。
    *   **Performance (v9.1)**: `filterAcceptsRow` 内での重いパス処理（`absoluteFilePath`）を遅延評価し、大量のファイル描画時のボトルネックを解消。
    *   **Sorting**: 「フォルダを常に上位に表示」など、Windows Explorerライクなソートロジックの実装。

---

## 4. 特記すべき実装仕様 (Key Implementations)

### 4.1. QuickLook (プレビュー機能)
macOSのQuickLookを模倣し、スペースキーで瞬時にファイルのプレビューを表示します。
*   **Mechanism**: シングルトンの `QuickLookWindow` をメインウィンドウが保持し、アクティブなペインの選択ファイルパスを渡して描画させる。
*   **Format Support**: 画像（Qt標準対応形式）、テキスト（ソースコード含む）、PDF（外部ツールのレンダリング画像またはテキスト抽出）に対応。

### 4.2. リサイズシステム (Modifier + Wheel)
直感的なレイアウト調整のため、ドラッグ操作不要のリサイズ機構を実装しています。
*   **Ctrl + Wheel**: ペインの横幅（`QSplitter`）を調整。
*   **Shift + Wheel**: レーンの高さ（縦方向 `QSplitter`）を調整。
*   **Propagation Block**: リサイズ中に画面がスクロールしてしまうのを防ぐため、再帰的なイベントフィルタリングによりホイールイベントを完全に消費(accept)している。

### 4.3. 非同期ファイル操作とUI更新
*   ファイルシステムへの変更（リネーム、削除、新規作成）は、`QFileSystemModel` がOSの `ReadDirectoryChangesW` (Windows) 等のAPIを通じて検知し、自動的に `signals` を発火してUIを更新します。
*   これにより、アプリ外でのファイル操作も即座に反映されます。

---

## 5. データ構造 (Data Structures)

### Session Data (`session.json`)
アプリ終了時に保存されるJSOn構造。
```json
{
  "geometry": "HexEncodedString...",
  "splitter_state": "HexEncodedString...",
  "active_tab_index": 0,
  "tabs": [
    {
      "title": "Workspace 1",
      "state": {
        "lanes": [
          {
            "panes": [
              {
                "paths": ["C:/Projects/Src"],
                "display_mode": 0,
                "sort_col": 0, 
                ...
              }
            ]
          }
        ]
      }
    }
  ]
}
```

---

## 6. 将来の拡張性 (Future Extensibility)
*   **Plugin System**: 特定のファイルタイプに対するカスタムアクションやプレビュー機構をプラグインとして分離可能にする設計の余地がある。
*   **Tagging System**: OSのファイルシステムに依存しない、サイドカーファイル(.meta)を用いたタグ管理機能の実装が可能（Model/Viewアーキテクチャのため拡張が容易）。
