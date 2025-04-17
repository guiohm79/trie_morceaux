#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Composant d'arborescence de fichiers pour l'application
"""

from PyQt5.QtWidgets import (
    QTreeView, QFileSystemModel, QMenu, QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal, QModelIndex, QDir

class FileTree(QTreeView):
    """Composant d'arborescence de fichiers basé sur QTreeView et QFileSystemModel"""
    
    # Signaux personnalisés
    item_selected = pyqtSignal(str)
    item_double_clicked = pyqtSignal(str)
    context_menu_requested = pyqtSignal(str, bool, object)  # path, is_dir, position
    
    def __init__(self, parent=None, allow_navigation_up=False):
        """
        Initialisation de l'arborescence de fichiers
        
        Args:
            parent (QWidget): Widget parent
            allow_navigation_up (bool): Autoriser la navigation vers les dossiers parents
        """
        super(FileTree, self).__init__(parent)
        
        # Stocker l'option de navigation
        self.allow_navigation_up = allow_navigation_up
        
        # Création du modèle de système de fichiers
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath("")
        
        # Configuration de la vue
        self.setModel(self.fs_model)
        self.setHeaderHidden(False)
        self.setMinimumWidth(250)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAnimated(True)
        self.setSortingEnabled(True)
        
        # Configuration des colonnes
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        
        # Configuration du menu contextuel
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu_requested)
        
        # Connexion des signaux
        self.clicked.connect(self._on_item_clicked)
        self.doubleClicked.connect(self._on_item_double_clicked)
    
    def set_root_path(self, path):
        """
        Définition du dossier racine de l'arborescence
        
        Args:
            path (str): Chemin du dossier racine
        """
        if not path:
            return
        
        # Définir le chemin racine dans le modèle
        self.fs_model.setRootPath(path)
        
        # Définir l'index racine dans la vue
        self.setRootIndex(self.fs_model.index(path))
        
        # Configurer la possibilité de remonter dans l'arborescence
        if self.allow_navigation_up:
            # Autoriser la navigation vers les dossiers parents
            self.setRootIsDecorated(True)
            # Ne pas masquer les dossiers parents dans le modèle
            self.fs_model.setFilter(self.fs_model.filter() & ~QDir.NoDotAndDotDot)
        else:
            # Masquer les dossiers parents (..) dans le modèle
            self.fs_model.setFilter(self.fs_model.filter() | QDir.NoDotAndDotDot)
    
    def get_selected_path(self):
        """
        Récupération du chemin de l'élément sélectionné
        
        Returns:
            str: Chemin de l'élément sélectionné ou None
        """
        indexes = self.selectedIndexes()
        if not indexes:
            return None
        
        return self.fs_model.filePath(indexes[0])
    
    def is_selected_dir(self):
        """
        Vérification si l'élément sélectionné est un dossier
        
        Returns:
            bool: True si l'élément sélectionné est un dossier, False sinon
        """
        indexes = self.selectedIndexes()
        if not indexes:
            return False
        
        return self.fs_model.isDir(indexes[0])
    
    def _on_item_clicked(self, index):
        """
        Gestion du clic sur un élément
        
        Args:
            index (QModelIndex): Index de l'élément cliqué
        """
        path = self.fs_model.filePath(index)
        self.item_selected.emit(path)
    
    def _on_item_double_clicked(self, index):
        """
        Gestion du double-clic sur un élément
        
        Args:
            index (QModelIndex): Index de l'élément double-cliqué
        """
        path = self.fs_model.filePath(index)
        self.item_double_clicked.emit(path)
    
    def _on_context_menu_requested(self, pos):
        """
        Gestion de la demande de menu contextuel
        
        Args:
            pos (QPoint): Position de la demande
        """
        index = self.indexAt(pos)
        if not index.isValid():
            return
        
        path = self.fs_model.filePath(index)
        is_dir = self.fs_model.isDir(index)
        
        self.context_menu_requested.emit(path, is_dir, self.viewport().mapToGlobal(pos))
    
    def select_path(self, path):
        """
        Sélection d'un élément par son chemin
        
        Args:
            path (str): Chemin de l'élément à sélectionner
            
        Returns:
            bool: Succès de l'opération
        """
        index = self.fs_model.index(path)
        if not index.isValid():
            return False
        
        self.setCurrentIndex(index)
        self.scrollTo(index)
        return True
