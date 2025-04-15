#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de lecture audio simplifié pour les fichiers WAV
Utilise le lecteur audio par défaut du système
"""

import os
import subprocess
from pathlib import Path
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSizePolicy, QStyle
)

class SimpleAudioPlayer(QWidget):
    """Lecteur audio simple qui utilise le lecteur par défaut du système"""
    
    # Signal émis lorsque la lecture est terminée
    playback_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Initialisation du lecteur audio
        
        Args:
            parent (QWidget): Widget parent
        """
        super(SimpleAudioPlayer, self).__init__(parent)
        
        # Chemin du fichier audio actuel
        self.current_file = None
        self.is_playing = False
        self.process = None
        
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
        
        # Layout pour les contrôles
        controls_layout = QHBoxLayout()
        
        # Bouton de lecture/pause
        self.btn_play = QPushButton("Lire")
        self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_play.clicked.connect(self.toggle_playback)
        self.btn_play.setEnabled(False)
        
        # Bouton d'arrêt
        self.btn_stop = QPushButton("Arrêter")
        self.btn_stop.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.btn_stop.clicked.connect(self.stop_playback)
        self.btn_stop.setEnabled(False)
        
        # Ajout des widgets au layout des contrôles
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_stop)
        
        # Ajout du layout des contrôles au layout principal
        layout.addLayout(controls_layout)
        
        # Configuration des tailles
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
    
    def load_file(self, file_path):
        """
        Chargement d'un fichier audio
        
        Args:
            file_path (str): Chemin du fichier audio
        
        Returns:
            bool: Succès du chargement
        """
        # Arrêt de la lecture en cours
        self.stop_playback()
        
        # Chargement du fichier
        path = Path(file_path)
        if not path.exists() or path.suffix.lower() != '.wav':
            self.lbl_filename.setText("Fichier invalide")
            self.current_file = None
            self.btn_play.setEnabled(False)
            self.btn_stop.setEnabled(False)
            return False
        
        # Mise à jour de l'interface
        self.lbl_filename.setText(path.name)
        self.current_file = str(path)
        
        # Activation des contrôles
        self.btn_play.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
        return True
    
    def toggle_playback(self):
        """Démarrage ou pause de la lecture"""
        if not self.current_file:
            return
        
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()
    
    def start_playback(self):
        """Démarrage de la lecture"""
        if not self.current_file or self.is_playing:
            return
        
        try:
            # Utiliser le lecteur par défaut du système
            if os.name == 'nt':  # Windows
                self.process = subprocess.Popen(['start', '', self.current_file], shell=True)
            elif os.name == 'posix':  # Linux/Mac
                self.process = subprocess.Popen(['xdg-open', self.current_file])
            
            self.is_playing = True
            self.btn_play.setText("Arrêter")
            self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.btn_stop.setEnabled(True)
            
            print(f"Lecture du fichier: {self.current_file}")
            return True
        except Exception as e:
            print(f"Erreur lors de la lecture: {e}")
            return False
    
    def stop_playback(self):
        """Arrêt de la lecture"""
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
            self.process = None
        
        self.is_playing = False
        self.btn_play.setText("Lire")
        self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_stop.setEnabled(False)
        self.playback_finished.emit()
