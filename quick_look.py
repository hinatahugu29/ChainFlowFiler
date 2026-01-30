
import os
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout,
                               QScrollArea, QSizePolicy, QApplication, QGraphicsOpacityEffect, QPushButton)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PySide6.QtGui import QPixmap, QImage, QFont, QColor, QPalette, QKeyEvent

class QuickLookWindow(QWidget):
    def __init__(self, parent=None):
        # WindowStaysOnTopHint: 常に最前面
        # WindowDoesNotAcceptFocus: フォーカスを奪わない（リスト操作を継続できる）
        flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus
        super().__init__(parent, flags) 
        
        self.setWindowTitle("Quick Look")
        self.resize(800, 600)
        
        # Debug Logger
        self.debug_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "quicklook_debug.log")
        self.log("Initialized")
        
        self.setup_ui()
        
    def log(self, message):
        try:
            with open(self.debug_log_path, "a", encoding="utf-8") as f:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except: pass

    def setup_ui(self):
        # 背景を半透明の黒っぽくする（ガラス効果風）
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # メインレイアウト（角丸のコンテナを作る）
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QWidget()
        self.container.setObjectName("Container")
        self.container.setStyleSheet("""
            QWidget#Container {
                background-color: rgba(30, 30, 30, 0.95);
                border: 1px solid #454545;
                border-radius: 12px;
            }
            QLabel { color: #ddd; }
        """)
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(1, 1, 1, 1) # コンテンツはギリギリまで
        self.container_layout.setSpacing(0)
        
        # ヘッダー（ファイル名表示）
        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(40)
        self.header_widget.setStyleSheet("""
            background-color: transparent;
            border-bottom: 1px solid #454545;
        """)
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        self.header_label = QLabel("FileName.txt")
        self.header_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px; border: none;")
        
        self.copy_btn = QPushButton("Copy Content")
        self.copy_btn.setFixedSize(100, 24)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #ccc;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #444;
                color: #fff;
                border-color: #666;
            }
        """)
        self.copy_btn.clicked.connect(self.copy_content)
        self.copy_btn.hide() # 初期状態は隠す（テキスト系のみ表示）

        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.copy_btn)
        
        self.container_layout.addWidget(self.header_widget)

        # コンテンツエリア
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0,0,0,0)
        
        # 各種ビューア
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.hide()
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        self.text_edit.hide()
        
        self.info_label = QLabel() # 非対応ファイル用
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 14px; color: #888;")
        self.info_label.hide()
        
        self.content_layout.addWidget(self.image_label)
        self.content_layout.addWidget(self.text_edit)
        self.content_layout.addWidget(self.info_label)
        
        self.container_layout.addWidget(self.content_area)
        self.main_layout.addWidget(self.container)
        
        # アニメーション用
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(150) # 高速に
        self.anim.setEasingCurve(QEasingCurve.OutQuad)

    def show_file(self, path):
        self.log(f"show_file: {path}")
        if not path or not os.path.exists(path):
            self.log("Path not found/empty")
            return
            
        try:
            self.header_label.setText(os.path.basename(path))
            
            # リセット
            self.image_label.hide()
            self.text_edit.hide()
            self.info_label.hide()
            self.copy_btn.hide()
            
            # フォルダの場合
            if os.path.isdir(path):
                self.log("Type: Folder")
                try:
                    items = len(os.listdir(path))
                    self.show_info(f"📁 Folder\n\nContains {items} items.")
                except:
                    self.show_info("📁 Folder\n\n(Access Denied)")
                return

            ext = os.path.splitext(path)[1].lower()
            self.log(f"Type: File ({ext})")
            
            # 画像
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.svg']:
                self._current_pixmap = QPixmap(path)
                if not self._current_pixmap.isNull():
                    view_w = self.width() - 40
                    view_h = self.height() - 80
                    scaled_pix = self._current_pixmap.scaled(view_w, view_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pix)
                    self.image_label.show()
                    self.copy_btn.show() # 画像表示時もコピーボタン有効
                    return

            # テキスト / コード
            # v7.6 .ahk support added
            text_exts = ['.txt', '.md', '.py', '.json', '.js', '.html', '.css', '.csv', '.xml', '.yaml', '.yml', '.ini', '.log', '.bat', '.sh', '.cpp', '.h', '.java', '.ahk']
            if ext in text_exts:
                try:
                    content = ""
                    for enc in ['utf-8', 'shift-jis', 'latin-1']:
                        try:
                            with open(path, 'r', encoding=enc) as f:
                                content = f.read(10000)
                            break
                        except: continue
                    
                    if content:
                        self.text_edit.setPlainText(content)
                        self.text_edit.show()
                        self.copy_btn.show() # テキスト表示時はコピーボタン有効
                    else:
                        self.show_info("Empty or unreadable text file.")
                    return
                except Exception as e:
                    self.log(f"Text read error: {e}")
                    self.show_info(f"Error reading file:\n{e}")
                    return
            
            # その他 (PDFなど非対応ファイル)
            size_str = "Unknown size"
            try:
                # PermissionErrorなどで落ちないように
                size_str = f"{os.path.getsize(path):,} bytes"
            except Exception as e:
                self.log(f"Getsize error: {e}")
                size_str = f"Error getting size: {e}"
            
            self.show_info(f"Preview not available for '{ext}' files.\n\nSize: {size_str}")

        except Exception as e:
            # 最悪のケース
            self.log(f"CRITICAL ERROR in show_file: {e}")
            print(f"QuickLook Error: {e}", file=sys.stderr)
            self.show_info(f"System Error:\n{str(e)}")

    def copy_content(self):
        """現在表示中のコンテンツをクリップボードにコピー"""
        feedback = False
        
        # テキストの場合
        if self.text_edit.isVisible():
            QApplication.clipboard().setText(self.text_edit.toPlainText())
            feedback = True
            
        # 画像の場合
        elif self.image_label.isVisible() and hasattr(self, '_current_pixmap') and not self._current_pixmap.isNull():
            QApplication.clipboard().setPixmap(self._current_pixmap)
            feedback = True

        if feedback:
            # フィードバック
            orig_text = self.copy_btn.text()
            self.copy_btn.setText("Copied!")
            QTimer.singleShot(1000, lambda: self.copy_btn.setText(orig_text))

    def show_info(self, text):
        self.log(f"Show Info: {text.replace(chr(10), ' ')}")
        self.info_label.setText(text)
        self.info_label.show()

    def popup(self, center_pos=None):
        """アニメーション付きで表示"""
        if self.isVisible() and self.anim.state() == QPropertyAnimation.Running and self.anim.endValue() == 1:
            return

        self.log("popup")
        try:
            self.anim.finished.disconnect()
        except Exception:
            pass

        if center_pos:
            # ウィンドウの中心を指定位置に合わせる
            geo = self.geometry()
            geo.moveCenter(center_pos)
            self.setGeometry(geo)
            
        self.show()
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(1)
        self.anim.start()

    def fade_out(self):
        """アニメーション付きで非表示（終了後にhide）"""
        if not self.isVisible() or self.anim.state() == QPropertyAnimation.Running and self.anim.endValue() == 0:
            return
            
        self.log("fade_out")
        try:
            self.anim.finished.disconnect()
        except Exception:
            pass
        
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(0)
        self.anim.finished.connect(self.hide)
        self.anim.start()

    def keyPressEvent(self, event):
        # QuickLook自体にフォーカスがある場合、SpaceやEscで閉じる
        if event.key() == Qt.Key_Space or event.key() == Qt.Key_Escape:
            self.fade_out()
        else:
            super().keyPressEvent(event)
