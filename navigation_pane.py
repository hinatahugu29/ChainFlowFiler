import os
import sys
import json
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QSplitter, QWidget, QLabel, QApplication,
                               QTreeView, QListWidget, QListWidgetItem, QMenu, QFileSystemModel)
from PySide6.QtCore import Qt, QDir, QUrl
from PySide6.QtGui import QAction, QDesktopServices

class DragDropListWidget(QListWidget):
    """
    ドラッグ＆ドロップでお気に入りを登録・並び替えできるカスタムリスト
    """
    def __init__(self, parent_nav):
        super().__init__()
        self.nav = parent_nav
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QListWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            # 外部（TreeView等）からのドロップ：お気に入り登録
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.exists(path): # ファイルも許可
                    self.nav.add_favorite(path)
            event.acceptProposedAction()
        else:
            # 内部での移動
            super().dropEvent(event)
            self.nav.refresh_item_labels() # v6.9 並べ替え後にホットキー表示を更新
            self.nav.save_favorites() # 並び替えを保存

class NavigationPane(QFrame):
    def __init__(self, parent_filer=None):
        super().__init__()
        self.parent_filer = parent_filer
        self.setMinimumWidth(0) # v9.2 手動で閉じ切れるように緩和（復活はCtrl+Bで）
        self.setObjectName("Sidebar")
        self.active_state = False # v6.8 ホバー状態管理フラグ
        # favorites.json は widgets フォルダの親(v4Root)に置く (v6.10 Portable対応)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.fav_file = os.path.join(base_dir, "favorites.json")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 全体を分けるスプリッター
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.setHandleWidth(4)
        self.main_splitter.setChildrenCollapsible(False) # 中身が消えないようにする
        self.main_splitter.setStyleSheet("QSplitter::handle { background: #333; }")
        
        # --- ドライブセクション ---
        drive_container = QWidget()
        drive_layout = QVBoxLayout(drive_container)
        drive_layout.setContentsMargins(0,0,0,0)
        drive_layout.setSpacing(0)
        
        header = QLabel("  SIDEBAR (Drives)")
        header.setFixedHeight(30)
        header.setMinimumWidth(0) # v9.2 コラプス時に邪魔しないように
        header.setStyleSheet("background: #252526; color: #555; font-weight: bold; font-size: 10px; border-bottom: 1px solid #333;")
        drive_layout.addWidget(header)
        
        self.model = QFileSystemModel()
        self.model.setRootPath("")
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.Drives)
        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(""))
        for i in range(1, 4): self.tree.hideColumn(i)
        self.tree.setHeaderHidden(True)
        self.tree.setFrameStyle(QFrame.NoFrame)
        self.tree.clicked.connect(self.on_clicked)
        
        # ドライブツリーへのドロップを有効化
        self.tree.setAcceptDrops(True)
        self.tree.setDragEnabled(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QTreeView.DragDrop)
        
        drive_layout.addWidget(self.tree)
        self.tree.installEventFilter(self) # v6.8
        
        self.main_splitter.addWidget(drive_container)
        
        # --- お気に入りセクション ---
        fav_container = QWidget()
        fav_layout = QVBoxLayout(fav_container)
        fav_layout.setContentsMargins(0,0,0,0)
        fav_layout.setSpacing(0)
        
        self.fav_header = QLabel("  FAVORITES")
        self.fav_header.setFixedHeight(30)
        self.fav_header.setMinimumWidth(0) # v9.2 コラプス時に邪魔しないように
        self.fav_header.setStyleSheet("background: #252526; color: #007acc; font-weight: bold; font-size: 10px; border-top: 1px solid #333; border-bottom: 1px solid #333;")
        fav_layout.addWidget(self.fav_header)
        
        self.fav_list = DragDropListWidget(self)
        self.fav_list.setObjectName("FavList")
        self.fav_list.setFrameStyle(QFrame.NoFrame)
        self.fav_list.setStyleSheet("""
            QListWidget { background: transparent; color: #bbb; outline: none; padding: 5px; }
            QListWidget::item { height: 25px; padding-left: 10px; border-radius: 4px; }
            QListWidget::item:selected { background-color: #094771; color: white; }
            QListWidget::item:hover { background-color: #2a2d2e; }
        """)
        self.fav_list.itemClicked.connect(self.on_fav_clicked)
        self.fav_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.fav_list.customContextMenuRequested.connect(self.open_fav_menu)
        fav_layout.addWidget(self.fav_list)
        self.fav_list.installEventFilter(self) # v6.8
        
        self.main_splitter.addWidget(fav_container)
        layout.addWidget(self.main_splitter)
        
        # 初期サイズ
        self.main_splitter.setSizes([600, 300])
        self.load_favorites()

    def eventFilter(self, watched, event):
        # v6.8 子要素（ツリーやリスト）へのホバーも拾う
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Enter:
            if not (QApplication.keyboardModifiers() & Qt.ControlModifier):
                if self.parent_filer:
                    self.parent_filer.set_active_pane(None)
                self.set_active(True)
        return super().eventFilter(watched, event)

    def enterEvent(self, event):
        # v6.7 Ctrlキーが押されている間はホバーによるアクティブ化をロックする（FilePaneと同様）
        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            return

        # サイドバー（お気に入り）のアクティブ化
        if self.parent_filer:
            self.parent_filer.set_active_pane(None)
        self.set_active(True)
        super().enterEvent(event)

    def load_favorites(self):
        self.fav_list.clear()
        if os.path.exists(self.fav_file):
            try:
                with open(self.fav_file, "r", encoding="utf-8") as f:
                    paths = json.load(f)
                    for p in paths:
                        self.add_fav_item(p)
                self.refresh_item_labels() # v6.11 読み込み後に表示を更新
            except: pass

    def save_favorites(self):
        paths = []
        for i in range(self.fav_list.count()):
            paths.append(self.fav_list.item(i).toolTip())
        try:
            with open(self.fav_file, "w", encoding="utf-8") as f:
                json.dump(paths, f, ensure_ascii=False, indent=2)
        except: pass

    def add_favorite(self, path):
        # 重複チェック
        for i in range(self.fav_list.count()):
            if self.fav_list.item(i).toolTip() == path:
                return
        self.add_fav_item(path)
        self.refresh_item_labels()
        self.save_favorites()

    def add_fav_item(self, path):
        # v6.9 シンプルに追加するだけに。実際のテキスト設定は refresh_item_labels で行う
        item = QListWidgetItem("")
        item.setToolTip(path)
        self.fav_list.addItem(item)

    def refresh_item_labels(self):
        """v6.9 リストの現在の並び順に基づいて、ホットキープレフィックスを再設定する"""
        hotkeys = ["Q", "A", "Z", "W", "S", "X", "E", "D", "C"]
        for i in range(self.fav_list.count()):
            item = self.fav_list.item(i)
            path = item.toolTip()
            name = os.path.basename(path) or path
            prefix = "📁 " if os.path.isdir(path) else "📄 "
            
            hk_prefix = ""
            if i < len(hotkeys):
                hk_prefix = f"[{hotkeys[i].lower()}] "
            
            item.setText(f"{hk_prefix}{prefix}{name}")

    def set_active(self, active):
        """v6.5 お気に入り欄がアクティブな時に色を変えて明示する"""
        self.active_state = active # v6.8
        if active:
            self.fav_header.setStyleSheet("""
                background: #094771; color: #fff; font-weight: bold; font-size: 10px; 
                border-top: 1px solid #007acc; border-bottom: 1px solid #007acc;
            """)
            self.fav_list.setStyleSheet("""
                QListWidget { background: #1a1a1a; color: #fff; outline: none; padding: 5px; border-left: 2px solid #007acc; }
                QListWidget::item { height: 25px; padding-left: 10px; border-radius: 4px; }
                QListWidget::item:selected { background-color: #007acc; color: white; }
                QListWidget::item:hover { background-color: #2a2d2e; }
            """)
        else:
            self.fav_header.setStyleSheet("""
                background: #252526; color: #007acc; font-weight: bold; font-size: 10px; 
                border-top: 1px solid #333; border-bottom: 1px solid #333;
            """)
            self.fav_list.setStyleSheet("""
                QListWidget { background: transparent; color: #bbb; outline: none; padding: 5px; border-left: 2px solid transparent; }
                QListWidget::item { height: 25px; padding-left: 10px; border-radius: 4px; }
                QListWidget::item:selected { background-color: #094771; color: white; }
                QListWidget::item:hover { background-color: #2a2d2e; }
            """)

    def on_fav_clicked(self, item):
        path = item.toolTip()
        if not os.path.exists(path): return
        
        # クリック時にお気に入り欄をアクティブにする
        self.parent_filer.set_active_pane(None) # 他のペインのハイライトをオフ
        self.set_active(True)
        
        if os.path.isdir(path):
            self.parent_filer.reset_flow_from(path)
        else:
            if os.name == 'nt':
                try:
                    import subprocess
                    cwd = os.path.dirname(path) if os.path.isdir(os.path.dirname(path)) else None
                    subprocess.Popen(f'start "" "{path}"', shell=True, cwd=cwd)
                except Exception:
                    pass
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def open_fav_menu(self, pos):
        item = self.fav_list.itemAt(pos)
        if not item: return
        
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; } QMenu::item:selected { background-color: #094771; }")
        remove_act = QAction("Remove from Favorites", self)
        remove_act.triggered.connect(lambda: self.remove_fav_item(item))
        menu.addAction(remove_act)
        menu.exec(self.fav_list.mapToGlobal(pos))

    def remove_fav_item(self, item):
        self.fav_list.takeItem(self.fav_list.row(item))
        self.refresh_item_labels()
        self.save_favorites()

    def on_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path): self.parent_filer.reset_flow_from(path)
