import os
import shutil
import zipfile
import subprocess
import sys
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QWidget, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QScrollArea, QSplitter, 
                               QTreeView, QHeaderView, QMenu, QInputDialog, QMessageBox,
                               QSizePolicy, QApplication, QFileSystemModel)
from PySide6.QtCore import Qt, QDir, QSize, QTimer, QEvent, QUrl, QMimeData
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence, QShortcut, QDrag, QIcon, QPixmap

from models.proxy_model import SmartSortFilterProxyModel

class BatchTreeView(QTreeView):
    """v7.4 複数ペイン・マーク済みアイテムを一括でドラッグするためのカスタムTreeView"""
    def __init__(self, owner_pane):
        super().__init__()
        self.owner_pane = owner_pane
        self.setMouseTracking(True) # v11.1 Hover Auto-Focus

    def enterEvent(self, event):
        # v11.1 Hover Auto-Focus Logic
        # Ctrlが押されていない場合、マウスが入っただけでフォーカスを奪う
        if not (QApplication.keyboardModifiers() & Qt.ControlModifier):
            self.setFocus()
            # 親ペインもアクティブにする
            self.owner_pane.parent_filer.set_active_pane(self.owner_pane)
            
            # v11.0 セパレータハイライトのために再描画要求などは eventFilter (FocusIn) で行われる
        
        super().enterEvent(event)

    def startDrag(self, supportedActions):
        # 1. ドラッグ対象のパスを全収集
        drag_paths = set()
        
        # A. マーク（収集カゴ）内のアイテム [Global]
        # 上位構造（タブエリア）にアクセスしてマークを取得
        if hasattr(self.owner_pane, 'parent_lane') and hasattr(self.owner_pane.parent_lane, 'parent_area'):
            area = self.owner_pane.parent_lane.parent_area
            if area and area.marked_paths:
                for p in area.marked_paths:
                    if os.path.exists(p):
                        drag_paths.add(os.path.abspath(p))
            
        # B. このビューの選択アイテム [Local]
        # v10.0 Updated: ペインをまたぐ（他ペインの）選択はドラッグ対象に含めない
        # あくまでも「マークされたもの」＋「現在掴んでいるもの」だけを動かす
        info = self.owner_pane.get_selection_info(view=self, proxy=self.model())
        for p in info['paths']:
            drag_paths.add(os.path.abspath(p))

        if not drag_paths:
            return

        # 2. MimeData作成
        mime = QMimeData()
        urls = [QUrl.fromLocalFile(p) for p in drag_paths]
        mime.setUrls(urls)
        
        # 3. Dragオブジェクト作成と実行
        drag = QDrag(self)
        drag.setMimeData(mime)
        
        drag.exec(supportedActions, Qt.CopyAction)


