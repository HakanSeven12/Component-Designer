"""
theme_dark.py — Dark Theme for Component Designer
==================================================
All visual constants (QColor, QPen, QBrush, stylesheet strings) are defined
here in one place.  Other modules import from this file instead of hard-coding
colors.

Usage
-----
    from .theme_dark import theme   # or: from theme_dark import theme

    # QColor access
    my_pen = QPen(theme.NODE_BORDER_NORMAL, 2)

    # Stylesheet access
    widget.setStyleSheet(theme.EDITOR_STYLE)

    # Apply app-wide QPalette
    theme.apply_palette(app)        # call once in main(), before show()
"""

from PySide2.QtGui  import QColor, QPalette, QFont
from PySide2.QtCore import Qt


# ---------------------------------------------------------------------------
# Internal palette entries — edit these to retune the whole theme
# ---------------------------------------------------------------------------

_BG_DARKEST   = QColor( 18,  20,  26)   # deepest background (scene, panels)
_BG_DARK      = QColor( 26,  29,  38)   # main window / splitter bg
_BG_MID       = QColor( 34,  38,  50)   # node body, panel bg
_BG_RAISED    = QColor( 44,  49,  64)   # toolbox header, combo bg
_BG_HOVER     = QColor( 55,  62,  80)   # hover highlight on rows
_BG_SELECTED  = QColor( 62,  75, 100)   # selection highlight

_ACCENT_BLUE  = QColor( 82, 148, 226)   # primary accent (header, links)
_ACCENT_AMBER = QColor(230, 152,  40)   # selected-node highlight
_ACCENT_GREEN = QColor( 72, 200, 130)   # output port, start node
_ACCENT_ORG   = QColor(220, 100,  50)   # input port dot

_TEXT_BRIGHT  = QColor(220, 225, 235)   # primary text (labels)
_TEXT_MID     = QColor(160, 168, 185)   # secondary text (port labels)
_TEXT_DIM     = QColor( 95, 103, 120)   # disabled / placeholder text

_BORDER_DARK  = QColor( 48,  53,  68)   # subtle border
_BORDER_MID   = QColor( 70,  78,  98)   # normal node border
_BORDER_SEL   = QColor(230, 152,  40)   # selected node border

_WIRE_COLOR   = QColor(140, 155, 180)   # connection wire
_SHADOW       = QColor(  0,   0,   0,  50)
_GLOW         = QColor(230, 152,  40,  90)

# Preview-specific
_AXIS_COLOR   = QColor( 75,  85, 110)
_SURFACE_CLR  = QColor( 60, 200, 110)
_ELEV_CLR     = QColor(220,  80,  60)
_OFFSET_CLR   = QColor( 70, 130, 240)

# Flowchart canvas background
_CANVAS_BG    = QColor( 22,  25,  34)


# ---------------------------------------------------------------------------
# Public theme object — import this in your modules
# ---------------------------------------------------------------------------

