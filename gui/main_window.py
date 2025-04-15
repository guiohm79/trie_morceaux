#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fenêtre principale de l'application
"""

import os
import sys
from pathlib import Path
import json
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTableView, QFileDialog,
    QGroupBox, QCheckBox, QMessageBox, QProgressBar,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QComboBox, QApplication, QAction, QToolBar, QStatusBar,
    QLineEdit, QMenu
)
from PyQt5.QtCore import Qt, QSize, pyqtSlot, QThread, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon, QFont, QColor, QBrush

from utils.scanner import CubaseScanner
from utils.pygame_audio_player import PygameAudioPlayer
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
        self.selected_directories = []
        self.destination_directory = None
        self.all_projects_data = []
        
        self.setWindowTitle("Tri Morceaux Cubase")
        self.setMinimumSize(1000, 700)
        
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
        else:
            # Mode clair
            app.setStyleSheet("")
            self.action_toggle_theme.setText("Mode sombre")
            print("Mode clair activé")
    
    def save_preferences(self):
        """Sauvegarde des préférences utilisateur"""
        prefs_dir = Path.home() / '.trie_morceaux'
        prefs_dir.mkdir(exist_ok=True)
        
        prefs_file = prefs_dir / 'preferences.json'
        
        prefs = {
            'dark_mode': self.action_toggle_theme.isChecked(),
            'remove_dotunderscore': self.chk_remove_dotunderscore.isChecked()
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
        
        details_layout.addWidget(self.file_tree)
        details_layout.addWidget(self.audio_player)
        
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
        
        # Bouton de sauvegarde
        self.btn_save = QPushButton("Sauvegarder le projet sélectionné")
        self.btn_save.clicked.connect(self.save_selected_project)
        self.btn_save.setEnabled(False)
        
        save_layout.addLayout(dest_layout)
        save_layout.addWidget(self.chk_keep_bak)
        save_layout.addWidget(self.chk_remove_dotunderscore)
        save_layout.addWidget(self.btn_save)
        
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
    
    def setup_toolbar(self):
        """Configuration de la barre d'outils"""
        toolbar = QToolBar("Barre d'outils principale")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Actions
        action_scan = QAction("Scanner", self)
        action_scan.triggered.connect(self.scan_directories)
        toolbar.addAction(action_scan)
        
        action_save = QAction("Sauvegarder", self)
        action_save.triggered.connect(self.save_selected_project)
        toolbar.addAction(action_save)
        
        toolbar.addSeparator()
        
        # Action pour basculer le thème
        self.action_toggle_theme = QAction("Mode sombre", self)
        self.action_toggle_theme.setCheckable(True)
        self.action_toggle_theme.triggered.connect(self.toggle_theme)
        toolbar.addAction(self.action_toggle_theme)
        
        # Charger l'état du thème depuis les préférences
        self.load_preferences()
        
        toolbar.addSeparator()
        
        action_quit = QAction("Quitter", self)
        action_quit.triggered.connect(self.close)
        toolbar.addAction(action_quit)
    
    @pyqtSlot()
    def add_directory(self):
        """Ajout d'un dossier à scanner"""
        directory = QFileDialog.getExistingDirectory(
            self, "Sélectionner un dossier", str(Path.home())
        )
        
        if directory:
            # Vérification que le dossier n'est pas déjà dans la liste
            if directory not in self.selected_directories:
                self.selected_directories.append(directory)
                item = QTreeWidgetItem([directory])
                self.dir_list.addTopLevelItem(item)
                self.btn_scan.setEnabled(True)
    
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
        
        # Mise à jour de l'arbre des fichiers
        self.file_tree.clear()
        
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
            self.btn_save.setEnabled(bool(indexes))
    
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
        success = self.scanner.copy_project(
            project_name, self.destination_directory, keep_bak, remove_dotunderscore
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
