import os
import sys

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRect, QSize
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QPushButton, QComboBox, QLabel,
    QSplitter, QTabWidget, QFrame, QProgressBar,
    QGridLayout, QApplication, QMessageBox,
    QMenuBar, QMenu, QFileDialog, QToolBar,
    QWidgetAction,
)
from PyQt6.QtGui import (
    QFont, QAction, QColor, QPainter, QPalette,
    QTextFormat, QDragEnterEvent, QDropEvent,
    QShortcut, QKeySequence, QTextCursor,
)

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from executor import run_code
from highlighter import CodeHighlighter


DARK_STYLE = """
QMainWindow, QWidget { background-color: #1e1e1e; color: #d4d4d4; }
QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c; font-family: 'Consolas','Courier New',monospace; }
QComboBox { background-color: #3c3c3c; color: #d4d4d4; border: 1px solid #555; padding: 4px 10px; border-radius: 4px; min-height: 24px; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background-color: #3c3c3c; color: #d4d4d4; selection-background-color: #094771; border: 1px solid #555; outline: none; }
QPushButton { background-color: #0e639c; color: white; border: none; padding: 7px 20px; border-radius: 4px; font-weight: bold; }
QPushButton:hover { background-color: #1177bb; }
QPushButton:pressed { background-color: #094771; }
QPushButton:disabled { background-color: #3c3c3c; color: #888; }
QPushButton#toolBtn { background-color: transparent; border: 1px solid #555; border-radius: 4px; padding: 6px 12px; min-height: 24px; }
QPushButton#toolBtn:hover { background-color: #3c3c3c; }
QPushButton#themeBtn { background-color: transparent; border: 1px solid #555; border-radius: 4px; padding: 6px 10px; font-size: 16px; min-width: 36px; }
QPushButton#themeBtn:hover { background-color: #3c3c3c; }
QTabWidget::pane { background-color: #1e1e1e; border: 1px solid #3c3c3c; border-top: none; }
QTabBar::tab { background-color: #2d2d2d; color: #888; padding: 8px 22px; border: 1px solid #3c3c3c; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
QTabBar::tab:selected { background-color: #1e1e1e; color: #fff; border-bottom: 1px solid #1e1e1e; }
QTabBar::tab:hover:!selected { color: #fff; }
QProgressBar { background-color: #3c3c3c; border: none; border-radius: 4px; text-align: center; color: white; font-size: 11px; height: 22px; }
QProgressBar::chunk { border-radius: 4px; }
QMenuBar { background-color: #2d2d2d; color: #d4d4d4; border-bottom: 1px solid #3c3c3c; padding: 2px; }
QMenuBar::item { padding: 4px 12px; border-radius: 4px; }
QMenuBar::item:selected { background-color: #094771; }
QMenu { background-color: #2d2d2d; color: #d4d4d4; border: 1px solid #3c3c3c; padding: 4px; }
QMenu::item { padding: 6px 30px 6px 20px; border-radius: 4px; }
QMenu::item:selected { background-color: #094771; }
QMenu::separator { height: 1px; background-color: #3c3c3c; margin: 4px 8px; }
QSplitter::handle { background-color: #3c3c3c; width: 2px; }
QToolBar { background-color: #2d2d2d; border-bottom: 1px solid #3c3c3c; spacing: 6px; padding: 4px 8px; }
"""

