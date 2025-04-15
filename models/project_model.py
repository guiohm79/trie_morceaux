#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèle de données pour les projets Cubase
"""

from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant, QModelIndex
from PyQt5.QtGui import QColor, QBrush
from datetime import datetime
from pathlib import Path

class ProjectTableModel(QAbstractTableModel):
    """Modèle de table pour l'affichage des projets dans la vue"""
    
    def __init__(self, data=None):
        """
        Initialisation du modèle
        
        Args:
            data (list): Liste de dictionnaires contenant les données des projets
        """
        super(ProjectTableModel, self).__init__()
        self._data = [] if data is None else data
        self._headers = [
            "Nom du projet", 
            "Source",
            "CPR récent", 
            "Date modif.", 
            "Nb CPR", 
            "Nb BAK", 
            "Nb WAV", 
            "Taille (MB)"
        ]
        self._columns = [
            'project_name', 
            'source',
            'latest_cpr', 
            'latest_cpr_date', 
            'cpr_count', 
            'bak_count', 
            'wav_count', 
            'total_size_mb'
        ]
        
        # Couleurs pour différencier les sources
        self._source_colors = {
            # Couleurs pastel pour différencier les sources
            0: QColor(230, 245, 255),  # Bleu clair
            1: QColor(255, 230, 230),  # Rouge clair
            2: QColor(230, 255, 230),  # Vert clair
            3: QColor(255, 255, 230),  # Jaune clair
            4: QColor(255, 230, 255),  # Magenta clair
            5: QColor(230, 255, 255),  # Cyan clair
        }
        
        # Dictionnaire pour stocker les couleurs associées à chaque source
        self._source_to_color = {}
        
        # Mode d'affichage (par projet ou par dossier)
        self._view_mode = "project"  # "project" ou "folder"
    
    def rowCount(self, parent=QModelIndex()):
        """Nombre de lignes dans le modèle"""
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        """Nombre de colonnes dans le modèle"""
        return len(self._headers)
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """En-têtes du tableau"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]
        return QVariant()
    
    def data(self, index, role=Qt.DisplayRole):
        """Données à afficher dans le tableau"""
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        
        if row >= len(self._data) or self._columns[col] not in self._data[row]:
            return QVariant()
        
        if role == Qt.DisplayRole:
            value = self._data[row][self._columns[col]]
            
            # Formatage des dates
            if isinstance(value, datetime):
                return value.strftime("%d/%m/%Y %H:%M")
            
            # Formatage des chemins de fichiers (afficher seulement le nom)
            if isinstance(value, str) and '\\' in value:
                return value.split('\\')[-1]
            
            return str(value)
        
        # Coloration des lignes en fonction de la source
        elif role == Qt.BackgroundRole:
            source = self._data[row].get('source', '')
            
            # Si c'est une source multiple, pas de coloration spécifique
            if source == "Plusieurs sources":
                return QVariant()
            
            # Sinon, attribuer une couleur à la source si ce n'est pas déjà fait
            if source not in self._source_to_color and source:
                color_index = len(self._source_to_color) % len(self._source_colors)
                self._source_to_color[source] = self._source_colors[color_index]
            
            # Retourner la couleur associée à la source
            if source in self._source_to_color:
                return QBrush(self._source_to_color[source])
        
        # Mise en évidence des fichiers les plus récents
        elif role == Qt.FontRole and col == 2:  # Colonne CPR récent
            if self._data[row].get('is_latest', False):
                from PyQt5.QtGui import QFont
                font = QFont()
                font.setBold(True)
                return font
        
        return QVariant()
    
    def update_data(self, data, view_mode="project"):
        """
        Mise à jour des données du modèle
        
        Args:
            data (list): Nouvelles données
            view_mode (str): Mode d'affichage ("project" ou "folder")
        """
        self.beginResetModel()
        self._data = data if data is not None else []
        self._view_mode = view_mode
        
        # Réinitialiser les couleurs des sources
        self._source_to_color = {}
        
        # Marquer les projets les plus récents dans chaque dossier
        if view_mode == "folder" and self._data:
            # Grouper par dossier et trouver le plus récent dans chaque groupe
            folders = {}
            for project in self._data:
                folder = Path(project.get('source', '')).name
                if folder not in folders:
                    folders[folder] = []
                folders[folder].append(project)
            
            # Marquer le plus récent dans chaque dossier
            for folder, projects in folders.items():
                if projects:
                    # Trouver le projet le plus récent dans ce dossier
                    latest = max(projects, key=lambda x: x.get('latest_cpr_date', datetime.min) 
                                if x.get('latest_cpr_date') else datetime.min)
                    latest['is_latest'] = True
        
        self.endResetModel()
    
    def get_project_at_row(self, row):
        """
        Récupération du nom du projet à une ligne donnée
        
        Args:
            row (int): Indice de la ligne
            
        Returns:
            str: Nom du projet
        """
        if 0 <= row < len(self._data):
            return self._data[row]['project_name']
        return None
        
    def get_source_color(self, source):
        """
        Récupération de la couleur associée à une source
        
        Args:
            source (str): Chemin de la source
            
        Returns:
            QColor: Couleur associée à la source
        """
        if source in self._source_to_color:
            return self._source_to_color[source]
        return None
    
    def set_view_mode(self, mode):
        """
        Définition du mode d'affichage
        
        Args:
            mode (str): Mode d'affichage ("project" ou "folder")
        """
        if mode in ["project", "folder"] and mode != self._view_mode:
            self._view_mode = mode
            return True
        return False
