#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de lecture audio pour les fichiers WAV utilisant pygame
"""

import os
import time
import threading
from pathlib import Path
import pygame
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSlider, QSizePolicy, QStyle
)

class PygameAudioPlayer(QWidget):
    """Lecteur audio utilisant pygame pour les fichiers WAV"""
    
    # Signal émis lorsque la lecture est terminée
    playback_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Initialisation du lecteur audio
        
        Args:
            parent (QWidget): Widget parent
        """
        super(PygameAudioPlayer, self).__init__(parent)
        
        # Initialisation de pygame (avec gestion des erreurs)
        self.pygame_available = False
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.pygame_available = True
            print("Initialisation de pygame réussie")
        except Exception as e:
            print(f"Erreur lors de l'initialisation de pygame: {e}")
            print("L'aperçu audio ne sera pas disponible")
        
        # Chemin du fichier audio actuel
        self.current_file = None
        self.is_playing = False
        self.duration = 0
        self.current_position = 0
        
        # Configuration de l'interface
        self.setup_ui()
        
        # Timer pour mettre à jour la position
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(100)  # 100ms
        self.update_timer.timeout.connect(self.update_position)
    
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
        self.btn_play = QPushButton()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_play.clicked.connect(self.toggle_playback)
        self.btn_play.setEnabled(False)
        
        # Bouton d'arrêt
        self.btn_stop = QPushButton()
        self.btn_stop.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.btn_stop.clicked.connect(self.stop_playback)
        self.btn_stop.setEnabled(False)
        
        # Labels pour la position et la durée
        self.lbl_position = QLabel("00:00")
        self.lbl_duration = QLabel("00:00")
        
        # Slider pour la position
        self.slider_position = QSlider(Qt.Horizontal)
        self.slider_position.setRange(0, 0)
        self.slider_position.sliderMoved.connect(self.set_position)
        self.slider_position.setEnabled(False)
        
        # Ajout des widgets au layout des contrôles
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_stop)
        controls_layout.addWidget(self.lbl_position)
        controls_layout.addWidget(self.slider_position)
        controls_layout.addWidget(self.lbl_duration)
        
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
        # Vérifier si pygame est disponible
        if not self.pygame_available:
            self.lbl_filename.setText("Aperçu audio non disponible")
            return False
            
        # Arrêt de la lecture en cours
        self.stop_playback()
        
        # Chargement du fichier
        path = Path(file_path)
        if not path.exists() or path.suffix.lower() != '.wav':
            self.lbl_filename.setText("Fichier invalide")
            self.current_file = None
            self.btn_play.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.slider_position.setEnabled(False)
            return False
        
        try:
            # Chargement du fichier avec pygame
            pygame.mixer.music.load(str(path))
            
            # Obtenir la durée du fichier (en secondes)
            sound = pygame.mixer.Sound(str(path))
            self.duration = sound.get_length() * 1000  # Convertir en millisecondes
            
            # Mise à jour de l'interface
            self.lbl_filename.setText(path.name)
            self.current_file = str(path)
            self.current_position = 0
            
            # Mise à jour du slider
            self.slider_position.setRange(0, int(self.duration))
            
            # Mise à jour du label de durée
            minutes = int(self.duration) // 60000
            seconds = (int(self.duration) % 60000) // 1000
            self.lbl_duration.setText(f"{minutes:02d}:{seconds:02d}")
            
            # Activation des contrôles
            self.btn_play.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.slider_position.setEnabled(True)
            
            print(f"Fichier audio chargé: {path.name}, durée: {self.duration/1000:.2f}s")
            return True
            
        except Exception as e:
            print(f"Erreur lors du chargement du fichier audio: {e}")
            self.lbl_filename.setText(f"Erreur: {str(e)}")
            self.current_file = None
            self.btn_play.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.slider_position.setEnabled(False)
            return False
    
    def toggle_playback(self):
        """Démarrage ou pause de la lecture"""
        if not self.pygame_available or not self.current_file:
            return
        
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()
    
    def start_playback(self):
        """Démarrage de la lecture"""
        if not self.pygame_available or not self.current_file or self.is_playing:
            return
        
        try:
            # Si on reprend après une pause, on se positionne au bon endroit
            if self.current_position > 0:
                pygame.mixer.music.set_pos(self.current_position / 1000)  # En secondes
            
            # Démarrage de la lecture
            pygame.mixer.music.play()
            
            # Configuration de l'événement de fin
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
            
            # Démarrage d'un thread pour surveiller la fin de la lecture
            self.monitor_thread = threading.Thread(target=self.monitor_playback)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            # Mise à jour de l'interface
            self.is_playing = True
            self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.btn_stop.setEnabled(True)
            
            # Démarrage du timer pour mettre à jour la position
            self.update_timer.start()
            
            print(f"Lecture démarrée: {self.current_file}")
            return True
            
        except Exception as e:
            print(f"Erreur lors de la lecture: {e}")
            return False
    
    def pause_playback(self):
        """Pause de la lecture"""
        if not self.pygame_available or not self.is_playing:
            return
        
        try:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.update_timer.stop()
            
            print(f"Lecture en pause: {self.current_file}")
            return True
            
        except Exception as e:
            print(f"Erreur lors de la pause: {e}")
            return False
    
    def stop_playback(self):
        """Arrêt de la lecture"""
        if not self.pygame_available or not self.current_file:
            return
        
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.current_position = 0
            self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.btn_stop.setEnabled(False)
            self.update_timer.stop()
            
            # Mise à jour du slider
            self.slider_position.setValue(0)
            self.lbl_position.setText("00:00")
            
            print(f"Lecture arrêtée: {self.current_file}")
            self.playback_finished.emit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'arrêt: {e}")
            return False
    
    def set_position(self, position):
        """
        Définition de la position de lecture
        
        Args:
            position (int): Nouvelle position en millisecondes
        """
        if not self.pygame_available or not self.current_file:
            return
        
        try:
            # Arrêt de la lecture
            was_playing = self.is_playing
            pygame.mixer.music.stop()
            
            # Mise à jour de la position
            self.current_position = position
            
            # Mise à jour du label de position
            minutes = position // 60000
            seconds = (position % 60000) // 1000
            self.lbl_position.setText(f"{minutes:02d}:{seconds:02d}")
            
            # Redémarrage de la lecture si nécessaire
            if was_playing:
                pygame.mixer.music.load(self.current_file)  # Recharger le fichier
                pygame.mixer.music.play(start=position / 1000)  # Position en secondes
                self.is_playing = True
            
            print(f"Position définie: {position/1000:.2f}s")
            
        except Exception as e:
            print(f"Erreur lors de la définition de la position: {e}")
    
    def update_position(self):
        """Mise à jour de la position actuelle"""
        if not self.is_playing:
            return
        
        try:
            # Obtenir la position actuelle
            if pygame.mixer.music.get_busy():
                # Pygame ne fournit pas directement la position actuelle,
                # on utilise donc une estimation basée sur le temps écoulé
                self.current_position += 100  # 100ms (intervalle du timer)
                if self.current_position > self.duration:
                    self.current_position = self.duration
            else:
                # La lecture est terminée
                self.current_position = 0
                self.stop_playback()
                return
            
            # Mise à jour du slider
            self.slider_position.setValue(int(self.current_position))
            
            # Mise à jour du label de position
            minutes = int(self.current_position) // 60000
            seconds = (int(self.current_position) % 60000) // 1000
            self.lbl_position.setText(f"{minutes:02d}:{seconds:02d}")
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la position: {e}")
    
    def monitor_playback(self):
        """Surveillance de la fin de la lecture"""
        while self.is_playing:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT:
                    # La lecture est terminée
                    self.is_playing = False
                    self.current_position = 0
                    self.playback_finished.emit()
                    return
            time.sleep(0.1)
    
    def closeEvent(self, event):
        """Gestion de la fermeture du widget"""
        self.stop_playback()
        super(PygameAudioPlayer, self).closeEvent(event)
