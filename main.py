#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Application de tri et gestion des projets Cubase
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    """Point d'entrée de l'application"""
    app = QApplication(sys.argv)
    app.setApplicationName("Tri Morceaux Cubase")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
