#!/usr/bin/env python3
"""
Component Designer for FreeCAD Road Workbench
Main entry point for the application
"""
import sys
from PySide2.QtWidgets import QApplication

from main_window import ComponentDesigner


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set application metadata
    app.setApplicationName("Component Designer")
    app.setOrganizationName("FreeCAD Road Workbench")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = ComponentDesigner()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
