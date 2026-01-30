# Chain Flow Filer Project Document
**Version:** 12.0 (Alpha)  
**Last Updated:** 2026-01-30

## 1. プロジェクト概要
**Chain Flow Filer** は、パワーユーザー向けの作業効率化ファイルマネージャーです。
v11では、Hover Auto-Focusや新アイコンの導入、ドラッグ仕様の大幅改善を行いました。
v12では、さらなるUX向上と機能拡張を目指します。

*   **Sectioned Sidebar**: ナビゲーションペインを `STANDARD`, `FAVORITES`, `DRIVES` の3セクションに分割し、折りたたみ可能にしました。
*   **Resizable Sidebar Sections**: サイドバー内の各セクション（Standard含む）はマウスドラッグまたは `Shift+Scroll` で高さを自由に調整可能。Spacerによる上詰め配置補正付き。
*   **Standard Folders**: デスクトップ、ダウンロードなどの標準フォルダへのクイックアクセスを実装。


*   **View Unstacking (v11.0)**: `Shift+W` で、ペイン全体ではなく「現在アクティブなビュー」だけを閉じることができます。
*   **Hover Auto-Focus (v11.1)**: ペイン内の個別のビュー（分割ブロック）に対しても、マウスオーバーだけでフォーカスが移動し、青いハイライトが追従します。
*   **Q-Key Fix (v11.1)**: `Q` (Go Up) キーが、アクティブなビューに対して正しく作用するように修正されました。
*   **New Icon (v11.1)**: 視認性を高めた新デザインのアイコンを採用。
*   **Unified Batch Drag (v10.1)**: 安全性を高めた一括ドラッグ機能。
*   **Quick Copy (v10.0)**: プレビューからのコンテンツコピー。
*   **Icon Update**: `app_icon.ico` を透過版画像で確実に上書きし、タスクバー等への反映を修正。


---

## 2. 実装済み機能 (Requirements Implemented)

### 2.1 ナビゲーション & ビュー
*   **Chain Flow Interface**: フォルダを開くたびに右側に新しいペインが追加される方式。
*   **Sectioned Sidebar (v12.0)**: `STANDARD`, `FAVORITES`, `DRIVES` の3セクション構成。全てのスプリッターが操作可能で、Spacerにより閉じた際の上詰めレイアウトを自動調整します。
*   **Standard Folders**: デスクトップ、ドキュメントなどへのクイックアクセス。
*   **Address Bar**: 現在地のパス表示と直接入力による高速ジャンプ。
*   **Hover Lock / Persistent Highlight**: マウス操作の焦点を維持し、誤操作を防ぐ。
*   **Hover Focus (v12.0 Fix)**: マウスオーバーだけで対象ペインを選択状態とし、クリックせずとも `Ctrl+C` 等のキー操作を受け付けます。
*   **Vertical Flow Lanes**: 複数のフローを縦に積み重ねて表示可能（`V` キー）。
*   **Tabbed Workspace**: 複数の作業スペースをタブとして管理（`Ctrl+T`）。
*   **Compact Mode (`C` Key)**: スタック表示時のスペース効率を最大化。
*   **Sidebar Toggle (`Ctrl+B`)**: ナビゲーションペインの表示切り替え。

### 2.2 プレビュー機能 (Quick Look)
*   **Popup Preview (`Space` Key)**: 選択中のファイルを即座にポップアップ表示。
*   **Supported Formats**:
    *   **Images**: 各種画像形式（png, jpg, webp, svg等）。
    *   **Text/Code**: ソースコード、Markdown、**AutoHotkey (.ahk)** 等。
*   **Copy Content Button (v10.0)**:
    *   プレビューウィンドウ右上のボタンから、表示中のテキストまたは画像データをクリップボードへコピー可能。
*   **Stays On Top & No Focus**: プレビューを表示したままリストを操作可能。

### 2.3 ファイル操作 & 実行
*   **Unified Batch Drag (v10.0)**:
    *   **Selection + Marks**: **現在操作中のペインの選択アイテム**と、`Alt+Mark` されたアイテムを**合算**してドラッグ開始可能。
    *   ※ 他のペインで「選択」されているだけ（非マーク）のアイテムはドラッグ対象に含まれません（誤操作防止のため）。
    *   これにより、あちこちのフォルダから素材を`Alt+Click`で集めて、一回で別フォルダや外部アプリへ放り込むことが可能。
