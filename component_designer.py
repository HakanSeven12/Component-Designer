#!/usr/bin/env python3
"""
Component Designer for FreeCAD Road Workbench
"""
import sys
from PySide2.QtWidgets import QApplication

from main_window import ComponentDesigner


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("Component Designer")
    app.setOrganizationName("FreeCAD Road Workbench")
    app.setApplicationVersion("1.0")

    window = ComponentDesigner()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()