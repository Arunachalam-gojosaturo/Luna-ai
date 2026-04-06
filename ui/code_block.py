"""
Inline code block display widget with:
  • Syntax-highlighted display
  • Copy to clipboard button
  • Save to workspace button
"""
try:
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                  QLabel, QPushButton, QTextEdit, QApplication)
    from PyQt6.QtCore    import Qt, QTimer
    from PyQt6.QtGui     import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
    _WORD_WRAP = Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard
    _MONO = True
except ImportError:
    from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                  QLabel, QPushButton, QTextEdit, QApplication)
    from PyQt5.QtCore    import Qt, QTimer
    from PyQt5.QtGui     import QFont, QColor, QTextCharFormat, QSyntaxHighlighter
    _WORD_WRAP = Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
    _MONO = True

import re
from core.code_parser import get_language_label


class LunaSyntaxHighlighter(QSyntaxHighlighter):
    """Minimal but effective highlighter for Python/JS/Bash/etc."""

    RULES = {
        "keyword":  (r"\b(def|class|return|if|elif|else|for|while|import|from|as|"
                     r"in|not|and|or|try|except|finally|with|lambda|yield|pass|break|"
                     r"continue|True|False|None|async|await|raise|del|global|nonlocal|"
                     r"function|var|let|const|export|default|new|this|typeof|instanceof|"
                     r"do|switch|case|struct|enum|pub|fn|use|mod|impl|mut|self|"
                     r"echo|sudo|apt|pip|cd|ls|mkdir|rm|cp|mv|chmod|chown)\b",
                     QColor(0, 200, 255)),
        "string1":  (r'"[^"\\]*(?:\\.[^"\\]*)*"',  QColor(255, 180, 80)),
        "string2":  (r"'[^'\\]*(?:\\.[^'\\]*)*'",  QColor(255, 180, 80)),
        "number":   (r"\b\d+\.?\d*\b",             QColor(180, 130, 255)),
        "comment":  (r"(#|//)[^\n]*",               QColor(90, 150, 90)),
        "decorator":(r"@\w+",                        QColor(255, 120, 180)),
        "builtin":  (r"\b(print|len|range|type|str|int|float|list|dict|set|tuple|"
                     r"open|os|sys|Path|subprocess|True|False)\b",
                     QColor(120, 230, 180)),
        "operator": (r"[\+\-\*/=<>!&|%\^~]+",      QColor(0, 180, 150)),
        "bracket":  (r"[\(\)\[\]\{\}]",             QColor(200, 160, 60)),
    }

    def __init__(self, document):
        super().__init__(document)
        self._rules = []
        for name, (pattern, color) in self.RULES.items():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            if name == "keyword":
                fmt.setFontWeight(700)
            elif name == "comment":
                fmt.setFontItalic(True)
            self._rules.append((re.compile(pattern), fmt))

    def highlightBlock(self, text):
        for regex, fmt in self._rules:
            for m in regex.finditer(text):
                self.setFormat(m.start(), m.end()-m.start(), fmt)


class CodeBlockWidget(QWidget):
    def __init__(self, code: str, language: str, index: int,
                 task_engine=None, parent=None):
        super().__init__(parent)
        self.code     = code
        self.language = language
        self.index    = index
        self.task_eng = task_engine
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 4)
        root.setSpacing(0)

        # ── Header bar ──
        hdr = QWidget(); hdr.setObjectName("codeHeader")
        hdr.setFixedHeight(34)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(12,0,8,0); hl.setSpacing(6)

        lang_lbl = QLabel(f"  {get_language_label(self.language)}")
        lang_lbl.setObjectName("codeLangLabel")
        hl.addWidget(lang_lbl); hl.addStretch()

        self._copy_btn = QPushButton("⎘ Copy"); self._copy_btn.setObjectName("codeActionBtn")
        self._copy_btn.setFixedHeight(26); self._copy_btn.setMinimumWidth(70)
        self._copy_btn.clicked.connect(self._copy)

        self._save_btn = QPushButton("💾 Save"); self._save_btn.setObjectName("codeActionBtn")
        self._save_btn.setFixedHeight(26); self._save_btn.setMinimumWidth(70)
        self._save_btn.clicked.connect(self._save_to_file)
        if not self.task_eng:
            self._save_btn.setEnabled(False)

        hl.addWidget(self._save_btn)
        hl.addWidget(self._copy_btn)
        root.addWidget(hdr)

        # ── Code area ──
        self._editor = QTextEdit(); self._editor.setObjectName("codeArea")
        self._editor.setReadOnly(True)
        self._editor.setPlainText(self.code)

        mono = QFont("Cascadia Code", 12)
        if not mono.exactMatch():
            mono = QFont("Fira Code", 12)
        if not mono.exactMatch():
            mono = QFont("Consolas", 12)
        if not mono.exactMatch():
            mono = QFont("Courier New", 12)
        mono.setFixedPitch(True)
        self._editor.setFont(mono)

        # Auto height (max 400px)
        lines = self.code.count('\n') + 1
        h = min(max(lines * 22 + 16, 60), 400)
        self._editor.setFixedHeight(h)

        LunaSyntaxHighlighter(self._editor.document())
        root.addWidget(self._editor)

    def _copy(self):
        QApplication.clipboard().setText(self.code)
        self._copy_btn.setText("✓ Copied!")
        self._copy_btn.setObjectName("codeActionBtnOk")
        self._copy_btn.style().unpolish(self._copy_btn)
        self._copy_btn.style().polish(self._copy_btn)
        QTimer.singleShot(1800, self._reset_copy_btn)

    def _reset_copy_btn(self):
        self._copy_btn.setText("⎘ Copy")
        self._copy_btn.setObjectName("codeActionBtn")
        self._copy_btn.style().unpolish(self._copy_btn)
        self._copy_btn.style().polish(self._copy_btn)

    def _save_to_file(self):
        if not self.task_eng: return
        ext_map = {"python":"py","py":"py","javascript":"js","js":"js",
                   "bash":"sh","sh":"sh","html":"html","css":"css",
                   "rust":"rs","go":"go","java":"java","cpp":"cpp","c":"c"}
        ext = ext_map.get(self.language.lower(), "txt")
        fname = f"luna_code_{self.index+1}.{ext}"
        result = self.task_eng.write_code_to_file(fname, self.code, self.language)
        self._save_btn.setText("✓ Saved!" if result.success else "✗ Failed")
        self._save_btn.setObjectName("codeActionBtnOk" if result.success else "codeActionBtnErr")
        self._save_btn.style().unpolish(self._save_btn)
        self._save_btn.style().polish(self._save_btn)
        QTimer.singleShot(2500, self._reset_save_btn)

    def _reset_save_btn(self):
        self._save_btn.setText("💾 Save")
        self._save_btn.setObjectName("codeActionBtn")
        self._save_btn.style().unpolish(self._save_btn)
        self._save_btn.style().polish(self._save_btn)
