from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt
from .file_pane import FilePane

class FlowLane(QWidget):
    """
    1つの水平方向のフロー（Chain）を管理するクラス
    複数のFilePaneを横に並べる責任を持つ
    """
    def __init__(self, parent_filer, parent_area):
        super().__init__()
        self.parent_filer = parent_filer # Main Window
        self.parent_area = parent_area   # FlowArea (Tab Content)
        self.panes = []
        
        # レイアウト
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        
        # 横方向のスプリッター
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setObjectName("LaneSplitter")
        self.splitter.setChildrenCollapsible(False) # ドラッグで消えないようにする
        self.layout.addWidget(self.splitter)
        
        # 初期ペイン追加
        self.add_pane()
        
    def add_pane(self):
        title = f"FLOW {len(self.panes)}"
        pane = FilePane(title, self.parent_filer) # parent_filerはMain Window
        pane.parent_lane = self # 自身（Lane）への参照を持たせる
        self.panes.append(pane)
        self.splitter.addWidget(pane)
        
        # 追加されたペインにストレッチを割り当て（既存のペインと均等に）
        for i in range(len(self.panes)):
            self.splitter.setStretchFactor(i, 1)
            
        return pane

    def remove_pane(self, pane):
        if pane in self.panes:
            # ペインが複数あるなら、単にペインを消す
            if len(self.panes) > 1:
                self.panes.remove(pane)
                pane.deleteLater()
                
                # Update stretch
                for i in range(len(self.panes)):
                    self.splitter.setStretchFactor(i, 1)

            # ペインがこれ1つしかないなら、レーンごと消すことを試みる
            else:
                if self.parent_area and len(self.parent_area.lanes) > 1:
                    self.parent_area.remove_lane(self)
            
    def display_path_in_first_pane(self, path):
        if self.panes:
            self.panes[0].display_folders([path])
            # 以降のペインはクリア
            for i in range(1, len(self.panes)):
                self.panes[i].display_folders([])

    def update_downstream(self, source_pane, paths):
        if source_pane not in self.panes: return
        idx = self.panes.index(source_pane)
        
        # 次のペインが必要なら作る
        if idx + 1 >= len(self.panes):
            self.add_pane()
            
        # 次のペインに表示
        # 次のペインに表示
        if idx + 1 < len(self.panes):
            next_pane = self.panes[idx+1]
            next_pane.display_folders(paths)
            
            # v9.1: 次のペイン(next_pane)が更新された結果、
            # もし「選択状態」が維持されているなら、さらにその先も更新を試みる。
            # 選択が消えているならクリアする。
            
            # next_pane は display_folders 実行中に on_selection_changed を発火しないかもしれない
            # (Selectionが維持されているだけなのでSignalが出ない可能性がある)
            # なので、明示的に現在の選択状態を確認する。
            
            # 少しWaitを入れないとViewの再構築が終わっていない可能性があるが、
            # display_foldersは同期的。
            
            # FilePane側で「選択中のパス」を取得するメソッドを活用する
            # ただし、FilePane.get_selection_info や get_current_selected_path は
            # 「ユーザーが最後にクリックしたもの」や「フォーカス」を見ている場合がある。
            # 自動復元された selection を取るには、selectionModelを舐めるのが確実。
            
            # display_folders内部で last_selected_paths が更新・維持されているはず。
            maintained_selection = next_pane.last_selected_paths
            
            if maintained_selection:
                # 再帰的に更新
                # しかしここから直接 update_downstream を呼ぶと無限再帰のリスクはなくとも
                # 構造的にややこしいので、ループで処理するか再帰呼び出しするか。
                # ここではシンプルに再帰的に呼び出す。
                self.update_downstream(next_pane, maintained_selection)
            else:
                # 選択がなくなったので、それ以降はクリア
                for i in range(idx + 2, len(self.panes)):
                    self.panes[i].display_folders([])

    def get_state(self):
        """レーン内の全ペインの状態を取得"""
        panes_state = []
        for pane in self.panes:
            panes_state.append(pane.get_state())
        return {"panes": panes_state}

    def restore_state(self, state):
        """レーンの状態を復元"""
        # 既存ペインを一旦クリア（初期ペイン以外削除、あるいは全削除して作り直す）
        # 簡単のため、初期ペイン1つにしてから調整する
        while len(self.panes) > 1:
            p = self.panes.pop()
            p.deleteLater()
        
        panes_data = state.get("panes", [])
        if not panes_data: return
        
        # 1つ目のペイン
        if self.panes:
            self.panes[0].restore_state(panes_data[0])
            
        # 2つ目以降
        for p_data in panes_data[1:]:
            new_pane = self.add_pane()
            new_pane.restore_state(p_data)
