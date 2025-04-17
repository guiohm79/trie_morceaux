#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fenêtre principale du mode Tri (multi-sources)
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

class ScanThread(QThread):
    """Thread pour le scan des dossiers"""
    scan_progress = pyqtSignal(int)
    scan_complete = pyqtSignal(dict)
    
    def __init__(self, directories):
        """
        Initialisation du thread
        
        Args:
            directories (list): Liste des dossiers à scanner
        """
        super().__init__()
        self.directories = directories
        self.scanner = CubaseScanner()
    
    def run(self):
        """Exécution du thread"""
        print(f"Démarrage du scan de {len(self.directories)} dossiers")
        total_dirs = len(self.directories)
        for i, directory in enumerate(self.directories):
            print(f"Scan du dossier: {directory}")
            self.scanner.scan_directory(directory)
            self.scan_progress.emit(int((i + 1) / total_dirs * 100))
        
        print(f"Scan terminé, {len(self.scanner.projects)} projets trouvés")
        self.scan_complete.emit(self.scanner.projects)

class SortWindow(BaseWindow):
    """Fenêtre principale du mode Tri (multi-sources)"""
    
    def __init__(self):
        """Initialisation de la fenêtre du mode Tri"""
        super().__init__()
        
        # Services
        self.scanner = CubaseScanner()
        self.metadata_service = MetadataService(mode='centralized')
        self.file_service = FileService()
        self.audio_service = AudioService()
        self.cubase_service = CubaseService()
        
        # Données
        self.selected_directories = []
        self.destination_directory = None
        self.all_projects_data = []
        
        # Configuration de l'interface
        self.setup_ui()
        
        # Mise à jour du titre
        self.setWindowTitle("Tri Morceaux Cubase - Mode Tri (multi-sources)")
    
    def setup_specific_toolbar(self):
        """Configuration spécifique de la barre d'outils"""
        # Action pour sauvegarder
        action_save = QAction("Sauvegarder", self)
        action_save.triggered.connect(self.save_selected_project)
        self.toolbar.addAction(action_save)
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Widget central déjà créé dans BaseWindow
        
        # Groupe pour la sélection des dossiers
        dir_group = QGroupBox("Sélection des dossiers")
        dir_layout = QVBoxLayout(dir_group)
        
        # Boutons pour ajouter/supprimer des dossiers
        btn_layout = QHBoxLayout()
        self.btn_add_dir = QPushButton("Ajouter un dossier")
        self.btn_add_dir.clicked.connect(self.add_directory)
        self.btn_clear_dirs = QPushButton("Effacer la liste")
        self.btn_clear_dirs.clicked.connect(self.clear_directories)
        btn_layout.addWidget(self.btn_add_dir)
        btn_layout.addWidget(self.btn_clear_dirs)
        
        # Liste des dossiers sélectionnés
        self.dir_list = QTreeWidget()
        self.dir_list.setHeaderLabels(["Dossiers sélectionnés"])
        self.dir_list.setColumnCount(1)
        
        # Bouton de scan
        self.btn_scan = QPushButton("Scanner les dossiers")
        self.btn_scan.clicked.connect(self.scan_directories)
        self.btn_scan.setEnabled(False)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Ajout des widgets au groupe
        dir_layout.addLayout(btn_layout)
        dir_layout.addWidget(self.dir_list)
        dir_layout.addWidget(self.btn_scan)
        dir_layout.addWidget(self.progress_bar)
        
        # Groupe pour les résultats
        results_group = QGroupBox("Résultats")
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
        
        filter_layout.addWidget(self.lbl_filter)
        filter_layout.addWidget(self.txt_filter, 2)
        filter_layout.addWidget(self.lbl_sort)
        filter_layout.addWidget(self.cmb_sort, 1)
        filter_layout.addWidget(self.chk_sort_desc)
        
        # Table des projets
        self.project_table = ProjectTable()
        
        # Ajout des contrôles de filtrage et tri au layout
        results_layout.addLayout(filter_layout)
        results_layout.addWidget(self.project_table)
        
        # Détails du projet sélectionné
        details_group = QGroupBox("Détails du projet")
        details_layout = QVBoxLayout(details_group)
        
        # Onglets pour les différentes vues
        self.details_tabs = QTabWidget()
        
        # Onglet des fichiers
        files_tab = QWidget()
        files_layout = QVBoxLayout(files_tab)
        
        # Arbre des fichiers du projet
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(FILE_TREE_COLUMNS)
        self.file_tree.setColumnCount(len(FILE_TREE_COLUMNS))
        self.file_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Lecteur audio pour les fichiers WAV
        self.audio_player = AudioPlayer()
        self.audio_player.setVisible(False)  # Masqué par défaut
        
        # Initialisation du service audio
        self.audio_service.initialize_player(self.audio_player)
        
        files_layout.addWidget(self.file_tree)
        files_layout.addWidget(self.audio_player)
        
        # Onglet des métadonnées
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout(metadata_tab)
        
        # Éditeur de métadonnées
        self.metadata_editor = MetadataEditor()
        self.metadata_editor.save_requested.connect(self.save_project_metadata)
        
        metadata_layout.addWidget(self.metadata_editor)
        
        # Ajout des onglets
        self.details_tabs.addTab(files_tab, "Fichiers")
        self.details_tabs.addTab(metadata_tab, "Tags & Notes")
        
        details_layout.addWidget(self.details_tabs)
        
        # Options de sauvegarde
        save_group = QGroupBox("Options de sauvegarde")
        save_layout = QVBoxLayout(save_group)
        
        # Sélection du dossier de destination
        dest_layout = QHBoxLayout()
        self.btn_dest_dir = QPushButton("Dossier de destination")
        self.btn_dest_dir.clicked.connect(self.select_destination)
        self.lbl_dest_dir = QLabel("Aucun dossier sélectionné")
        dest_layout.addWidget(self.btn_dest_dir)
        dest_layout.addWidget(self.lbl_dest_dir, 1)
        
        # Options de sauvegarde
        self.chk_keep_bak = QCheckBox("Conserver les fichiers .bak")
        self.chk_remove_dotunderscore = QCheckBox("Supprimer les fichiers commençant par ._")
        self.chk_remove_dotunderscore.setChecked(settings.remove_dotunderscore)
        
        # Option pour renommer le répertoire du projet
        rename_layout = QHBoxLayout()
        self.lbl_rename = QLabel("Renommer le projet:")
        self.txt_rename = QLineEdit()
        self.txt_rename.setPlaceholderText("Laissez vide pour conserver le nom original")
        self.txt_rename.setText(settings.last_rename)
        rename_layout.addWidget(self.lbl_rename)
        rename_layout.addWidget(self.txt_rename, 1)
        
        # Champ pour les notes du projet
        notes_group = QGroupBox("Notes du projet")
        notes_layout = QVBoxLayout(notes_group)
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Ajoutez ici des notes sur le projet (sera sauvegardé dans un fichier notes.txt)")
        self.txt_notes.setMinimumHeight(80)
        self.txt_notes.setText(settings.last_notes)
        notes_layout.addWidget(self.txt_notes)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        # Bouton de sauvegarde
        self.btn_save = QPushButton("Sauvegarder le projet sélectionné")
        self.btn_save.clicked.connect(self.save_selected_project)
        self.btn_save.setEnabled(False)
        
        # Bouton pour lancer le projet dans Cubase
        self.btn_open_in_cubase = QPushButton("Ouvrir dans Cubase")
        self.btn_open_in_cubase.clicked.connect(self.open_in_cubase)
        self.btn_open_in_cubase.setEnabled(False)
        
        buttons_layout.addWidget(self.btn_save)
        buttons_layout.addWidget(self.btn_open_in_cubase)
        
        save_layout.addLayout(dest_layout)
        save_layout.addLayout(rename_layout)
        save_layout.addWidget(notes_group)
        save_layout.addWidget(self.chk_keep_bak)
        save_layout.addWidget(self.chk_remove_dotunderscore)
        save_layout.addLayout(buttons_layout)
        
        # Splitter pour les détails et les options de sauvegarde
        details_splitter = QSplitter(Qt.Vertical)
        details_splitter.addWidget(details_group)
        details_splitter.addWidget(save_group)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(results_group)
        main_splitter.addWidget(details_splitter)
        main_splitter.setSizes([400, 600])
        
        # Ajout des groupes au layout principal
        self.main_layout.addWidget(dir_group)
        self.main_layout.addWidget(main_splitter, 3)
        
        # Connexion des signaux
        self.project_table.project_selected.connect(self.show_project_details)
        self.chk_remove_dotunderscore.stateChanged.connect(self.on_remove_dotunderscore_changed)
    
    def add_directory(self):
        """Ajout d'un dossier à scanner"""
        directory = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier", str(Path.home()))
        if directory and directory not in self.selected_directories:
            self.selected_directories.append(directory)
            item = QTreeWidgetItem([directory])
            self.dir_list.addTopLevelItem(item)
            self.btn_scan.setEnabled(True)
    
    def clear_directories(self):
        """Effacement de la liste des dossiers"""
        self.selected_directories = []
        self.dir_list.clear()
        self.btn_scan.setEnabled(False)
    
    def scan_directories(self):
        """Lancement du scan des dossiers"""
        if not self.selected_directories:
            QMessageBox.warning(self, "Erreur", "Aucun dossier sélectionné!")
            return
        
        # Affichage de la barre de progression
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Création et lancement du thread de scan
        self.scan_thread = ScanThread(self.selected_directories)
        self.scan_thread.scan_progress.connect(self.update_scan_progress)
        self.scan_thread.scan_complete.connect(self.on_scan_complete)
        self.scan_thread.start()
    
    def update_scan_progress(self, value):
        """
        Mise à jour de la barre de progression
        
        Args:
            value (int): Valeur de progression (0-100)
        """
        self.progress_bar.setValue(value)
    
    def on_scan_complete(self, projects):
        """
        Traitement des résultats du scan
        
        Args:
            projects (dict): Dictionnaire des projets trouvés
        """
        # Masquage de la barre de progression
        self.progress_bar.setVisible(False)
        
        # Conversion des données pour le modèle
        self.all_projects_data = self.scanner.df_projects
        
        # Mise à jour de la table des projets
        self.project_table.update_data(self.all_projects_data)
        
        # Message de statut
        self.statusBar.showMessage(f"{len(self.all_projects_data)} projets trouvés")
    
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
        
        # Récupération des métadonnées du projet
        try:
            metadata = self.metadata_service.get_project_metadata(project_name)
            self.metadata_editor.set_metadata(metadata)
        except Exception as e:
            print(f"Erreur lors de la récupération des métadonnées: {e}")
            self.metadata_editor.set_metadata({'tags': [], 'rating': 0, 'notes': ''})
        
        # Mise à jour de l'arbre des fichiers
        self.update_file_tree(project_name)
        
        # Activation des boutons
        self.btn_save.setEnabled(True)
        self.btn_open_in_cubase.setEnabled(True)
        
        # Message de statut
        self.statusBar.showMessage(f"Projet sélectionné: {project_name}")
    
    def update_file_tree(self, project_name):
        """
        Mise à jour de l'arbre des fichiers pour un projet
        
        Args:
            project_name (str): Nom du projet
        """
        # Effacement de l'arbre
        self.file_tree.clear()
        
        # Récupération des détails du projet
        project_details = self.scanner.get_project_details(project_name)
        if not project_details:
            return
        
        # Création des éléments pour les fichiers CPR
        cpr_parent = QTreeWidgetItem(self.file_tree, ["Fichiers CPR"])
        for file_info in project_details['cpr_files']:
            path = Path(file_info['path'])
            item = QTreeWidgetItem(cpr_parent, [
                path.name,
                f"{file_info['size'] / (1024 * 1024):.2f} MB",
                file_info['modified'].strftime("%d/%m/%Y %H:%M")
            ])
            item.setData(0, Qt.UserRole, file_info['path'])
        
        # Création des éléments pour les fichiers BAK
        bak_parent = QTreeWidgetItem(self.file_tree, ["Fichiers BAK"])
        for file_info in project_details['bak_files']:
            path = Path(file_info['path'])
            item = QTreeWidgetItem(bak_parent, [
                path.name,
                f"{file_info['size'] / (1024 * 1024):.2f} MB",
                file_info['modified'].strftime("%d/%m/%Y %H:%M")
            ])
            item.setData(0, Qt.UserRole, file_info['path'])
        
        # Création des éléments pour les fichiers WAV
        wav_parent = QTreeWidgetItem(self.file_tree, ["Fichiers WAV"])
        for file_info in project_details['wav_files']:
            path = Path(file_info['path'])
            item = QTreeWidgetItem(wav_parent, [
                path.name,
                f"{file_info['size'] / (1024 * 1024):.2f} MB",
                file_info['modified'].strftime("%d/%m/%Y %H:%M")
            ])
            item.setData(0, Qt.UserRole, file_info['path'])
        
        # Création des éléments pour les autres fichiers
        other_parent = QTreeWidgetItem(self.file_tree, ["Autres fichiers"])
        for file_info in project_details['other_files']:
            path = Path(file_info['path'])
            item = QTreeWidgetItem(other_parent, [
                path.name,
                f"{file_info['size'] / (1024 * 1024):.2f} MB",
                file_info['modified'].strftime("%d/%m/%Y %H:%M")
            ])
            item.setData(0, Qt.UserRole, file_info['path'])
        
        # Expansion des éléments parents
        self.file_tree.expandAll()
    
    def on_item_double_clicked(self, item, column):
        """
        Gestion du double-clic sur un élément de l'arbre des fichiers
        
        Args:
            item (QTreeWidgetItem): Élément cliqué
            column (int): Colonne cliquée
        """
        # Récupération du chemin du fichier
        file_path = item.data(0, Qt.UserRole)
        if not file_path:
            return
        
        # Vérification du type de fichier
        path = Path(file_path)
        if path.suffix.lower() == '.wav':
            # Lecture du fichier WAV
            self.audio_service.load_file(file_path)
            self.audio_player.setVisible(True)
            self.audio_service.play()
        elif path.suffix.lower() == '.cpr':
            # Ouverture du fichier CPR dans Cubase
            self.open_in_cubase(file_path)
    
    def select_destination(self):
        """Sélection du dossier de destination"""
        directory = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier de destination", str(Path.home()))
        if directory:
            self.destination_directory = directory
            self.lbl_dest_dir.setText(directory)
    
    def save_selected_project(self):
        """Sauvegarde du projet sélectionné"""
        # Vérification de la sélection
        project = self.project_table.get_selected_project()
        if not project:
            QMessageBox.warning(self, "Erreur", "Aucun projet sélectionné!")
            return
        
        # Vérification du dossier de destination
        if not self.destination_directory:
            QMessageBox.warning(self, "Erreur", "Aucun dossier de destination sélectionné!")
            return
        
        # Récupération des options
        project_name = project.get('project_name')
        keep_bak = self.chk_keep_bak.isChecked()
        remove_dotunderscore = self.chk_remove_dotunderscore.isChecked()
        new_project_name = self.txt_rename.text().strip()
        project_notes = self.txt_notes.toPlainText()
        
        # Sauvegarde des préférences
        settings.remove_dotunderscore = remove_dotunderscore
        settings.last_rename = new_project_name
        settings.last_notes = project_notes
        settings.save()
        
        # Copie du projet
        success = self.scanner.copy_project(
            project_name,
            self.destination_directory,
            keep_bak,
            remove_dotunderscore,
            new_project_name,
            project_notes
        )
        
        if success:
            QMessageBox.information(self, "Succès", f"Projet '{project_name}' sauvegardé avec succès!")
            self.statusBar.showMessage(f"Projet '{project_name}' sauvegardé dans {self.destination_directory}")
        else:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde du projet '{project_name}'")
    
    def save_project_metadata(self):
        """Sauvegarde des métadonnées du projet sélectionné"""
        # Vérification de la sélection
        project = self.project_table.get_selected_project()
        if not project:
            QMessageBox.warning(self, "Erreur", "Aucun projet sélectionné!")
            return
        
        # Récupération des métadonnées
        project_name = project.get('project_name')
        metadata = self.metadata_editor.get_metadata()
        
        # Sauvegarde des métadonnées
        try:
            success = self.metadata_service.set_project_metadata(project_name, metadata)
            if success:
                QMessageBox.information(self, "Succès", f"Métadonnées du projet '{project_name}' sauvegardées avec succès!")
                self.statusBar.showMessage(f"Métadonnées du projet '{project_name}' sauvegardées")
            else:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde des métadonnées du projet '{project_name}'")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde des métadonnées: {e}")
    
    def open_in_cubase(self, file_path=None):
        """
        Ouverture d'un fichier dans Cubase
        
        Args:
            file_path (str): Chemin du fichier à ouvrir (facultatif)
        """
        # Si aucun chemin n'est fourni, utiliser le fichier CPR du projet sélectionné
        if not file_path:
            project = self.project_table.get_selected_project()
            if not project or not project.get('latest_cpr'):
                QMessageBox.warning(self, "Erreur", "Aucun fichier CPR disponible!")
                return
            
            file_path = project.get('latest_cpr')
        
        # Ouverture du fichier dans Cubase
        success = self.cubase_service.open_project(file_path)
        if not success:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'ouverture du fichier dans Cubase")
    
    def on_remove_dotunderscore_changed(self, state):
        """
        Gestion du changement de l'option de suppression des fichiers ._
        
        Args:
            state (int): État de la case à cocher
        """
        settings.remove_dotunderscore = (state == Qt.Checked)
        settings.save()