LIGHT_STYLE = """
QMainWindow, QWidget { background-color: #fff; color: #1e1e1e; }
QPlainTextEdit { background-color: #fafafa; color: #1e1e1e; border: 1px solid #d0d0d0; font-family: 'Consolas','Courier New',monospace; }
QComboBox { background-color: #fff; color: #1e1e1e; border: 1px solid #d0d0d0; padding: 4px 10px; border-radius: 4px; min-height: 24px; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background-color: #fff; color: #1e1e1e; selection-background-color: #cce5ff; border: 1px solid #d0d0d0; outline: none; }
QPushButton { background-color: #0078d4; color: white; border: none; padding: 7px 20px; border-radius: 4px; font-weight: bold; }
QPushButton:hover { background-color: #106ebe; }
QPushButton:pressed { background-color: #005a9e; }
QPushButton:disabled { background-color: #e0e0e0; color: #999; }
QPushButton#toolBtn { background-color: transparent; border: 1px solid #ccc; border-radius: 4px; padding: 6px 12px; min-height: 24px; }
QPushButton#toolBtn:hover { background-color: #f0f0f0; }
QPushButton#themeBtn { background-color: transparent; border: 1px solid #ccc; border-radius: 4px; padding: 6px 10px; font-size: 16px; min-width: 36px; }
QPushButton#themeBtn:hover { background-color: #f0f0f0; }
QTabWidget::pane { background-color: #fff; border: 1px solid #d0d0d0; border-top: none; }
QTabBar::tab { background-color: #f0f0f0; color: #666; padding: 8px 22px; border: 1px solid #d0d0d0; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
QTabBar::tab:selected { background-color: #fff; color: #1e1e1e; border-bottom: 1px solid #fff; }
QTabBar::tab:hover:!selected { color: #1e1e1e; }
QProgressBar { background-color: #e8e8e8; border: none; border-radius: 4px; text-align: center; color: #333; font-size: 11px; height: 22px; }
QProgressBar::chunk { border-radius: 4px; }
QMenuBar { background-color: #f0f0f0; color: #1e1e1e; border-bottom: 1px solid #d0d0d0; padding: 2px; }
QMenuBar::item { padding: 4px 12px; border-radius: 4px; }
QMenuBar::item:selected { background-color: #cce5ff; }
QMenu { background-color: #fff; color: #1e1e1e; border: 1px solid #d0d0d0; padding: 4px; }
QMenu::item { padding: 6px 30px 6px 20px; border-radius: 4px; }
QMenu::item:selected { background-color: #cce5ff; }
QMenu::separator { height: 1px; background-color: #e0e0e0; margin: 4px 8px; }
QSplitter::handle { background-color: #d0d0d0; width: 2px; }
QToolBar { background-color: #f8f8f8; border-bottom: 1px solid #d0d0d0; spacing: 6px; padding: 4px 8px; }
"""


MPL_DARK = {
    'figure.facecolor': '#1e1e1e', 'axes.facecolor': '#252526',
    'axes.edgecolor': '#3c3c3c', 'axes.labelcolor': '#d4d4d4',
    'text.color': '#d4d4d4', 'xtick.color': '#d4d4d4',
    'ytick.color': '#d4d4d4', 'grid.color': '#333333', 'grid.alpha': 0.25,
    'legend.facecolor': '#2d2d2d', 'legend.edgecolor': '#3c3c3c',
    'legend.labelcolor': '#d4d4d4', 'axes.spines.top': False,
    'axes.spines.right': False,
}
MPL_LIGHT = {
    'figure.facecolor': '#ffffff', 'axes.facecolor': '#fafafa',
    'axes.edgecolor': '#cccccc', 'axes.labelcolor': '#333333',
    'text.color': '#333333', 'xtick.color': '#555555',
    'ytick.color': '#555555', 'grid.color': '#e8e8e8', 'grid.alpha': 0.5,
    'legend.facecolor': '#ffffff', 'legend.edgecolor': '#cccccc',
    'legend.labelcolor': '#333333', 'axes.spines.top': False,
    'axes.spines.right': False,
}

COLORS = {
    'cpu': '#569cd6', 'gpu': '#dcdcaa', 'ram': '#4ec9b0',
    'ssd_r': '#4ec9b0', 'ssd_w': '#f14c4c',
}

CODE_EXAMPLES = {
    'Python': '''def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

n = 35
result = fibonacci(n)
print(f"fib({n}) = {result}")
''',
    'C': '''#include <stdio.h>

int fib(int n) {
    if (n <= 1) return n;
    return fib(n-1) + fib(n-2);
}

int main() {
    int n = 40;
    printf("fib(%d) = %d\\n", n, fib(n));
    return 0;
}
''',
    'C++': '''#include <iostream>

int fib(int n) {
    if (n <= 1) return n;
    return fib(n-1) + fib(n-2);
}

int main() {
    int n = 40;
    std::cout << "fib(" << n << ") = " << fib(n) << std::endl;
    return 0;
}
''',
    'Java': '''public class Main {
    static int fib(int n) {
        if (n <= 1) return n;
        return fib(n-1) + fib(n-2);
    }

    public static void main(String[] args) {
        int n = 35;
        System.out.println("fib(" + n + ") = " + fib(n));
    }
}
''',
    'C#': '''using System;

class Program {
    static int Fib(int n) {
        if (n <= 1) return n;
        return Fib(n-1) + Fib(n-2);
    }

    static void Main() {
        int n = 35;
        Console.WriteLine($"fib({n}) = {Fib(n)}");
    }
}
''',
    'Fortran': '''program fibonacci
    implicit none
    integer :: n, result
    n = 35
    result = fib(n)
    print *, "fib(", n, ") = ", result
contains
    recursive function fib(n) result(r)
        integer, intent(in) :: n
        integer :: r
        if (n <= 1) then
            r = n
        else
            r = fib(n-1) + fib(n-2)
        end if
    end function fib
end program fibonacci
''',
}


