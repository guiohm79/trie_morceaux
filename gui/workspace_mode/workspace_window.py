#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fenêtre principale du mode Espace de Travail (unique)
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog,
    QGroupBox, QCheckBox, QMessageBox, QProgressBar,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QComboBox, QAction, QLineEdit, QMenu, QTextEdit, QTabWidget,
    QInputDialog, QToolBar, QShortcut, QFrame, QToolButton
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QDir
from PyQt5.QtGui import QIcon, QKeySequence

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
from services.lectureCPR import trouve_vsti

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
        
        # Thread de scan
        self.scan_thread = None
        
        # Configuration de l'interface
        self.setup_ui()
        
        # Mise à jour du titre
        self.setWindowTitle("Tri Morceaux Cubase - Mode Espace de Travail")
        
        # Chargement du workspace s'il existe
        if self.workspace_dir and os.path.exists(self.workspace_dir):
            self.setup_workspace_view(self.workspace_dir)
    
    def closeEvent(self, event):
        """Gestion de la fermeture de la fenêtre
        
        Args:
            event (QCloseEvent): Événement de fermeture
        """
        print("closeEvent appelé - Début de la fermeture de la fenêtre")
        
        # Arrêt du thread de scan s'il est en cours d'exécution
        if hasattr(self, 'scan_thread') and self.scan_thread is not None:
            print(f"Thread de scan existant: {self.scan_thread}, en cours d'exécution: {self.scan_thread.isRunning()}")
            if self.scan_thread.isRunning():
                print("Arrêt du thread de scan...")
                self.scan_thread.stop()
                self.scan_thread.wait(2000)  # Attendre 2 secondes maximum
                print("Thread de scan arrêté")
        else:
            print("Aucun thread de scan à arrêter")
        
        # S'assurer que tous les threads sont arrêtés avant de fermer
        print("Attente de la fin de tous les threads...")
        QThread.msleep(500)  # Pause pour laisser le temps aux threads de se terminer
        
        # Accepter l'événement de fermeture
        print("closeEvent terminé - Fermeture de la fenêtre acceptée")
        event.accept()
    
    def setup_specific_toolbar(self):
        """Configuration spécifique de la barre d'outils"""
        # Action pour choisir le dossier de travail
        self.action_select_workspace = QAction("Choisir dossier de travail...", self)
        self.action_select_workspace.triggered.connect(self.select_workspace_dir)
        self.action_select_workspace.setShortcut(QKeySequence("Ctrl+O"))
        self.action_select_workspace.setStatusTip("Sélectionner un dossier de travail")
        self.toolbar.addAction(self.action_select_workspace)
        
        # Action pour vider le workspace
        self.action_reset_workspace = QAction("Vider le workspace", self)
        self.action_reset_workspace.setToolTip("Réinitialiser le workspace")
        self.action_reset_workspace.triggered.connect(self.reset_workspace)
        self.action_reset_workspace.setShortcut(QKeySequence("Ctrl+R"))
        self.toolbar.addAction(self.action_reset_workspace)
        
        # Séparateur
        self.toolbar.addSeparator()
        
        # Action pour actualiser
        self.action_refresh = QAction("Actualiser", self)
        self.action_refresh.setToolTip("Actualiser le workspace")
        self.action_refresh.triggered.connect(self.refresh_workspace)
        self.action_refresh.setShortcut(QKeySequence("F5"))
        self.toolbar.addAction(self.action_refresh)
        
        # Séparateur
        self.toolbar.addSeparator()
        
        # Action pour créer un nouveau dossier
        self.action_new_folder = QAction("Nouveau dossier", self)
        self.action_new_folder.setToolTip("Créer un nouveau dossier")
        self.action_new_folder.triggered.connect(lambda: self.create_new_folder(self.file_tree_right.get_selected_path() or self.workspace_dir))
        self.action_new_folder.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.toolbar.addAction(self.action_new_folder)
        
        # Action pour ouvrir le projet sélectionné dans Cubase
        self.action_open_in_cubase = QAction("Ouvrir dans Cubase", self)
        self.action_open_in_cubase.setToolTip("Ouvrir le projet sélectionné dans Cubase")
        self.action_open_in_cubase.triggered.connect(self.open_selected_in_cubase)
        self.action_open_in_cubase.setShortcut(QKeySequence("Ctrl+P"))
        self.toolbar.addAction(self.action_open_in_cubase)
    
    def open_vsti_manager_dialog(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QInputDialog, QMessageBox
        from services.vsti_manager import load_vsti_list, save_vsti_list
        class VstiManagerDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Gestion des VSTi connus")
                self.setMinimumWidth(400)
                layout = QVBoxLayout(self)
                self.list_widget = QListWidget()
                self.vsti_list = sorted(load_vsti_list(), key=lambda x: x.lower())
                self.refresh_list()
                layout.addWidget(self.list_widget)
                btn_layout = QHBoxLayout()
                self.btn_add = QPushButton("Ajouter")
                self.btn_edit = QPushButton("Renommer")
                self.btn_del = QPushButton("Supprimer")
                btn_layout.addWidget(self.btn_add)
                btn_layout.addWidget(self.btn_edit)
                btn_layout.addWidget(self.btn_del)
                layout.addLayout(btn_layout)
                self.btn_add.clicked.connect(self.add_vsti)
                self.btn_edit.clicked.connect(self.edit_vsti)
                self.btn_del.clicked.connect(self.del_vsti)
                self.list_widget.itemDoubleClicked.connect(self.edit_vsti)
            def refresh_list(self):
                self.list_widget.clear()
                self.vsti_list.sort(key=lambda x: x.lower())
                self.list_widget.addItems(self.vsti_list)
            def save_and_refresh(self):
                save_vsti_list(self.vsti_list)
                self.refresh_list()
            def add_vsti(self):
                name, ok = QInputDialog.getText(self, "Ajouter un VSTi", "Nom du VSTi :")
                if ok and name.strip():
                    name = name.strip()
                    if name not in self.vsti_list:
                        self.vsti_list.append(name)
                        self.save_and_refresh()
            def edit_vsti(self):
                item = self.list_widget.currentItem()
                if not item:
                    return
                old = item.text()
                new, ok = QInputDialog.getText(self, "Renommer le VSTi", "Nouveau nom :", text=old)
                if ok and new.strip() and new != old:
                    if new not in self.vsti_list:
                        idx = self.vsti_list.index(old)
                        self.vsti_list[idx] = new
                        self.save_and_refresh()
            def del_vsti(self):
                item = self.list_widget.currentItem()
                if not item:
                    return
                name = item.text()
                r = QMessageBox.question(self, "Supprimer", f"Supprimer {name} ?")
                if r == QMessageBox.Yes:
                    self.vsti_list.remove(name)
                    self.save_and_refresh()
            def accept(self):
                save_vsti_list(self.vsti_list)
                super().accept()
        dlg = VstiManagerDialog(self)
        dlg.exec_()

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
        
        # Arborescences de fichiers avec étiquettes descriptives
        # Conteneur principal pour les deux arborescences
        trees_container = QWidget()
        trees_layout = QVBoxLayout(trees_container)
        
        # Étiquette pour les arborescences
        trees_label = QLabel("<b>Navigation des fichiers</b>")
        trees_layout.addWidget(trees_label)
        
        # Splitter horizontal pour les deux arborescences
        trees_splitter = QSplitter(Qt.Vertical)  # Vertical pour avoir les arbres l'un au-dessus de l'autre
        
        # Conteneur pour l'arborescence gauche (navigation globale)
        left_tree_container = QWidget()
        left_tree_layout = QVBoxLayout(left_tree_container)
        left_tree_layout.setContentsMargins(0, 0, 0, 0)
        left_tree_label = QLabel("<b>Navigation globale</b> - Dossier de travail complet")
        
        # Historique de navigation pour l'arborescence gauche (sans interface visible)
        # Ces variables sont conservées pour les fonctionnalités d'historique
        
        # Création de l'arborescence gauche avec la possibilité de remonter dans l'arborescence
        self.file_tree_left = FileTree(allow_navigation_up=True)
        self.file_tree_left.context_menu_requested.connect(self.show_file_tree_left_context_menu)
        self.file_tree_left.files_dropped.connect(self.on_files_dropped_left)
        
        # Historique de navigation pour l'arborescence gauche
        self.left_nav_history = []
        self.left_nav_current = -1
        
        # Optimisation de l'affichage des colonnes pour l'arborescence gauche
        self.file_tree_left.header().setStretchLastSection(False)
        self.file_tree_left.header().setSectionResizeMode(0, QHeaderView.Stretch)
        # Renommer les colonnes en utilisant le modèle existant avec les noms corrects
        # Dans QFileSystemModel, l'ordre des colonnes est : Nom (0), Taille (1), Type (2), Date de modification (3)
        self.file_tree_left.fs_model.setHeaderData(0, Qt.Horizontal, "Nom")
        self.file_tree_left.fs_model.setHeaderData(1, Qt.Horizontal, "Taille")
        self.file_tree_left.fs_model.setHeaderData(2, Qt.Horizontal, "Type")
        self.file_tree_left.fs_model.setHeaderData(3, Qt.Horizontal, "Date de modification")
        
        # Ajuster la largeur des colonnes pour une meilleure lisibilité
        self.file_tree_left.header().resizeSection(1, 100)  # Taille
        self.file_tree_left.header().resizeSection(2, 100)  # Type
        self.file_tree_left.header().resizeSection(3, 150)  # Date
        
        left_tree_layout.addWidget(left_tree_label)
        left_tree_layout.addWidget(self.file_tree_left)
        
        # Conteneur pour l'arborescence droite (détails du projet)
        right_tree_container = QWidget()
        right_tree_layout = QVBoxLayout(right_tree_container)
        right_tree_layout.setContentsMargins(0, 0, 0, 0)
        right_tree_label = QLabel("<b>Détails du projet</b> - Contenu du projet sélectionné")
        
        # Historique de navigation pour l'arborescence droite (sans interface visible)
        # Ces variables sont conservées pour les fonctionnalités d'historique
        
        # Création de l'arborescence droite
        self.file_tree_right = FileTree()
        self.file_tree_right.context_menu_requested.connect(self.show_file_tree_right_context_menu)
        self.file_tree_right.files_dropped.connect(self.on_files_dropped_right)
        
        # Historique de navigation pour l'arborescence droite
        self.right_nav_history = []
        self.right_nav_current = -1
        
        # Optimisation de l'affichage des colonnes pour l'arborescence droite
        self.file_tree_right.header().setStretchLastSection(False)
        self.file_tree_right.header().setSectionResizeMode(0, QHeaderView.Stretch)
        # Renommer les colonnes en utilisant le modèle existant avec les noms corrects
        # Dans QFileSystemModel, l'ordre des colonnes est : Nom (0), Taille (1), Type (2), Date de modification (3)
        self.file_tree_right.fs_model.setHeaderData(0, Qt.Horizontal, "Nom")
        self.file_tree_right.fs_model.setHeaderData(1, Qt.Horizontal, "Taille")
        self.file_tree_right.fs_model.setHeaderData(2, Qt.Horizontal, "Type")
        self.file_tree_right.fs_model.setHeaderData(3, Qt.Horizontal, "Date de modification")
        
        # Ajuster la largeur des colonnes pour une meilleure lisibilité
        self.file_tree_right.header().resizeSection(1, 100)  # Taille
        self.file_tree_right.header().resizeSection(2, 100)  # Type
        self.file_tree_right.header().resizeSection(3, 150)  # Date
        
        right_tree_layout.addWidget(right_tree_label)
        right_tree_layout.addWidget(self.file_tree_right)
        
        # Ajout des conteneurs au splitter
        trees_splitter.addWidget(left_tree_container)
        trees_splitter.addWidget(right_tree_container)
        trees_splitter.setSizes([300, 300])  # Tailles initiales égales
        
        # Ajout du splitter au conteneur principal
        trees_layout.addWidget(trees_splitter)
        
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

        # Zone d'affichage des VSTi
        self.vsti_text = QTextEdit()
        self.vsti_text.setReadOnly(True)
        self.vsti_text.setPlaceholderText("VSTi utilisés : sélectionnez un projet pour voir la liste.")
        # Ligne label + bouton paramètres
        vsti_label_layout = QHBoxLayout()
        vsti_label = QLabel("<b>VSTi utilisés dans ce projet :</b>")
        vsti_label_layout.addWidget(vsti_label)
        self.vsti_settings_btn = QToolButton()
        # Icône roue dentée universelle (QStyle)
        from PyQt5.QtWidgets import QStyle
        style = self.style()
        icon = style.standardIcon(QStyle.SP_FileDialogDetailedView)
        self.vsti_settings_btn.setIcon(icon)
        self.vsti_settings_btn.setToolTip("Gérer la liste des VSTi connus")
        self.vsti_settings_btn.clicked.connect(self.open_vsti_manager_dialog)
        vsti_label_layout.addWidget(self.vsti_settings_btn)
        vsti_label_layout.addStretch(1)
        metadata_layout.addLayout(vsti_label_layout)
        metadata_layout.addWidget(self.vsti_text)
        # Barre de progression globale sous le menu (layout principal)
        self.vsti_progress = QProgressBar()
        self.vsti_progress.setMinimum(0)
        self.vsti_progress.setMaximum(100)
        self.vsti_progress.setValue(0)
        self.vsti_progress.setVisible(False)
        self.vsti_progress.setTextVisible(True)
        self.main_layout.insertWidget(1, self.vsti_progress)  # Juste après le menu/label workspace
        print('[DEBUG] Barre de progression VSTi ajoutée au layout principal')

        # Ajout des onglets
        self.details_tabs.addTab(files_tab, "Lecteur Audio")
        self.details_tabs.addTab(metadata_tab, "Tags & Notes / VSTi")
        
        # Ajout du splitter horizontal : à gauche les arborescences, à droite les tabs de détails
        self.details_splitter = QSplitter(Qt.Horizontal)
        self.details_splitter.addWidget(trees_container)
        self.details_splitter.addWidget(self.details_tabs)
        self.details_splitter.setStretchFactor(0, 2)  # Donner plus d'espace aux arborescences
        self.details_splitter.setStretchFactor(1, 1)
        
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
        
        # Connecter les signaux pour l'historique de navigation de l'arborescence droite
        self.file_tree_right.fs_model.rootPathChanged.connect(self.on_file_tree_right_path_changed)
        
        # Initialiser l'état des boutons de navigation
        self.update_navigation_buttons()
    
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
        Configuration de la vue pour le workspace (ASYNCHRONE avec barre de progression)
        Args:
            directory (str): Chemin du dossier de travail
        """
        # Pour l'arborescence gauche, on affiche tout le système de fichiers
        self.file_tree_left.set_root_path("")
        self.file_tree_left.setCurrentIndex(self.file_tree_left.fs_model.index(directory))
        self.file_tree_left.scrollTo(self.file_tree_left.fs_model.index(directory))
        self.file_tree_left.expand(self.file_tree_left.fs_model.index(directory))

        # Afficher la barre de progression en mode indéterminé (marquee)
        self.vsti_progress.setVisible(True)
        self.vsti_progress.setMinimum(0)
        self.vsti_progress.setMaximum(0)  # Indéterminé
        self.vsti_progress.setFormat("Scan des projets en cours...")
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()  # Forcer le rafraîchissement de l'UI pour afficher la barre

        # Thread et worker pour le scan
        from PyQt5.QtCore import QObject, pyqtSignal
        class WorkspaceScanWorker(QObject):
            progressChanged = pyqtSignal(int)
            finished = pyqtSignal(object)
            def __init__(self, scanner, directory):
                super().__init__()
                self.scanner = scanner
                self.directory = directory
            def run(self):
                import os
                self.scanner.clear()
                # Compter ET scanner dans le worker pour ne rien bloquer
                total = 0
                for _ in os.walk(self.directory):
                    total += 1
                current = 0
                for root, dirs, files in os.walk(self.directory):
                    self.scanner.scan_directory(root)
                    current += 1
                    percent = int((current / total) * 100) if total > 0 else 100
                    self.progressChanged.emit(percent)
                self.finished.emit(self.scanner)

        # Arrêter un éventuel thread précédent
        if hasattr(self, 'scan_thread') and self.scan_thread is not None:
            if self.scan_thread.isRunning():
                self.scan_thread.quit()
                self.scan_thread.wait()
        self.scan_thread = QThread()
        self.scan_worker = WorkspaceScanWorker(self.scanner, directory)
        self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.progressChanged.connect(self.vsti_progress.setValue)

        def on_scan_finished(scanner):
            for project_name, project_data in scanner.projects.items():
                project_dir = project_data.get('project_dir', '')
                if not project_dir or not os.path.exists(project_dir):
                    if project_data.get('cpr_files') and len(project_data['cpr_files']) > 0:
                        first_cpr = project_data['cpr_files'][0]
                        project_dir = os.path.dirname(first_cpr['path'])
                        project_data['project_dir'] = project_dir
                    elif project_data.get('wav_files') and len(project_data['wav_files']) > 0:
                        first_wav = project_data['wav_files'][0]
                        project_dir = os.path.dirname(first_wav['path'])
                        project_data['project_dir'] = project_dir
                    elif project_data.get('bak_files') and len(project_data['bak_files']) > 0:
                        first_bak = project_data['bak_files'][0]
                        project_dir = os.path.dirname(first_bak['path'])
                        project_data['project_dir'] = project_dir
                    elif project_data.get('other_files') and len(project_data['other_files']) > 0:
                        first_other = project_data['other_files'][0]
                        project_dir = os.path.dirname(first_other['path'])
                        project_data['project_dir'] = project_dir
                    else:
                        project_dir = os.path.join(directory, project_name)
                        if os.path.exists(project_dir) and os.path.isdir(project_dir):
                            project_data['project_dir'] = project_dir
                        else:
                            project_data['project_dir'] = directory
            scanner._create_dataframe()
            self.all_projects_data = scanner.df_projects
            self.project_table.update_data(self.all_projects_data)
            self.vsti_progress.setMaximum(100)
            self.vsti_progress.setValue(100)
            self.vsti_progress.setVisible(False)
            self.statusBar.showMessage(f"{len(self.all_projects_data)} projets trouvés dans le dossier de travail")
            self.scan_thread.quit()
            self.scan_thread.wait()
        self.scan_worker.finished.connect(on_scan_finished)
        self.scan_thread.start()

    
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
        
    def refresh_workspace(self):
        """Actualisation du workspace"""
        if not self.workspace_dir or not os.path.exists(self.workspace_dir):
            QMessageBox.warning(self, "Erreur", "Aucun dossier de travail sélectionné ou le dossier n'existe plus.")
            return
            
        # Réinitialiser le scanner
        self.scanner.clear()
        
        # Rescanner le dossier de travail
        self.setup_workspace_view(self.workspace_dir)
        
        # Message de statut
        self.statusBar.showMessage(f"Workspace actualisé : {len(self.all_projects_data)} projets trouvés")
        
    def open_selected_in_cubase(self):
        """Ouvre le projet sélectionné dans Cubase"""
        # Vérifier si un projet est sélectionné dans la table des projets
        project = self.project_table.get_selected_project()
        if project:
            # Vérifier si le projet a un fichier CPR
            if project.get('latest_cpr'):
                self.cubase_service.open_project(project.get('latest_cpr'))
                self.statusBar.showMessage(f"Ouverture du projet {project.get('project_name')} dans Cubase")
                return
                
        # Vérifier si un fichier CPR est sélectionné dans l'arborescence de droite
        selected_path = self.file_tree_right.get_selected_path()
        if selected_path and selected_path.lower().endswith('.cpr'):
            self.cubase_service.open_project(selected_path)
            self.statusBar.showMessage(f"Ouverture du fichier {os.path.basename(selected_path)} dans Cubase")
            return
            
        QMessageBox.warning(self, "Erreur", "Aucun projet Cubase sélectionné.")
    
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
        
        # Réinitialiser les métadonnées avant de les mettre à jour
        # Cela évite que les métadonnées d'un projet précédent ne persistent
        self.metadata_editor.set_metadata({'tags': [], 'rating': 0, 'notes': ''})
        
        # Récupération des métadonnées du projet
        try:
            metadata = self.metadata_service.get_project_metadata(project_name, project_folder)
            if metadata:
                # Mise à jour des métadonnées dans l'éditeur
                self.metadata_editor.set_metadata(metadata)
                print(f"Métadonnées chargées pour {project_name} depuis {project_folder}")
            else:
                print(f"Aucune métadonnée trouvée pour {project_name}")
        except Exception as e:
            print(f"Erreur lors de la récupération des métadonnées: {e}")

        # Arrêt propre du thread VSTi précédent s'il existe
        if hasattr(self, '_vsti_thread') and self._vsti_thread is not None:
            print('[DEBUG] Arrêt du thread VSTi précédent...')
            self._vsti_thread.quit()
            self._vsti_thread.wait(1000)
            self._vsti_thread = None
            self._vsti_worker = None
        # Affichage de la barre de progression globale dès le début du chargement
        self.vsti_progress.setMinimum(0)
        self.vsti_progress.setMaximum(0)  # indéterminée
        self.vsti_progress.setFormat('Chargement en cours...')
        self.vsti_progress.setVisible(True)
        self.vsti_progress.show()
        print('[DEBUG] Barre de progression globale visible')
        self.vsti_text.setEnabled(False)
        self._vsti_progress_shown_time = None
        from PyQt5.QtCore import QTimer
        self._vsti_hide_timer = QTimer(self)
        self._vsti_hide_timer.setSingleShot(True)
        self._vsti_hide_timer.timeout.connect(lambda: self.vsti_progress.hide())
        from PyQt5.QtCore import QThread, pyqtSignal, QObject
        import traceback
        class VstiWorker(QObject):
            finished = pyqtSignal(set, str)
            progressChanged = pyqtSignal(int)
            def __init__(self, cpr_path):
                super().__init__()
                self.cpr_path = cpr_path
            def run(self):
                try:
                    from services.lectureCPR import trouve_vsti
                    import os
                    found = set()
                    if self.cpr_path and os.path.exists(self.cpr_path):
                        def progress_callback(percent):
                            self.progressChanged.emit(percent)
                        found = trouve_vsti(self.cpr_path, progress_callback=progress_callback)
                        self.finished.emit(found, "")
                    else:
                        self.finished.emit(set(), "Aucun fichier CPR trouvé dans le dossier du projet.")
                except Exception as e:
                    tb = traceback.format_exc()
                    self.finished.emit(set(), f"Erreur lors de l'analyse du fichier CPR : {e}\n{tb}")
        # Recherche du CPR principal
        cpr_path = None
        if project_folder and os.path.exists(project_folder):
            for file in os.listdir(project_folder):
                if file.lower().endswith('.cpr'):
                    cpr_path = os.path.join(project_folder, file)
                    break
        self._vsti_thread = QThread()
        self._vsti_worker = VstiWorker(cpr_path)
        self._vsti_worker.moveToThread(self._vsti_thread)
        self._vsti_thread.started.connect(self._vsti_worker.run)
        import time
        def on_vsti_finished(vsti_set, error):
            elapsed = 0
            if self._vsti_progress_shown_time is not None:
                elapsed = (time.time() - self._vsti_progress_shown_time) * 1000  # ms
            min_duration = 500  # ms
            def hide_progress():
                self.vsti_progress.setVisible(False)
                self.vsti_progress.hide()
                print('[DEBUG] Barre de progression VSTi masquée')
            if elapsed < min_duration:
                self._vsti_hide_timer.start(int(min_duration - elapsed))
            else:
                hide_progress()
            self.vsti_text.setEnabled(True)
            if error:
                self.vsti_text.setPlainText(error)
            elif vsti_set:
                self.vsti_text.setPlainText("\n".join(sorted(vsti_set)))
            else:
                self.vsti_text.setPlainText("Aucun VSTi détecté dans ce projet.")
            self._vsti_thread.quit()
            self._vsti_thread.wait()
            self._vsti_thread = None
            self._vsti_worker = None
        # Mémoriser le moment d'affichage de la barre
        import time
        self._vsti_progress_shown_time = time.time()
        def on_vsti_progress(percent):
            pass  # Désactivé, barre indéterminée
        self._vsti_worker.finished.connect(on_vsti_finished)
        self._vsti_worker.progressChanged.connect(on_vsti_progress)
        self._vsti_thread.start()

        # Message de statut
        self.statusBar.showMessage(f"Projet sélectionné: {project_name}")
    
    def on_file_tree_left_selected(self, path):
        """
        Gestion de la sélection d'un élément dans l'arborescence de gauche
        
        Args:
            path (str): Chemin de l'élément sélectionné
        """
        if os.path.isdir(path):
            # Mettre à jour l'arborescence de droite
            self.file_tree_right.set_root_path(path)
            
            # Mettre à jour l'historique de navigation de l'arborescence gauche
            # Si nous sommes au milieu de l'historique, supprimer les entrées après l'index courant
            if self.left_nav_current < len(self.left_nav_history) - 1:
                self.left_nav_history = self.left_nav_history[:self.left_nav_current + 1]
            
            # Ajouter le chemin à l'historique s'il est différent du dernier
            if not self.left_nav_history or self.left_nav_history[-1] != path:
                self.left_nav_history.append(path)
                self.left_nav_current = len(self.left_nav_history) - 1
            
            # Mettre à jour l'état des boutons de navigation
            self.update_navigation_buttons()
    
    def on_file_tree_right_path_changed(self, path):
        """
        Gestion du changement de dossier dans l'arborescence de droite
        
        Args:
            path (str): Nouveau chemin racine de l'arborescence
        """
        if not path or not os.path.exists(path):
            return
            
        # Mettre à jour l'historique de navigation de l'arborescence droite
        # Si nous sommes au milieu de l'historique, supprimer les entrées après l'index courant
        if self.right_nav_current < len(self.right_nav_history) - 1:
            self.right_nav_history = self.right_nav_history[:self.right_nav_current + 1]
        
        # Ajouter le chemin à l'historique s'il est différent du dernier
        if not self.right_nav_history or self.right_nav_history[-1] != path:
            self.right_nav_history.append(path)
            self.right_nav_current = len(self.right_nav_history) - 1
        
        # Mettre à jour l'état des boutons de navigation
        self.update_navigation_buttons()
    
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
    
    def update_navigation_buttons(self):
        """Mise à jour de l'état des boutons de navigation"""
        # Cette méthode ne fait plus rien car les boutons ont été supprimés
        # L'historique de navigation est toujours conservé en arrière-plan
        pass
        
    def on_files_dropped_left(self, source_paths, target_path):
        """
        Gestion du dépôt de fichiers dans l'arborescence gauche
        
        Args:
            source_paths (list): Liste des chemins sources
            target_path (str): Chemin cible
        """
        self._copy_or_move_files(source_paths, target_path)
    
    def on_files_dropped_right(self, source_paths, target_path):
        """
        Gestion du dépôt de fichiers dans l'arborescence droite
        
        Args:
            source_paths (list): Liste des chemins sources
            target_path (str): Chemin cible
        """
        self._copy_or_move_files(source_paths, target_path)
    
    def _copy_or_move_files(self, source_paths, target_path):
        """
        Copie ou déplacement de fichiers
        
        Args:
            source_paths (list): Liste des chemins sources
            target_path (str): Chemin cible
        """
        # Vérifier que le chemin cible existe
        if not os.path.exists(target_path):
            QMessageBox.warning(self, "Erreur", f"Le dossier cible {target_path} n'existe pas.")
            return
            
        # Vérifier que le chemin cible est un dossier
        if not os.path.isdir(target_path):
            target_path = os.path.dirname(target_path)
            
        # Demander à l'utilisateur s'il veut copier ou déplacer
        copy_button = QMessageBox.Yes
        move_button = QMessageBox.No
        cancel_button = QMessageBox.Cancel
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Copier ou déplacer")
        msg_box.setText(f"Voulez-vous copier ou déplacer {len(source_paths)} fichier(s) vers {target_path}?")
        msg_box.addButton("Copier", QMessageBox.YesRole)
        msg_box.addButton("Déplacer", QMessageBox.NoRole)
        msg_box.addButton("Annuler", QMessageBox.RejectRole)
        msg_box.setDefaultButton(QMessageBox.Yes)
        
        reply = msg_box.exec_()
        
        if reply == 2:  # Annuler (troisième bouton, index 2)
            return
            
        is_move = (reply == 1)  # Déplacer (deuxième bouton, index 1)
        operation_name = "Déplacement" if is_move else "Copie"
        
        # Copier ou déplacer chaque fichier
        success_count = 0
        error_count = 0
        
        for source_path in source_paths:
            # Vérifier que le chemin source existe
            if not os.path.exists(source_path):
                error_count += 1
                continue
                
            # Déterminer le chemin de destination
            filename = os.path.basename(source_path)
            dest_path = os.path.join(target_path, filename)
            
            # Vérifier si le fichier existe déjà à destination
            if os.path.exists(dest_path):
                # Demander confirmation pour écraser
                overwrite_reply = QMessageBox.question(
                    self,
                    "Fichier existant",
                    f"Le fichier {filename} existe déjà dans le dossier cible. Voulez-vous le remplacer?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if overwrite_reply == QMessageBox.No:
                    continue
            
            try:
                # Copier ou déplacer le fichier
                if is_move:
                    shutil.move(source_path, dest_path)
                else:
                    if os.path.isdir(source_path):
                        # Copier un dossier avec son contenu
                        shutil.copytree(source_path, dest_path)
                    else:
                        # Copier un fichier
                        shutil.copy2(source_path, dest_path)
                        
                success_count += 1
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Erreur lors de l'opération: {str(e)}")
                error_count += 1
        
        # Afficher un résumé des opérations
        if success_count > 0:
            self.statusBar.showMessage(
                f"{operation_name} terminée: {success_count} fichier(s) traité(s) avec succès" +
                (f", {error_count} erreur(s)" if error_count > 0 else ""),
                5000
            )
            
            # Rafraîchir les arborescences
            self.refresh_workspace()
    
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
        
        # Ajouter une action pour ouvrir dans Cubase si c'est un fichier CPR
        if not is_dir and path.lower().endswith('.cpr'):
            menu.addSeparator()
            open_in_cubase_action = menu.addAction("Ouvrir dans Cubase")
        else:
            open_in_cubase_action = None
        
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
        elif action == open_in_cubase_action:
            self.cubase_service.open_project(path)
            self.statusBar.showMessage(f"Ouverture du fichier {os.path.basename(path)} dans Cubase")
    
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
    
    def navigate_back(self, tree_view):
        """Navigation en arrière dans l'historique
        
        Args:
            tree_view (FileTree): Arborescence à naviguer
        """
        if tree_view == self.file_tree_left:
            history = self.left_nav_history
            current = self.left_nav_current
        else:
            history = self.right_nav_history
            current = self.right_nav_current
        
        if current > 0:
            current -= 1
            path = history[current]
            
            # Désactiver temporairement la mise à jour de l'historique
            tree_view.blockSignals(True)
            tree_view.set_root_path(path)
            tree_view.blockSignals(False)
            
            # Mettre à jour l'index courant
            if tree_view == self.file_tree_left:
                self.left_nav_current = current
            else:
                self.right_nav_current = current
    
    def navigate_forward(self, tree_view):
        """Navigation en avant dans l'historique
        
        Args:
            tree_view (FileTree): Arborescence à naviguer
        """
        if tree_view == self.file_tree_left:
            history = self.left_nav_history
            current = self.left_nav_current
        else:
            history = self.right_nav_history
            current = self.right_nav_current
        
        if current < len(history) - 1:
            current += 1
            path = history[current]
            
            # Désactiver temporairement la mise à jour de l'historique
            tree_view.blockSignals(True)
            tree_view.set_root_path(path)
            tree_view.blockSignals(False)
            
            # Mettre à jour l'index courant
            if tree_view == self.file_tree_left:
                self.left_nav_current = current
            else:
                self.right_nav_current = current
    
    def navigate_up(self, tree_view):
        """Navigation vers le dossier parent
        
        Args:
            tree_view (FileTree): Arborescence à naviguer
        """
        current_path = tree_view.get_selected_path()
        if not current_path:
            # Si aucun élément n'est sélectionné, utiliser le dossier racine
            current_path = tree_view.fs_model.rootPath()
        
        if os.path.isdir(current_path):
            parent_dir = os.path.dirname(current_path)
        else:
            parent_dir = os.path.dirname(os.path.dirname(current_path))
        
        if os.path.exists(parent_dir):
            tree_view.set_root_path(parent_dir)
    
    def navigate_home(self, tree_view):
        """Navigation vers le dossier de travail
        
        Args:
            tree_view (FileTree): Arborescence à naviguer
        """
        if self.workspace_dir and os.path.exists(self.workspace_dir):
            tree_view.set_root_path(self.workspace_dir)
    
    def filter_files(self, tree_view, filter_text):
        """Filtrage des fichiers dans l'arborescence
        
        Args:
            tree_view (FileTree): Arborescence à filtrer
            filter_text (str): Texte de filtrage
        """
        if not filter_text:
            # Réinitialiser le filtre
            tree_view.fs_model.setNameFilters([])
            tree_view.fs_model.setNameFilterDisables(True)
            return
        
        # Créer un filtre basé sur le texte de recherche
        # On utilise une expression régulière pour faire une recherche insensible à la casse
        try:
            regex = re.compile(filter_text, re.IGNORECASE)
            
            # Filtrer les éléments dans l'arborescence
            for i in range(tree_view.model().rowCount(tree_view.rootIndex())):
                index = tree_view.model().index(i, 0, tree_view.rootIndex())
                item_text = tree_view.model().data(index)
                
                # Masquer ou afficher l'élément selon le filtre
                if regex.search(item_text):
                    tree_view.setRowHidden(i, tree_view.rootIndex(), False)
                else:
                    tree_view.setRowHidden(i, tree_view.rootIndex(), True)
        except re.error:
            # En cas d'erreur dans l'expression régulière, ne pas filtrer
            pass
    
    def delete_item(self, path):
        """Suppression d'un élément
        
        Args:
            path (str): Chemin de l'élément à supprimer
        """
        if not os.path.exists(path):
            return
            
        # Confirmation de la suppression
        msg = "Voulez-vous vraiment supprimer cet élément ?\n\n" + path
        reply = QMessageBox.question(self, "Confirmation", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success = False
            try:
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                success = True
            except Exception as e:
                self.show_error("Erreur", f"Impossible de supprimer l'élément: {e}")
            
            if success:
                self.statusBar.showMessage(f"Elément supprimé: {path}")
                # Rafraîchir l'arborescence
                parent_dir = os.path.dirname(path)
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
        
        try:
            # Récupérer les métadonnées existantes du service
            existing_metadata = self.metadata_service.get_project_metadata(project_name, project_folder)
            if existing_metadata:
                # Fusionner les métadonnées existantes avec celles de l'éditeur
                # pour s'assurer que toutes les informations sont préservées
                for key, value in existing_metadata.items():
                    if key not in metadata or not metadata[key]:
                        metadata[key] = value
            
            # Ajouter la date de sauvegarde aux métadonnées
            metadata['saved_date'] = datetime.datetime.now().isoformat()
            metadata['name'] = project_name
            
            # Sauvegarde des métadonnées
            success = self.metadata_service.set_project_metadata(project_name, metadata, project_folder)
            
            if success:
                # Afficher uniquement un message dans la barre d'état
                self.statusBar.showMessage(f"Métadonnées du projet '{project_name}' sauvegardées")
                print(f"Métadonnées sauvegardées pour {project_name} dans {project_folder}")
            else:
                self.show_warning("Erreur", f"Erreur lors de la sauvegarde des métadonnées du projet '{project_name}'")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des métadonnées: {e}")
            self.statusBar.showMessage(f"Erreur lors de la sauvegarde des métadonnées: {e}")
