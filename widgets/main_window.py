import os
import sys
import json
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
                               QTabWidget, QTabBar, QApplication, QMenu, QInputDialog, QLineEdit)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QIcon

from .navigation_pane import NavigationPane
from .quick_look import QuickLookWindow
from .flow_area import FlowArea

class ChainFlowFiler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChainFlow Filer v12.0 (Alpha)")
        self.resize(1800, 950)
        
        # --- Dark Title Bar for Windows (v9.2) ---
        try:
            import ctypes
            from ctypes import wintypes
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            # Set the attribute to enable dark title bar
            hwnd = int(self.winId())
            value = ctypes.c_int(2) # 2 = Always Dark
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass
        # ----------------------------------------

        # --- v6.11 Icon Settings ---
        icon_path = ""
        # 1. PyInstallerバンドル内（一時フォルダ）のリソースを探す
        if getattr(sys, 'frozen', False):
            # sys._MEIPASS はPyInstallerが一時的にファイルを展開する場所
            bundle_dir = sys._MEIPASS
            icon_path = os.path.join(bundle_dir, "app_icon.ico")
        else:
            # 2. 通常実行時はスクリプトと同じディレクトリを探す
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_icon.ico")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        # ---------------------------
        
        self.hovered_pane = None
        self.internal_clipboard = {"paths": [], "mode": "copy"} # v6.2 一括操作用
        
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Address Bar Area
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setContentsMargins(5, 5, 5, 5)
        self.toolbar_layout.setSpacing(5)
        
        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText("Enter path here...")
        self.address_bar.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #ccc;
                border: 1px solid #555;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border-color: #007acc;
                color: #fff;
            }
        """)
        self.address_bar.returnPressed.connect(self.on_address_return)
        self.toolbar_layout.addWidget(self.address_bar)
        
        self.main_layout.addLayout(self.toolbar_layout)
        
        self.main_splitter = QSplitter(Qt.Horizontal)
        # self.main_splitter.setChildrenCollapsible(False) # 従来
        self.main_splitter.setChildrenCollapsible(True) # v9.2 サイドバーを完全に消せるようにする
        self.main_layout.addWidget(self.main_splitter)
        
        # 左：ナビゲーション
        self.nav = NavigationPane(self)
        self.main_splitter.addWidget(self.nav)
        
        # 中央：タブ付きフロー領域
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        # タブバーのスタイルなど適宜調整
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab { background: #2d2d2d; color: #ccc; padding: 5px 10px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #1e1e1e; color: #fff; font-weight: bold; }
            QTabBar::tab:hover { background: #3e3e3e; }
        """)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        self.main_splitter.addWidget(self.tab_widget)

        # QuickLook (Hidden by default)
        self.quick_look = QuickLookWindow(self)
        
        # 初期タブ追加
        self.add_new_tab()
        
        # 全体の初期レイアウト比率を設定 (サイドバー, フローエリア)
        self.main_splitter.setSizes([240, 1550])
        
        self.setup_shortcuts()
        self.apply_theme()
        
        # タブバーの拡張
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_tab)
        self.tab_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.show_tab_context_menu)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # セッション復元 (v6.10 Portable対応: 実行ファイルと同階層に保存)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        self.session_file = os.path.join(base_dir, "session.json")
        self.load_session()

    def closeEvent(self, event):
        self.save_session()
        super().closeEvent(event)

    def load_session(self):
        if not os.path.exists(self.session_file): return
        
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                session = json.load(f)
                
            # Geometry
            if "geometry" in session:
                self.restoreGeometry(bytes.fromhex(session["geometry"]))
                
            # Splitter State
            if "splitter_state" in session:
                self.main_splitter.restoreState(bytes.fromhex(session["splitter_state"]))
            
            # Tabs
            tabs_data = session.get("tabs", [])
            if not tabs_data: return
            
            # 既存タブをクリア（初期タブがあれば）
            while self.tab_widget.count() > 0:
                widget = self.tab_widget.widget(0)
                self.tab_widget.removeTab(0)
                if widget: widget.deleteLater()
                
            for t_data in tabs_data:
                area = FlowArea(self)
                title = t_data.get("title", "Workspace")
                idx = self.tab_widget.addTab(area, title)
                area.restore_state(t_data.get("state", {}))
                
            active_tab = session.get("active_tab_index", 0)
            if 0 <= active_tab < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(active_tab)
                
        except Exception as e:
            print(f"Failed to load session: {e}", file=sys.stderr)
            # エラー時はデフォルトのタブを一つ追加しておく
            if self.tab_widget.count() == 0:
                self.add_new_tab()

    def save_session(self):
        session = {}
        
        # Geometry
        session["geometry"] = self.saveGeometry().toHex().data().decode()
        
        # Splitter
        session["splitter_state"] = self.main_splitter.saveState().toHex().data().decode()
        
        # Tabs
        tabs_data = []
        for i in range(self.tab_widget.count()):
            area = self.tab_widget.widget(i)
            if isinstance(area, FlowArea):
                tabs_data.append({
                    "title": self.tab_widget.tabText(i),
                    "state": area.get_state()
                })
        session["tabs"] = tabs_data
        session["active_tab_index"] = self.tab_widget.currentIndex()
        
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save session: {e}", file=sys.stderr)

    def show_tab_context_menu(self, pos):
        idx = self.tab_widget.tabBar().tabAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; } QMenu::item:selected { background-color: #094771; }")
        
        # Actions
        new_tab_act = QAction("New Tab", self)
        new_tab_act.triggered.connect(self.add_new_tab)
        menu.addAction(new_tab_act)
        
        if idx >= 0:
            dup_act = QAction("Duplicate Tab", self)
            dup_act.triggered.connect(lambda: self.duplicate_tab(idx))
            
            rename_act = QAction("Rename Tab", self)
            rename_act.triggered.connect(lambda: self.rename_tab(idx))
            
            close_act = QAction("Close Tab", self)
            close_act.triggered.connect(lambda: self.close_tab(idx))
            
            menu.addSeparator()
            menu.addAction(dup_act)
            menu.addAction(rename_act)
            menu.addSeparator()
            menu.addAction(close_act)
            
        menu.exec(self.tab_widget.mapToGlobal(pos))

    def rename_tab(self, index):
        if index < 0: return
        current_name = self.tab_widget.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Rename Tab", "Tab Name:", text=current_name)
        if ok and new_name:
            self.tab_widget.setTabText(index, new_name)

    def duplicate_tab(self, index):
        if index < 0: return
        source_area = self.tab_widget.widget(index)
        if isinstance(source_area, FlowArea):
            new_area = source_area.duplicate()
            current_name = self.tab_widget.tabText(index)
            new_idx = self.tab_widget.addTab(new_area, f"{current_name} (Copy)")
            self.tab_widget.setCurrentIndex(new_idx)

    def set_active_pane(self, pane):
        """v6.4 最後にホバーしたペインを永続的にハイライトする管理メソッド"""
        if self.hovered_pane == pane:
            return
            
        # 以前のアクティブペインのハイライトをオフにする
        if self.hovered_pane:
            try:
                self.hovered_pane.highlight(False)
            except RuntimeError: # 削除済みの場合
                pass

        # サイドバーのアクティブ表示もオフにする
        if hasattr(self, 'nav'):
            self.nav.set_active(False)
                
        # 新しいアクティブペインをセットしてハイライト
        self.hovered_pane = pane
        if self.hovered_pane:
            self.hovered_pane.highlight(True)

    def setup_shortcuts(self):
        # --- ペイン基本操作 ---
        QShortcut(QKeySequence("N"), self).activated.connect(self.add_pane_to_hovered_lane)
        QShortcut(QKeySequence("Backspace"), self).activated.connect(self.go_up_hovered)
        QShortcut(QKeySequence("F"), self).activated.connect(self.toggle_favorites_focus)
        QShortcut(QKeySequence("."), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.toggle_hidden()))
        QShortcut(QKeySequence("V"), self).activated.connect(self.split_lane_vertically)
        
        # --- QuickLook / Global ---
        QShortcut(QKeySequence("Space"), self).activated.connect(self.toggle_quick_look)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close_quick_look)

        # --- v6.7 統合ショートカット・ディスパッチャ (Q,A,Z,W,S,X,E,D,C) ---
        # これらは「お気に入り欄にフォーカスがあるか」で挙動が変わる
        self.hk_map = {"Q":0, "A":1, "Z":2, "W":3, "S":4, "X":5, "E":6, "D":7, "C":8}
        for key in self.hk_map:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda k=key: self.dispatch_shortcut(k))

        # --- 標準ファイル操作 (v6.2) ---
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.action_copy()))
        QShortcut(QKeySequence("Ctrl+X"), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.action_cut()))
        QShortcut(QKeySequence("Ctrl+V"), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.action_paste()))
        QShortcut(QKeySequence("Delete"), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.action_delete()))
        QShortcut(QKeySequence("F2"), self).activated.connect(lambda: self.run_on_hovered(lambda p: p.action_rename()))
        
        # v10.1 Shift+W: ペイン内のビュー分割を減らす（末尾削除）
        QShortcut(QKeySequence("Shift+W"), self).activated.connect(self.remove_hovered_view)

        # --- タブ・基本システム ---
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.add_new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close_current_tab)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self.focus_address_bar)
        QShortcut(QKeySequence("Alt+D"), self).activated.connect(self.focus_address_bar)
        
        # --- v9.2 サイドバー開閉 ---
        QShortcut(QKeySequence("Ctrl+B"), self).activated.connect(self.toggle_sidebar)

    @property
    def current_flow_area(self) -> FlowArea:
        w = self.tab_widget.currentWidget()
        if isinstance(w, FlowArea):
            return w
        return None

    def add_new_tab(self):
        new_area = FlowArea(self)
        idx = self.tab_widget.addTab(new_area, f"Workspace {self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentIndex(idx)

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            widget = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            widget.deleteLater()

    def close_current_tab(self):
        self.close_tab(self.tab_widget.currentIndex())
    
    def remove_hovered_view(self):
        """Shift+W: ホバー中のペインの一番下のビューを削除"""
        if self.hovered_pane:
            self.hovered_pane.pop_active_view()

    def on_tab_changed(self, index):
        area = self.tab_widget.widget(index)
        if isinstance(area, FlowArea):
            lane = area.active_lane
            if lane and lane.panes and lane.panes[0].current_paths:
                self.update_address_bar(lane.panes[0].current_paths[0])

    def apply_theme(self):
        # VSCode Dark-like Theme
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #cccccc; }
            QWidget { font-family: 'Segoe UI', sans-serif; font-size: 10pt; }
            QTreeView { 
                background-color: #1e1e1e; color: #cccccc; border: none; 
                selection-background-color: #094771; selection-color: #ffffff;
            }
            QTreeView::item:hover { background-color: #2a2d2e; }
            QTreeView::item:selected:active { background-color: #094771; }
            QTreeView::item:selected:!active { background-color: #37373d; }
            QHeaderView::section { background-color: #252526; color: #cccccc; border: none; padding: 4px; }
            
            QSplitter::handle { background-color: #333333; }
            QSplitter::handle:item:hover { background-color: #007acc; }

            /* 縦並びレーン間のスプリッター（通常色へ戻す） */
            QSplitter#VerticalFlowSplitter::handle { height: 4px; background: #111; border-top: 1px solid #222; border-bottom: 1px solid #222; }
            QSplitter#VerticalFlowSplitter::handle:hover { background: #333; }

            /* ScrollBar customization: Accent Rounded */
            QScrollBar:vertical {
                border: 1px solid #333;
                background: #252525;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #153b93;
                min-height: 30px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3a62bd;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QScrollBar:horizontal {
                border: 1px solid #333;
                background: #252525;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #153b93;
                min-width: 30px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #3a62bd;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }

            QMenu { background-color: #252526; color: #ccc; border: 1px solid #333; }
            QMenu::item:selected { background-color: #094771; }
        """)

    # --- Delegated Actions ---
    
    def run_on_hovered(self, func):
        if self.hovered_pane:
            func(self.hovered_pane)

    def add_pane_to_hovered_lane(self):
        if self.hovered_pane and hasattr(self.hovered_pane, 'parent_lane'):
            self.hovered_pane.parent_lane.add_pane()
        elif self.current_flow_area and self.current_flow_area.active_lane:
            self.current_flow_area.active_lane.add_pane()

    def remove_hovered_pane(self):
        if self.hovered_pane and hasattr(self.hovered_pane, 'parent_lane'):
            self.hovered_pane.parent_lane.remove_pane(self.hovered_pane)

    def go_up_hovered(self):
        if self.hovered_pane:
            self.hovered_pane.go_up()

    def split_lane_vertically(self):
        if self.current_flow_area:
            self.current_flow_area.split_lane_vertically()

    def reset_flow_from(self, path):
        # ナビゲーションからのリセット。現在のタブに対して適用
        if self.current_flow_area:
            self.current_flow_area.reset_flow_from(path)
        else:
            # タブがない場合は作る（基本ありえないが）
            self.add_new_tab()
            self.current_flow_area.reset_flow_from(path)

    def update_downstream(self, source_pane, paths):
        # ソースペインが属するレーンに委譲
        if hasattr(source_pane, 'parent_lane'):
            source_pane.parent_lane.update_downstream(source_pane, paths)

    def update_preview(self, path):
        try:
            # QuickLookが表示中なら内容を更新する
            if self.quick_look and self.quick_look.isVisible():
                self.quick_look.show_file(path)
        except Exception as e:
            print(f"Error in update_preview: {e}", file=sys.stderr)
            
    def toggle_quick_look(self):
        # 表示中なら閉じる
        if self.quick_look.isVisible():
            self.quick_look.fade_out()
            return

        # ホバー中のペインを取得
        target_pane = self.hovered_pane
        if not target_pane and self.current_flow_area and self.current_flow_area.active_lane:
             panes = self.current_flow_area.active_lane.panes
             if panes: target_pane = panes[-1]
        
        if target_pane:
            path = target_pane.get_current_selected_path()
            if path:
                self.quick_look.show_file(path)
                self.quick_look.popup(self.geometry().center())

    def close_quick_look(self):
        if self.quick_look.isVisible():
            self.quick_look.fade_out()
        else:
            # Escは通常通りフォーカス外しなどとして機能させるためにイベントを無視しない
            # ただし、Shortcutとして登録されているのでEscを押すとここに来る。
            # 他にEscを使いたい場所（FilePaneのクリア検索など）との兼ね合いがある。
            pass


    def add_to_favorites(self, path):
        self.nav.add_favorite(path)

    # --- Address Bar Actions ---

    def toggle_favorites_focus(self):
        """v6.5 Fキーでお気に入り欄とペインのフォーカスを行き来する"""
        fav_list = self.nav.fav_list
        if fav_list.hasFocus():
            self.nav.set_active(False)
            if self.hovered_pane:
                info = self.hovered_pane.get_selection_info()
                if info["view"]:
                    info["view"].setFocus()
        else:
            # 他のペインのハイライトをオフにする（自分をアクティブにする前に）
            if self.hovered_pane:
                self.hovered_pane.highlight(False)
            
            self.nav.set_active(True)
            fav_list.setFocus()
            if fav_list.count() > 0 and not fav_list.currentItem():
                fav_list.setCurrentRow(0)

    def handle_favorites_hotkey(self, index):
        """v6.6 お気に入り欄フォーカス時のクイックジャンプ"""
        if index < self.nav.fav_list.count():
            item = self.nav.fav_list.item(index)
            if item:
                self.nav.on_fav_clicked(item)

    def dispatch_shortcut(self, key):
        """v6.7 お気に入り欄と通常の動作を振り分ける中央ディスパッチャ"""
        # v6.8 お気に入り欄がアクティブ（ホバー含む）な場合
        if self.nav.active_state:
            idx = self.hk_map.get(key)
            if idx is not None:
                self.handle_favorites_hotkey(idx)
        else:
            # 通常（ペイン操作）時
            if key == "Q": self.go_up_hovered()
            elif key == "W": self.remove_hovered_pane()
            elif key == "A": self.run_on_hovered(lambda p: p.toggle_sort(0))
            elif key == "S": self.run_on_hovered(lambda p: p.toggle_sort(2))
            elif key == "Z": self.run_on_hovered(lambda p: p.toggle_sort(3))
            elif key == "D": self.run_on_hovered(lambda p: p.cycle_display_mode())
            elif key == "C": self.run_on_hovered(lambda p: p.toggle_compact())
            # X, E は現在はグローバルアクションなし

    def focus_address_bar(self):
        if self.address_bar.hasFocus():
            # アドレスバーにフォーカスがある場合は最後に触れたペインへ戻す
            if self.hovered_pane:
                info = self.hovered_pane.get_selection_info()
                if info["view"]:
                    info["view"].setFocus()
        else:
            self.address_bar.setFocus()
            self.address_bar.selectAll()

    def on_address_return(self):
        path = self.address_bar.text().strip()
        if path and os.path.exists(path):
            self.reset_flow_from(path)
            self.tab_widget.currentWidget().setFocus() # フォーカスを戻す
        elif path:
             # パスが無効な場合は通知（簡易的に）
             self.address_bar.setStyleSheet(self.address_bar.styleSheet() + "QLineEdit { border-color: #f44; }")

    def update_address_bar(self, path):
        if not self.address_bar.hasFocus():
            # ユーザーが入力中でなければ更新する
            self.address_bar.setText(path)
            # エラースタイルを戻す
            self.address_bar.setStyleSheet("""
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #ccc;
                    border: 1px solid #555;
                    padding: 4px 10px;
                    border-radius: 4px;
                }
                QLineEdit:focus {
                    border-color: #007acc;
                    color: #fff;
                }
            """)

    def toggle_sidebar(self):
        """v9.2 サイドバーの表示・非表示を切り替える"""
        # 単純に幅0にするだけだとハンドルや最小幅の影響でゴミが残ることがあるため、
        # setVisibleを使って完全に消す。
        
        if self.nav.isVisible():
            # 閉じる
            # 現在の幅を保存しておくと親切だが、今回はシンプルに非表示化のみ
            self.nav.setVisible(False)
        else:
            # 開く
            self.nav.setVisible(True)
            
            # もし幅が潰れていたら復活させる
            sizes = self.main_splitter.sizes()
            if sizes and sizes[0] == 0:
                target_w = 120
                current_total = sum(sizes)
                new_sizes = [target_w, current_total - target_w]
                self.main_splitter.setSizes(new_sizes)