*   **Context Menu Extensions (v10.0)**:
    *   **Create Shortcut**: その場にショートカット(.lnk)を作成。
    *   **Properties**: Windows標準のプロパティ画面を表示。
    *   **Copy Path Special**: パス、ファイル名、Unix形式パスなどのコピー。
*   **Collection Bucket (Alt-Marking)**: 
    *   **Alt + Click**: 赤いマーク（ワインレッド）でアイテムを「カゴ」に入れる。移動しても維持される。
    *   **Batch Menu**: マークされたアイテムに対する一括操作メニュー。
*   **Standard Actions**: Copy/Cut/Paste, Delete, Rename (F2), Drag & Drop.

### 2.4 その他
*   **Session Persistence**: アプリ終了時の状態を保存 (Portable対応)。
*   **Smart Sorting**: 自然順ソート。
*   **Deep Blue Scrollbars**: v10で採用された、落ち着いた青色の角丸スクロールバー。

---

## 3. 操作マニュアル (Key Bindings)

| Key | Action | Description |
| :--- | :--- | :--- |
| **Space** | **Quick Look** | プレビュー表示 (Copyボタン付き) |
| **Alt + Click** | **Mark (Bucket)** | アイテムを赤くマーク (ドラッグ対象に追加) |
| **Alt + C** | **Clear Marked** | マーク全解除 |
| **Drag** | **Batch Drag** | 選択+マーク項目を一括ドラッグ |
| **Q / Backspace** | Go Up | 親ディレクトリへ戻る |
| **V** | Vertical Split | 新しいレーンを追加 |
| **C** | Compact Mode | 表示モード切替 |
| **Ctrl+C / V** | Copy / Paste | クリップボード操作 |
| **Ctrl+B** | Sidebar Toggle | サイドバー表示切替 |
| **Ctrl/Shift + Wheel** | Resize | ペイン幅/レーン高さ調整 |

---

## 4. 技術スタックとアーキテクチャ
*   **Language**: Python 3.11+
*   **GUI Framework**: PySide6 (Qt6)
*   **Build Tool**: PyInstaller (onedir mode)
*   **Icons**: Standard .ico support

---

## 5. 作業履歴要約 (Development History)
*   **v12.0 (Alpha)**:
    *   **Sidebar Refactoring**: `Standard`, `Favorites`, `Drives` の3セクション分割 + Spacer。
    *   **Focus UX Improvement**: ホバー時のフォーカス・操作対象認識ロジック改良。
    *   **Column UX**: 「名前」列を自動伸縮(Stretch)に設定し、ペインリサイズ操作だけで長いファイル名の確認を容易化。
    *   **Build**: PyInstallerによる単一ファイルビルドワークフローの確立。
*   **v11.0 - v11.1**:
    *   **New Icon**: 透過対応モダンアイコン (`112.png`) の採用。
    *   **Hover Auto-Focus**: マウスオーバーによる直感的なフォーカス切り替え機能。
    *   **View Unstacking**: Shift+Wでの個別ビュー破棄。
    *   **Q-Key Fix**: 上位階層移動の挙動改善。
*   **v10.0 (Alpha)**:
    *   **Unified Batch Drag**: `BatchTreeView` クラスの実装により、選択アイテムとマーク済みアイテムの合同ドラッグを実現。
    *   **Quick Look Ehancements**: `.ahk` 対応、コピーボタン実装（テキスト/画像）。
    *   **Context Menu**: ショートカット作成、プロパティ表示、パスコピー拡張。
    *   **UI Polish**: スクロールバーカラーを Deep Blue (#153b93) に変更。
*   **v9.2 (Stable)**: Sidebar Toggle, Scroll Event Fix.
*   **v9.0**: Mouse Wheel Resizing.
*   **v8.0**: Custom UI Styling (Accent Rounded).
*   **v7.0 - v7.2**: Collection Bucket, PDF Converter.

---

## 6. ビルド情報
```powershell
py -m PyInstaller --clean --onedir --noconsole --name "ChainFlowFiler_v10" --icon="app_icon.ico" --add-data "app_icon.ico;." main.py
```
