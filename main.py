#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Application de tri et gestion des projets Cubase
"""

import sys
import argparse
from PyQt5.QtWidgets import QApplication

from gui.sort_mode.sort_window import SortWindow
from gui.workspace_mode.workspace_window import WorkspaceWindow
from config.constants import MODE_TRI, MODE_WORKSPACE, UI_WINDOW_TITLE
from config.settings import settings

def parse_arguments():
    """Analyse des arguments de la ligne de commande"""
    parser = argparse.ArgumentParser(description="Application de gestion de projets Cubase")
    parser.add_argument(
        "--mode", 
        choices=[MODE_TRI, MODE_WORKSPACE], 
        default=MODE_WORKSPACE,
        help="Mode de fonctionnement de l'application (tri ou workspace)"
    )
    return parser.parse_args()

def main():
    """Point d'entrée de l'application"""
    # Analyse des arguments
    args = parse_arguments()
    
    # Création de l'application
    app = QApplication(sys.argv)
    app.setApplicationName(UI_WINDOW_TITLE)
    
    # Création de la fenêtre selon le mode
    if args.mode == MODE_TRI:
        window = SortWindow()
    else:  # MODE_WORKSPACE par défaut
        window = WorkspaceWindow()
    
    # Affichage de la fenêtre
    window.show()
    
    # Exécution de l'application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