class CodeRunner(QThread):
    finished = pyqtSignal(object)

    def __init__(self, code, language):
        super().__init__()
        self.code = code
        self.language = language

    def run(self):
        self.finished.emit(run_code(self.code, self.language))


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_paint(event)


class CodeEditor(QPlainTextEdit):
    file_dropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.setAcceptDrops(True)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.update_line_number_width()

    def line_number_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def update_line_number_width(self, _=None):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(),
                self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()))

    def line_number_paint(self, event):
        p = QPainter(self.line_number_area)
        bg = QColor('#252526' if self.palette().color(QPalette.ColorRole.Base) == QColor('#1e1e1e') else '#f0f0f0')
        p.fillRect(event.rect(), bg)

        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        fg = QColor('#858585' if bg.lightness() < 128 else '#999999')

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                p.setPen(fg)
                p.drawText(0, top, self.line_number_area.width() - 4,
                           self.fontMetrics().height(),
                           Qt.AlignmentFlag.AlignRight, str(num + 1))
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            num += 1
        p.end()

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            line_color = QColor('#2a2a2a' if self.palette().color(QPalette.ColorRole.Base) == QColor('#1e1e1e') else '#e8e8e8')
            sel.format.setBackground(line_color)
            sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            extra_selections.append(sel)
        self.setExtraSelections(extra_selections)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and os.path.isfile(urls[0].toLocalFile()):
                event.acceptProposedAction()
                return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path and os.path.isfile(path):
                    self.file_dropped.emit(path)
                    event.acceptProposedAction()
                    return
        event.ignore()