class _DarkTheme:
    """
    Singleton-style container for all theme constants.
    Access via the module-level ``theme`` instance.
    """

    # ── Node colours ────────────────────────────────────────────────────────
    INPUT_PORT_COLOR   = _ACCENT_ORG
    OUTPUT_PORT_COLOR  = _ACCENT_GREEN

    HEADER_BG          = _ACCENT_BLUE.darker(130)    # QColor( 50,  90, 145)
    HEADER_BG_SELECTED = _ACCENT_AMBER

    NODE_BODY_BG       = _BG_MID
    NODE_BORDER_NORMAL = _BORDER_MID
    NODE_BORDER_SEL    = _BORDER_SEL
    NODE_SHADOW        = _SHADOW
    NODE_GLOW          = _GLOW

    ROW_HOVER_INPUT    = QColor(_ACCENT_ORG.red(),   _ACCENT_ORG.green(),   _ACCENT_ORG.blue(),   45)
    ROW_HOVER_OUTPUT   = QColor(_ACCENT_GREEN.red(), _ACCENT_GREEN.green(), _ACCENT_GREEN.blue(), 45)

    # ── Wire ────────────────────────────────────────────────────────────────
    WIRE_COLOR         = _WIRE_COLOR

    # ── Canvas / scene ──────────────────────────────────────────────────────
    CANVAS_BG          = _CANVAS_BG
    PREVIEW_BG         = _BG_DARKEST

    # ── Preview overlays ────────────────────────────────────────────────────
    AXIS_COLOR         = _AXIS_COLOR
    SURFACE_COLOR      = _SURFACE_CLR
    ELEVATION_COLOR    = _ELEV_CLR
    OFFSET_COLOR       = _OFFSET_CLR

    # Preview point / link item colours
    POINT_NORMAL_PEN   = QColor( 30,  35,  50)
    POINT_NORMAL_FILL  = QColor( 82, 148, 226)
    POINT_SEL_PEN      = _ACCENT_AMBER
    POINT_SEL_FILL     = QColor(240, 190,  90)

    LINK_NORMAL_COLOR  = QColor( 72, 175, 110)
    LINK_SEL_COLOR     = _ACCENT_AMBER

    DASHED_LINK_COLOR  = QColor(100, 110, 150)
    DASHED_SEL_COLOR   = QColor(220, 155,  70)

    # Text label colours (preview)
    POINT_LABEL_COLOR  = QColor(110, 170, 240)
    LINK_LABEL_COLOR   = QColor( 72, 200, 130)
    CODE_LABEL_COLOR   = QColor(160, 200, 255)
    CODE_LINK_COLOR    = QColor( 90, 200, 145)

    # ── Stylesheets ─────────────────────────────────────────────────────────

    EDITOR_STYLE: str = """
        QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox {
            background: #1e2230;
            color: #d8dde9;
            border: 1px solid #464e62;
            border-radius: 3px;
            padding: 1px 4px;
            font-size: 8pt;
        }
        QDoubleSpinBox:focus, QSpinBox:focus,
        QLineEdit:focus, QComboBox:focus {
            border: 2px solid #5294e2;
        }
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
        QSpinBox::up-button,       QSpinBox::down-button {
            background: #2c3244;
            border: none;
            width: 14px;
        }
        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,
        QSpinBox::up-button:hover,       QSpinBox::down-button:hover {
            background: #3a4460;
        }
        QComboBox::drop-down { border: none; width: 18px; }
        QComboBox::down-arrow {
            border-left:  4px solid transparent;
            border-right: 4px solid transparent;
            border-top:   5px solid #a0a8b9;
            margin-right: 4px;
        }
        QComboBox QAbstractItemView {
            background: #1e2230;
            color: #d8dde9;
            selection-background-color: #3a4e72;
            selection-color: #ffffff;
            border: 1px solid #464e62;
        }
    """

    EDITOR_STYLE_DISABLED: str = """
        QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox {
            background: #161820;
            color: #5f6778;
            border: 1px solid #2e3344;
            border-radius: 3px;
            padding: 1px 4px;
            font-size: 8pt;
        }
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
        QSpinBox::up-button,       QSpinBox::down-button {
            background: #1a1d28;
            border: none;
            width: 14px;
        }
        QComboBox::drop-down { border: none; width: 18px; }
        QComboBox::down-arrow {
            border-left:  4px solid transparent;
            border-right: 4px solid transparent;
            border-top:   5px solid #3a4050;
            margin-right: 4px;
        }
    """

    COMBO_STYLE: str = """
        QComboBox {
            background: #1e2230;
            color: #d8dde9;
            border: 1px solid #464e62;
            border-radius: 3px;
            padding: 2px 4px;
            font-size: 8pt;
        }
        QComboBox:focus { border: 2px solid #5294e2; }
        QComboBox::drop-down { border: none; width: 18px; }
        QComboBox::down-arrow {
            border-left:  4px solid transparent;
            border-right: 4px solid transparent;
            border-top:   5px solid #a0a8b9;
            margin-right: 4px;
        }
        QComboBox QAbstractItemView {
            background: #1e2230;
            color: #d8dde9;
            selection-background-color: #3a4e72;
            selection-color: #ffffff;
            border: 1px solid #464e62;
        }
    """

    LABEL_STYLE: str = (
        "QLabel { font-size: 8pt; color: #a0a8b9; background: transparent; }"
    )

    HEADER_LABEL_STYLE: str = (
        "QLabel { color: #dce3f0; font-weight: bold; "
        "font-size: 9pt; background: transparent; }"
    )

    NAME_EDIT_STYLE: str = (
        "QLineEdit { color: #e8edf8; font-weight: bold; font-size: 9pt;"
        " background: rgba(255,255,255,25); border: 1px solid #8ab0d8;"
        " border-radius: 3px; padding: 2px; }"
    )

    CHECKBOX_STYLE: str = """
        QCheckBox { spacing: 4px; font-size: 8pt; background: transparent;
                    color: #a0a8b9; }
        QCheckBox::indicator           { width: 14px; height: 14px; }
        QCheckBox::indicator:unchecked { border: 1px solid #464e62;
                                         border-radius: 2px;
                                         background: #1e2230; }
        QCheckBox::indicator:checked   { border: 1px solid #5294e2;
                                         border-radius: 2px;
                                         background: #5294e2; }
    """

    # Section divider between combo area and port rows
    SEPARATOR_STYLE: str = "background: #2e3448;"

    # Vertical divider between input and output columns
    VDIVIDER_STYLE: str  = "background: #2e3448;"

    # Flowchart panel label (top bar above the canvas)
    PANEL_LABEL_STYLE: str = (
        "font-weight: bold; background: #1a1d28;"
        " color: #8ab0d8; padding: 5px;"
    )

    # Toolbox tree widget
    TOOLBOX_STYLE: str = """
        QTreeWidget {
            background: #161820;
            color: #c0c8d8;
            border: none;
            font-size: 9pt;
        }
        QTreeWidget::item:hover {
            background: #252d40;
        }
        QTreeWidget::item:selected {
            background: #2e4268;
            color: #e0e8f8;
        }
        QTreeWidget::branch {
            background: #161820;
        }
        QHeaderView::section {
            background: #1a1d28;
            color: #8ab0d8;
            border: none;
            padding: 4px;
            font-weight: bold;
        }
        QScrollBar:vertical {
            background: #161820;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: #3a4460;
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover { background: #4a5878; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    """

    # Main window menu bar
    MENUBAR_STYLE: str = """
        QMenuBar {
            background: #12141a;
            color: #c0c8d8;
            border-bottom: 1px solid #2a2e3e;
        }
        QMenuBar::item:selected {
            background: #2a3550;
            color: #e0e8f8;
        }
        QMenu {
            background: #1a1d28;
            color: #c0c8d8;
            border: 1px solid #3a4460;
        }
        QMenu::item:selected {
            background: #2a3e60;
            color: #e8f0ff;
        }
        QMenu::separator {
            height: 1px;
            background: #2e3448;
            margin: 2px 8px;
        }
    """

    # Toolbar
    TOOLBAR_STYLE: str = """
        QToolBar {
            background: #161820;
            border-bottom: 1px solid #2a2e3e;
            spacing: 4px;
            padding: 2px 4px;
        }
        QToolBar::separator {
            background: #2a2e3e;
            width: 1px;
            margin: 4px 2px;
        }
        QToolButton {
            background: transparent;
            color: #b0b8cc;
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 3px 8px;
            font-size: 9pt;
        }
        QToolButton:hover  { background: #252d40; border-color: #3a4460; }
        QToolButton:pressed{ background: #2e3a58; }
    """

    # Status bar
    STATUSBAR_STYLE: str = """
        QStatusBar {
            background: #12141a;
            color: #707888;
            border-top: 1px solid #2a2e3e;
            font-size: 8pt;
        }
    """

    # Splitter handle
    SPLITTER_STYLE: str = """
        QSplitter::handle {
            background: #1e2230;
        }
        QSplitter::handle:horizontal { width:  4px; }
        QSplitter::handle:vertical   { height: 4px; }
        QSplitter::handle:hover      { background: #3a4460; }
    """

    # Combo box in the preview toolbar (mode selector)
    PREVIEW_COMBO_STYLE: str = """
        QComboBox {
            background: #1e2230;
            color: #c0c8d8;
            border: 1px solid #3a4460;
            border-radius: 3px;
            padding: 2px 6px;
            font-size: 8pt;
        }
        QComboBox:focus { border: 1px solid #5294e2; }
        QComboBox::drop-down { border: none; width: 18px; }
        QComboBox::down-arrow {
            border-left:  4px solid transparent;
            border-right: 4px solid transparent;
            border-top:   5px solid #8ab0d8;
            margin-right: 4px;
        }
        QComboBox QAbstractItemView {
            background: #1e2230;
            color: #c0c8d8;
            selection-background-color: #2e4268;
            border: 1px solid #3a4460;
        }
    """

    # Preview header bar (contains Mode combo, Codes / Comments checkboxes)
    PREVIEW_HEADER_STYLE: str = (
        "background: #1a1d28; border-bottom: 1px solid #2a2e3e;"
    )

    PREVIEW_LABEL_STYLE: str = (
        "font-weight: bold; background: transparent;"
        " color: #8ab0d8; padding: 5px;"
    )

    PREVIEW_CHECKBOX_STYLE: str = """
        QCheckBox {
            color: #8a98b0;
            font-size: 8pt;
            background: transparent;
            spacing: 4px;
        }
        QCheckBox::indicator           { width: 13px; height: 13px; }
        QCheckBox::indicator:unchecked { border: 1px solid #464e62;
                                         border-radius: 2px;
                                         background: #1e2230; }
        QCheckBox::indicator:checked   { border: 1px solid #5294e2;
                                         border-radius: 2px;
                                         background: #5294e2; }
    """

    # Scroll bars (used in QGraphicsView viewports)
    SCROLLBAR_STYLE: str = """
        QScrollBar:vertical, QScrollBar:horizontal {
            background: #161820;
            border-radius: 4px;
        }
        QScrollBar:vertical   { width:  8px; }
        QScrollBar:horizontal { height: 8px; }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background: #3a4460;
            border-radius: 4px;
            min-width:  20px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover,
        QScrollBar::handle:horizontal:hover { background: #4a5878; }
        QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
    """

    # ── QPalette ─────────────────────────────────────────────────────────────

    def build_palette(self) -> QPalette:
        """Return a QPalette that makes Qt widgets follow the dark theme."""
        p = QPalette()

        # Window / base backgrounds
        p.setColor(QPalette.Window,          _BG_DARK)
        p.setColor(QPalette.WindowText,      _TEXT_BRIGHT)
        p.setColor(QPalette.Base,            _BG_MID)
        p.setColor(QPalette.AlternateBase,   _BG_RAISED)
        p.setColor(QPalette.ToolTipBase,     _BG_RAISED)
        p.setColor(QPalette.ToolTipText,     _TEXT_BRIGHT)

        # Text
        p.setColor(QPalette.Text,            _TEXT_BRIGHT)
        p.setColor(QPalette.BrightText,      QColor(255, 255, 255))
        p.setColor(QPalette.PlaceholderText, _TEXT_DIM)

        # Buttons
        p.setColor(QPalette.Button,          _BG_RAISED)
        p.setColor(QPalette.ButtonText,      _TEXT_BRIGHT)

        # Highlights
        p.setColor(QPalette.Highlight,       _BG_SELECTED)
        p.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        # Links
        p.setColor(QPalette.Link,            _ACCENT_BLUE)
        p.setColor(QPalette.LinkVisited,     QColor(180, 100, 220))

        # Disabled variants
        p.setColor(QPalette.Disabled, QPalette.WindowText, _TEXT_DIM)
        p.setColor(QPalette.Disabled, QPalette.Text,       _TEXT_DIM)
        p.setColor(QPalette.Disabled, QPalette.ButtonText, _TEXT_DIM)
        p.setColor(QPalette.Disabled, QPalette.Base,       QColor(22, 24, 32))

        return p

    def apply_palette(self, app) -> None:
        """
        Call once at startup to apply the dark palette to the whole app.

        Example::

            from theme_dark import theme
            theme.apply_palette(app)   # app = QApplication instance
        """
        app.setPalette(self.build_palette())
        app.setStyle("Fusion")   # Fusion respects custom palettes correctly


# Module-level singleton — the only object other modules need to import
theme = _DarkTheme()
