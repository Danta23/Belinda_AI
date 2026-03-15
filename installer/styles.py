
DARK_STYLE_TEMPLATE = """
QMainWindow {{
    background-color: transparent;
}}

#MainFrame {{
    background-color: rgba(15, 15, 20, 200);
    border: 1px solid rgba(255, 255, 255, 15);
    border-radius: 20px;
}}

#Sidebar {{
    background-color: rgba(25, 25, 30, 150);
    border-right: 1px solid rgba(255, 255, 255, 10);
    border-top-left-radius: 20px;
    border-bottom-left-radius: 20px;
}}

QLabel {{
    color: #E0E0E0;
    font-family: '{font_family}', sans-serif;
    font-size: {font_size}px;
}}

#TitleLabel {{
    font-size: {title_size}px;
    font-weight: bold;
    color: #36BCF7;
}}

QPushButton {{
    background-color: rgba(54, 188, 247, 10);
    border: 1px solid rgba(54, 188, 247, 30);
    border-radius: 12px;
    color: #E0E0E0;
    padding: 10px 20px;
    font-size: {font_size}px;
}}

QPushButton:hover {{
    background-color: rgba(54, 188, 247, 30);
    border: 1px solid rgba(54, 188, 247, 80);
}}

#NavButton {{
    text-align: left;
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 12px;
    font-size: {font_size}px;
    color: #AAAAAA;
}}

#NavButton:hover {{
    background-color: rgba(54, 188, 247, 20);
    color: #36BCF7;
}}

#NavButton[active="true"] {{
    background-color: rgba(54, 188, 247, 40);
    color: #36BCF7;
    border-left: 3px solid #36BCF7;
}}

QLineEdit {{
    background-color: rgba(0, 0, 0, 50);
    border: 1px solid rgba(255, 255, 255, 10);
    border-radius: 6px;
    color: white;
    padding: 8px;
    font-size: {font_size}px;
}}

QProgressBar {{
    border: none;
    background-color: rgba(255, 255, 255, 10);
    height: 8px;
    border-radius: 4px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #36BCF7, stop:1 #9932CC);
    border-radius: 4px;
}}

#Card {{
    background-color: rgba(255, 255, 255, 5);
    border: 1px solid rgba(255, 255, 255, 10);
    border-radius: 12px;
}}

QDialog {{
    background-color: #1a1a20;
    border: 1px solid #36BCF7;
}}

QComboBox {{
    background-color: rgba(0, 0, 0, 80);
    border: 1px solid rgba(255, 255, 255, 20);
    border-radius: 6px;
    padding: 5px;
    color: white;
}}
"""

LIGHT_STYLE_TEMPLATE = """
QMainWindow {{
    background-color: transparent;
}}

#MainFrame {{
    background-color: rgba(245, 245, 250, 200);
    border: 1px solid rgba(0, 0, 0, 15);
    border-radius: 20px;
}}

#Sidebar {{
    background-color: rgba(230, 230, 240, 150);
    border-right: 1px solid rgba(0, 0, 0, 10);
    border-top-left-radius: 20px;
    border-bottom-left-radius: 20px;
}}

QLabel {{
    color: #333333;
    font-family: '{font_family}', sans-serif;
    font-size: {font_size}px;
}}

#TitleLabel {{
    font-size: {title_size}px;
    font-weight: bold;
    color: #2D9CDB;
}}

QPushButton {{
    background-color: rgba(0, 0, 0, 10);
    border: 1px solid rgba(0, 0, 0, 15);
    border-radius: 12px;
    color: #333333;
    padding: 10px 20px;
    font-size: {font_size}px;
}}

QPushButton:hover {{
    background-color: rgba(0, 0, 0, 20);
    border: 1px solid #2D9CDB;
}}

#NavButton {{
    text-align: left;
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 12px;
    font-size: {font_size}px;
    color: #666666;
}}

#NavButton:hover {{
    background-color: rgba(45, 156, 219, 20);
    color: #2D9CDB;
}}

#NavButton[active="true"] {{
    background-color: rgba(45, 156, 219, 40);
    color: #2D9CDB;
    border-left: 3px solid #2D9CDB;
}}

QLineEdit {{
    background-color: rgba(255, 255, 255, 150);
    border: 1px solid rgba(0, 0, 0, 10);
    border-radius: 6px;
    color: #333333;
    padding: 8px;
    font-size: {font_size}px;
}}

QProgressBar {{
    border: none;
    background-color: rgba(0, 0, 0, 10);
    height: 8px;
    border-radius: 4px;
}}

QProgressBar::chunk {{
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #2D9CDB, stop:1 #8E44AD);
    border-radius: 4px;
}}

#Card {{
    background-color: rgba(0, 0, 0, 5);
    border: 1px solid rgba(0, 0, 0, 10);
    border-radius: 12px;
}}

QDialog {{
    background-color: #f0f0f5;
    border: 1px solid #2D9CDB;
}}

QComboBox {{
    background-color: white;
    border: 1px solid rgba(0, 0, 0, 20);
    border-radius: 6px;
    padding: 5px;
    color: #333333;
}}
"""