class FilePane(QFrame):
    """個別のファイルペイン（縦割り）"""
    def __init__(self, title="Flow", parent_filer=None):
        super().__init__()
        self.parent_filer = parent_filer # これはMainWindowを指す想定
        self.setFrameStyle(QFrame.NoFrame)
        self.setObjectName("Pane")
        self.setMouseTracking(True)
        self.setMinimumWidth(100) # 最小幅を設定して「0か1か」を防ぐ
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 固定ヘッダー
        self.header = QWidget()
        self.header.setFixedHeight(30)
        self.header.setObjectName("PaneHeader")
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(10, 0, 5, 0)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; color: #007acc; font-size: 11px;")
        h_layout.addWidget(self.title_label)
        
        # 検索ボックス (インクリメンタルサーチ)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.setFixedWidth(120)
        self.search_box.setStyleSheet("""
            QLineEdit { 
                background: #1e1e1e; color: #ccc; border: 1px solid #333; 
                border-radius: 4px; padding: 2px 5px; font-size: 11px;
            }
            QLineEdit:focus { border: 1px solid #007acc; background: #252526; }
        """)
        self.search_box.textChanged.connect(self.on_search_text_changed)
        h_layout.addWidget(self.search_box)
        
        h_layout.addStretch()
        
        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedSize(20, 20)
        self.up_btn.setStyleSheet("border: none; color: #555; font-weight: bold; background: transparent;")
        self.up_btn.clicked.connect(self.go_up)
        h_layout.addWidget(self.up_btn)
        
        self.main_layout.addWidget(self.header)

        # 全体をスクロール可能にする領域
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setObjectName("PaneScrollArea")
        
        # コンテンツを保持する垂直スプリッター
        self.content_splitter = QSplitter(Qt.Vertical)
        self.content_splitter.setObjectName("PaneSplitter")
        self.scroll.setWidget(self.content_splitter)
        
        # ショートカット: Ctrl+F, Esc
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.focus_search)
        QShortcut(QKeySequence("Esc"), self, activated=self.clear_search)
        
        self.main_layout.addWidget(self.scroll)
        
        # --- Model Architecture Change ---
        # base_model はデータを供給するだけ
        self.base_model = QFileSystemModel()
        # Drivesを含めないとルート表示がおかしくなることがある
        self.base_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden | QDir.Drives)
        self.base_model.setRootPath(QDir.rootPath())
        self.base_model.setReadOnly(False) # 右クリック操作（削除・リネーム）のために必要
        
        # 状態変数
        self.display_mode = 0  
        self.show_hidden = False
        self.current_sort_col = 0
        self.sort_order = Qt.AscendingOrder
        
        self.views = [] # (view, proxy, path, sep_widget) のタプルを保持
        self.current_paths = []
        self.last_selected_paths = [] # 前回選択されていたパス（順序維持用）
        self.is_compact = False # コンパクトモード状態
        # v7.2 Alt+Clickでマークされたパス（永続選択）。
        # FlowArea（タブ単位）で管理される実体への参照を取得する。
        self._marked_paths_ref = None 
        
        self.installEventFilter(self)
        
        # v9.0 スクロール抑止のために子要素も監視
        self.scroll.installEventFilter(self)
        self.scroll.viewport().installEventFilter(self)
        self.content_splitter.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Wheel:
            # v9.0 Ctrl+Wheelで幅変更、Shift+Wheelで高さ変更
            # どの子要素でホイールしてもここでキャッチして親へ伝播させない
            msg_modifiers = event.modifiers()
            delta = event.angleDelta().y()
            
            if msg_modifiers & Qt.ControlModifier:
                # Ctrl + Wheel -> 横幅変更 (Paneの幅)
                # Laneのスプリッターを取得してサイズ変更
                if hasattr(self, 'parent_lane') and self.parent_lane:
                    splitter = self.parent_lane.splitter
                    idx = splitter.indexOf(self)
                    if idx != -1:
                        sizes = splitter.sizes()
                        # 変化量の計算（スクロール1ノッチで適度に）
                    if idx != -1:
                        sizes = splitter.sizes()
                        change = 40 if delta > 0 else -40
                        
                        
                        # 自身(idx)の幅を変えるため、右隣または左隣との境界を動かす必要がある
                        # 基本的に「自身の幅を増やす」=「隣を減らす」
                        # ここでは簡易的に「自分を増減させ、隣接する残りを調整」するが、
                        # QSplitterの挙動上、sizesリスト全体をセットし直すのが確実。
                        
                        if len(sizes) > 1:
                            new_w = sizes[idx] + change
                            if new_w < 50: new_w = 50 # 最小幅ガード
                            
                            # 差分を他のペインから吸い取る（あるいは押し付ける）
                            # 簡単のため「次のペイン」があるならそこと調整、なければ「前のペイン」と調整
                            target_neighbor = idx + 1 if idx + 1 < len(sizes) else idx - 1
                            
                            diff = new_w - sizes[idx]
                            neighbor_w = sizes[target_neighbor] - diff
                            
                            if neighbor_w >= 50: # 隣も最小幅ガード
                                sizes[idx] = new_w
                                sizes[target_neighbor] = neighbor_w
                                splitter.setSizes(sizes)
                            
                event.accept()
                return True # イベント消費（スクロールさせない）
                
            elif msg_modifiers & Qt.ShiftModifier:
                # Shift + Wheel -> 高さ変更 (Laneの高さ)
                # Areaのスプリッターを取得してサイズ変更
                if hasattr(self, 'parent_lane') and hasattr(self.parent_lane, 'parent_area'):
                    lane = self.parent_lane
                    area = lane.parent_area
                    splitter = area.vertical_splitter
                    idx = splitter.indexOf(lane)
                    
                    if idx != -1:
                        sizes = splitter.sizes()
                        change = 40 if delta > 0 else -40
                        
                        if len(sizes) > 1:
                            new_h = sizes[idx] + change
                            if new_h < 50: new_h = 50
                            
                            target_neighbor = idx + 1 if idx + 1 < len(sizes) else idx - 1
                            diff = new_h - sizes[idx]
                            neighbor_h = sizes[target_neighbor] - diff
                            
                            if neighbor_h >= 50:
                                sizes[idx] = new_h
                                sizes[target_neighbor] = neighbor_h
                                splitter.setSizes(sizes)
                                
                event.accept()
                return True # イベント消費（スクロールさせない）

        elif event.type() == QEvent.Enter:
            # v11.1: FilePane自体へのホバー処理
            # Viewへのホバーは BatchTreeView.enterEvent で処理されるため、
            # ここでは「ペインの余白」などにマウスが来た場合の処理、
            # あるいは「ペイン全体のアクティブ化」を担保する。
            
            # Ctrlキーロック
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                return False

            # 親(MainWindow)のアクティブペイン管理を通じて状態更新
            if watched == self:
                self.parent_filer.set_active_pane(self)
                if hasattr(self, 'parent_lane') and hasattr(self.parent_lane, 'parent_area'):
                    self.parent_lane.parent_area.active_lane = self.parent_lane
                if self.current_paths:
                    self.parent_filer.update_address_bar(self.current_paths[0])
                    
        elif event.type() == QEvent.Leave:
            # v6.4 離れてもアクティブ状態は維持する（他のペインがアクティブになるまで）
            pass
            
        elif event.type() == QEvent.KeyPress:
            # v7.2 Alt + C で全マーク解除 (eventFilterで確実にキャッチ)
            if (event.modifiers() & Qt.AltModifier) and event.key() == Qt.Key_C:
                self.clear_all_marks()
                return True
            
            # v7.3 Backspace で上の階層へ
            if event.key() == Qt.Key_Backspace:
                self.go_up()
                return True

            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # 監視対象がView（QTreeView）かつEnterが押された場合
                for view, proxy, _, _ in self.views:
                    if watched == view:
                        idx = view.currentIndex()
                        if idx.isValid():
                            self.on_double_clicked(idx, view)
                        return True # イベントを消費
        
        # v11.0: フォーカスフィードバック（アクティブなViewのセパレータを強調）
        elif event.type() == QEvent.FocusIn:
            # Watched object is a View (BatchTreeView)
            for i, (view, _, _, sep) in enumerate(self.views):
                if watched == view:
                    # Highlight this separator
                    if sep:
                        sep.setStyleSheet("background: #094771; color: #fff; font-size: 9px; padding-left: 10px; border-bottom: 1px solid #007acc; font-weight: bold;")
                    else:
                        # 0番目のアイテムでsepが無い場合（Compactモードでない場合など）
                        # ヘッダー自体の色を変える等はHighlightメソッドでペイン全体やってるが、
                        # ここでは個別のViewのアクティブ感を出したい。
                        # しかしsepがない場合は構造上難しいのでスキップして良いか、
                        # あるいはItemContainerの枠を変えるか。
                        # 現状はsepがある場合（2つ目以降、またはパス1つの場合のタイトルバー）のみ対応。
                        pass
        elif event.type() == QEvent.FocusOut:
             for i, (view, _, _, sep) in enumerate(self.views):
                if watched == view:
                    # Restore style
                    if sep:
                        sep.setStyleSheet("background: #2d2d2d; color: #888; font-size: 9px; padding-left: 10px; border-bottom: 1px solid #222;")
        
        return super().eventFilter(watched, event)

    def highlight(self, active):
        if active:
            self.header.setStyleSheet("background: #37373d; border-bottom: 2px solid #007acc;")
            self.up_btn.setStyleSheet("border: none; color: #007acc; font-weight: bold; background: transparent;")
        else:
            self.header.setStyleSheet("background: #252526; border-bottom: 1px solid #333;")
            self.up_btn.setStyleSheet("border: none; color: #555; background: transparent;")

    def display_folders(self, paths):
        self.current_paths = [os.path.abspath(p) for p in paths]
        # v7.2 マーク機能の参照を確実にリンクする（タブ間移動などで親が変わる可能性に備え）
        if self._marked_paths_ref is None and hasattr(self, 'parent_lane'):
            if hasattr(self.parent_lane, 'parent_area'):
                self._marked_paths_ref = self.parent_lane.parent_area.marked_paths
        
        if not paths:
            self.title_label.setText("...waiting for flow")
            # 全クリア
            while self.content_splitter.count():
                w = self.content_splitter.widget(0)
                w.setParent(None)
                w.deleteLater()
            self.views.clear()
            
            dummy = QWidget()
            dummy.setObjectName("EmptySpace")
            dummy.setStyleSheet("background: #1e1e1e;") # v9.2 Fix: 空領域を黒くする
            self.content_splitter.addWidget(dummy)
            return

        # 1. 削除処理: 新しいパスに含まれない既存Viewを削除
        # 逆順で消さないとインデックスがずれる可能性があるが、リストから消すので注意
        new_path_set = set(self.current_paths)
        i = len(self.views) - 1
        while i >= 0:
            view, proxy, path, sep = self.views[i]
            if path not in new_path_set:
                # コンテナ（Viewの親）を削除する必要がある
                # sepがある場合、それはitem_containerの中にあるので一緒に消えるはず
                # view.parent() は item_container
                container = view.parentWidget() # QFrame
                if container:
                    container.setParent(None)
                    container.deleteLater()
                self.views.pop(i)
            i -= 1

        # Waiting状態のダミーがあれば消す
        for i in range(self.content_splitter.count()):
            w = self.content_splitter.widget(i)
            if w.objectName() == "EmptySpace":
                w.deleteLater()

        # 既存Viewのマップを作成 (path -> (view, proxy, sep, container))
        existing_map = {}
        for v, p, path, s in self.views:
            existing_map[path] = (v, p, s, v.parentWidget())
            
        new_views_list = []

        # 2. 追加・並び替え処理
        for i, path in enumerate(self.current_paths):
            if not os.path.exists(path): continue
            
            # 既存にあるか？
            if path in existing_map:
                view, proxy, sep, container = existing_map[path]
                # splitter内の現在の位置を確認
                current_idx = self.content_splitter.indexOf(container)
                
                # 期待する位置(i)と違うなら移動
                if current_idx != i:
                    self.content_splitter.insertWidget(i, container)
                
                # sepの状態更新（パス数による表示切り替え）
                if len(self.current_paths) > 1:
                    if sep is None:
                        # sepがなかった（＝以前は単独表示だった）場合、作る必要がある
                        # レイアウトに追加
                        sep = QLabel(f" ■ {os.path.basename(path)}")
                        sep.setFixedHeight(20)
                        sep.setStyleSheet("background: #2d2d2d; color: #888; font-size: 9px; padding-left: 10px; border-bottom: 1px solid #222;")
                        container.layout().insertWidget(0, sep)
                        if self.is_compact: sep.hide()
                    else:
                        sep.setVisible(not self.is_compact)
                else:
                    if sep:
                        sep.hide()
                
                # ヘッダー制御
                if self.is_compact:
                    if i > 0: view.setHeaderHidden(True)
                    else: view.setHeaderHidden(False)

                new_views_list.append((view, proxy, path, sep))

            else:
                # 新規作成
                item_container = QFrame()
                item_container.setObjectName("ItemContainer")
                item_layout = QVBoxLayout(item_container)
                item_layout.setContentsMargins(0, 0, 0, 0)
                item_layout.setSpacing(0)
                
                sep = None
                if len(self.current_paths) > 1:
                    sep = QLabel(f" ■ {os.path.basename(path)}")
                    sep.setFixedHeight(20)
                    sep.setStyleSheet("background: #2d2d2d; color: #888; font-size: 9px; padding-left: 10px; border-bottom: 1px solid #222;")
                    item_layout.addWidget(sep)

                # Proxy作成
                proxy = SmartSortFilterProxyModel()
                proxy.setSourceModel(self.base_model)
                proxy.setTargetRootPath(path)
                proxy.setDisplayMode(self.display_mode)
                proxy.setShowHidden(self.show_hidden)
                # v7.2 マーク共有（実体への参照を渡す）
                if self._marked_paths_ref is None and hasattr(self, 'parent_lane'):
                    self._marked_paths_ref = self.parent_lane.parent_area.marked_paths
                proxy.setMarkedPathsRef(self._marked_paths_ref)
                proxy.sort(self.current_sort_col, self.sort_order)

                view = BatchTreeView(self)
                view.setModel(proxy)
                
                source_idx = self.base_model.index(path)
                proxy_idx = proxy.mapFromSource(source_idx)
                view.setRootIndex(proxy_idx)
                
                view.setSortingEnabled(True)
                view.setItemsExpandable(False) 
                view.setExpandsOnDoubleClick(False)
                view.setRootIsDecorated(False)
                view.setSelectionBehavior(QTreeView.SelectRows)
                view.setSelectionMode(QTreeView.ExtendedSelection)
                view.setEditTriggers(QTreeView.NoEditTriggers) # ダブルクリックでのリネームを無効化
                view.setHeaderHidden(False)
                view.setIndentation(0)
                
                view.hideColumn(1) 
                
                # Header Resizing Strategy (v12.0)
                header = view.header()
                header.setSectionResizeMode(0, QHeaderView.Stretch)       # Name: 余白を埋める
                header.setSectionResizeMode(2, QHeaderView.Interactive)   # Size: ユーザー可変 (初期値固定)
                header.setSectionResizeMode(3, QHeaderView.Interactive)   # Date: ユーザー可変 (初期値固定)
                
                # 初期幅の設定
                view.setColumnWidth(2, 80)
                view.setColumnWidth(3, 140)
                
                view.setFrameStyle(QFrame.NoFrame)
                view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
                view.setDragEnabled(True)
                view.setAcceptDrops(True)
                view.setDropIndicatorShown(True)
                view.setDragDropMode(QTreeView.DragDrop)
                view.setDefaultDropAction(Qt.MoveAction)
                
                view.header().setSortIndicator(self.current_sort_col, self.sort_order)
                
                view.setContextMenuPolicy(Qt.CustomContextMenu)
                view.customContextMenuRequested.connect(lambda pos, v=view, p=proxy: self.open_context_menu(pos, v, p))
                
                # キーイベント監視
                view.installEventFilter(self)
                view.viewport().installEventFilter(self)

                view.selectionModel().selectionChanged.connect(self.on_selection_changed)
                view.clicked.connect(self.on_item_clicked)
                view.doubleClicked.connect(lambda idx, v=view: self.on_double_clicked(idx, v))
                
                if self.is_compact:
                    if len(self.current_paths) > 1:
                        if sep: sep.hide()
                    if i > 0:
                        view.setHeaderHidden(True)

                item_layout.addWidget(view)
                
                # 挿入
                self.content_splitter.insertWidget(i, item_container)
                new_views_list.append((view, proxy, path, sep))

        self.views = new_views_list

        # 初回のサイズ調整だけ行い、あとはユーザー調整を尊重したいが、
        # 追加されたときは等分しないとつぶれて見えないことがある
        # ここでは簡易的に、新しく追加された場合のみサイズ調整するロジックにするのは複雑なので
        # パス数が変わった場合のみリセットくらいにするか？
        # いや、維持したいという要望ならサイズも維持すべきだが、増えた分を表示領域確保する必要がある。
        # 既存の比率を保ったまま...は難しいので、パス数が変わったら再計算（等分）が無難か。
        # リセットされるのが嫌という要望なので、なるべく維持したいが。
        
        # ひとまず「パス数が変わった時だけ」等分リセットを行う。
        # (厳密にはこれでもスクロール領域が変わるかもしれないが、中身の状態は維持される)
        
        # しかし splitter.sizes() を取得して、よしなに計算するのは高度すぎる。
        # 追加時は単純に等分で再設定する。（これが一番安全）
        if len(paths) > 0 and self.content_splitter.count() == len(paths):
            # 現在のサイズ合計
            total_h = sum(self.content_splitter.sizes()) 
            if total_h < 100: total_h = self.height()
            each_h = total_h // len(paths)
            
            # もし大幅に数が増減したならリサイズ、そうでなければ維持...
            # 「既存維持」が最優先なので、setSizesを呼ばないほうがいいかもしれない。
            # QSplitterはウィジェット追加時に自動でスペースを割り当てるはず。
            # いったん setSizes を呼ばないで様子を見る。
            pass
            
        self.update_header_title()

    def get_state(self):
        """現在のペインの状態を辞書で返す（セッション保存用）"""
        # pathsは現在のcurrent_pathsを使う
        # ただし、有効なパスのみ
        valid_paths = [p for p in self.current_paths if os.path.exists(p)]
        return {
            "paths": valid_paths,
            "display_mode": self.display_mode,
            "show_hidden": self.show_hidden,
            "sort_col": self.current_sort_col,
            "sort_order": self.sort_order.value, # Enum to int
            "is_compact": self.is_compact
        }

    def restore_state(self, state):
        """辞書からペインの状態を復元する"""
        self.display_mode = state.get("display_mode", 0)
        self.show_hidden = state.get("show_hidden", False)
        self.current_sort_col = state.get("sort_col", 0)
        self.sort_order = Qt.SortOrder(state.get("sort_order", 0))
        self.is_compact = state.get("is_compact", False)
        
        paths = state.get("paths", [])
        if paths:
            self.display_folders(paths)
        else:
            # デフォルト
            self.display_folders([os.path.abspath(".")])

    def open_context_menu(self, pos, view, proxy):
        index = view.indexAt(pos)
        
        # v7.2 ペイン内の全てのViewから選択中のファイルを集める（横串バッチ処理対応）
        all_selected_paths = []
        for v, p, _, _ in self.views:
            indices = v.selectionModel().selectedIndexes()
            processed_rows = set()
            for idx in indices:
                row = idx.row()
                if row not in processed_rows:
                    processed_rows.add(row)
                    col0_idx = idx.siblingAtColumn(0)
                    all_selected_paths.append(self.base_model.filePath(p.mapToSource(col0_idx)))
        
        # 重複排除と存在確認
        paths = list(set([p for p in all_selected_paths if os.path.exists(p)]))
        
        # v7.2 マーク済みのアイテム（バケツ）を取得（全タブ/ペイン横断）
        marked_list = []
        if self._marked_paths_ref:
            marked_list = [p for p in self._marked_paths_ref if os.path.exists(p)]
        
        # 従来の単体View用セレクション情報
        selection = self.get_selection_info(view, proxy)
        if not paths:
            paths = selection["paths"]
        
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; } QMenu::item:selected { background-color: #094771; }")

        # --- Batch Actions Section (Marked Items) ---
        if marked_list:
            batch_menu = menu.addMenu(f"★ Batch Actions ({len(marked_list)} marked)")
            batch_menu.setStyleSheet("QMenu { background-color: #3a1a1a; }") # 背景を少し赤っぽくして区別
            
            # PDF変換
            office_exts = ('.docx', '.doc', '.xlsx', '.xls')
            marked_office = [p for p in marked_list if not os.path.isdir(p) and p.lower().endswith(office_exts)]
            if marked_office:
                act = QAction(f"Convert {len(marked_office)} marked office files to PDF", self)
                act.triggered.connect(lambda: self.action_convert_to_pdf(marked_office))
                batch_menu.addAction(act)
            
            # コピー・移動
            copy_batch_act = QAction(f"Copy {len(marked_list)} marked items", self)
            copy_batch_act.triggered.connect(lambda: self.action_aggregate_clipboard(marked_list, "copy"))
            batch_menu.addAction(copy_batch_act)
            
            move_batch_act = QAction(f"Cut/Move {len(marked_list)} marked items", self)
            move_batch_act.triggered.connect(lambda: self.action_aggregate_clipboard(marked_list, "move"))
            batch_menu.addAction(move_batch_act)
            
            batch_menu.addSeparator()
            clear_mark_act = QAction("Clear All Marks", self)
            clear_mark_act.triggered.connect(self.clear_all_marks)
            batch_menu.addAction(clear_mark_act)
            
            menu.addSeparator()
        # Actions
        # v7.3 Mark/Unmark Selected (Add to Bucket)
        # 選択中のアイテムがマーク済みかどうか判定
        # pathsは現在選択中のすべてのパス
        has_unmarked = False
        has_marked = False
        if self._marked_paths_ref is not None:
             for p in paths:
                 p_abs = os.path.abspath(p)
                 if p_abs in self._marked_paths_ref:
                     has_marked = True
                 else:
                     has_unmarked = True

        if paths:
            # 状況に応じてメニューを出し分ける
            if has_unmarked:
                mark_act = QAction("Mark Selected (Add to Bucket)", self)
                # ショートカット表示（あくまで表示のみ、実際のキーバインドは別途必要だが今回はメニューメイン）
                # mark_act.setShortcut("Alt+M") 
                mark_act.triggered.connect(lambda: self.action_mark_selected(paths, True))
                menu.addAction(mark_act)
            
            if has_marked:
                unmark_act = QAction("Unmark Selected (Remove from Bucket)", self)
                unmark_act.triggered.connect(lambda: self.action_mark_selected(paths, False))
                menu.addAction(unmark_act)
            
            menu.addSeparator()

        open_act = QAction("Open", self)
        open_exp_act = QAction("Reveal in Explorer", self)
        copy_path_act = QAction("Copy Path", self)
        term_act = QAction("Terminal Here", self)
        
        # Archive Actions
        zip_act = QAction("Compress to ZIP...", self)
        unzip_act = QAction("Extract Here (Smart)", self)
        
        # 編集系
        new_folder_act = QAction("New Folder", self)
        rename_act = QAction("Rename", self)
        delete_act = QAction("Delete", self)
        fav_act = QAction("Add to Favorites", self)
        
        # v6.2 Cut/Copy/Paste
        num_files = len([p for p in paths if not os.path.isdir(p)])
        num_dirs = len([p for p in paths if os.path.isdir(p)])
        
        # メニューラベルの動的生成
        label_suffix = ""
        if len(paths) > 1:
            parts = []
            if num_files > 0: parts.append(f"{num_files} files")
            if num_dirs > 0: parts.append(f"{num_dirs} dirs")
            label_suffix = f" ({', '.join(parts)})"
            
        cut_act = QAction(f"Cut{label_suffix}", self)
        copy_obj_act = QAction(f"Copy{label_suffix}", self)
        paste_act = QAction("Paste", self)

        # v7.0 PDF Conversion
        office_extensions = ('.docx', '.doc', '.xlsx', '.xls')
        office_files = [p for p in paths if not os.path.isdir(p) and p.lower().endswith(office_extensions)]
        
        show_pdf_convert = len(office_files) > 0
        pdf_label = "Convert to PDF"
        if len(office_files) > 1:
            pdf_label = f"Convert {len(office_files)} files to PDF"
        pdf_convert_act = QAction(pdf_label, self)

        # Add Actions
        if paths:
            # v7.5 Shortcut Creation (Requested Action 1)
            create_shortcut_act = QAction("Create Shortcut", self)
            create_shortcut_act.triggered.connect(lambda: self.action_create_shortcut(paths))
            menu.addAction(create_shortcut_act)

            menu.addAction(open_act)
            if show_pdf_convert:
                menu.addAction(pdf_convert_act)
            if len(paths) == 1 and not os.path.isdir(paths[0]):
                open_with_act = QAction("Open with...", self)
                open_with_act.triggered.connect(lambda checked=False, p=paths[0]: self.open_with_dialog(p))
                menu.addAction(open_with_act)
            menu.addAction(open_exp_act)
            
            # v7.5 Properties (Requested Action 4)
            if len(paths) == 1:
                prop_act = QAction("Properties", self)
                prop_act.triggered.connect(lambda: self.action_show_properties(paths[0]))
                menu.addAction(prop_act)

            menu.addSeparator()
            
            # v7.5 Enhanced Copy Path (Requested Action 2)
            # copy_path_act = QAction("Copy Path", self) # Removed simple action
            copy_menu = menu.addMenu("Copy Path Special")
            
            cp_full = QAction("Copy Full Path", self)
            cp_full.triggered.connect(lambda: self.copy_to_clipboard("\n".join(paths)))
            copy_menu.addAction(cp_full)
            
            cp_name = QAction("Copy Name", self)
            cp_name.triggered.connect(lambda: self.copy_to_clipboard("\n".join([os.path.basename(p) for p in paths])))
            copy_menu.addAction(cp_name)
            
            cp_quote = QAction('Copy as "Path"', self)
            cp_quote.triggered.connect(lambda: self.copy_to_clipboard("\n".join([f'"{p}"' for p in paths])))
            copy_menu.addAction(cp_quote)

            cp_unix = QAction("Copy Unix Path (/)", self)
            cp_unix.triggered.connect(lambda: self.copy_to_clipboard("\n".join([p.replace("\\", "/") for p in paths])))
            copy_menu.addAction(cp_unix)

            menu.addAction(term_act)
            menu.addSeparator()
            menu.addAction(zip_act)
            if selection["has_zip"]:
                menu.addAction(unzip_act)
            menu.addSeparator()
            
        menu.addAction(new_folder_act)
        menu.addSeparator()
        if paths:
            menu.addAction(cut_act)
            menu.addAction(copy_obj_act)
            
        if self.parent_filer.internal_clipboard["paths"]:
            menu.addAction(paste_act)
        
        if paths:
            if all(os.path.isdir(p) for p in paths):
                menu.addAction(fav_act)
            menu.addAction(rename_act)
            menu.addAction(delete_act)
            
        action = menu.exec(view.mapToGlobal(pos))
        if not action: return

        if action == open_act:
            for p in paths:
                if os.name == 'nt':
                     try:
                        # v6.12 作業ディレクトリ(CWD)を対象ファイルの場所に設定し、startコマンドで起動
                        # これによりショートカットやエクスプローラーからの起動と同等の挙動を確保する
                        cwd = os.path.dirname(p) if os.path.isdir(os.path.dirname(p)) else None
                        subprocess.Popen(f'start "" "{p}"', shell=True, cwd=cwd)
                     except Exception as e:
                        print(f"Exec Error: {e}")
                else:
                     QDesktopServices.openUrl(QUrl.fromLocalFile(p))
        elif action == open_exp_act:
            if paths: subprocess.Popen(f'explorer /select,"{os.path.abspath(paths[0])}"')
        # Copy Path logic handled by sub-actions now
        elif action == term_act:
            self.action_terminal(paths)
        elif action == fav_act:
            for p in paths: self.parent_filer.add_to_favorites(p)
        elif action == zip_act:
            # zip_act 等は一旦そのまま（あるいはメソッド化しても良いが）
            self.action_zip(selection)
        elif action == unzip_act:
            self.action_unzip(selection)
        elif action == new_folder_act:
            self.action_new_folder(view, proxy)
        elif action == rename_act:
            self.action_rename()
        elif action == delete_act:
            self.action_delete()
        elif action == cut_act:
            self.action_aggregate_clipboard(paths, "move")
        elif action == copy_obj_act:
            self.action_aggregate_clipboard(paths, "copy")
        elif action == pdf_convert_act:
            self.action_convert_to_pdf(office_files)
        elif action == paste_act:
            # 貼り付け先: 右クリックしたアイテムがフォルダならその中
            dest_dir = None
            if index.isValid():
                p_under_mouse = self.base_model.filePath(proxy.mapToSource(index))
                if os.path.isdir(p_under_mouse):
                    dest_dir = p_under_mouse
            self.action_paste(dest_dir)

    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)

    def action_create_shortcut(self, paths):
        """v7.5 選択したファイルのショートカットを作成"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            
            for target in paths:
                target_abs = os.path.abspath(target)
                parent_dir = os.path.dirname(target_abs)
                name = os.path.basename(target_abs)
                base, _ = os.path.splitext(name)
                
                # Desktop以外の場合は同階層に作成
                link_path = os.path.join(parent_dir, f"{base} - Shortcut.lnk")
                
                # 同名回避
                c = 1
                while os.path.exists(link_path):
                    link_path = os.path.join(parent_dir, f"{base} - Shortcut ({c}).lnk")
                    c += 1
                
                shortcut = shell.CreateShortcut(link_path)
                shortcut.TargetPath = target_abs
                shortcut.WorkingDirectory = parent_dir
                shortcut.Save()
        except Exception as e:
            QMessageBox.critical(self, "Shortcut Error", f"Failed to create shortcut:\n{e}")

    def action_show_properties(self, path):
        """v7.5 Windows標準のプロパティ画面を表示"""
        try:
            import ctypes
            from ctypes import wintypes
            
            SEE_MASK_INVOKEIDLIST = 0x0000000C
            SW_SHOWNORMAL = 1
            
            class SHELLEXECUTEINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_uint32),
                    ("fMask", ctypes.c_uint32),
                    ("hwnd", wintypes.HWND),
                    ("lpVerb", wintypes.LPCWSTR),
                    ("lpFile", wintypes.LPCWSTR),
                    ("lpParameters", wintypes.LPCWSTR),
                    ("lpDirectory", wintypes.LPCWSTR),
                    ("nShow", ctypes.c_int),
                    ("hInstApp", wintypes.HINSTANCE),
                    ("lpIDList", ctypes.c_void_p),
                    ("lpClass", wintypes.LPCWSTR),
                    ("hkeyClass", ctypes.c_void_p),
                    ("dwHotKey", ctypes.c_uint32),
                    ("hIcon", ctypes.c_void_p),
                    ("hProcess", ctypes.c_void_p),
                ]
            
            sei = SHELLEXECUTEINFO()
            sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
            sei.fMask = SEE_MASK_INVOKEIDLIST
            sei.hwnd = int(self.window().winId()) # 親ウィンドウハンドル
            sei.lpVerb = "properties"
            sei.lpFile = os.path.abspath(path)
            sei.nShow = SW_SHOWNORMAL
            
            ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
            
        except Exception as e:
             QMessageBox.critical(self, "Properties Error", f"Failed to show properties:\n{e}")


    def get_selection_info(self, view=None, proxy=None):
        if view is None or proxy is None:
            # 1. アクティブ（フォーカスあり）なViewを探す
            view, proxy = None, None
            for v, p, _, _ in self.views:
                if v.hasFocus():
                    view, proxy = v, p
                    break
            
            # 2. フォーカスがない場合、選択項目があるViewを探す (v12.0 fix: ホバー操作時のUX改善)
            # クリックせずにマウスオーバーだけでCtrl+C等をする場合、フォーカスが当たっていない可能性があるため
            if not view:
                for v, p, _, _ in self.views:
                    if v.selectionModel().hasSelection():
                        view, proxy = v, p
                        break
            
            # 3. それでもなければ先頭をデフォルトとする
            if not view and self.views:
                view, proxy = self.views[0][0], self.views[0][1]

        paths = []
        full_infos = []
        has_zip = False
        if view:
            selected_indexes = view.selectionModel().selectedRows()
            for idx in selected_indexes:
                src_idx = proxy.mapToSource(idx)
                path = self.base_model.filePath(src_idx)
                if os.path.exists(path):
                    paths.append(path)
                    is_dir = os.path.isdir(path)
                    full_infos.append({"index": src_idx, "path": path, "is_dir": is_dir})
                    if not is_dir and path.lower().endswith('.zip'):
                        has_zip = True
        return {"paths": paths, "full_infos": full_infos, "has_zip": has_zip, "view": view, "proxy": proxy}

    def action_aggregate_clipboard(self, paths, mode):
        """v7.2 全Viewから集めた項目をクリップボードにセット（重複排除・入れ子対応）"""
        if not paths: return
        
        # 入れ子関係の排除ロジック:
        # 親フォルダが選択されている場合、その中にある選択済みファイルはリストから除外する
        sorted_paths = sorted(paths, key=len) # 短いパス（親ディレクトリ）から順に処理
        final_list = []
        
        for p in sorted_paths:
            p_abs = os.path.abspath(p)
            # すでにfinal_listにあるフォルダの配下かどうかチェック
            is_redundant = False
            for existing in final_list:
                if os.path.isdir(existing):
                    # existing が p_abs の親ディレクトリであるか確認
                    common = os.path.commonpath([existing, p_abs])
                    if common == os.path.abspath(existing) and existing != p_abs:
                        is_redundant = True
                        break
            if not is_redundant:
                final_list.append(p)
                
        self.parent_filer.internal_clipboard = {"paths": final_list, "mode": mode}
        
        # v7.2 収集コピー起動時はマークをクリア
        if self._marked_paths_ref:
            for p in final_list:
                if p in self._marked_paths_ref:
                    self._marked_paths_ref.remove(p)
            self.refresh_all_views_in_tab()

    def action_cut(self):
        info = self.get_selection_info()
        if info["paths"]:
            self.parent_filer.internal_clipboard = {"paths": info["paths"], "mode": "move"}

    def action_copy(self):
        info = self.get_selection_info()
        if info["paths"]:
            self.parent_filer.internal_clipboard = {"paths": info["paths"], "mode": "copy"}

    def action_paste(self, dest_dir=None):
        if dest_dir is None:
            dest_dir = self.current_paths[0] if self.current_paths else None
        
        if not dest_dir or not os.path.exists(dest_dir): return
        
        cb = self.parent_filer.internal_clipboard
        if cb["paths"]:
            self.execute_batch_paste(cb["paths"], dest_dir, cb["mode"])
            if cb["mode"] == "move":
                self.parent_filer.internal_clipboard = {"paths": [], "mode": "copy"}

    def action_delete(self):
        info = self.get_selection_info()
        paths = info["paths"]
        if paths:
            ret = QMessageBox.question(self, "Delete", f"Are you sure you want to delete {len(paths)} items?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                for item in info["full_infos"]:
                    self.base_model.remove(item["index"])

    def action_rename(self):
        info = self.get_selection_info()
        if info["view"]:
            idx = info["view"].currentIndex()
            if idx.isValid():
                info["view"].edit(idx)

    def action_new_folder(self, view=None, proxy=None):
        if view is None or proxy is None:
            info = self.get_selection_info()
            view, proxy = info["view"], info["proxy"]
        
        if view and proxy:
            src_root_idx = proxy.mapToSource(view.rootIndex())
            name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:")
            if ok and name:
                self.base_model.mkdir(src_root_idx, name)

    def action_terminal(self, paths):
        target_dir = paths[0] if paths and os.path.isdir(paths[0]) else os.path.dirname(paths[0]) if paths else self.current_paths[0]
        if os.path.exists(target_dir):
            subprocess.Popen(f'start cmd /k "cd /d {target_dir}"', shell=True)

    def action_zip(self, selection):
        paths = selection["paths"]
        full_infos = selection["full_infos"]
        if not paths: return
        base_name = os.path.basename(paths[0])
        if len(paths) > 1: base_name = os.path.basename(os.path.dirname(paths[0])) or "Archive"
        if os.path.isdir(paths[0]) and len(paths) == 1: pass 
        else: base_name = os.path.splitext(base_name)[0]
        
        default_zip = f"{base_name}.zip"
        zip_name, ok = QInputDialog.getText(self, "Compress", "ZIP File Name:", text=default_zip)
        if ok and zip_name:
            parent_dir = os.path.dirname(paths[0])
            target_zip = os.path.join(parent_dir, zip_name)
            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                with zipfile.ZipFile(target_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for item in full_infos:
                        p, is_d = item["path"], item["is_dir"]
                        if is_d:
                            for root, dirs, files in os.walk(p):
                                for file in files:
                                    fp = os.path.join(root, file)
                                    arcname = os.path.relpath(fp, parent_dir)
                                    zf.write(fp, arcname)
                        else:
                            arcname = os.path.relpath(p, parent_dir)
                            zf.write(p, arcname)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            finally:
                QApplication.restoreOverrideCursor()

    def action_unzip(self, selection):
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            for item in selection["full_infos"]:
                p, is_d = item["path"], item["is_dir"]
                if not is_d and p.lower().endswith('.zip'):
                    out_dir = os.path.splitext(p)[0]
                    base_out = out_dir
                    c = 1
                    while os.path.exists(out_dir):
                        out_dir = f"{base_out}_{c}"
                        c += 1
                    os.makedirs(out_dir, exist_ok=True)
                    shutil.unpack_archive(p, out_dir)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            QApplication.restoreOverrideCursor()

    def execute_batch_paste(self, src_paths, dest_dir, mode):
        if not os.path.exists(dest_dir): return
        
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            for src in src_paths:
                if not os.path.exists(src): continue
                
                name = os.path.basename(src)
                dest = os.path.join(dest_dir, name)
                
                # 同名衝突回避
                if os.path.exists(dest):
                    base, ext = os.path.splitext(name)
                    c = 1
                    while os.path.exists(os.path.join(dest_dir, f"{base}_{c}{ext}")):
                        c += 1
                    dest = os.path.join(dest_dir, f"{base}_{c}{ext}")
                
                try:
                    if mode == "copy":
                        if os.path.isdir(src):
                            shutil.copytree(src, dest)
                        else:
                            shutil.copy2(src, dest)
                    else: # move
                        shutil.move(src, dest)
                except Exception as e:
                    print(f"Paste Error ({src}): {e}", file=sys.stderr)
                    
        finally:
            QApplication.restoreOverrideCursor()

    def open_with_dialog(self, path):
        try:
            path = os.path.normpath(path)
            
            # 試行1: OpenWith.exe (Windows 10/11)
            cmd = f'C:\\Windows\\System32\\OpenWith.exe "{path}"'
            subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
            
        except Exception as e:
            # フォールバック: rundll32
            try:
                cmd = f'rundll32.exe shell32.dll,OpenAs_RunDLL "{path}"'
                subprocess.Popen(cmd, shell=True)
            except Exception:
                 pass

    def update_header_title(self):
        titles = []
        for p in self.current_paths:
            name = os.path.basename(p) if os.path.basename(p) else p
            titles.append(name)
        
        mode_text = ["All", "Dirs", "Files"][self.display_mode]
        hidden_text = "+H" if self.show_hidden else ""
        col_names = {0: "Name", 2: "Type", 3: "Date"}
        sort_name = col_names.get(self.current_sort_col, "?")
        order_text = "ASC" if self.sort_order == Qt.AscendingOrder else "DESC"
        
        tag = f"[{mode_text}{' ' + hidden_text if hidden_text else ''} | {sort_name} {order_text}]"
        compact_tag = " (COMPACT)" if self.is_compact else ""
        self.title_label.setText(f"{tag}{compact_tag}  " + " + ".join(titles) if titles else "Empty")

    def toggle_sort(self, col):
        current_col = self.current_sort_col
        if current_col == col:
            new_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            new_order = Qt.AscendingOrder

        self.current_sort_col = col
        self.sort_order = new_order
            
        for view, proxy, _, _ in self.views:
            proxy.sort(col, self.sort_order)
            view.header().setSortIndicator(col, self.sort_order)
            
        self.update_header_title()

    def cycle_display_mode(self):
        self.display_mode = (self.display_mode + 1) % 3
        # モード切替時にViewがルート(My Computer)に飛ぶのを防ぐため、
        # 各Viewのルートインデックスを現在のパスで再拘束する
        for i, (view, proxy, path, _) in enumerate(self.views):
            proxy.setDisplayMode(self.display_mode)
            
            # 再設定
            source_idx = self.base_model.index(path)
            proxy_idx = proxy.mapFromSource(source_idx)
            view.setRootIndex(proxy_idx)
            
        self.update_header_title()

    def toggle_hidden(self):
        self.show_hidden = not self.show_hidden
        for i, (view, proxy, path, _) in enumerate(self.views):
            proxy.setShowHidden(self.show_hidden)
            # 再設定
            source_idx = self.base_model.index(path)
            proxy_idx = proxy.mapFromSource(source_idx)
            view.setRootIndex(proxy_idx)
            
        self.update_header_title()

    def on_selection_changed(self):
        current_selected = []
        for view, proxy, _, _ in self.views:
            for idx in view.selectionModel().selectedRows():
                # ProxyインデックスなのでSourceに戻してパス取得
                source_idx = proxy.mapToSource(idx)
                p = self.base_model.filePath(source_idx)
                if os.path.isdir(p): current_selected.append(p)
        
        if not current_selected:
            # 選択解除された場合、空にするかどうかは要検討だが、
            # ChainFlowFilerとしては「何も表示しない」のが正しい
            self.last_selected_paths = []
            return

        # 順序維持ロジック:
        # 新しい選択リストを作成する際、「前回選択されていたもの」が今回も含まれていれば、
        # それらをリストの先頭に（前回の順序のまま）配置する。
        # 新しく追加されたものは、その後ろに追加する。
        
        prioritized_paths = []
        new_paths_set = set(current_selected)
        
        # 1. 前回の選択に含まれていて、かつ今回も選択されているものを先頭へ
        for p in self.last_selected_paths:
            if p in new_paths_set:
                prioritized_paths.append(p)
                new_paths_set.remove(p) # 追加済み
        
        # 2. 残り（新規追加分）を後ろへ。元のcurrent_selectedの順序（基本は名前順）を守る
        for p in current_selected:
            if p in new_paths_set:
                prioritized_paths.append(p)
        
        # 更新
        self.last_selected_paths = prioritized_paths
        
        # アドレスバー更新
        if prioritized_paths:
            self.parent_filer.update_address_bar(prioritized_paths[-1])
        
        # 反映
        if prioritized_paths:
            QTimer.singleShot(10, lambda: self.parent_filer.update_downstream(self, prioritized_paths))

    def on_item_clicked(self, index):
        # indexはProxyIndex
        view = self.sender()
        if not view: return
        # viewに対応するproxyを探す（ちょっと非効率だが確実）
        target_proxy = None
        for v, p, _, _ in self.views:
            if v == view:
                target_proxy = p
                break
        if target_proxy:
            source_idx = target_proxy.mapToSource(index)
            path = os.path.abspath(self.base_model.filePath(source_idx))
            
            # v7.2 Alt + Click でマーク処理
            if QApplication.keyboardModifiers() & Qt.AltModifier and self._marked_paths_ref is not None:
                if path in self._marked_paths_ref:
                    self._marked_paths_ref.remove(path)
                else:
                    self._marked_paths_ref.add(path)
                # 全Viewの表示を更新するためにinvalidateをかける
                self.refresh_all_views_in_tab()
                return # Altクリック時は通常のプレビュー更新などはしない（邪魔しない）

            self.parent_filer.update_preview(path)
            self.parent_filer.update_address_bar(path)

    def refresh_all_views_in_tab(self):
        """タブ内の全ペインの全Viewの見た目をリフレッシュ（マーク色反映用）"""
        if hasattr(self, 'parent_lane') and hasattr(self.parent_lane, 'parent_area'):
            area = self.parent_lane.parent_area
            for lane in area.lanes:
                for pane in lane.panes:
                    for _, p, _, _ in pane.views:
                        p.invalidate()

    def clear_all_marks(self):
        if self._marked_paths_ref is not None:
            self._marked_paths_ref.clear()
            self.refresh_all_views_in_tab()

    def get_current_selected_path(self):
        """現在選択されているアイテムのパスを返す（QuickLook用）"""
        # 複数のViewがある場合、フォーカスがあるViewを優先したいが、
        # ここでは単純に「選択がある最初のView」からパスを取得する
        for view, proxy, _, _ in self.views:
            sel = view.selectionModel().selectedRows()
            if sel:
                # 最後の選択を取得
                idx = sel[-1]
                source_idx = proxy.mapToSource(idx)
                return self.base_model.filePath(source_idx)
        return None

    def on_double_clicked(self, index, view):
        # ここもProxyIndexが来る
        target_proxy = None
        for v, p, _, _ in self.views:
            if v == view: target_proxy = p; break
            
        if target_proxy:
            source_idx = target_proxy.mapToSource(index)
            path = self.base_model.filePath(source_idx)
            
            if os.path.isdir(path):
                # フォルダなら下流ペインへ遷移
                self.navigate_to(view, path)
            else:
                # ファイルならOS標準のアプリで開く
                if os.name == 'nt':
                    try:
                        # v6.12 作業ディレクトリを適切に設定
                        cwd = os.path.dirname(path) if os.path.isdir(os.path.dirname(path)) else None
                        subprocess.Popen(f'start "" "{path}"', shell=True, cwd=cwd)
                    except Exception as e:
                        print(f"Exec Error: {e}")
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def on_search_text_changed(self, text):
        """インクリメンタルサーチ実行"""
        for i, (view, proxy, path, _) in enumerate(self.views):
            proxy.setSearchText(text)
            # フィルタ変更によるルートロスト防止：位置を再固定
            source_idx = self.base_model.index(path)
            proxy_idx = proxy.mapFromSource(source_idx)
            view.setRootIndex(proxy_idx)
            
    def focus_search(self):
        self.search_box.setFocus()
        self.search_box.selectAll()
        
    def clear_search(self):
        self.search_box.clear()

    def action_mark_selected(self, paths, mark=True):
        """v7.3 選択したアイテムを一括でマーク/マーク解除する"""
        if not paths: return
        
        # 参照がない場合のフェイルセーフ
        if self._marked_paths_ref is None:
            if hasattr(self, 'parent_lane') and hasattr(self.parent_lane, 'parent_area'):
                self._marked_paths_ref = self.parent_lane.parent_area.marked_paths
        
        if self._marked_paths_ref is None: return

        changed = False
        for p in paths:
            # パスを正規化（絶対パス）して使用する
            p_abs = os.path.abspath(p)
            if mark:
                if p_abs not in self._marked_paths_ref:
                    self._marked_paths_ref.add(p_abs)
                    changed = True
            else:
                if p_abs in self._marked_paths_ref:
                    self._marked_paths_ref.remove(p_abs)
                    changed = True
        
        if changed:
            self.refresh_all_views_in_tab()

    def refresh_all_views_in_tab(self):
        """タブ内の全ペインの全Viewの見た目をリフレッシュ（マーク色反映用）"""
        if hasattr(self, 'parent_lane') and hasattr(self.parent_lane, 'parent_area'):
            area = self.parent_lane.parent_area
            for lane in area.lanes:
                for pane in lane.panes:
                    for _, p, _, _ in pane.views:
                        # 色の変更（data関数の結果変更）を反映させるには layoutChanged が確実
                        p.layoutChanged.emit()

    def action_convert_to_pdf(self, paths):
        """v7.1 Hybrid PDF Conversion (MS Office -> LibreOffice)"""
        if not paths: return
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            office_success_paths = []
            
            # --- Try Microsoft Office first ---
            try:
                import win32com.client
                import pythoncom
                pythoncom.CoInitialize()
                
                word_app = None
                excel_app = None
                
                for path in paths:
                    abs_path = os.path.abspath(path)
                    ext = os.path.splitext(abs_path)[1].lower()
                    pdf_path = os.path.splitext(abs_path)[0] + ".pdf"
                    
                    # 同名回避
                    if os.path.exists(pdf_path):
                        base, _ = os.path.splitext(pdf_path)
                        c = 1
                        while os.path.exists(f"{base}_{c}.pdf"):
                            c += 1
                        pdf_path = f"{base}_{c}.pdf"

                    try:
                        if ext in ('.docx', '.doc'):
                            if not word_app:
                                word_app = win32com.client.Dispatch("Word.Application")
                                word_app.Visible = False
                            doc = word_app.Documents.Open(abs_path)
                            doc.ExportAsFixedFormat(pdf_path, 17) # wdExportFormatPDF = 17
                            doc.Close(False)
                            office_success_paths.append(path)
                        elif ext in ('.xlsx', '.xls'):
                            if not excel_app:
                                excel_app = win32com.client.Dispatch("Excel.Application")
                                excel_app.Visible = False
                                excel_app.DisplayAlerts = False
                            wb = excel_app.Workbooks.Open(abs_path)
                            wb.ExportAsFixedFormat(0, pdf_path) # xlTypePDF = 0
                            wb.Close(False)
                            office_success_paths.append(path)
                    except Exception as e:
                        print(f"MS Office Error for {path}: {e}")

                if word_app: word_app.Quit()
                if excel_app: excel_app.Quit()
            
                # v7.2 バッチ処理成功後にマークを解除（もしカゴから実行された場合）
                if hasattr(self, '_marked_paths_ref') and self._marked_paths_ref:
                    # 変換に成功したパス（または渡されたパス全体）をマークから消す
                    for p in paths:
                        if p in self._marked_paths_ref:
                            self._marked_paths_ref.remove(p)
                    self.refresh_all_views_in_tab()
                
            except Exception as e:
                print(f"MS Office Dispatch failed or not installed: {e}")

            # --- Try LibreOffice for remaining files ---
            remaining_paths = [p for p in paths if p not in office_success_paths]
            if remaining_paths:
                # sofficeのパスを探す
                soffice_path = shutil.which("soffice") or shutil.which("soffice.exe")
                # 標準的なインストールパスを確認（Windows）
                if not soffice_path:
                    possible_paths = [
                        r"C:\Program Files\LibreOffice\program\soffice.exe",
                        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
                    ]
                    for p in possible_paths:
                        if os.path.exists(p):
                            soffice_path = p
                            break
                
                if soffice_path:
                    for path in remaining_paths:
                        abs_path = os.path.abspath(path)
                        out_dir = os.path.dirname(abs_path)
                        try:
                            # soffice --headless --convert-to pdf --outdir "output_dir" "input_file"
                            subprocess.run([soffice_path, "--headless", "--convert-to", "pdf", "--outdir", out_dir, abs_path], 
                                         check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                        except Exception as e:
                            print(f"LibreOffice Error for {path}: {e}")
                else:
                    if remaining_paths == paths:
                        # 全く何もできなかった場合
                        QMessageBox.warning(self, "PDF Conversion", "Neither MS Office nor LibreOffice was found.")
            
        except Exception as e:
            QMessageBox.critical(self, "PDF Conversion Error", str(e))
        finally:
            QApplication.restoreOverrideCursor()
            self.search_box.clearFocus()

    def go_up(self):
        # 1. アクティブなViewを探す
        target_view = None
        target_path = None
        
        # フォーカスがあるViewを優先
        for view, _, path, _ in self.views:
            if view.hasFocus():
                target_view = view
                target_path = path
                break
        
        # フォーカスがない場合は、既存の挙動(views[0])または安全策として何もしない
        # ここでは「何も選択されていないなら一番上」という従来の挙動をフォールバックとして残す
        if target_view is None and self.views:
            target_view, _, target_path, _ = self.views[0]

        if not target_view:
            return

        parent_path = os.path.dirname(target_path)
        if parent_path and parent_path != target_path:
            self.navigate_to(target_view, parent_path)

    def navigate_to(self, view, path):
        # ターゲットViewを探して更新
        for i, info in enumerate(self.views):
            v, proxy, p = info[0], info[1], info[2]
            if v == view:
                # ターゲットルート更新（これを先にやらないとフィルタで弾かれてsetRootIndexが失敗する）
                proxy.setTargetRootPath(path)
                
                # RootIndex更新
                source_idx = self.base_model.index(path)
                proxy_idx = proxy.mapFromSource(source_idx)
                view.setRootIndex(proxy_idx)
                
                # タプルを更新 (view, proxy, path, sep)
                new_info = list(info)
                new_info[2] = path
                self.views[i] = tuple(new_info)
                self.current_paths[i] = path
                self.parent_filer.update_address_bar(path)
                break
        self.update_header_title()

    def toggle_compact(self):
        self.is_compact = not self.is_compact
        for i, (view, proxy, path, sep) in enumerate(self.views):
            if sep:
                sep.setVisible(not self.is_compact)
            
            # 1つ目のviewのヘッダーは常に表示、2つ目以降を制御
            if i > 0:
                view.setHeaderHidden(self.is_compact)
            else:
                view.setHeaderHidden(False)
        
        # タイトル更新で状態を表示
        self.update_header_title()

    def pop_active_view(self):
        """v10.1 Shift+W: フォーカスのあるビュー(または末尾)を削除する"""
        if len(self.current_paths) <= 1:
            return

        # フォーカスのあるViewを探す
        target_index = -1
        for i, (view, _, _, _) in enumerate(self.views):
            if view.hasFocus():
                target_index = i
                break
        
        # フォーカスがなければ末尾を対象にする
        if target_index == -1:
            target_index = len(self.current_paths) - 1
            
        # 削除実行
        # 先頭(index 0)を消すとペインが空になるわけではないが、仕様として「ペインそのものは消さない」ので、
        # もし全部消そうとしているなら(len<=1)すでにreturn済み。
        # ここでは target_index を消す。
        if 0 <= target_index < len(self.current_paths):
            self.current_paths.pop(target_index)
            self.display_folders(self.current_paths)
            
            # アドレスバー更新
            if self.current_paths:
                # 消した場所の手前、あるいは末尾などに合わせるのが親切
                new_focus_idx = min(target_index, len(self.current_paths) - 1)
                self.parent_filer.update_address_bar(self.current_paths[new_focus_idx])
                
                # フォーカス復元（できれば）
                # display_foldersでViewが再生成されるため、indexで追うしかない
                if 0 <= new_focus_idx < len(self.views):
                     self.views[new_focus_idx][0].setFocus()
