QSS = """
QWidget { color: #e6e9ef; font-size: 13px; }
#root { background: #14171d; border: 1px solid #2a2f3a; border-radius: 10px; }
#titlebar { background: #1a1e26; border-top-left-radius: 9px; border-top-right-radius: 9px; }
#appTitle { font-weight: 600; font-size: 14px; }
#card { background: #1c2028; border: 1px solid #272c37; border-radius: 10px; }
#cardTitle { color: #8b93a5; font-size: 11px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
#muted { color: #8b93a5; }
#error { color: #ef5350; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }
QPushButton { background: transparent; border: none; border-radius: 6px; padding: 4px 10px; }
QPushButton:hover { background: #2a2f3a; }
#closeBtn:hover { background: #ef5350; }
QMenu { background: #1c2028; border: 1px solid #2a2f3a; padding: 4px; }
QMenu::item { padding: 6px 18px; border-radius: 4px; }
QMenu::item:selected { background: #2a2f3a; }
QMenu::separator { height: 1px; background: #2a2f3a; margin: 4px 6px; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #2f3542; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
"""
