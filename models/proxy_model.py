import os
from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtCore import Qt, QSortFilterProxyModel

class SmartSortFilterProxyModel(QSortFilterProxyModel):
    """
    高度なソートとフィルタリングを提供するProxyモデル
    QFileSystemModelの非同期性やフィルタの癖を吸収し、即時反映を実現する。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        # 階層構造におけるフィルタリングを正しく行うため
        self.setRecursiveFilteringEnabled(True)
        # 0: All, 1: Dirs Only, 2: Files Only
        self._display_mode = 0
        self._show_hidden = False
        self._search_text = ""
        self._target_root_path = ""
        self._marked_paths_ref = None # set() の外部参照

    def setTargetRootPath(self, path):
        self._target_root_path = os.path.abspath(path).lower()
        self.invalidateFilter()

    def setDisplayMode(self, mode):
        self._display_mode = mode
        self.invalidateFilter()

    def setShowHidden(self, show):
        self._show_hidden = show
        self.invalidateFilter()
        
    def setSearchText(self, text):
        self._search_text = text.lower()
        # 標準のフィルタ機能を使って再帰検索を有効にする
        self.setFilterFixedString(text)
        self.invalidateFilter()
        
    def setMarkedPathsRef(self, marked_set):
        """マークされたパスのセット（外部参照）を設定"""
        self._marked_paths_ref = marked_set

    def data(self, index, role=Qt.DisplayRole):
        """見た目のカスタマイズ（マークされた行に色をつける）"""
        if role == Qt.BackgroundRole and self._marked_paths_ref:
            # カラムに関わらず、行全体のパスを確認
            col0_idx = index.siblingAtColumn(0)
            source_idx = self.mapToSource(col0_idx)
            model = self.sourceModel()
            if hasattr(model, 'filePath'):
                path = os.path.abspath(model.filePath(source_idx))
                if path in self._marked_paths_ref:
                    # 落ち着いた深みのある赤 (ワインレッド系)
                    from PySide6.QtGui import QColor
                    return QColor(80, 20, 20)
        
        return super().data(index, role)

    def filterAcceptsRow(self, source_row, source_parent):
        """行を表示するかどうかの判定"""
        # 親クラスの判定（標準の検索フィルタ + Recursive）をまず確認
        if self._search_text:
            if not super().filterAcceptsRow(source_row, source_parent):
                return False
        
        # ここから先は「検索にはヒットしている（またはヒットする子を持つ）」要素に対する
        # 追加のフィルタリング（Dotファイル隠し、モード別表示）
        
        model = self.sourceModel()
        idx = model.index(source_row, 0, source_parent)
        
        if isinstance(model, QFileSystemModel):
            file_info = model.fileInfo(idx)
            name = file_info.fileName()

            # 最適化 v9.1: 重い絶対パス取得とlower()は必要な時まで遅延させる

            # ドットファイルの処理 (.始まりかつ . と .. を除く)
            # これは名前だけで判定できるので先にやる
            if name.startswith('.') and name not in ['.', '..']:
                if not self._show_hidden:
                    return False
            
            # 以下、パス比較が必要な場合の処理
            # ターゲットルート維持確認は、表示除外されそうな時だけで良い。
            
            is_dir = file_info.isDir()
            
            # モードによる弾き判定
            should_hide_by_mode = False
            if self._display_mode == 1: # Dirs Only
                if not is_dir: should_hide_by_mode = True
            elif self._display_mode == 2: # Files Only
                if is_dir: should_hide_by_mode = True

            # 「隠さなくて良い」なら、重いパスチェックをするまでもなく True
            if not should_hide_by_mode:
                return True

            # ここに来る = モード的には隠すべきアイテム（FilesOnlyモードでのフォルダなど）
            # しかし、それがターゲットルートへの道筋なら表示する必要がある。ここで初めてパスを取得する。
            if self._target_root_path:
                file_path = file_info.absoluteFilePath().lower()
                
                # ターゲット自体
                if file_path == self._target_root_path:
                    return True
                # ターゲットの親ディレクトリ群
                if self._target_root_path.startswith(file_path + os.sep) or \
                   (file_path.endswith(os.sep) and self._target_root_path.startswith(file_path)):
                     return True

            # 救済されなかったので隠す
            return False
                
        return True # super()を通過し、ここまでの条件もクリアしたら表示

    def lessThan(self, left, right):
        """ソートロジックの強化"""
        model = self.sourceModel()
        if isinstance(model, QFileSystemModel):
            left_info = model.fileInfo(left)
            right_info = model.fileInfo(right)
            
            # フォルダは常に上位に来るようにする (Explorerライク)
            if left_info.isDir() and not right_info.isDir():
                return self.sortOrder() == Qt.AscendingOrder
            if not left_info.isDir() and right_info.isDir():
                return self.sortOrder() != Qt.AscendingOrder
                
            col = left.column()
            # 3: Date
            if col == 3:
                return left_info.lastModified() < right_info.lastModified()
            # 1: Size
            if col == 1:
                return left_info.size() < right_info.size()
                
        return super().lessThan(left, right)
