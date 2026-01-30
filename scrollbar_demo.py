
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QListWidget, QLabel, QFrame, QScrollBar, QSlider, QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class ScrollBarDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scrollbar Color Tuning Demo (Interactive)")
        self.resize(1000, 600)
        
        # Apply dark theme base
        self.setStyleSheet("background-color: #1e1e1e; color: #ddd;")

        # Main Layout
        self.main_layout = QHBoxLayout(self)
        
        # 1. Lighter Version
        self.lighter_widget = self.create_demo_column("Lighter", "#8ac6f7")
        self.main_layout.addWidget(self.lighter_widget)
        
        # 2. Current Version
        self.current_widget = self.create_demo_column("Current (v8)", "#61afef")
        self.main_layout.addWidget(self.current_widget)
        
        # 3. Darker Version
        self.darker_widget = self.create_demo_column("Darker", "#4a86b8")
        self.main_layout.addWidget(self.darker_widget)

        # 4. Interactive Adjuster
        self.adjuster_container = QFrame()
        self.adjuster_layout = QVBoxLayout(self.adjuster_container)
        
        # 調整用コントロール
        self.control_panel = QWidget()
        self.control_layout = QGridLayout(self.control_panel)
        
        # Sliders
        self.h_slider = self.create_slider("Hue", 0, 360, 210, self.update_custom_color)
        self.s_slider = self.create_slider("Sat", 0, 255, 200, self.update_custom_color)
        self.l_slider = self.create_slider("Light", 0, 255, 170, self.update_custom_color)
        
        # Color Info Label
        self.custom_color_label = QLabel("Custom\n#??????")
        self.custom_color_label.setAlignment(Qt.AlignCenter)
        self.custom_color_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 5px;")
        
        self.adjuster_layout.addWidget(self.custom_color_label)
        self.adjuster_layout.addWidget(self.control_panel)
        
        # Preview List
        self.custom_list = QListWidget()
        for i in range(100):
            self.custom_list.addItem(f"Custom Color Item {i+1}")
        
        # Base List Style
        self.base_list_style = """
            QListWidget {
                background-color: #252526;
                color: #ccc;
                border: 1px solid #333;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                border: 1px solid #333;
                background: #252525;
                width: 14px;
                margin: 0px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """
        self.custom_list.setStyleSheet(self.base_list_style) # 初期状態
        self.adjuster_layout.addWidget(self.custom_list)
        
        self.main_layout.addWidget(self.adjuster_container)
        
        # 初期描画
        self.update_custom_color()

    def create_slider(self, label, mi, ma, val, callback):
        row = self.control_layout.rowCount()
        lbl = QLabel(f"{label}: {val}")
        slider = QSlider(Qt.Horizontal)
        slider.setRange(mi, ma)
        slider.setValue(val)
        slider.valueChanged.connect(lambda v: [lbl.setText(f"{label}: {v}"), callback()])
        
        self.control_layout.addWidget(lbl, row, 0)
        self.control_layout.addWidget(slider, row, 1)
        return slider

    def update_custom_color(self):
        h = self.h_slider.value()
        s = self.s_slider.value()
        l = self.l_slider.value()
        
        color = QColor.fromHsl(h, s, l)
        hex_color = color.name()
        
        self.custom_color_label.setText(f"Custom\n{hex_color}")
        self.custom_color_label.setStyleSheet(f"font-weight: bold; font-size: 16px; margin-bottom: 5px; color: {hex_color}; background-color: #333; padding: 5px; border-radius: 5px;")
        
        # Apply style to custom list
        hover_color = color.lighter(110).name()
        
        style = self.base_list_style + f"""
            QScrollBar::handle:vertical {{
                background: {hex_color};
                min-height: 30px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {hover_color};
            }}
        """
        self.custom_list.setStyleSheet(style)

    def create_demo_column(self, title, base_color):
        container = QFrame()
        layout = QVBoxLayout(container)
        
        # Title & Color Info
        title_label = QLabel(f"{title}\n{base_color}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Dummy List with many items to force scrollbar
        list_widget = QListWidget()
        for i in range(100):
            list_widget.addItem(f"Demo Item {i+1} for {title}")
        
        layout.addWidget(list_widget)
        
        # Apply specific stylesheet to this list widget's scrollbar
        hover_color = self.lighten_color(base_color, 20)
        
        style = f"""
            QListWidget {{
                background-color: #252526;
                color: #ccc;
                border: 1px solid #333;
                border-radius: 4px;
            }}
            QScrollBar:vertical {{
                border: 1px solid #333;
                background: #252525;
                width: 14px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {base_color};
                min-height: 30px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {hover_color};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """
        list_widget.setStyleSheet(style)
        
        return container
    
    def lighten_color(self, hex_color, amount=20):
        # Simple color lighter
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)
        
        return f"#{r:02x}{g:02x}{b:02x}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScrollBarDemo()
    window.show()
    sys.exit(app.exec())
