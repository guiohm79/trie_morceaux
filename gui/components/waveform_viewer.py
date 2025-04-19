import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QBrush
from scipy.io import wavfile

class ModernWaveformPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setMinimumWidth(400)
        
        # Variables pour les données audio
        self.waveform_data = None
        self.sample_rate = None
        self.duration = 0
        self.current_position = 0
        
        # Interface
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Widget personnalisé pour le rendu de la forme d'onde
        self.waveform_widget = WaveformWidget(self)
        layout.addWidget(self.waveform_widget)
        
        # Contrôles (temps actuel et durée totale)
        controls_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.duration_label = QLabel("0:00")
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.setValue(0)
        self.position_slider.sliderMoved.connect(self.seek_position)
        
        controls_layout.addWidget(self.current_time_label)
        controls_layout.addWidget(self.position_slider)
        controls_layout.addWidget(self.duration_label)
        
        layout.addLayout(controls_layout)
        
        # Timer pour simuler la lecture
        self.timer = QTimer(self)
        self.timer.setInterval(50)  # Mise à jour toutes les 50ms
        self.timer.timeout.connect(self.update_position)
        
        # États
        self.is_playing = False
        
    def load_file(self, file_path):
        """Charge un fichier audio et prépare la visualisation"""
        try:
            # Charger les données audio
            sample_rate, data = wavfile.read(file_path)
            
            # Conversion mono si stéréo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            
            # Normaliser les données
            if data.dtype != np.float32:
                data = data.astype(np.float32) / (2**15 if data.dtype == np.int16 else 2**31)
            
            # Sous-échantillonner pour l'affichage
            # Pour un affichage fluide, réduire à ~1000-2000 points
            step = max(1, len(data) // 1500)
            waveform_data = data[::step]
            
            # Stocker les données
            self.waveform_data = waveform_data
            self.sample_rate = sample_rate
            self.duration = len(data) / sample_rate
            self.current_position = 0
            
            # Mettre à jour les labels
            self.duration_label.setText(self.format_time(self.duration))
            self.current_time_label.setText(self.format_time(0))
            
            # Mettre à jour le widget de forme d'onde
            self.waveform_widget.set_waveform_data(waveform_data)
            
            # Réinitialiser le slider
            self.position_slider.setValue(0)
            
            return True
        except Exception as e:
            print(f"Erreur lors du chargement du fichier audio: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def play_pause(self):
        """Démarre ou met en pause la lecture"""
        if not self.waveform_data is None:
            self.is_playing = not self.is_playing
            
            if self.is_playing:
                self.timer.start()
            else:
                self.timer.stop()
                
            return self.is_playing
        return False
    
    def stop(self):
        """Arrête la lecture et réinitialise la position"""
        self.is_playing = False
        self.timer.stop()
        self.current_position = 0
        self.position_slider.setValue(0)
        self.current_time_label.setText(self.format_time(0))
        self.waveform_widget.set_progress(0)
        
    def update_position(self):
        """Met à jour la position de lecture"""
        if self.duration > 0:
            # Simuler l'avancement (dans une vraie implémentation, vous obtiendriez 
            # cette valeur depuis le lecteur audio réel)
            self.current_position += 0.05  # +50ms
            
            if self.current_position >= self.duration:
                self.stop()
                return
            
            # Calculer la progression en pourcentage
            progress = self.current_position / self.duration
            
            # Mettre à jour le slider
            self.position_slider.setValue(int(progress * 1000))
            
            # Mettre à jour le label de temps
            self.current_time_label.setText(self.format_time(self.current_position))
            
            # Mettre à jour la visualisation
            self.waveform_widget.set_progress(progress)
    
    def seek_position(self, value):
        """Change la position de lecture"""
        if self.duration > 0:
            # Calculer la nouvelle position
            position = (value / 1000) * self.duration
            
            # Mettre à jour la position actuelle
            self.current_position = position
            
            # Mettre à jour le label de temps
            self.current_time_label.setText(self.format_time(position))
            
            # Mettre à jour la visualisation
            self.waveform_widget.set_progress(value / 1000)
    
    def format_time(self, seconds):
        """Formate le temps en minutes:secondes"""
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes}:{seconds:02d}"


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        
        # Données pour le rendu
        self.waveform_data = None
        self.progress = 0  # 0 à 1
        
        # Couleurs
        self.played_color = QColor(255, 120, 0)  # Orange pour la partie jouée
        self.remaining_color = QColor(255, 255, 255)  # Blanc pour la partie restante
        self.background_color = QColor(30, 30, 30)  # Fond presque noir
        
    def set_waveform_data(self, data):
        """Définit les données de forme d'onde à afficher"""
        self.waveform_data = data
        self.update()
        
    def set_progress(self, progress):
        """Définit la progression de la lecture (0-1)"""
        self.progress = max(0, min(1, progress))
        self.update()
        
    def paintEvent(self, event):
        """Dessine la forme d'onde"""
        if self.waveform_data is None:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fond
        painter.fillRect(self.rect(), self.background_color)
        
        # Dimensions
        width = self.width()
        height = self.height()
        center_y = height / 2
        
        # Position de progression
        progress_x = int(width * self.progress)
        
        # Dessin de la forme d'onde
        if len(self.waveform_data) > 0:
            # Distance entre chaque point
            dx = width / len(self.waveform_data)
            
            # Amplitude maximale pour la mise à l'échelle
            max_amp = max(abs(self.waveform_data.min()), abs(self.waveform_data.max()))
            scale = (height * 0.8) / (max_amp * 2)
            
            # Dessin de chaque segment de la forme d'onde
            for i in range(len(self.waveform_data) - 1):
                x1 = i * dx
                x2 = (i + 1) * dx
                
                amp1 = self.waveform_data[i] * scale
                amp2 = self.waveform_data[i + 1] * scale
                
                y1 = center_y - amp1
                y2 = center_y - amp2
                
                # Choisir la couleur selon la position
                if x1 <= progress_x:
                    pen = QPen(self.played_color, 2)
                else:
                    pen = QPen(self.remaining_color, 2)
                
                painter.setPen(pen)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                
                # Dessiner aussi la partie inférieure de la forme d'onde
                y1_bottom = center_y + amp1
                y2_bottom = center_y + amp2
                painter.drawLine(int(x1), int(y1_bottom), int(x2), int(y2_bottom))
        
        # Dessiner les indicateurs de temps
        time_font = painter.font()
        time_font.setPointSize(8)
        painter.setFont(time_font)
        
        # Début (toujours orange)
        painter.setPen(self.played_color)
        painter.drawText(5, height - 5, "0:00")
        
        # Fin (toujours blanc)
        painter.setPen(self.remaining_color)
        painter.drawText(width - 40, height - 5, "5:37")  # Exemple de durée