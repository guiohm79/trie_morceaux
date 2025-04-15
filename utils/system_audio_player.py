#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module pour ouvrir les fichiers audio avec le lecteur par défaut du système
"""

import os
import subprocess
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSizePolicy, QMessageBox
)

class SystemAudioPlayer(QWidget):
    """Ouvre les fichiers audio avec le lecteur par défaut du système"""
    
    def __init__(self, parent=None):
        """
        Initialisation du lecteur audio
        
        Args:
            parent (QWidget): Widget parent
        """
        super(SystemAudioPlayer, self).__init__(parent)
        
        # Configuration de l'interface
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Label pour le nom du fichier
        self.lbl_filename = QLabel("Aucun fichier sélectionné")
        self.lbl_filename.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_filename)
        
        # Bouton pour ouvrir le fichier
        self.btn_open = QPushButton("Ouvrir avec le lecteur par défaut")
        self.btn_open.clicked.connect(self.open_file)
        self.btn_open.setEnabled(False)
        
        # Ajout du bouton au layout
        layout.addWidget(self.btn_open)
        
        # Configuration des tailles
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Fichier actuel
        self.current_file = None
    
    def load_file(self, file_path):
        """
        Préparation pour ouvrir un fichier audio
        
        Args:
            file_path (str): Chemin du fichier audio
        
        Returns:
            bool: Succès du chargement
        """
        # Vérification du fichier
        path = Path(file_path)
        if not path.exists() or path.suffix.lower() != '.wav':
            self.lbl_filename.setText("Fichier invalide")
            self.current_file = None
            self.btn_open.setEnabled(False)
            return False
        
        # Mise à jour de l'interface
        self.lbl_filename.setText(f"Fichier: {path.name}")
        self.current_file = str(path)
        self.btn_open.setEnabled(True)
        
        # Ouvrir automatiquement le fichier
        self.open_file()
        
        return True
    
    def open_file(self):
        """Ouvre le fichier avec le lecteur par défaut du système"""
        if not self.current_file:
            return
        
        try:
            print(f"Ouverture du fichier: {self.current_file}")
            
            # Ouvrir avec le lecteur par défaut du système
            if os.name == 'nt':  # Windows
                os.startfile(self.current_file)
            elif os.name == 'posix':  # Linux/Mac
                subprocess.Popen(['xdg-open', self.current_file])
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'ouverture du fichier: {e}")
            QMessageBox.warning(
                self, 
                "Erreur", 
                f"Impossible d'ouvrir le fichier audio:\n{str(e)}"
            )
            return False
    
    def toggle_playback(self):
        """Pour compatibilité avec l'interface précédente"""
        self.open_file()
