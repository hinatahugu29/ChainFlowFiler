import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Qt
from .flow_lane import FlowLane

class FlowArea(QWidget):
    """
    複数のFlowLaneを垂直に並べて管理するエリア。
    タブの中身として機能する。
    """
    def __init__(self, parent_filer):
        super().__init__()
        self.parent_filer = parent_filer # Main Window
        
        self.lanes = [] # 複数のFlowLaneを管理
        self.active_lane = None # このエリア内で最後にアクティブになったレーン
        self.marked_paths = set() # v7.2 Alt+Clickでマークされたパス（このタブ内で共有）
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        
        self.vertical_splitter = QSplitter(Qt.Vertical)
        self.vertical_splitter.setObjectName("VerticalFlowSplitter")
        self.vertical_splitter.setHandleWidth(4)
        self.vertical_splitter.setStyleSheet("QSplitter::handle { background: #111; border-top: 1px solid #222; border-bottom: 1px solid #222; } QSplitter::handle:hover { background: #007acc; }")
        
        self.layout.addWidget(self.vertical_splitter)
        
        # 初期レーン追加
        self.init_default_lane()

    def init_default_lane(self):
        # 最初のレーンを追加してホームを表示
        self.add_lane()
        self.lanes[0].display_path_in_first_pane(os.path.abspath("."))

    def add_lane(self):
        lane = FlowLane(self.parent_filer, self)
        self.lanes.append(lane)
        self.vertical_splitter.addWidget(lane)
        self.active_lane = lane
        return lane

    def split_lane_vertically(self):
        """
        現在のコンテキスト（ホバー中のパスやアクティブレーン）に基づいて
        新しいレーンを垂直分割で追加する
        """
        start_path = os.path.abspath(".")
        
        # 親Filerが知っている「ホバー中のペイン」があればそれを優先
        hovered = self.parent_filer.hovered_pane
        # ホバー中のペインがこのエリアに属しているか確認が必要だが、
        # タブが表示されている=アクティブなら概ね合っている。
        # 厳密には parent_lane を辿ればわかる。
        
        is_hovered_in_this_area = False
        if hovered and hasattr(hovered, 'parent_lane'):
            if hovered.parent_lane in self.lanes:
                is_hovered_in_this_area = True

        if is_hovered_in_this_area and hovered.current_paths:
             start_path = hovered.current_paths[0]
        elif self.active_lane and self.active_lane.panes and self.active_lane.panes[0].current_paths:
             start_path = self.active_lane.panes[0].current_paths[0]
        
        new_lane = self.add_lane()
        new_lane.display_path_in_first_pane(start_path)

    def reset_flow_from(self, path):
        """指定パスでフローをリセット（お気に入りジャンプ等）"""
        target_lane = self.active_lane
        if not target_lane and self.lanes:
            target_lane = self.lanes[0]
            
        if target_lane:
            target_lane.display_path_in_first_pane(path)
            self.active_lane = target_lane
            
    def remove_lane(self, lane):
        if lane in self.lanes:
            self.lanes.remove(lane)
            lane.deleteLater()
            # アクティブレーンの更新
            if self.lanes:
                self.active_lane = self.lanes[-1]
            else:
                self.active_lane = None

    def get_state(self):
        """エリア（タブ）の状態を取得"""
        lanes_state = []
        for lane in self.lanes:
            lanes_state.append(lane.get_state())
            
        active_idx = -1
        if self.active_lane in self.lanes:
            active_idx = self.lanes.index(self.active_lane)
            
        return {
            "lanes": lanes_state,
            "active_lane_index": active_idx
        }

    def restore_state(self, state):
        """エリアの状態を復元"""
        # 既存レーンクリア（初期レーン以外削除）
        while len(self.lanes) > 1:
            l = self.lanes.pop()
            l.deleteLater()
            
        lanes_data = state.get("lanes", [])
        if not lanes_data: return
        
        # 1つ目のレーン
        if self.lanes:
            self.lanes[0].restore_state(lanes_data[0])
            
        # 2つ目以降
        for l_data in lanes_data[1:]:
            new_lane = self.add_lane()
            new_lane.restore_state(l_data)
            
        # アクティブレーン復元
        active_idx = state.get("active_lane_index", -1)
        if 0 <= active_idx < len(self.lanes):
            self.active_lane = self.lanes[active_idx]
            # 視覚的ハイライト更新のために本当はFilePaneのアップデートが必要だが、
            # マウスオーバーで更新されるので一旦よしとする
            
    def duplicate(self):
        """現在のタブの状態をコピーして新しいエリアを返す"""
        state = self.get_state()
        new_area = FlowArea(self.parent_filer)
        new_area.restore_state(state)
        return new_area
