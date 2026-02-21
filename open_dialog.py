"""
Open Component Dialog  —  .cdj files
======================================
Looks and behaves like a standard OS file dialog, with an extra
preview panel on the right that shows the embedded thumbnail.

┌─────────────────────────────────────────────────────────────────────┐
│ ← →   📁 C:/Users/hakan/components                                  │
├──────────────────┬──────────────────────────┬───────────────────────┤
│ 📁 Desktop       │ Name            Modified  │  ┌─────────────────┐ │
│ 📁 Documents     │ ──────────────────────── │  │                 │ │
│ 📁 components  ▶ │ 📄 road_a.cdj   02-21    │  │   thumbnail     │ │
│   📁 bridges     │ 📄 bridge.cdj   02-20    │  │                 │ │
│   📁 tunnels     │ 📄 tunnel.cdj   02-19    │  └─────────────────┘ │
│                  │                          │  road_a.cdj          │
│                  │                          │  21 Feb 2026  14:32  │
│                  │                          │  4 nodes · 2 conns   │
├──────────────────┴──────────────────────────┴───────────────────────┤
│ File name:  road_a.cdj                          [Cancel]   [Open]   │
└─────────────────────────────────────────────────────────────────────┘
"""

import base64
import json
import os
from datetime import datetime

from PySide2.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QListView, QLabel, QPushButton,
    QLineEdit, QFrame, QSizePolicy, QWidget,
    QToolButton, QAbstractItemView, QHeaderView,
    QFileSystemModel,
)
from PySide2.QtCore import (
    Qt, QSize, QDir, QSortFilterProxyModel,
    QModelIndex, QFileInfo,
)
from PySide2.QtGui import QPixmap, QColor, QPainter, QFont, QIcon

from .theme_dark import theme


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_cdj_meta(path: str) -> dict:
    result = {'thumbnail': None, 'n_nodes': 0, 'n_conns': 0, 'mtime': ''}
    try:
        mtime = os.path.getmtime(path)
        result['mtime'] = datetime.fromtimestamp(mtime).strftime('%d %b %Y   %H:%M')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        result['thumbnail'] = data.get('thumbnail')
        result['n_nodes']   = len(data.get('nodes', []))
        result['n_conns']   = len(data.get('connections', []))
    except Exception:
        pass
    return result


def _pixmap_from_b64(b64_uri: str, w: int, h: int):
    try:
        raw = base64.b64decode(b64_uri.split(',', 1)[1])
        pix = QPixmap()
        pix.loadFromData(raw)
        if pix.isNull():
            return None
        return pix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    except Exception:
        return None


def _placeholder_pixmap(w: int, h: int) -> QPixmap:
    pix = QPixmap(w, h)
    pix.fill(QColor(28, 30, 38))
    p = QPainter(pix)
    p.setPen(QColor(80, 88, 108))
    f = QFont(); f.setPointSize(8)
    p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignCenter, "No preview")
    p.end()
    return pix


# ---------------------------------------------------------------------------
# Proxy model: show only directories + .cdj files
# ---------------------------------------------------------------------------

