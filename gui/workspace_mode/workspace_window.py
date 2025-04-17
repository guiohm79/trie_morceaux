#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fenêtre principale du mode Espace de Travail (unique)
"""

import os
from pathlib import Path
import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog,
    QGroupBox, QCheckBox, QMessageBox, QProgressBar,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QComboBox, QAction, QLineEdit, QMenu, QTextEdit, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

from gui.base.base_window import BaseWindow
from gui.components.audio_player import AudioPlayer
from gui.components.file_tree import FileTree
from gui.components.metadata_editor import MetadataEditor
from gui.components.project_table import ProjectTable

from services.scanner import CubaseScanner
from services.metadata_service import MetadataService
from services.file_service import FileService
from services.audio_service import AudioService
from services.cubase_service import CubaseService

from config.constants import FILE_TREE_COLUMNS
from config.settings import settings

class WorkspaceWindow(BaseWindow):
    """Fenêtre principale du mode Espace de Travail (unique)"""
    
    def __init__(self):
        """Initialisation de la fenêtre du mode Espace de Travail"""
        super().__init__()
        
        # Services
        self.scanner = CubaseScanner()
        self.metadata_service = MetadataService(mode='local')
        self.file_service = FileService()
        self.audio_service = AudioService()
        self.cubase_service = CubaseService()
        
        # Données
        self.workspace_dir = settings.last_workspace
        self.all_projects_data = []
        
        # Configuration de l'interface
        self.setup_ui()
        
        # Mise à jour du titre
        self.setWindowTitle("Tri Morceaux Cubase - Mode Espace de Travail")
        
        # Chargement du workspace s'il existe
        if self.workspace_dir and os.path.exists(self.workspace_dir):
            self.setup_workspace_view(self.workspace_dir)
    
    def setup_specific_toolbar(self):
        """Configuration spécifique de la barre d'outils"""
        # Action pour choisir le dossier de travail
        self.action_select_workspace = QAction("Choisir dossier de travail...", self)
        self.action_select_workspace.triggered.connect(self.select_workspace_dir)
        self.toolbar.addAction(self.action_select_workspace)
        
        # Action pour vider le workspace
        self.action_reset_workspace = QAction("Vider le workspace", self)
        self.action_reset_workspace.setToolTip("Réinitialiser le workspace")
        self.action_reset_workspace.triggered.connect(self.reset_workspace)
        self.toolbar.addAction(self.action_reset_workspace)
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Widget central déjà créé dans BaseWindow
        
        # Label pour le chemin du workspace courant
        self.lbl_workspace_path = QLabel()
        if self.workspace_dir:
            self.lbl_workspace_path.setText(f"Dossier de travail : {self.workspace_dir}")
        else:
            self.lbl_workspace_path.setText("Dossier de travail : (aucun)")
        self.main_layout.addWidget(self.lbl_workspace_path)
        
        # Groupe pour les résultats
        results_group = QGroupBox("Projets")
        results_layout = QVBoxLayout(results_group)
        
        # Contrôles de filtrage et tri
        filter_layout = QHBoxLayout()
        
        # Filtre par nom
        self.lbl_filter = QLabel("Filtrer par nom:")
        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("Entrez un nom de projet...")
        self.txt_filter.textChanged.connect(self.filter_projects)
        
        # Tri par colonne
        self.lbl_sort = QLabel("Trier par:")
        self.cmb_sort = QComboBox()
        self.cmb_sort.addItems(["Nom du projet", "Date de modification", "Taille"])
        self.cmb_sort.currentIndexChanged.connect(self.sort_projects)
        
        # Ordre de tri
        self.chk_sort_desc = QCheckBox("Ordre décroissant")
        self.chk_sort_desc.stateChanged.connect(self.sort_projects)
        
        # Mode de visualisation
        self.lbl_view_mode = QLabel("Mode d'affichage:")
        self.cmb_view_mode = QComboBox()
        self.cmb_view_mode.addItems(["Par projet", "Par dossier"])
        self.cmb_view_mode.currentIndexChanged.connect(self.change_view_mode)
        
        filter_layout.addWidget(self.lbl_filter)
        filter_layout.addWidget(self.txt_filter, 2)
        filter_layout.addWidget(self.lbl_sort)
        filter_layout.addWidget(self.cmb_sort, 1)
        filter_layout.addWidget(self.chk_sort_desc)
        filter_layout.addWidget(self.lbl_view_mode)
        filter_layout.addWidget(self.cmb_view_mode, 1)
        
        # Table des projets
        self.project_table = ProjectTable()
        
        # Ajout des contrôles de filtrage et tri au layout
        results_layout.addLayout(filter_layout)
        results_layout.addWidget(self.project_table)
        
        # Détails du projet sélectionné
        details_group = QGroupBox("Détails du projet")
        details_layout = QVBoxLayout(details_group)
        
        # Arborescences de fichiers
        self.file_tree_left = FileTree()
        self.file_tree_left.context_menu_requested.connect(self.show_file_tree_left_context_menu)
        
        self.file_tree_right = FileTree()
        self.file_tree_right.context_menu_requested.connect(self.show_file_tree_right_context_menu)
        
        # Onglets pour les différentes vues
        self.details_tabs = QTabWidget()
        
        # Onglet des fichiers
        files_tab = QWidget()
        files_layout = QVBoxLayout(files_tab)
        
        # Lecteur audio pour les fichiers WAV
        self.audio_player = AudioPlayer()
        self.audio_player.setVisible(False)  # Masqué par défaut
        
        # Initialisation du service audio
        self.audio_service.initialize_player(self.audio_player)
        
        files_layout.addWidget(self.audio_player)
        
        # Onglet des métadonnées
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout(metadata_tab)
        
        # Éditeur de métadonnées
        self.metadata_editor = MetadataEditor()
        self.metadata_editor.save_requested.connect(self.save_project_metadata)
        
        metadata_layout.addWidget(self.metadata_editor)
        
        # Ajout des onglets
        self.details_tabs.addTab(files_tab, "Lecteur Audio")
        self.details_tabs.addTab(metadata_tab, "Tags & Notes")
        
        # Ajout du splitter horizontal : à gauche file_tree_left, au centre file_tree_right, à droite les tabs de détails
        self.details_splitter = QSplitter(Qt.Horizontal)
        self.details_splitter.addWidget(self.file_tree_left)
        self.details_splitter.addWidget(self.file_tree_right)
        self.details_splitter.addWidget(self.details_tabs)
        self.details_splitter.setStretchFactor(0, 1)
        self.details_splitter.setStretchFactor(1, 1)
        self.details_splitter.setStretchFactor(2, 2)
        
        details_layout.addWidget(self.details_splitter)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(results_group)
        main_splitter.addWidget(details_group)
        main_splitter.setSizes([400, 600])
        
        # Ajout du splitter au layout principal
        self.main_layout.addWidget(main_splitter, 3)
        
        # Connexion des signaux
        self.project_table.project_selected.connect(self.show_project_details)
        self.file_tree_left.item_selected.connect(self.on_file_tree_left_selected)
        self.file_tree_left.item_double_clicked.connect(self.on_file_tree_item_double_clicked)
        self.file_tree_right.item_double_clicked.connect(self.on_file_tree_item_double_clicked)
    
    def select_workspace_dir(self):
        """Sélection du dossier de travail"""
        directory = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier de travail", str(Path.home()))
        if directory:
            self.workspace_dir = directory
            self.lbl_workspace_path.setText(f"Dossier de travail : {directory}")
            settings.last_workspace = directory
            settings.save()
            
            # Configuration de la vue pour le workspace
            self.setup_workspace_view(directory)
    
    def setup_workspace_view(self, directory):
        """
        Configuration de la vue pour le workspace
        
        Args:
            directory (str): Chemin du dossier de travail
        """
        # Définition des racines des arborescences
        self.file_tree_left.set_root_path(directory)
        
        # Scan du dossier pour trouver les projets
        self.scanner.clear()
        self.scanner.scan_directory(directory)
        
        # Mise à jour de la table des projets
        self.all_projects_data = self.scanner.df_projects
        self.project_table.update_data(self.all_projects_data)
        
        # Message de statut
        self.statusBar.showMessage(f"{len(self.all_projects_data)} projets trouvés dans le dossier de travail")
    
    def reset_workspace(self):
        """Réinitialisation du workspace"""
        self.workspace_dir = None
        self.lbl_workspace_path.setText("Dossier de travail : (aucun)")
        settings.last_workspace = ""
        settings.save()
        
        # Réinitialisation des vues
        self.file_tree_left.set_root_path("")
        self.file_tree_right.set_root_path("")
        self.project_table.update_data([])
        
        # Message de statut
        self.statusBar.showMessage("Workspace vidé")
    
    def filter_projects(self):
        """Filtrage des projets par nom"""
        filter_text = self.txt_filter.text().strip()
        self.project_table.set_filter(filter_text)
    
    def sort_projects(self):
        """Tri des projets selon les critères sélectionnés"""
        column_index = self.cmb_sort.currentIndex()
        descending = self.chk_sort_desc.isChecked()
        order = Qt.DescendingOrder if descending else Qt.AscendingOrder
        
        # Correspondance entre l'index du combobox et la colonne du modèle
        column_mapping = {
            0: 0,  # Nom du projet
            1: 2,  # Date de modification
            2: 6   # Taille
        }
        
        if column_index in column_mapping:
            self.project_table.set_sort_column(column_mapping[column_index], order)
    
    def change_view_mode(self):
        """Changement du mode de visualisation"""
        view_mode = "folder" if self.cmb_view_mode.currentIndex() == 1 else "project"
        self.project_table.update_data(self.all_projects_data, view_mode)
    
    def show_project_details(self, project):
        """
        Affichage des détails d'un projet
        
        Args:
            project (dict): Projet sélectionné
        """
        if not project:
            return
        
        # Récupération des détails du projet
        project_name = project.get('project_name')
        
        # Utiliser directement le chemin du dossier du projet s'il est disponible
        project_folder = project.get('project_dir', '')
        
        # Si le chemin n'est pas disponible ou n'existe pas, essayer de le déterminer
        if not project_folder or not os.path.exists(project_folder):
            # Stratégie 1: Utiliser le chemin du premier fichier CPR s'il existe
            cpr_files = project.get('cpr_files', [])
            if cpr_files and len(cpr_files) > 0:
                # Utiliser le premier fichier CPR pour déterminer le dossier du projet
                cpr_path = cpr_files[0]
                if os.path.exists(cpr_path):
                    project_folder = os.path.dirname(cpr_path)
            
            # Si aucun dossier n'a été trouvé, utiliser le dossier source
            if not project_folder or not os.path.exists(project_folder):
                project_folder = project.get('source', '')
        
        # Mise à jour de l'arborescence de droite
        if project_folder and os.path.exists(project_folder):
            self.file_tree_right.set_root_path(project_folder)
        
        # Récupération des métadonnées du projet
        try:
            metadata = self.metadata_service.get_project_metadata(project_name, project_folder)
            self.metadata_editor.set_metadata(metadata)
        except Exception as e:
            print(f"Erreur lors de la récupération des métadonnées: {e}")
            self.metadata_editor.set_metadata({'tags': [], 'rating': 0, 'notes': ''})
        
        # Message de statut
        self.statusBar.showMessage(f"Projet sélectionné: {project_name}")
    
    def on_file_tree_left_selected(self, path):
        """
        Gestion de la sélection d'un élément dans l'arborescence de gauche
        
        Args:
            path (str): Chemin de l'élément sélectionné
        """
        if os.path.isdir(path):
            self.file_tree_right.set_root_path(path)
    
    def on_file_tree_item_double_clicked(self, path):
        """
        Gestion du double-clic sur un élément dans une arborescence
        
        Args:
            path (str): Chemin de l'élément double-cliqué
        """
        if not os.path.exists(path):
            return
        
        if os.path.isdir(path):
            # Si c'est un dossier, on l'affiche dans l'arborescence de droite
            self.file_tree_right.set_root_path(path)
        else:
            # Si c'est un fichier, on vérifie son type
            file_path = Path(path)
            if file_path.suffix.lower() == '.wav':
                # Lecture du fichier WAV
                self.audio_service.load_file(path)
                self.audio_player.setVisible(True)
                self.audio_service.play()
            elif file_path.suffix.lower() == '.cpr':
                # Ouverture du fichier CPR dans Cubase
                self.cubase_service.open_project(path)
    
    def show_file_tree_left_context_menu(self, path, is_dir, position):
        """
        Affichage du menu contextuel pour l'arborescence de gauche
        
        Args:
            path (str): Chemin de l'élément sélectionné
            is_dir (bool): True si l'élément est un dossier
            position (QPoint): Position du clic
        """
        menu = QMenu()
        
        # Actions communes
        set_workspace_action = menu.addAction("Définir comme dossier de travail")
        show_in_right_view_action = menu.addAction("Afficher dans la deuxième arborescence")
        
        # Affichage du menu
        action = menu.exec_(position)
        
        # Traitement de l'action sélectionnée
        if action == set_workspace_action:
            self.workspace_dir = path
            self.lbl_workspace_path.setText(f"Dossier de travail : {path}")
            settings.last_workspace = path
            settings.save()
            self.setup_workspace_view(path)
        elif action == show_in_right_view_action:
            self.file_tree_right.set_root_path(path)
    
    def show_file_tree_right_context_menu(self, path, is_dir, position):
        """
        Affichage du menu contextuel pour l'arborescence de droite
        
        Args:
            path (str): Chemin de l'élément sélectionné
            is_dir (bool): True si l'élément est un dossier
            position (QPoint): Position du clic
        """
        menu = QMenu()
        
        # Actions communes
        set_workspace_action = menu.addAction("Définir comme dossier de travail")
        menu.addSeparator()
        
        # Actions spécifiques aux dossiers
        if is_dir:
            create_folder_action = menu.addAction("Créer un nouveau dossier")
            create_file_action = menu.addAction("Créer un nouveau fichier")
            menu.addSeparator()
        
        # Actions pour tous les éléments
        rename_action = menu.addAction("Renommer")
        delete_action = menu.addAction("Supprimer")
        
        # Affichage du menu
        action = menu.exec_(position)
        
        # Traitement de l'action sélectionnée
        if action == set_workspace_action:
            self.workspace_dir = path
            self.lbl_workspace_path.setText(f"Dossier de travail : {path}")
            settings.last_workspace = path
            settings.save()
            self.setup_workspace_view(path)
        elif is_dir and action == create_folder_action:
            self.create_new_folder(path)
        elif is_dir and action == create_file_action:
            self.create_new_file(path)
        elif action == rename_action:
            self.rename_item(path)
        elif action == delete_action:
            self.delete_item(path)
    
    def create_new_folder(self, parent_path):
        """
        Création d'un nouveau dossier
        
        Args:
            parent_path (str): Chemin du dossier parent
        """
        folder_name, ok = QInputDialog.getText(self, "Nouveau dossier", "Nom du dossier:")
        
        if ok and folder_name:
            new_folder_path = os.path.join(parent_path, folder_name)
            success = self.file_service.create_directory(new_folder_path)
            
            if success:
                self.statusBar.showMessage(f"Dossier créé: {new_folder_path}")
                # Rafraîchir l'arborescence
                self.file_tree_right.set_root_path(parent_path)
            else:
                self.show_error("Erreur", f"Impossible de créer le dossier: {new_folder_path}")
    
    def create_new_file(self, parent_path):
        """
        Création d'un nouveau fichier
        
        Args:
            parent_path (str): Chemin du dossier parent
        """
        file_name, ok = QInputDialog.getText(self, "Nouveau fichier", "Nom du fichier:")
        
        if ok and file_name:
            new_file_path = os.path.join(parent_path, file_name)
            success = self.file_service.create_file(new_file_path)
            
            if success:
                self.statusBar.showMessage(f"Fichier créé: {new_file_path}")
                # Rafraîchir l'arborescence
                self.file_tree_right.set_root_path(parent_path)
            else:
                self.show_error("Erreur", f"Impossible de créer le fichier: {new_file_path}")
    
    def rename_item(self, path):
        """
        Renommage d'un élément
        
        Args:
            path (str): Chemin de l'élément à renommer
        """
        old_name = os.path.basename(path)
        parent_dir = os.path.dirname(path)
        
        new_name, ok = QInputDialog.getText(self, "Renommer", "Nouveau nom:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(parent_dir, new_name)
            success = self.file_service.rename_item(path, new_path)
            
            if success:
                self.statusBar.showMessage(f"Élément renommé: {path} -> {new_path}")
                # Rafraîchir l'arborescence
                self.file_tree_right.set_root_path(parent_dir)
            else:
                self.show_error("Erreur", f"Impossible de renommer l'élément: {path}")
    
    def delete_item(self, path):
        """
        Suppression d'un élément
        
        Args:
            path (str): Chemin de l'élément à supprimer
        """
        item_name = os.path.basename(path)
        is_dir = os.path.isdir(path)
        item_type = "dossier" if is_dir else "fichier"
        parent_dir = os.path.dirname(path)
        
        confirm = self.show_question(
            "Confirmation",
            f"Voulez-vous vraiment supprimer {item_type} '{item_name}' ?"
        )
        
        if confirm:
            success = self.file_service.delete_item(path)
            
            if success:
                self.statusBar.showMessage(f"{item_type.capitalize()} supprimé: {path}")
                # Rafraîchir l'arborescence
                self.file_tree_right.set_root_path(parent_dir)
            else:
                self.show_error("Erreur", f"Impossible de supprimer l'élément: {path}")
    
    def save_project_metadata(self):
        """Sauvegarde des métadonnées du projet sélectionné"""
        # Récupération du projet sélectionné
        selected_project = self.project_table.get_selected_project()
        if not selected_project:
            return
        
        project_name = selected_project.get('project_name')
        
        # Utiliser directement le chemin du dossier du projet s'il est disponible
        project_folder = selected_project.get('project_dir', '')
        
        # Si le chemin n'est pas disponible, utiliser le dossier source
        if not project_folder or not os.path.exists(project_folder):
            project_folder = selected_project.get('source', '')
        
        if not project_folder or not os.path.exists(project_folder):
            self.show_warning("Erreur", "Impossible de déterminer le dossier du projet!")
            return
        
        # Récupération des métadonnées depuis l'éditeur
        metadata = self.metadata_editor.get_metadata()
        
        # Sauvegarde des métadonnées
        try:
            self.metadata_service.set_project_metadata(project_name, metadata, project_folder)
            self.statusBar.showMessage(f"Métadonnées sauvegardées pour {project_name}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des métadonnées: {e}")
            self.statusBar.showMessage(f"Erreur lors de la sauvegarde des métadonnées: {e}")
