import os
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class PreviewPane(QFrame):
    def __init__(self, parent_filer=None):
        super().__init__()
        self.parent_filer = parent_filer
        self.setMinimumWidth(200) # 最小幅を設定
        self.setObjectName("PreviewArea")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("  QUICK PREVIEW")
        self.label.setFixedHeight(30)
        self.label.setStyleSheet("background: #252526; color: #007acc; font-weight: bold; font-size: 10px; border-bottom: 1px solid #333;")
        layout.addWidget(self.label)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.hide()
        layout.addWidget(self.image_label)
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.hide()
        layout.addWidget(self.text_preview)
        layout.addStretch()
    
    def show_preview(self, path):
        self.image_label.hide()
        self.text_preview.hide()
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            pix = QPixmap(path)
            if not pix.isNull():
                self.image_label.setPixmap(pix.scaled(330, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.image_label.show()
        else:
            try:
                content = ""
                for enc in ['utf-8', 'shift-jis', 'latin-1']:
                    try:
                        with open(path, 'r', encoding=enc) as f:
                            content = f.read(5000)
                            break
                    except: continue
                if content:
                    self.text_preview.setPlainText(content)
                    self.text_preview.show()
            except: pass