class ResourceBar(QWidget):
    def __init__(self, name, color, parent=None):
        super().__init__(parent)
        self.color = color
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        self.label = QLabel(name)
        self.label.setFixedWidth(48)
        self.label.setStyleSheet('font-weight: bold; font-size: 12px;')
        layout.addWidget(self.label)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setFixedHeight(22)
        layout.addWidget(self.bar, 1)
        self.val = QLabel('0%')
        self.val.setFixedWidth(320)
        self.val.setStyleSheet('font-size: 12px;')
        layout.addWidget(self.val)

    def set(self, percent, human):
        self.bar.setValue(max(0, min(100, int(percent))))
        self.val.setText(human)

    def style_bar(self, dark):
        bg = '#3c3c3c' if dark else '#e8e8e8'
        tx = 'white' if dark else '#333'
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background-color: {bg}; border: none; border-radius: 4px;
                text-align: center; color: {tx}; font-size: 11px; height: 22px; }}
            QProgressBar::chunk {{ background-color: {self.color}; border-radius: 4px; }}
        """)


class GraphPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.figure = Figure(figsize=(6, 4), dpi=110)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)
        self._dark = True
        self._last = None
        self._show_placeholder('Run some code to see graphs')

    def _show_placeholder(self, msg):
        self._last = None
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        bg = '#2d2d2d' if self._dark else '#f0f0f0'
        tc = '#888' if self._dark else '#999'
        ax.set_facecolor(bg)
        ax.text(0.5, 0.5, msg, ha='center', va='center',
                fontsize=13, color=tc, transform=ax.transAxes, style='italic')
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
        self.figure.tight_layout(); self.canvas.draw()

    def _style_ax(self, ax, title, ylabel):
        ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
        ax.set_xlabel('Time (seconds)', fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.tick_params(labelsize=8)
        ax.grid(True, alpha=0.2 if self._dark else 0.35,
                linestyle='-', linewidth=0.5)
        self.figure.tight_layout(); self.canvas.draw()

    def show_graph(self, title, data, ylabel, color):
        self._last = dict(title=title, data=data, ylabel=ylabel, color=color)
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        has_x = isinstance(data, dict) and data.get('x')
        if not has_x:
            self._show_placeholder('No data'); return

        is_io = 'y_read' in data or 'y_write' in data

        if is_io:
            self._plot_io(ax, data)
        else:
            self._plot_series(ax, data, color)

        self._style_ax(ax, title, ylabel)

    def _plot_series(self, ax, data, color):
        x, y = data['x'], data.get('y', [])
        if not y:
            return

        if len(x) < 3:
            n = len(x)
            ax.text(0.5, 0.5, f'Code ran too fast\n({n} sample{"s" if n!=1 else ""} collected)',
                    ha='center', va='center', fontsize=11,
                    color='#888', transform=ax.transAxes, style='italic')
            ax.plot(x, y, color=color, linewidth=1.5, marker='o', markersize=5, alpha=0.7)
            return

        ax.plot(x, y, color=color, linewidth=1.8)
        if max(y) - min(y) > 0.001:
            ax.fill_between(x, y, alpha=0.08, color=color)
            avg = sum(y) / len(y)
            ax.axhline(y=avg, color=color, linestyle='--', linewidth=0.8, alpha=0.5)
            pad = (max(x) - min(x)) * 0.02 if len(x) > 1 else 1
            ax.text(max(x) + pad, avg, f' avg {avg:.1f}',
                    va='center', fontsize=8, color=color, alpha=0.8)

    def _plot_io(self, ax, data):
        x = data['x']
        yr = data.get('y_read', [])
        yw = data.get('y_write', [])
        has_r = yr and any(v != 0 for v in yr)
        has_w = yw and any(v != 0 for v in yw)

        if not has_r and not has_w:
            ax.text(0.5, 0.5, 'No disk activity', ha='center', va='center',
                    fontsize=11, color='#888', transform=ax.transAxes, style='italic')
            return

        if has_r: ax.plot(x, yr, label='Read', color=COLORS['ssd_r'], linewidth=1.5)
        if has_w: ax.plot(x, yw, label='Write', color=COLORS['ssd_w'], linewidth=1.8)
        ax.legend(fontsize=9, framealpha=0.8, loc='upper right')

    def set_theme(self, dark):
        self._dark = dark
        matplotlib.rcParams.update(MPL_DARK if dark else MPL_LIGHT)
        if self._last:
            self.show_graph(**self._last)
        else:
            self._show_placeholder('Run some code to see graphs')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_dark = True
        self.runner = None
        self.results = None
        self._file = None
        self.highlighter = None
        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        self.setWindowTitle('LogicCode — Resource Usage Analyzer')
        self.setMinimumSize(1200, 720)
        self.resize(1400, 800)

        self._build_menubar()
        self._build_toolbar()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel
        left = QWidget()
        lo = QVBoxLayout(left); lo.setContentsMargins(0,0,0,0); lo.setSpacing(5)
        lo.addWidget(self._title('Code Input'))
        self.editor = CodeEditor()
        self.editor.setFont(QFont('Consolas, Courier New, monospace', 11))
        self.editor.setPlaceholderText('Paste your code, drag & drop a file, or use File → Examples…')
        self.editor.file_dropped.connect(self._load_file)
        lo.addWidget(self.editor, 1)
        self.highlighter = CodeHighlighter(self.editor.document(), is_dark=True)

        ctrl = QHBoxLayout(); ctrl.setSpacing(8)
        ctrl.addWidget(self._label('Language:'))
        self.lang_cb = QComboBox()
        self.lang_cb.addItems(['Auto','Python','C','C++','Java','C#','Fortran'])
        self.lang_cb.currentIndexChanged.connect(self._on_lang)
        ctrl.addWidget(self.lang_cb)
        ctrl.addStretch()
        self.run_btn = QPushButton('Run Code')
        self.run_btn.setMinimumSize(110, 32)
        self.run_btn.clicked.connect(self._run)
        ctrl.addWidget(self.run_btn)
        lo.addLayout(ctrl)
        splitter.addWidget(left)

        # Right panel
        right = QWidget()
        ro = QVBoxLayout(right); ro.setContentsMargins(0,0,0,0); ro.setSpacing(5)
        ro.addWidget(self._title('Resource Usage'))

        self.tabs = QTabWidget(); self.tabs.setMinimumWidth(520)

        self.summary_tab = QWidget(); self._build_summary();
        self.tabs.addTab(self.summary_tab, 'Summary')

        self.graphs_tab = QWidget(); self._build_graphs();
        self.tabs.addTab(self.graphs_tab, 'Graphs')

        self.console_tab = QWidget(); self._build_console();
        self.tabs.addTab(self.console_tab, 'Console')

        ro.addWidget(self.tabs, 1)
        splitter.addWidget(right)
        splitter.setSizes([500, 700])

        cw = QWidget(); ml = QHBoxLayout(cw); ml.setContentsMargins(10,6,10,10)
        ml.addWidget(splitter)
        self.setCentralWidget(cw)

        QShortcut(QKeySequence('Ctrl+O'), self, self._open)
        QShortcut(QKeySequence('Ctrl+R'), self, self._run)
        QShortcut(QKeySequence('Ctrl+Shift+N'), self, self._load_example)

    def _title(self, text):
        l = QLabel(text)
        l.setStyleSheet('font-size: 14px; font-weight: bold;')
        return l

    def _label(self, text):
        l = QLabel(text)
        l.setStyleSheet('font-size: 12px;')
        return l

    def _build_menubar(self):
        mb = self.menuBar()

        fm = mb.addMenu('&File')
        a = QAction('&Open…\tCtrl+O', self); a.triggered.connect(self._open); fm.addAction(a)
        fm.addSeparator()
        ex = fm.addMenu('&Examples')
        for lang_name in ['Python','C','C++','Java','C#','Fortran']:
            a = QAction(lang_name, self)
            a.setData(lang_name)
            a.triggered.connect(lambda _, n=lang_name: self._load_example(n))
            ex.addAction(a)
        fm.addSeparator()
        a = QAction('E&xit', self); a.triggered.connect(self.close); fm.addAction(a)

        vm = mb.addMenu('&View')
        self.theme_act = QAction('Dark Mode', self)
        self.theme_act.setCheckable(True); self.theme_act.setChecked(True)
        self.theme_act.triggered.connect(self._toggle_theme)
        vm.addAction(self.theme_act)
        vm.addSeparator()
        a = QAction('&About', self); a.triggered.connect(self._about); vm.addAction(a)

    def _build_toolbar(self):
        tb = QToolBar('Main'); tb.setMovable(False); self.addToolBar(tb)

        self.open_btn = QPushButton('Open')
        self.open_btn.setObjectName('toolBtn'); self.open_btn.clicked.connect(self._open)
        tb.addWidget(self.open_btn)

        self.ex_btn = QPushButton('Examples')
        self.ex_btn.setObjectName('toolBtn'); self.ex_btn.clicked.connect(self._load_example)
        tb.addWidget(self.ex_btn)

        tb.addSeparator()

        self.theme_btn = QPushButton('\u263E')
        self.theme_btn.setObjectName('themeBtn')
        self.theme_btn.setToolTip('Toggle Dark/Light')
        self.theme_btn.clicked.connect(self._toggle_theme)
        tb.addWidget(self.theme_btn)

        tb.addSeparator()

        self.status_lbl = QLabel('Ready')
        self.status_lbl.setStyleSheet('font-size: 11px; color: #888;')
        tb.addWidget(self.status_lbl)

    def _build_summary(self):
        lo = QVBoxLayout(self.summary_tab); lo.setSpacing(2)
        self.cpu_bar = ResourceBar('CPU', COLORS['cpu'])
        self.gpu_bar = ResourceBar('GPU', COLORS['gpu'])
        self.ram_bar = ResourceBar('RAM', COLORS['ram'])
        self.ssd_bar = ResourceBar('SSD', COLORS['ssd_w'])
        for w in [self.cpu_bar, self.gpu_bar, self.ram_bar, self.ssd_bar]:
            lo.addWidget(w)

        lo.addWidget(QFrame(frameShape=QFrame.Shape.HLine, frameShadow=QFrame.Shadow.Sunken))

        g = QGridLayout(); g.setSpacing(8); g.setContentsMargins(4,6,4,4)
        def info(text, r, c):
            lbl = QLabel(text); lbl.setStyleSheet('font-size: 12px;')
            v = QLabel('--'); v.setStyleSheet('font-size: 12px; font-weight: bold;')
            g.addWidget(lbl, r, c*2); g.addWidget(v, r, c*2+1); return v
        self.time_v = info('Time:', 0, 0)
        self.gui_v = info('GUI:', 0, 1)
        self.lang_v = info('Language:', 1, 0)
        self.stat_v = info('Status:', 1, 1)
        lo.addLayout(g); lo.addStretch()

    def _build_graphs(self):
        lo = QVBoxLayout(self.graphs_tab); lo.setSpacing(6)
        row = QHBoxLayout()
        row.addWidget(self._label('Show:'))
        self.graph_cb = QComboBox()
        self.graph_cb.addItems(['CPU Usage','GPU Usage','RAM Usage','Disk I/O'])
        self.graph_cb.currentIndexChanged.connect(self._update_graph)
        row.addWidget(self.graph_cb); row.addStretch(); lo.addLayout(row)
        self.graph = GraphPanel()
        lo.addWidget(self.graph, 1)

    def _build_console(self):
        lo = QVBoxLayout(self.console_tab)
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont('Consolas, Courier New, monospace', 10))
        lo.addWidget(self.console)

    def _toggle_theme(self):
        self.is_dark = not self.is_dark
        self._apply_theme()

    def _apply_theme(self):
        self.setStyleSheet(DARK_STYLE if self.is_dark else LIGHT_STYLE)
        self.theme_btn.setText('\u2600' if not self.is_dark else '\u263E')
        self.theme_act.setChecked(self.is_dark)
        self.theme_act.setText('Dark Mode' if self.is_dark else 'Light Mode')
        matplotlib.rcParams.update(MPL_DARK if self.is_dark else MPL_LIGHT)
        for b in [self.cpu_bar, self.gpu_bar, self.ram_bar, self.ssd_bar]:
            b.style_bar(self.is_dark)
        if self.highlighter:
            self.highlighter.set_theme(self.is_dark)
        if hasattr(self, 'graph'):
            self.graph.set_theme(self.is_dark)

    def _on_lang(self, idx):
        m = {0:'auto',1:'python',2:'c',3:'cpp',4:'java',5:'csharp',6:'fortran'}
        if self.highlighter:
            self.highlighter.set_language(m.get(idx, 'auto'))

    def _open(self):
        p, _ = QFileDialog.getOpenFileName(
            self, 'Open Code File', '',
            'Source Files (*.py *.c *.cpp *.cxx *.h *.hpp *.java *.cs *.f90 *.f *.for);;All (*)')
        if p: self._load_file(p)

    def _load_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                self.editor.setPlainText(f.read())
            ext = os.path.splitext(path)[1].lower()
            em = {'.py':'Python','.c':'C','.cpp':'C++','.cxx':'C++',
                  '.h':'C','.hpp':'C++','.java':'Java','.cs':'C#',
                  '.f90':'Fortran','.f':'Fortran','.for':'Fortran'}
            if ext in em:
                for i in range(self.lang_cb.count()):
                    if self.lang_cb.itemText(i).lower() == em[ext].lower():
                        self.lang_cb.setCurrentIndex(i)
                        break
            self._file = os.path.basename(path)
            self.status_lbl.setText(f'Loaded: {self._file}')
            m = {0:'auto',1:'python',2:'c',3:'cpp',4:'java',5:'csharp',6:'fortran'}
            if self.highlighter:
                self.highlighter.set_language(m.get(self.lang_cb.currentIndex(), 'auto'))
            self.editor.highlight_current_line()
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))

    def _load_example(self, name=None):
        if not name:
            name, ok = QFileDialog.getOpenFileName(
                self, 'Load Example', '', 'JSON (*.json)')
            if not ok: return
        if isinstance(name, str) and name in CODE_EXAMPLES:
            self.editor.setPlainText(CODE_EXAMPLES[name])
            for i in range(self.lang_cb.count()):
                if self.lang_cb.itemText(i) == name:
                    self.lang_cb.setCurrentIndex(i)
                    break
            self.status_lbl.setText(f'Example: {name}')
            m = {0:'auto',1:'python',2:'c',3:'cpp',4:'java',5:'csharp',6:'fortran'}
            if self.highlighter:
                self.highlighter.set_language(m.get(self.lang_cb.currentIndex(), 'auto'))
        else:
            self._open()

    def _about(self):
        QMessageBox.about(self, 'About LogicCode',
            '<b>LogicCode</b> — Resource Usage Analyzer<p>'
            'Paste code, run in a sandbox, and measure CPU, GPU, RAM, Disk usage, '
            'execution time, and GUI requirement.<p>'
            'Python + PyQt6 + psutil + matplotlib')

    def _run(self):
        code = self.editor.toPlainText()
        if not code.strip():
            QMessageBox.warning(self, 'No Code', 'Enter some code first.')
            return
        idx = self.lang_cb.currentIndex()
        m = {0:'auto',1:'python',2:'c',3:'cpp',4:'java',5:'csharp',6:'fortran'}
        lang = m.get(idx, 'auto')

        self.run_btn.setEnabled(False); self.run_btn.setText('Running…')
        self.status_lbl.setText('Running…')
        self.stat_v.setText('Running…')
        self.stat_v.setStyleSheet('font-size: 12px; font-weight: bold; color: #dcdcaa;')
        self.console.clear()
        self.graph._show_placeholder('Analyzing…')

        self.runner = CodeRunner(code, lang)
        self.runner.finished.connect(self._on_done)
        self.runner.start()

    def _on_done(self, result):
        self.run_btn.setEnabled(True); self.run_btn.setText('Run Code')
        self.results = result

        lang_name = result.get('language', '?').capitalize()
        ok = result.get('success', False)
        gui = result.get('needs_gui', False)
        out = result.get('output', '')
        err = result.get('error', '')

        self.lang_v.setText(lang_name)

        if ok:
            self.stat_v.setText('Completed')
            self.stat_v.setStyleSheet('font-size: 12px; font-weight: bold; color: #4ec9b0;')
        else:
            self.stat_v.setText('Failed')
            self.stat_v.setStyleSheet('font-size: 12px; font-weight: bold; color: #f14c4c;')

        c = result.get('cpu', {}); g = result.get('gpu', {})
        r = result.get('ram', {}); s = result.get('ssd', {}); t = result.get('time', {})

        self.cpu_bar.set(c.get('percent',0), c.get('human','0%'))
        self.gpu_bar.set(g.get('percent',0), g.get('human','N/A'))
        self.ram_bar.set(r.get('percent',0), r.get('human','0 B'))
        self.ssd_bar.set(s.get('percent',0), s.get('human','0 B'))

        self.time_v.setText(t.get('human','0s'))
        self.gui_v.setText('Yes' if gui else 'No')

        if out:
            self.console.appendPlainText('─── STDOUT ───')
            self.console.appendPlainText(out)
        if err:
            if out: self.console.appendPlainText('')
            self.console.appendPlainText('─── STDERR ───')
            self.console.appendPlainText(err)

        self.status_lbl.setText('Completed' if ok else 'Failed')
        self._update_graph()
        self.tabs.setCurrentIndex(0)

    def _update_graph(self):
        if not hasattr(self, 'graph') or not self.results:
            return
        idx = self.graph_cb.currentIndex()
        is_dark = self.is_dark

        if idx == 0:
            self.graph.show_graph('CPU Usage',
                self.results.get('cpu',{}).get('graph',{}), 'CPU %', COLORS['cpu'])
        elif idx == 1:
            g = self.results.get('gpu', {})
            d = g.get('graph', {})
            if d and d.get('y') and any(v and v > 0 for v in d['y']):
                self.graph.show_graph('GPU Usage', d, 'GPU %', COLORS['gpu'])
            else:
                self.graph._show_placeholder(g.get('human', 'GPU unavailable'))
        elif idx == 2:
            self.graph.show_graph('RAM Usage',
                self.results.get('ram',{}).get('graph',{}), 'RAM (MB)', COLORS['ram'])
        elif idx == 3:
            self.graph.show_graph('Disk I/O',
                self.results.get('ssd',{}).get('graph',{}), 'Bytes', COLORS['ssd_w'])