class _CdjFilterProxy(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        idx   = self.sourceModel().index(source_row, 0, source_parent)
        finfo = self.sourceModel().fileInfo(idx)
        if finfo.isDir():
            return True
        return finfo.suffix().lower() == 'cdj'


# ---------------------------------------------------------------------------
# Preview panel (right side)
# ---------------------------------------------------------------------------

class _PreviewPanel(QWidget):
    _W = 200
    _H = 200

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        self._img = QLabel()
        self._img.setFixedSize(self._W, self._H)
        self._img.setAlignment(Qt.AlignCenter)
        self._img.setStyleSheet(
            "background:#1a1c24; border:1px solid #323640; border-radius:3px;")
        self._img.setPixmap(_placeholder_pixmap(self._W, self._H))
        lay.addWidget(self._img)

        self._info = QLabel()
        self._info.setWordWrap(True)
        self._info.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._info.setStyleSheet("color:#8a98b0; font-size:8pt; background:transparent;")
        self._info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        lay.addWidget(self._info)
        lay.addStretch()

    def show_file(self, path: str):
        meta = _load_cdj_meta(path)
        name = os.path.basename(path)

        pix = None
        if meta['thumbnail']:
            pix = _pixmap_from_b64(meta['thumbnail'], self._W, self._H)
        self._img.setPixmap(pix or _placeholder_pixmap(self._W, self._H))

        n, c = meta['n_nodes'], meta['n_conns']
        self._info.setText(
            f"<b style='color:#c8cdd8'>{name}</b><br><br>"
            f"{meta['mtime']}<br><br>"
            f"{n} node{'s' if n != 1 else ''}  ·  {c} connection{'s' if c != 1 else ''}"
        )

    def clear(self):
        self._img.setPixmap(_placeholder_pixmap(self._W, self._H))
        self._info.clear()


# ---------------------------------------------------------------------------
# Main dialog
# ---------------------------------------------------------------------------

class OpenComponentDialog(QDialog):
    """
    Standard-looking file dialog for .cdj files with an embedded
    thumbnail preview panel.

    Usage
    -----
        dlg = OpenComponentDialog(parent, initial_dir="/path/to/dir")
        if dlg.exec_() == QDialog.Accepted:
            path = dlg.selected_path()
    """

    def __init__(self, parent=None, initial_dir: str = ''):
        super().__init__(parent)
        self.setWindowTitle("Open Component")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.resize(860, 520)
        self.setMinimumSize(640, 400)

        self._selected_path = None
        self._current_dir   = initial_dir or os.path.expanduser('~')
        self._history       = [self._current_dir]
        self._hist_idx      = 0

        self._build_models()
        self._build_ui()
        self._apply_styles()
        self._navigate_to(self._current_dir, record=False)

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------

    def _build_models(self):
        # Shared source model for both views
        self._fs = QFileSystemModel()
        self._fs.setRootPath('')
        self._fs.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)

        # Folder tree: only dirs
        self._dir_proxy = QSortFilterProxyModel()
        self._dir_proxy.setSourceModel(self._fs)
        self._dir_proxy.setFilterRole(Qt.DisplayRole)

        # File list: dirs + .cdj files
        self._file_proxy = _CdjFilterProxy()
        self._file_proxy.setSourceModel(self._fs)
        self._file_proxy.setSortCaseSensitivity(Qt.CaseInsensitive)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ────────────────────────────────────────────────────
        tb = QWidget()
        tb.setObjectName("toolbar")
        tb.setFixedHeight(36)
        tb_lay = QHBoxLayout(tb)
        tb_lay.setContentsMargins(8, 4, 8, 4)
        tb_lay.setSpacing(4)

        self._back_btn = QToolButton(); self._back_btn.setText("‹")
        self._fwd_btn  = QToolButton(); self._fwd_btn.setText("›")
        self._back_btn.setFixedSize(24, 24)
        self._fwd_btn.setFixedSize(24, 24)
        self._back_btn.setObjectName("navbtn")
        self._fwd_btn.setObjectName("navbtn")
        self._back_btn.setEnabled(False)
        self._fwd_btn.setEnabled(False)
        self._back_btn.clicked.connect(self._go_back)
        self._fwd_btn.clicked.connect(self._go_fwd)

        self._addr = QLineEdit(self._current_dir)
        self._addr.setObjectName("addr")
        self._addr.setFixedHeight(24)
        self._addr.returnPressed.connect(self._on_addr_enter)

        tb_lay.addWidget(self._back_btn)
        tb_lay.addWidget(self._fwd_btn)
        tb_lay.addWidget(self._addr, 1)
        root.addWidget(tb)

        root.addWidget(self._hline())

        # ── Main splitter ──────────────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("main_split")

        # Left: folder tree (dirs only)
        self._tree = QTreeView()
        self._tree.setObjectName("tree")
        self._tree.setModel(self._dir_proxy)
        self._tree.setRootIndex(
            self._dir_proxy.mapFromSource(self._fs.index('')))
        # Show only the Name column
        self._tree.setHeaderHidden(True)
        for col in range(1, self._fs.columnCount()):
            self._tree.hideColumn(col)
        self._tree.setAnimated(True)
        self._tree.setIndentation(14)
        self._tree.setMinimumWidth(160)
        self._tree.clicked.connect(self._on_tree_clicked)
        splitter.addWidget(self._tree)

        # Centre: file list
        self._view = QListView()
        self._view.setObjectName("filelist")
        self._view.setModel(self._file_proxy)
        self._view.setViewMode(QListView.ListMode)
        self._view.setSelectionMode(QAbstractItemView.SingleSelection)
        self._view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._view.setIconSize(QSize(16, 16))
        self._view.setSpacing(1)
        self._view.selectionModel().currentChanged.connect(
            self._on_file_selection_changed)
        self._view.doubleClicked.connect(self._on_file_double_clicked)
        splitter.addWidget(self._view)

        # Right: preview
        self._preview = _PreviewPanel()
        splitter.addWidget(self._preview)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([180, 420, 230])

        root.addWidget(splitter, 1)
        root.addWidget(self._hline())

        # ── Bottom bar ─────────────────────────────────────────────────
        bot = QWidget()
        bot.setObjectName("bottom")
        bot.setFixedHeight(46)
        bot_lay = QHBoxLayout(bot)
        bot_lay.setContentsMargins(12, 8, 12, 8)
        bot_lay.setSpacing(8)

        bot_lay.addWidget(QLabel("File name:"))

        self._fname = QLineEdit()
        self._fname.setObjectName("fname")
        self._fname.setReadOnly(True)
        self._fname.setFixedHeight(24)
        self._fname.returnPressed.connect(self._try_accept)
        bot_lay.addWidget(self._fname, 1)

        bot_lay.addWidget(QLabel("Component Designer (*.cdj)"))

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(80, 26)
        cancel_btn.clicked.connect(self.reject)
        bot_lay.addWidget(cancel_btn)

        self._open_btn = QPushButton("Open")
        self._open_btn.setFixedSize(80, 26)
        self._open_btn.setDefault(True)
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._try_accept)
        bot_lay.addWidget(self._open_btn)

        root.addWidget(bot)

    @staticmethod
    def _hline():
        f = QFrame()
        f.setFrameShape(QFrame.HLine)
        f.setObjectName("hline")
        return f

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _apply_styles(self):
        bg  = theme.CANVAS_BG.name()
        self.setStyleSheet(f"""
            QDialog {{ background:{bg}; color:#c8cdd8; }}

            QWidget#toolbar {{ background:#16181f; }}
            QWidget#bottom  {{ background:#16181f; }}

            QToolButton#navbtn {{
                background:transparent; border:none;
                color:#9aa0b8; font-size:14pt; font-weight:bold;
                border-radius:3px;
            }}
            QToolButton#navbtn:hover   {{ background:#2a2e3e; color:#e0e4f0; }}
            QToolButton#navbtn:pressed {{ background:#1e2230; }}
            QToolButton#navbtn:disabled{{ color:#3a3e50; }}

            QLineEdit#addr, QLineEdit#fname {{
                background:#1e2028; border:1px solid #3a3e4a;
                border-radius:3px; color:#c8cdd8;
                padding:0 6px; font-size:9pt;
                selection-background-color:#2e4a7a;
            }}

            QTreeView#tree {{
                background:#1a1c24; border:none;
                color:#b0b8cc; font-size:9pt; outline:none;
            }}
            QTreeView#tree::item {{ padding:3px 4px; }}
            QTreeView#tree::item:selected {{
                background:#2e4a7a; color:#ffffff;
            }}
            QTreeView#tree::item:hover:!selected {{ background:#232636; }}

            QListView#filelist {{
                background:#1e2028; border:none;
                color:#c8cdd8; font-size:9pt; outline:none;
            }}
            QListView#filelist::item {{ padding:4px 8px; border-radius:2px; }}
            QListView#filelist::item:selected {{
                background:#2e4a7a; color:#ffffff;
            }}
            QListView#filelist::item:hover:!selected {{ background:#252836; }}

            QSplitter#main_split::handle {{
                background:#2a2e3a; width:1px;
            }}

            QFrame#hline {{ color:#2a2e3a; max-height:1px; }}

            QPushButton {{
                background:#2e3240; border:1px solid #3a3e4a;
                border-radius:4px; color:#c8cdd8; font-size:9pt;
            }}
            QPushButton:hover   {{ background:#3a4060; }}
            QPushButton:pressed {{ background:#253050; }}
            QPushButton:default {{
                background:#1e4a8a; border-color:#2a6aaa; color:#fff;
            }}
            QPushButton:default:hover    {{ background:#2a5a9a; }}
            QPushButton:default:disabled {{
                background:#252830; color:#555870; border-color:#252830;
            }}

            QLabel {{ background:transparent; color:#8a98b0; font-size:9pt; }}
            QScrollBar:vertical {{
                background:#1a1c24; width:10px; border:none;
            }}
            QScrollBar::handle:vertical {{
                background:#3a3e50; border-radius:5px; min-height:20px;
            }}
            QScrollBar::handle:vertical:hover {{ background:#4a4e62; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height:0;
            }}
            QScrollBar:horizontal {{
                background:#1a1c24; height:10px; border:none;
            }}
            QScrollBar::handle:horizontal {{
                background:#3a3e50; border-radius:5px; min-width:20px;
            }}
            QScrollBar::handle:horizontal:hover {{ background:#4a4e62; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width:0;
            }}
        """)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate_to(self, path: str, record: bool = True):
        if not os.path.isdir(path):
            return
        self._current_dir = path
        self._addr.setText(path)

        src_idx  = self._fs.index(path)
        file_idx = self._file_proxy.mapFromSource(src_idx)
        self._view.setRootIndex(file_idx)
        self._view.clearSelection()
        self._preview.clear()
        self._fname.clear()
        self._open_btn.setEnabled(False)

        # Expand and scroll tree to current dir
        dir_idx = self._dir_proxy.mapFromSource(src_idx)
        self._tree.setCurrentIndex(dir_idx)
        self._tree.scrollTo(dir_idx)
        self._tree.expand(dir_idx)

        if record:
            self._history = self._history[:self._hist_idx + 1]
            self._history.append(path)
            self._hist_idx = len(self._history) - 1

        self._back_btn.setEnabled(self._hist_idx > 0)
        self._fwd_btn.setEnabled(self._hist_idx < len(self._history) - 1)

    def _go_back(self):
        if self._hist_idx > 0:
            self._hist_idx -= 1
            self._navigate_to(self._history[self._hist_idx], record=False)
            self._back_btn.setEnabled(self._hist_idx > 0)
            self._fwd_btn.setEnabled(True)

    def _go_fwd(self):
        if self._hist_idx < len(self._history) - 1:
            self._hist_idx += 1
            self._navigate_to(self._history[self._hist_idx], record=False)
            self._back_btn.setEnabled(True)
            self._fwd_btn.setEnabled(self._hist_idx < len(self._history) - 1)

    def _on_addr_enter(self):
        path = self._addr.text().strip()
        if os.path.isdir(path):
            self._navigate_to(path)
        elif os.path.isfile(path) and path.endswith('.cdj'):
            self._selected_path = path
            self.accept()

    # ------------------------------------------------------------------
    # Tree click → navigate
    # ------------------------------------------------------------------

    def _on_tree_clicked(self, proxy_idx: QModelIndex):
        src_idx = self._dir_proxy.mapToSource(proxy_idx)
        finfo   = self._fs.fileInfo(src_idx)
        if finfo.isDir():
            self._navigate_to(finfo.absoluteFilePath())

    # ------------------------------------------------------------------
    # File list selection
    # ------------------------------------------------------------------

    def _on_file_selection_changed(self, current: QModelIndex, _prev):
        src_idx = self._file_proxy.mapToSource(current)
        finfo   = self._fs.fileInfo(src_idx)

        if finfo.isDir():
            self._open_btn.setEnabled(True)
            self._fname.setText(finfo.fileName())
            self._preview.clear()
            self._selected_path = None
            return

        if finfo.suffix().lower() == 'cdj':
            path = finfo.absoluteFilePath()
            self._selected_path = path
            self._fname.setText(finfo.fileName())
            self._open_btn.setEnabled(True)
            self._preview.show_file(path)
        else:
            self._selected_path = None
            self._fname.clear()
            self._open_btn.setEnabled(False)
            self._preview.clear()

    def _on_file_double_clicked(self, proxy_idx: QModelIndex):
        src_idx = self._file_proxy.mapToSource(proxy_idx)
        finfo   = self._fs.fileInfo(src_idx)

        if finfo.isDir():
            self._navigate_to(finfo.absoluteFilePath())
        elif finfo.suffix().lower() == 'cdj':
            self._selected_path = finfo.absoluteFilePath()
            self.accept()

    # ------------------------------------------------------------------
    # Accept
    # ------------------------------------------------------------------

    def _try_accept(self):
        # If a .cdj file is selected, open it
        if self._selected_path and os.path.isfile(self._selected_path):
            self.accept()
            return
        # If a directory is highlighted, navigate into it
        idx = self._view.currentIndex()
        if idx.isValid():
            src  = self._file_proxy.mapToSource(idx)
            info = self._fs.fileInfo(src)
            if info.isDir():
                self._navigate_to(info.absoluteFilePath())

    def selected_path(self):
        """Return the chosen .cdj file path, or None if cancelled."""
        return self._selected_path if self.result() == QDialog.Accepted else None