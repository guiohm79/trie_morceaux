#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe de base pour les fenêtres principales de l'application
"""

import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QToolBar, QAction, QStatusBar, QLabel, QSplitter,
    QApplication, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from config.constants import UI_WINDOW_TITLE, UI_MIN_WIDTH, UI_MIN_HEIGHT
from config.settings import settings

class BaseWindow(QMainWindow):
    """Classe de base pour les fenêtres principales de l'application"""
    
    def __init__(self):
        """Initialisation de la fenêtre de base"""
        super().__init__()
        
        # Configuration de base de la fenêtre
        self.setWindowTitle(UI_WINDOW_TITLE)
        self.setMinimumSize(UI_MIN_WIDTH, UI_MIN_HEIGHT)
        
        # Chargement des préférences
        settings.load()
        
        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Barre d'outils
        self.setup_toolbar()
        
        # Barre de statut
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Prêt")
        
        # Application du thème
        self.apply_theme()
    
    def setup_toolbar(self):
        """Configuration de la barre d'outils commune"""
        self.toolbar = QToolBar("Barre d'outils principale")
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)
        
        # Action pour basculer le thème (mode sombre)
        self.action_toggle_theme = QAction("Mode sombre", self)
        self.action_toggle_theme.setCheckable(True)
        self.action_toggle_theme.setChecked(settings.dark_mode)
        self.action_toggle_theme.toggled.connect(self.toggle_theme)
        self.toolbar.addAction(self.action_toggle_theme)
        
        # Les classes dérivées peuvent ajouter leurs propres actions
        self.setup_specific_toolbar()
        
        self.toolbar.addSeparator()
    
    def setup_specific_toolbar(self):
        """
        Méthode à surcharger dans les classes dérivées pour ajouter
        des actions spécifiques à la barre d'outils
        """
        pass
    
    def toggle_theme(self):
        """Basculer entre le mode clair et le mode sombre"""
        settings.dark_mode = self.action_toggle_theme.isChecked()
        settings.save()
        
        self.apply_theme()
    
    def apply_theme(self):
        """Appliquer le thème actuel"""
        app = QApplication.instance()
        
        if settings.dark_mode:
            # Mode sombre
            style_path = Path(__file__).parent.parent.parent / 'styles' / 'dark_theme.qss'
            if style_path.exists():
                with open(style_path, 'r') as f:
                    app.setStyleSheet(f.read())
                self.action_toggle_theme.setText("Mode clair")
                print("Mode sombre activé")
        else:
            # Mode clair
            app.setStyleSheet("")
            self.action_toggle_theme.setText("Mode sombre")
            print("Mode clair activé")
    
    def closeEvent(self, event):
        """Gestion de la fermeture de l'application"""
        # Sauvegarder les préférences
        settings.save()
        
        # Accepter l'événement de fermeture
        event.accept()
    
    def show_error(self, title, message):
        """Afficher un message d'erreur"""
        QMessageBox.critical(self, title, message)
    
    def show_warning(self, title, message):
        """Afficher un message d'avertissement"""
        QMessageBox.warning(self, title, message)
    
    def show_info(self, title, message):
        """Afficher un message d'information"""
        QMessageBox.information(self, title, message)
    
    def show_question(self, title, message):
        """Afficher une question avec boutons Oui/Non"""
        return QMessageBox.question(
            self, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        ) == QMessageBox.Yes
