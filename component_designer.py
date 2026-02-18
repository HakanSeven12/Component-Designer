#!/usr/bin/env python3
"""
Component Designer for FreeCAD Road Workbench
"""
import sys
from PySide2.QtWidgets import QApplication

from .main_window import ComponentDesigner


def main():
    # Reuse existing QApplication instance if already running (e.g. inside FreeCAD)
    app = QApplication.instance()
    if app is None:
        # Standalone mode: create a new QApplication
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        standalone = True
    else:
        standalone = False

    app.setApplicationName("Component Designer")
    app.setOrganizationName("FreeCAD Road Workbench")
    app.setApplicationVersion("1.0")

    window = ComponentDesigner()
    window.show()

    if standalone:
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()