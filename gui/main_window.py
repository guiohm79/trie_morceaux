#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fenêtre principale de l'application
"""

import os
import sys
from pathlib import Path
import json
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTableView, QFileDialog,
    QGroupBox, QCheckBox, QMessageBox, QProgressBar,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QComboBox, QApplication, QAction, QToolBar, QStatusBar,
    QLineEdit, QMenu, QTextEdit, QTabWidget, QCompleter
)
from PyQt5.QtCore import Qt, QSize, pyqtSlot, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush

from utils.scanner import CubaseScanner
from utils.pygame_audio_player import PygameAudioPlayer
from utils.metadata_manager import MetadataManager
from models.project_model import ProjectTableModel

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


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        """Initialisation de la fenêtre principale"""
        super().__init__()
        
        self.scanner = CubaseScanner()
        self.metadata_manager = MetadataManager()
        self.selected_directories = []
        self.destination_directory = None
        self.all_projects_data = []
        
        self.setWindowTitle("Tri Morceaux Cubase")
        self.setMinimumSize(1000, 700)
        
        # Mode d'application : 'multi_sources' (par défaut) ou 'workspace'
        self.app_mode = 'multi_sources'  # ou 'workspace'
        self.workspace_dir = None
        self.setup_ui()
    
    def closeEvent(self, event):
        """Gestion de la fermeture de l'application"""
        # Sauvegarder les préférences
        self.save_preferences()
        
        # Accepter l'événement de fermeture
        event.accept()
    
    def toggle_theme(self):
        """Basculer entre le mode clair et le mode sombre"""
        app = QApplication.instance()
        
        if self.action_toggle_theme.isChecked():
            # Mode sombre
            style_path = Path(__file__).parent.parent / 'styles' / 'dark_theme.qss'
            if style_path.exists():
                with open(style_path, 'r') as f:
                    app.setStyleSheet(f.read())
                self.action_toggle_theme.setText("Mode clair")
                print("Mode sombre activé")
            # Synchroniser le modèle
            self.project_model.dark_mode = True
            self.project_model.layoutChanged.emit()
        else:
            # Mode clair
            app.setStyleSheet("")
            self.action_toggle_theme.setText("Mode sombre")
            print("Mode clair activé")
            self.project_model.dark_mode = False
            self.project_model.layoutChanged.emit()
    
    def save_preferences(self):
        """Sauvegarde des préférences utilisateur"""
        prefs_dir = Path.home() / '.trie_morceaux'
        prefs_dir.mkdir(exist_ok=True)
        
        prefs_file = prefs_dir / 'preferences.json'
        
        prefs = {
            'dark_mode': self.action_toggle_theme.isChecked(),
            'remove_dotunderscore': self.chk_remove_dotunderscore.isChecked(),
            'last_rename': self.txt_rename.text().strip(),
            'last_notes': self.txt_notes.toPlainText(),
            'cubase_path': getattr(self, 'cubase_path', '')
        }
        
        with open(prefs_file, 'w') as f:
            json.dump(prefs, f)
    
    def load_preferences(self):
        """Chargement des préférences utilisateur"""
        prefs_file = Path.home() / '.trie_morceaux' / 'preferences.json'
        
        if prefs_file.exists():
            try:
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
                
                # Appliquer le thème
                if prefs.get('dark_mode', False):
                    self.action_toggle_theme.setChecked(True)
                    self.toggle_theme()
                
                # Appliquer l'option de suppression des fichiers ._
                if prefs.get('remove_dotunderscore', False):
                    self.chk_remove_dotunderscore.setChecked(True)
                
                # Restaurer le dernier nom de projet utilisé
                last_rename = prefs.get('last_rename', '')
                if last_rename:
                    self.txt_rename.setText(last_rename)
                
                # Restaurer les dernières notes utilisées
                last_notes = prefs.get('last_notes', '')
                if last_notes:
                    self.txt_notes.setText(last_notes)
                
                # Restaurer le chemin de Cubase
                self.cubase_path = prefs.get('cubase_path', '')
            except Exception as e:
                print(f"Erreur lors du chargement des préférences: {e}")
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barre d'outils
        self.setup_toolbar()
        
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
        # Par défaut, le groupe est visible (mode multi-sources)
        dir_group.setVisible(True)
        self.dir_group = dir_group

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
        
        # Tableau des projets
        self.project_table = QTableView()
        self.project_model = ProjectTableModel()
        self.project_table.setModel(self.project_model)
        self.project_table.setSelectionBehavior(QTableView.SelectRows)
        self.project_table.setSelectionMode(QTableView.SingleSelection)
        self.project_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.project_table.clicked.connect(self.show_project_details)
        
        # Ajout des contrôles de filtrage et tri au layout
        results_layout.addLayout(filter_layout)
        
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
        self.file_tree.setObjectName("file_tree")  # ID pour le ciblage CSS
        self.file_tree.setHeaderLabels(["Fichier", "Taille", "Date de modification"])
        self.file_tree.setColumnCount(3)
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_file_context_menu)
        # Double-clic sur un fichier WAV pour le prévisualiser
        self.file_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Lecteur audio pour les fichiers WAV
        self.audio_player = PygameAudioPlayer()
        self.audio_player.setVisible(False)  # Masqué par défaut
        
        files_layout.addWidget(self.file_tree)
        files_layout.addWidget(self.audio_player)
        
        # Onglet des métadonnées (tags et notes)
        metadata_tab = QWidget()
        metadata_layout = QVBoxLayout(metadata_tab)
        
        # Section des tags
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)
        
        # Champ pour ajouter des tags
        tags_input_layout = QHBoxLayout()
        self.lbl_tags = QLabel("Ajouter un tag:")
        self.txt_tag_input = QLineEdit()
        self.txt_tag_input.setPlaceholderText("Entrez un tag et appuyez sur Entrée")
        self.txt_tag_input.returnPressed.connect(self.add_tag)
        
        # Auto-complétion des tags
        self.tag_completer = QCompleter([])
        self.tag_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.txt_tag_input.setCompleter(self.tag_completer)
        
        self.btn_add_tag = QPushButton("Ajouter")
        self.btn_add_tag.clicked.connect(self.add_tag)
        
        tags_input_layout.addWidget(self.lbl_tags)
        tags_input_layout.addWidget(self.txt_tag_input, 1)
        tags_input_layout.addWidget(self.btn_add_tag)
        
        # Affichage des tags actuels
        self.lbl_current_tags = QLabel("Tags actuels:")
        self.tags_container = QWidget()
        self.tags_container_layout = QHBoxLayout(self.tags_container)
        self.tags_container_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_container_layout.setSpacing(5)
        self.tags_container_layout.setAlignment(Qt.AlignLeft)
        
        tags_layout.addLayout(tags_input_layout)
        tags_layout.addWidget(self.lbl_current_tags)
        tags_layout.addWidget(self.tags_container)
        
        # Section de notation à étoiles
        rating_group = QGroupBox("Note du projet")
        rating_layout = QHBoxLayout(rating_group)
        
        self.lbl_rating = QLabel("Attribuer une note:")
        rating_layout.addWidget(self.lbl_rating)
        
        # Création des boutons d'étoiles
        self.rating_buttons = []
        for i in range(6):  # 0 à 5 étoiles
            btn = QPushButton(str(i) + " ★" if i > 0 else "0")
            btn.setProperty("rating", i)
            btn.clicked.connect(self.set_project_rating)
            self.rating_buttons.append(btn)
            rating_layout.addWidget(btn)
        
        # Bouton de sauvegarde des métadonnées
        self.btn_save_metadata = QPushButton("Sauvegarder les métadonnées")
        self.btn_save_metadata.clicked.connect(self.save_project_metadata)
        
        metadata_layout.addWidget(tags_group)
        metadata_layout.addWidget(rating_group)
        metadata_layout.addWidget(self.btn_save_metadata)
        
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
        self.chk_remove_dotunderscore.setToolTip("Supprime les fichiers temporaires/cachés commençant par ._ lors de la sauvegarde")
        
        # Option pour renommer le répertoire du projet
        rename_layout = QHBoxLayout()
        self.lbl_rename = QLabel("Renommer le projet:")
        self.txt_rename = QLineEdit()
        self.txt_rename.setPlaceholderText("Laissez vide pour conserver le nom original")
        rename_layout.addWidget(self.lbl_rename)
        rename_layout.addWidget(self.txt_rename, 1)
        
        # Champ pour les notes du projet
        notes_group = QGroupBox("Notes du projet")
        notes_layout = QVBoxLayout(notes_group)
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Ajoutez ici des notes sur le projet (sera sauvegardé dans un fichier notes.txt)")
        self.txt_notes.setMinimumHeight(80)  # Hauteur minimale pour le champ de notes
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
        
        # Ajout des widgets au groupe des résultats
        results_layout.addWidget(self.project_table, 1)
        
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
        main_layout.addWidget(dir_group, 1)
        main_layout.addWidget(main_splitter, 3)
        
        # Barre de statut
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Prêt")
    
    def add_directory(self):
        """Ajout d'un dossier à scanner"""
        directory = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier", str(Path.home()))
        if directory and directory not in self.selected_directories:
            self.selected_directories.append(directory)
            item = QTreeWidgetItem([directory])
            self.dir_list.addTopLevelItem(item)
            self.btn_scan.setEnabled(True)

    def setup_toolbar(self):
        """Configuration de la barre d'outils"""
        toolbar = QToolBar("Barre d'outils principale")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Action pour basculer le thème (mode sombre)
        self.action_toggle_theme = QAction("Mode sombre", self)
        self.action_toggle_theme.setCheckable(True)
        self.action_toggle_theme.toggled.connect(self.toggle_theme)
        toolbar.addAction(self.action_toggle_theme)

        # Action pour sauvegarder
        action_save = QAction("Sauvegarder", self)
        action_save.triggered.connect(self.save_selected_project)
        toolbar.addAction(action_save)
        
        toolbar.addSeparator()

        # Sélecteur de mode global (multi-sources / espace de travail)
        self.cmb_app_mode = QComboBox()
        self.cmb_app_mode.addItems(["Mode multi-sources (tri)", "Mode espace de travail unique"])
        self.cmb_app_mode.currentIndexChanged.connect(self.on_app_mode_changed)
        toolbar.addWidget(QLabel("Mode : "))
        toolbar.addWidget(self.cmb_app_mode)

        # Action pour choisir le dossier de travail (workspace)
        self.action_select_workspace = QAction("Choisir dossier de travail...", self)
        self.action_select_workspace.triggered.connect(self.select_workspace_dir)
        toolbar.addAction(self.action_select_workspace)
        self.action_select_workspace.setVisible(False)

    def on_app_mode_changed(self, index):
        if index == 0:
            self.app_mode = 'multi_sources'
            self.action_select_workspace.setVisible(False)
            self.dir_group.setVisible(True)
        else:
            self.app_mode = 'workspace'
            self.action_select_workspace.setVisible(True)
            self.dir_group.setVisible(False)
            # Optionnel : lancer scan automatique du workspace si déjà choisi
            if self.workspace_dir:
                self.scan_workspace_projects()

    def select_workspace_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Choisir le dossier de travail (workspace)")
        if dir_path:
            self.workspace_dir = dir_path
            # Utiliser la logique du mode tri : scan_directories sur ce dossier unique
            self.selected_directories = [dir_path]
            self.scan_directories()

    def scan_workspace_projects(self):
        """Scan du dossier workspace pour détecter tous les projets Cubase et charger leurs métadonnées locales"""
        if not self.workspace_dir:
            return
        projects = []
        for root, dirs, files in os.walk(self.workspace_dir):
            for file in files:
                if file.endswith('.cpr'):
                    project_dir = root
                    project_name = os.path.splitext(file)[0]
                    # Lecture des métadonnées locales
                    from utils.metadata_manager import MetadataManager
                    meta_mgr = MetadataManager(mode='local')
                    metadata = meta_mgr.get_project_metadata(project_name, project_dir)
                    # Ajout à la liste
                    projects.append({
                        'project_name': project_name,
                        'source': project_dir,
                        'latest_cpr_date': None,  # À calculer si besoin
                        'cpr_count': 1,  # à ajuster
                        'bak_count': len([f for f in os.listdir(project_dir) if f.endswith('.bak')]),
                        'wav_count': len([f for f in os.listdir(project_dir) if f.endswith('.wav')]),
                        'total_size_mb': round(sum(os.path.getsize(os.path.join(project_dir, f)) for f in os.listdir(project_dir) if os.path.isfile(os.path.join(project_dir, f))) / 1048576, 2),
                        'rating': metadata.get('rating', 0),
                        'metadata': metadata
                    })
        # Mise à jour du modèle
        self.project_model._data = projects
        self.project_model.layoutChanged.emit()
        # Efface la sélection
        self.project_table.clearSelection()
        # Affiche un message si aucun projet trouvé
        if not projects:
            QMessageBox.information(self, "Aucun projet trouvé", "Aucun projet Cubase (.cpr) trouvé dans ce dossier.")
    
    @pyqtSlot()
    def clear_directories(self):
        """Effacement de la liste des dossiers"""
        self.selected_directories.clear()
        self.dir_list.clear()
        self.btn_scan.setEnabled(False)
    
    @pyqtSlot()
    def scan_directories(self):
        """Scan des dossiers sélectionnés"""
        if not self.selected_directories:
            QMessageBox.warning(
                self, "Aucun dossier", 
                "Veuillez sélectionner au moins un dossier à scanner."
            )
            return
        
        # Affichage de la barre de progression
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.statusBar.showMessage("Scan en cours...")
        
        # Désactivation des boutons pendant le scan
        self.btn_scan.setEnabled(False)
        self.btn_add_dir.setEnabled(False)
        self.btn_clear_dirs.setEnabled(False)
        
        # Lancement du scan dans un thread séparé
        self.scan_thread = ScanThread(self.selected_directories)
        self.scan_thread.scan_progress.connect(self.update_progress)
        self.scan_thread.scan_complete.connect(self.scan_complete)
        self.scan_thread.start()
    
    @pyqtSlot(int)
    def update_progress(self, value):
        """Mise à jour de la barre de progression"""
        self.progress_bar.setValue(value)
    
    @pyqtSlot(dict)
    def scan_complete(self, projects):
        """Traitement des résultats du scan"""
        # Affichage de debug
        print(f"Scan complet, projets trouvés: {len(projects)}")
        for project_name, data in projects.items():
            print(f"Projet: {project_name}, CPR: {len(data['cpr_files'])}, BAK: {len(data['bak_files'])}, WAV: {len(data['wav_files'])}")
        
        # Mise à jour du modèle de données
        self.scanner.projects = projects
        
        # Forcer la création du dataframe
        self.scanner._create_dataframe()
        print(f"DataFrame créé avec {len(self.scanner.df_projects)} entrées")
        
        # Sauvegarde des données complètes pour le filtrage
        self.all_projects_data = self.scanner.df_projects.copy()
        
        # Mise à jour du modèle
        self.project_model.update_data(self.scanner.df_projects)
        
        # Réactivation des boutons
        self.btn_scan.setEnabled(True)
        self.btn_add_dir.setEnabled(True)
        self.btn_clear_dirs.setEnabled(True)
        
        # Masquage de la barre de progression
        self.progress_bar.setVisible(False)
        
        # Mise à jour de la barre de statut
        project_count = len(projects)
        self.statusBar.showMessage(f"Scan terminé : {project_count} projets trouvés")
    
    @pyqtSlot(QPoint)
    def show_file_context_menu(self, position):
        """Affichage du menu contextuel pour les fichiers
        
        Args:
            position (QPoint): Position du clic
        """
        # Récupération de l'item sélectionné
        item = self.file_tree.itemAt(position)
        if not item:
            print("Aucun item sélectionné")
            return
        
        # Vérifier si c'est un fichier WAV
        item_text = item.text(0)
        print(f"Item sélectionné: {item_text}")
        
        # Vérifier si c'est un fichier WAV (plus permissif)
        if '.wav' not in item_text.lower():
            print(f"Ce n'est pas un fichier WAV: {item_text}")
            return
        
        # Création du menu contextuel
        menu = QMenu(self)
        action_play = menu.addAction("Prévisualiser le fichier audio")
        print("Menu contextuel créé")
        
        # Exécution du menu
        action = menu.exec_(self.file_tree.viewport().mapToGlobal(position))
        print(f"Action sélectionnée: {action}")
        
        # Traitement de l'action sélectionnée
        if action == action_play:
            # Récupération du chemin du fichier
            parent = item.parent()
            if not parent:
                return
            
            # Remonter jusqu'à trouver l'item source
            source_item = parent
            while source_item and not source_item.text(0).startswith("Source:"):
                source_item = source_item.parent()
            
            if not source_item:
                return
            
            # Extraction du nom du projet et du fichier
            project_name = self.get_selected_project_name()
            if not project_name:
                return
            
            # Recherche du fichier WAV dans les données du projet
            project = self.scanner.get_project_details(project_name)
            if not project:
                return
            
            # Recherche du fichier correspondant
            file_name = item_text.split(" (PLUS RÉCENT)")[0]  # Supprimer le suffixe si présent
            wav_file = None
            
            for file in project['wav_files']:
                if Path(file['path']).name == file_name:
                    wav_file = file
                    break
            
            if not wav_file:
                QMessageBox.warning(self, "Fichier introuvable", 
                                  f"Le fichier {file_name} n'a pas été trouvé.")
                return
            
            # Chargement et lecture du fichier
            self.preview_audio_file(wav_file['path'])
    
    def preview_audio_file(self, file_path):
        """Prévisualisation d'un fichier audio
        
        Args:
            file_path (str): Chemin du fichier audio
        """
        print(f"Prévisualisation du fichier: {file_path}")
        
        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Fichier introuvable", 
                              f"Le fichier {file_path} n'existe pas.")
            return
        
        # Affichage du lecteur audio
        self.audio_player.setVisible(True)
        
        # Chargement du fichier
        if self.audio_player.load_file(file_path):
            # Démarrage de la lecture
            self.audio_player.toggle_playback()
            print("Lecture audio démarrée")
        else:
            QMessageBox.warning(self, "Erreur", 
                              "Impossible de charger le fichier audio.")
            print("Erreur lors du chargement du fichier audio")
    
    def get_selected_project_name(self):
        """Récupération du nom du projet sélectionné
        
        Returns:
            str: Nom du projet sélectionné ou None
        """
        indexes = self.project_table.selectedIndexes()
        if not indexes:
            return None
        
        row = indexes[0].row()
        return self.project_model.get_project_at_row(row)
    
    @pyqtSlot(QTreeWidgetItem, int)
    def on_item_double_clicked(self, item, column):
        """Gestion du double-clic sur un élément de l'arbre
        
        Args:
            item (QTreeWidgetItem): Item sur lequel on a double-cliqué
            column (int): Colonne sur laquelle on a double-cliqué
        """
        if not item:
            return
        
        # Vérifier si c'est un fichier WAV
        item_text = item.text(0)
        print(f"Double-clic sur: {item_text}")
        
        if '.wav' not in item_text.lower():
            return
        
        # Récupération du nom du projet
        project_name = self.get_selected_project_name()
        if not project_name:
            return
        
        # Récupération des détails du projet
        project = self.scanner.get_project_details(project_name)
        if not project:
            return
        
        # Recherche du fichier correspondant
        file_name = item_text.split(" (PLUS RÉCENT)")[0]  # Supprimer le suffixe si présent
        wav_file = None
        
        for file in project['wav_files']:
            if Path(file['path']).name == file_name:
                wav_file = file
                break
        
        if not wav_file:
            print(f"Fichier WAV non trouvé: {file_name}")
            return
        
        # Prévisualisation du fichier
        self.preview_audio_file(wav_file['path'])
    
    @pyqtSlot()
    def add_tag(self):
        """Ajout d'un tag au projet sélectionné"""
        # Vérification qu'un projet est sélectionné
        project_name = self.get_selected_project_name()
        if not project_name:
            return
        
        # Récupération du tag saisi
        tag = self.txt_tag_input.text().strip()
        if not tag:
            return
        
        # Récupération des métadonnées du projet
        metadata = self.metadata_manager.get_project_metadata(project_name)
        
        # Ajout du tag s'il n'existe pas déjà
        if tag not in metadata['tags']:
            metadata['tags'].append(tag)
            self.metadata_manager.set_project_tags(project_name, metadata['tags'])
            
            # Mise à jour de l'affichage des tags
            self.display_project_tags(project_name)
            
            # Mise à jour de l'auto-complétion
            self.update_tag_completer()
        
        # Effacement du champ de saisie
        self.txt_tag_input.clear()
    
    def remove_tag(self, tag):
        """Suppression d'un tag du projet sélectionné
        
        Args:
            tag (str): Tag à supprimer
        """
        # Vérification qu'un projet est sélectionné
        project_name = self.get_selected_project_name()
        if not project_name:
            return
        
        # Récupération des métadonnées du projet
        metadata = self.metadata_manager.get_project_metadata(project_name)
        
        # Suppression du tag s'il existe
        if tag in metadata['tags']:
            metadata['tags'].remove(tag)
            self.metadata_manager.set_project_tags(project_name, metadata['tags'])
            
            # Mise à jour de l'affichage des tags
            self.display_project_tags(project_name)
    
    def display_project_tags(self, project_name):
        """Affichage des tags d'un projet
        
        Args:
            project_name (str): Nom du projet
        """
        # Effacement des tags existants
        while self.tags_container_layout.count():
            item = self.tags_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Récupération des métadonnées du projet
        metadata = self.metadata_manager.get_project_metadata(project_name)
        
        # Affichage des tags
        for tag in metadata['tags']:
            # Création d'un bouton pour chaque tag
            tag_btn = QPushButton(tag)
            tag_btn.setStyleSheet(
                "QPushButton { background-color: #3498db; color: white; border-radius: 10px; padding: 5px; }"
                "QPushButton:hover { background-color: #2980b9; }"
            )
            
            # Création d'un menu contextuel pour le tag
            tag_menu = QMenu(self)
            remove_action = tag_menu.addAction("Supprimer")
            remove_action.triggered.connect(lambda checked, t=tag: self.remove_tag(t))
            tag_btn.setContextMenuPolicy(Qt.CustomContextMenu)
            tag_btn.customContextMenuRequested.connect(
                lambda pos, btn=tag_btn, menu=tag_menu: menu.exec_(btn.mapToGlobal(pos))
            )
            
            self.tags_container_layout.addWidget(tag_btn)
        
        # Ajout d'un spacer pour aligner les tags à gauche
        self.tags_container_layout.addStretch()
    
    def update_tag_completer(self):
        """Mise à jour de l'auto-complétion des tags"""
        all_tags = self.metadata_manager.get_all_tags()
        from PyQt5.QtCore import QStringListModel
        self.tag_completer.setModel(QStringListModel(all_tags))
    
    def set_project_rating(self):
        """Attribution d'une note en étoiles au projet"""
        # Vérification qu'un projet est sélectionné
        project_name = self.get_selected_project_name()
        if not project_name:
            return
        
        # Récupération de la note depuis le bouton cliqué
        sender = self.sender()
        rating = sender.property("rating")
        
        # Mise à jour visuelle des boutons
        self.update_rating_buttons(rating)
        
        # Sauvegarde de la note
        self.metadata_manager.set_project_rating(project_name, rating)
        
        # Mise à jour du modèle de données
        self.update_project_in_model(project_name, rating)
    
    def update_rating_buttons(self, selected_rating):
        """Mise à jour visuelle des boutons d'étoiles
        
        Args:
            selected_rating (int): Note sélectionnée (0-5)
        """
        for btn in self.rating_buttons:
            rating = btn.property("rating")
            if rating <= selected_rating:
                btn.setStyleSheet("QPushButton { background-color: #f1c40f; color: white; }")
            else:
                btn.setStyleSheet("")
    
    def update_project_in_model(self, project_name, rating):
        """Mise à jour de la note d'un projet dans le modèle de données
        
        Args:
            project_name (str): Nom du projet
            rating (int): Nouvelle note
        """
        # Recherche du projet dans les données du modèle
        for i, project in enumerate(self.project_model._data):
            if project['project_name'] == project_name:
                # Mise à jour de la note
                project['rating'] = rating
                # Notification du modèle du changement
                index = self.project_model.index(i, self.project_model._columns.index('rating'))
                self.project_model.dataChanged.emit(index, index)
                break
    
    def save_project_metadata(self):
        """Sauvegarde des métadonnées du projet"""
        # Vérification qu'un projet est sélectionné
        project_name = self.get_selected_project_name()
        if not project_name:
            QMessageBox.warning(
                self, "Aucun projet", 
                "Veuillez sélectionner un projet pour sauvegarder les métadonnées."
            )
            return
        
        QMessageBox.information(
            self, "Métadonnées sauvegardées", 
            f"Les métadonnées du projet '{project_name}' ont été sauvegardées."
        )
    
    def show_project_details(self):
        """Affichage des détails du projet sélectionné"""
        # Récupération de l'index sélectionné
        indexes = self.project_table.selectedIndexes()
        if not indexes:
            return
        
        # Récupération du nom du projet
        row = indexes[0].row()
        project_name = self.project_model.get_project_at_row(row)
        
        if not project_name:
            return
        
        # Récupération des détails du projet
        project = self.scanner.get_project_details(project_name)
        # Correction : recherche alternative si None (mode workspace)
        if project is None:
            for key in self.scanner.projects.keys():
                if project_name == key or project_name in key or key in project_name:
                    project = self.scanner.projects[key]
                    break
        if project is None or 'cpr_files' not in project or not isinstance(project['cpr_files'], list):
            QMessageBox.warning(self, "Projet introuvable ou corrompu", "Impossible d'afficher les détails de ce projet.")
            return
        
        # Mise à jour de l'arbre des fichiers
        self.file_tree.clear()
        
        # Mise à jour des métadonnées
        self.display_project_tags(project_name)
        
        # Affichage de la note en étoiles du projet
        metadata = self.metadata_manager.get_project_metadata(project_name)
        rating = metadata.get('rating', 0)
        self.update_rating_buttons(rating)
        
        # Mise à jour de l'auto-complétion des tags
        self.update_tag_completer()
        
        # Ajout des fichiers CPR groupés par source
        cpr_parent = QTreeWidgetItem(["Fichiers CPR"])
        cpr_parent.setBackground(0, QBrush(QColor(60, 70, 100)))  # Bleu foncé pour le mode sombre
        cpr_parent.setForeground(0, QBrush(QColor(255, 255, 255)))  # Texte blanc
        cpr_parent.setData(0, Qt.UserRole, "category")  # Marquer comme catégorie pour le CSS
        self.file_tree.addTopLevelItem(cpr_parent)
        
        # Regrouper les fichiers par source
        cpr_by_source = {}
        for file in project['cpr_files']:
            source = file.get('source', 'Source inconnue')
            if source not in cpr_by_source:
                cpr_by_source[source] = []
            cpr_by_source[source].append(file)
        
        # Ajouter les fichiers groupés par source
        for source, files in cpr_by_source.items():
            source_name = Path(source).name
            source_item = QTreeWidgetItem([f"Source: {source_name}"])
            
            # Appliquer la couleur de la source
            source_color = self.project_model.get_source_color(source)
            if source_color:
                for col in range(3):  # Appliquer à toutes les colonnes
                    source_item.setBackground(col, QBrush(source_color))
            
            cpr_parent.addChild(source_item)
            
            # Trier les fichiers par date de modification (le plus récent en premier)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            for i, file in enumerate(files):
                path = Path(file['path'])
                item = QTreeWidgetItem([
                    path.name,
                    f"{file['size'] / 1024 / 1024:.2f} MB",
                    file['modified'].strftime("%d/%m/%Y %H:%M")
                ])
                
                # Mettre en évidence le fichier le plus récent
                if i == 0:  # Premier fichier (le plus récent)
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
                    item.setText(0, f"{path.name} (PLUS RÉCENT)")
                    item.setData(0, Qt.UserRole, "highlighted")  # Marquer comme mis en évidence pour le CSS
                    
                    # Couleurs adaptées au mode sombre
                    highlight_color = QColor(80, 120, 170) if source_color else QColor(80, 100, 120)
                    text_color = QColor(255, 255, 255)
                    
                    for col in range(3):
                        item.setBackground(col, QBrush(highlight_color))
                        item.setForeground(col, QBrush(text_color))
                else:
                    # Appliquer une couleur adaptée au mode sombre pour les autres fichiers
                    if source_color:
                        darker_color = QColor(50, 50, 60)
                        text_color = QColor(220, 220, 220)
                        
                        for col in range(3):
                            item.setBackground(col, QBrush(darker_color))
                            item.setForeground(col, QBrush(text_color))
                
                source_item.addChild(item)
        
        # Ajout des fichiers BAK groupés par source
        bak_parent = QTreeWidgetItem(["Fichiers BAK"])
        bak_parent.setBackground(0, QBrush(QColor(100, 60, 60)))  # Rouge foncé pour le mode sombre
        bak_parent.setForeground(0, QBrush(QColor(255, 255, 255)))  # Texte blanc
        bak_parent.setData(0, Qt.UserRole, "category")  # Marquer comme catégorie pour le CSS
        self.file_tree.addTopLevelItem(bak_parent)
        
        # Regrouper les fichiers par source
        bak_by_source = {}
        for file in project['bak_files']:
            source = file.get('source', 'Source inconnue')
            if source not in bak_by_source:
                bak_by_source[source] = []
            bak_by_source[source].append(file)
        
        # Ajouter les fichiers groupés par source
        for source, files in bak_by_source.items():
            source_name = Path(source).name
            source_item = QTreeWidgetItem([f"Source: {source_name}"])
            
            # Appliquer la couleur de la source
            source_color = self.project_model.get_source_color(source)
            if source_color:
                for col in range(3):
                    source_item.setBackground(col, QBrush(source_color))
            
            bak_parent.addChild(source_item)
            
            # Trier les fichiers par date de modification (le plus récent en premier)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            for i, file in enumerate(files):
                path = Path(file['path'])
                item = QTreeWidgetItem([
                    path.name,
                    f"{file['size'] / 1024 / 1024:.2f} MB",
                    file['modified'].strftime("%d/%m/%Y %H:%M")
                ])
                
                # Mettre en évidence le fichier le plus récent
                if i == 0:  # Premier fichier (le plus récent)
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
                    item.setText(0, f"{path.name} (PLUS RÉCENT)")
                    item.setData(0, Qt.UserRole, "highlighted")  # Marquer comme mis en évidence pour le CSS
                    
                    # Couleurs adaptées au mode sombre
                    highlight_color = QColor(80, 120, 170) if source_color else QColor(80, 100, 120)
                    text_color = QColor(255, 255, 255)
                    
                    for col in range(3):
                        item.setBackground(col, QBrush(highlight_color))
                        item.setForeground(col, QBrush(text_color))
                else:
                    # Appliquer une couleur adaptée au mode sombre pour les autres fichiers
                    if source_color:
                        darker_color = QColor(50, 50, 60)
                        text_color = QColor(220, 220, 220)
                        
                        for col in range(3):
                            item.setBackground(col, QBrush(darker_color))
                            item.setForeground(col, QBrush(text_color))
                
                source_item.addChild(item)
        
        # Ajout des fichiers WAV groupés par source
        wav_parent = QTreeWidgetItem(["Fichiers WAV"])
        wav_parent.setBackground(0, QBrush(QColor(60, 100, 60)))  # Vert foncé pour le mode sombre
        wav_parent.setForeground(0, QBrush(QColor(255, 255, 255)))  # Texte blanc
        wav_parent.setData(0, Qt.UserRole, "category")  # Marquer comme catégorie pour le CSS
        self.file_tree.addTopLevelItem(wav_parent)
        
        # Regrouper les fichiers par source
        wav_by_source = {}
        for file in project['wav_files']:
            source = file.get('source', 'Source inconnue')
            if source not in wav_by_source:
                wav_by_source[source] = []
            wav_by_source[source].append(file)
        
        # Ajouter les fichiers groupés par source
        for source, files in wav_by_source.items():
            source_name = Path(source).name
            source_item = QTreeWidgetItem([f"Source: {source_name}"])
            
            # Appliquer la couleur de la source
            source_color = self.project_model.get_source_color(source)
            if source_color:
                for col in range(3):
                    source_item.setBackground(col, QBrush(source_color))
            
            wav_parent.addChild(source_item)
            
            # Trier les fichiers par date de modification (le plus récent en premier)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            for i, file in enumerate(files):
                path = Path(file['path'])
                item = QTreeWidgetItem([
                    path.name,
                    f"{file['size'] / 1024 / 1024:.2f} MB",
                    file['modified'].strftime("%d/%m/%Y %H:%M")
                ])
                
                # Mettre en évidence le fichier le plus récent
                if i == 0:  # Premier fichier (le plus récent)
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
                    item.setText(0, f"{path.name} (PLUS RÉCENT)")
                    item.setData(0, Qt.UserRole, "highlighted")  # Marquer comme mis en évidence pour le CSS
                    
                    # Couleurs adaptées au mode sombre
                    highlight_color = QColor(80, 120, 170) if source_color else QColor(80, 100, 120)
                    text_color = QColor(255, 255, 255)
                    
                    for col in range(3):
                        item.setBackground(col, QBrush(highlight_color))
                        item.setForeground(col, QBrush(text_color))
                else:
                    # Appliquer une couleur adaptée au mode sombre pour les autres fichiers
                    if source_color:
                        darker_color = QColor(50, 50, 60)
                        text_color = QColor(220, 220, 220)
                        
                        for col in range(3):
                            item.setBackground(col, QBrush(darker_color))
                            item.setForeground(col, QBrush(text_color))
                
                source_item.addChild(item)
        
        # Expansion de l'arbre
        self.file_tree.expandAll()
        
        # Activation du bouton de sauvegarde si un dossier de destination est sélectionné
        self.btn_save.setEnabled(self.destination_directory is not None)
        
        # Activation du bouton pour ouvrir dans Cubase
        has_cpr = project and len(project['cpr_files']) > 0
        self.btn_open_in_cubase.setEnabled(has_cpr)
    
    @pyqtSlot()
    def select_destination(self):
        """Sélection du dossier de destination"""
        directory = QFileDialog.getExistingDirectory(
            self, "Sélectionner un dossier de destination", str(Path.home())
        )
        
        if directory:
            self.destination_directory = directory
            self.lbl_dest_dir.setText(directory)
            
            # Activation du bouton de sauvegarde si un projet est sélectionné
            indexes = self.project_table.selectedIndexes()
            has_selection = bool(indexes)
            self.btn_save.setEnabled(has_selection)
            
            # Désactivation du bouton pour ouvrir dans Cubase (sera activé lors de la sélection d'un projet)
            self.btn_open_in_cubase.setEnabled(False)
    
    @pyqtSlot()
    def filter_projects(self):
        """Filtrage des projets par nom"""
        filter_text = self.txt_filter.text().lower()
        
        if not filter_text:
            # Si aucun filtre, afficher tous les projets
            filtered_data = self.all_projects_data
        else:
            # Filtrer les projets par nom
            filtered_data = [p for p in self.all_projects_data 
                            if filter_text in p['project_name'].lower()]
        
        # Appliquer le tri actuel aux données filtrées
        self.sort_projects(filtered_data=filtered_data)
        
    @pyqtSlot(int)
    def change_view_mode(self, index):
        """Changement du mode de visualisation
        
        Args:
            index (int): Index du mode sélectionné (0: Par projet, 1: Par dossier)
        """
        view_mode = "project" if index == 0 else "folder"
        
        # Mettre à jour le modèle avec le nouveau mode
        self.sort_projects(view_mode=view_mode)
    
    @pyqtSlot()
    def sort_projects(self, filtered_data=None, view_mode=None):
        """Tri des projets selon le critère sélectionné
        
        Args:
            filtered_data (list): Données filtrées à trier
            view_mode (str): Mode de visualisation ("project" ou "folder")
        """
        # Utiliser les données filtrées si fournies, sinon utiliser toutes les données
        data = filtered_data if filtered_data is not None else self.all_projects_data
        
        # Déterminer le mode de visualisation
        if view_mode is None:
            # Utiliser le mode actuel
            view_mode = "project" if self.cmb_view_mode.currentIndex() == 0 else "folder"
        else:
            # Mettre à jour le sélecteur de mode si nécessaire
            if (view_mode == "project" and self.cmb_view_mode.currentIndex() != 0) or \
               (view_mode == "folder" and self.cmb_view_mode.currentIndex() != 1):
                self.cmb_view_mode.setCurrentIndex(0 if view_mode == "project" else 1)
        
        # Déterminer le critère de tri
        sort_index = self.cmb_sort.currentIndex()
        reverse = self.chk_sort_desc.isChecked()
        
        if sort_index == 0:  # Nom du projet
            sorted_data = sorted(data, key=lambda x: x['project_name'], reverse=reverse)
        elif sort_index == 1:  # Date de modification
            sorted_data = sorted(data, 
                                key=lambda x: x['latest_cpr_date'] if x['latest_cpr_date'] else datetime.min, 
                                reverse=reverse)
        elif sort_index == 2:  # Taille
            sorted_data = sorted(data, key=lambda x: x['total_size'], reverse=reverse)
        else:
            sorted_data = data
        
        # Mise à jour du modèle avec les données triées et le mode de visualisation
        self.project_model.update_data(sorted_data, view_mode)
        
        # Mise à jour de la barre de statut
        mode_text = "par dossier" if view_mode == "folder" else "par projet"
        self.statusBar.showMessage(f"{len(sorted_data)} projets affichés ({mode_text})")
    
    @pyqtSlot()
    def open_in_cubase(self):
        """Ouvre le projet sélectionné dans Cubase"""
        # Vérification qu'un projet est sélectionné
        project_name = self.get_selected_project_name()
        if not project_name:
            QMessageBox.warning(
                self, "Aucun projet", 
                "Veuillez sélectionner un projet à ouvrir."
            )
            return
        
        # Récupération des détails du projet
        project = self.scanner.get_project_details(project_name)
        if not project or not project['cpr_files']:
            QMessageBox.warning(
                self, "Pas de fichier CPR", 
                f"Le projet '{project_name}' ne contient pas de fichier CPR."
            )
            return
        
        # Récupération du fichier CPR le plus récent
        latest_cpr = max(project['cpr_files'], key=lambda x: x['modified'])
        cpr_path = latest_cpr['path']
        
        # Vérification du chemin de Cubase
        if not hasattr(self, 'cubase_path') or not self.cubase_path:
            self.select_cubase_path()
            if not hasattr(self, 'cubase_path') or not self.cubase_path:
                return
        
        try:
            # Lancement de Cubase avec le fichier CPR
            subprocess.Popen([self.cubase_path, cpr_path])
            self.statusBar.showMessage(f"Ouverture du projet '{project_name}' dans Cubase...")
        except Exception as e:
            QMessageBox.critical(
                self, "Erreur", 
                f"Impossible d'ouvrir Cubase: {e}"
            )
    
    def select_cubase_path(self):
        """Sélection du chemin de l'exécutable Cubase"""
        # Suggestions de chemins courants pour Cubase
        default_paths = [
            "C:\\Program Files\\Steinberg\\Cubase 12\\Cubase12.exe",
            "C:\\Program Files\\Steinberg\\Cubase 11\\Cubase11.exe",
            "C:\\Program Files\\Steinberg\\Cubase 10\\Cubase10.exe",
            "C:\\Program Files\\Steinberg\\Cubase 9.5\\Cubase9.5.exe",
            "C:\\Program Files\\Steinberg\\Cubase 9\\Cubase9.exe",
            "C:\\Program Files\\Steinberg\\Cubase 8.5\\Cubase8.5.exe",
            "C:\\Program Files\\Steinberg\\Cubase 8\\Cubase8.exe",
            "C:\\Program Files\\Steinberg\\Cubase 7.5\\Cubase7.5.exe",
            "C:\\Program Files\\Steinberg\\Cubase 7\\Cubase7.exe",
            "C:\\Program Files\\Steinberg\\Cubase 6\\Cubase6.exe"
        ]
        
        # Vérification des chemins par défaut
        for path in default_paths:
            if os.path.exists(path):
                self.cubase_path = path
                self.save_preferences()  # Sauvegarde immédiate du chemin
                return
        
        # Si aucun chemin par défaut n'est valide, demander à l'utilisateur
        cubase_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner l'exécutable Cubase", 
            "C:\\Program Files\\Steinberg",
            "Exécutables (*.exe)"
        )
        
        if cubase_path:
            self.cubase_path = cubase_path
            self.save_preferences()  # Sauvegarde immédiate du chemin
    
    @pyqtSlot()
    def save_selected_project(self):
        """Sauvegarde du projet sélectionné"""
        # Vérification qu'un projet est sélectionné
        indexes = self.project_table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(
                self, "Aucun projet", 
                "Veuillez sélectionner un projet à sauvegarder."
            )
            return
        
        # Vérification qu'un dossier de destination est sélectionné
        if not self.destination_directory:
            QMessageBox.warning(
                self, "Aucune destination", 
                "Veuillez sélectionner un dossier de destination."
            )
            return
        
        # Récupération du nom du projet
        row = indexes[0].row()
        project_name = self.project_model.get_project_at_row(row)
        
        if not project_name:
            return
        
        # Sauvegarde du projet
        keep_bak = self.chk_keep_bak.isChecked()
        remove_dotunderscore = self.chk_remove_dotunderscore.isChecked()
        
        # Récupération du nouveau nom du projet (si spécifié)
        new_project_name = self.txt_rename.text().strip()
        
        # Récupération des notes du projet (si spécifiées)
        project_notes = self.txt_notes.toPlainText().strip()
        
        success = self.scanner.copy_project(
            project_name, self.destination_directory, keep_bak, remove_dotunderscore, new_project_name, project_notes
        )
        
        if success:
            QMessageBox.information(
                self, "Sauvegarde réussie", 
                f"Le projet '{project_name}' a été sauvegardé avec succès."
            )
        else:
            QMessageBox.critical(
                self, "Erreur", 
                f"Une erreur est survenue lors de la sauvegarde du projet '{project_name}'."
            )
