#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Composant d'édition des métadonnées pour l'application
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QCompleter, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal

class TagButton(QPushButton):
    """Bouton de tag avec signal de suppression"""
    
    remove_requested = pyqtSignal(str)
    
    def __init__(self, tag_text, parent=None):
        """
        Initialisation du bouton de tag
        
        Args:
            tag_text (str): Texte du tag
            parent (QWidget): Widget parent
        """
        super(TagButton, self).__init__(tag_text, parent)
        self.tag_text = tag_text
        self.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 10px;
                padding: 5px 10px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        """Gestion du clic sur le bouton"""
        self.remove_requested.emit(self.tag_text)

class MetadataEditor(QWidget):
    """Composant d'édition des métadonnées (tags, notes, notation)"""
    
    # Signaux
    metadata_changed = pyqtSignal(dict)
    tag_added = pyqtSignal(str)
    tag_removed = pyqtSignal(str)
    rating_changed = pyqtSignal(int)
    notes_changed = pyqtSignal(str)
    save_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Initialisation de l'éditeur de métadonnées
        
        Args:
            parent (QWidget): Widget parent
        """
        super(MetadataEditor, self).__init__(parent)
        
        # Données
        self.current_tags = []
        self.current_rating = 0
        self.all_tags = []  # Pour l'auto-complétion
        
        # Configuration de l'interface
        self.setup_ui()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
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
        self.tag_completer = QCompleter(self.all_tags)
        self.tag_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.txt_tag_input.setCompleter(self.tag_completer)
        
        self.btn_add_tag = QPushButton("Ajouter")
        self.btn_add_tag.clicked.connect(self.add_tag)
        
        tags_input_layout.addWidget(self.lbl_tags)
        tags_input_layout.addWidget(self.txt_tag_input, 1)
        tags_input_layout.addWidget(self.btn_add_tag)
        
        # Affichage des tags actuels
        self.lbl_current_tags = QLabel("Tags actuels:")
        
        # Conteneur de tags avec défilement
        self.tags_scroll = QScrollArea()
        self.tags_scroll.setWidgetResizable(True)
        self.tags_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tags_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.tags_container = QWidget()
        self.tags_container_layout = QHBoxLayout(self.tags_container)
        self.tags_container_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_container_layout.setSpacing(5)
        self.tags_container_layout.setAlignment(Qt.AlignLeft)
        
        self.tags_scroll.setWidget(self.tags_container)
        
        tags_layout.addLayout(tags_input_layout)
        tags_layout.addWidget(self.lbl_current_tags)
        tags_layout.addWidget(self.tags_scroll)
        
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
            btn.clicked.connect(self.set_rating)
            self.rating_buttons.append(btn)
            rating_layout.addWidget(btn)
        
        # Section des notes
        notes_group = QGroupBox("Notes du projet")
        notes_layout = QVBoxLayout(notes_group)
        
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Ajoutez ici des notes sur le projet")
        self.txt_notes.setMinimumHeight(100)
        self.txt_notes.textChanged.connect(self._on_notes_changed)
        
        notes_layout.addWidget(self.txt_notes)
        
        # Bouton de sauvegarde
        self.btn_save = QPushButton("Sauvegarder les métadonnées")
        self.btn_save.clicked.connect(self._on_save_clicked)
        
        # Ajout des sections au layout principal
        main_layout.addWidget(tags_group)
        main_layout.addWidget(rating_group)
        main_layout.addWidget(notes_group)
        main_layout.addWidget(self.btn_save)
    
    def set_all_tags(self, tags):
        """
        Définition de la liste complète des tags pour l'auto-complétion
        
        Args:
            tags (list): Liste de tous les tags
        """
        self.all_tags = tags
        self.tag_completer.setModel(self.tag_completer.model())
    
    def set_metadata(self, metadata):
        """
        Définition des métadonnées à éditer
        
        Args:
            metadata (dict): Métadonnées du projet
        """
        # Mise à jour des tags
        self.current_tags = metadata.get('tags', [])
        self.update_tags_display()
        
        # Mise à jour de la note
        self.current_rating = metadata.get('rating', 0)
        self.update_rating_buttons()
        
        # Mise à jour des notes
        self.txt_notes.setText(metadata.get('notes', ''))
    
    def get_metadata(self):
        """
        Récupération des métadonnées éditées
        
        Returns:
            dict: Métadonnées du projet
        """
        return {
            'tags': self.current_tags,
            'rating': self.current_rating,
            'notes': self.txt_notes.toPlainText()
        }
    
    def add_tag(self):
        """Ajout d'un tag à la liste"""
        tag = self.txt_tag_input.text().strip()
        if not tag:
            return
        
        # Vérifier si le tag existe déjà
        if tag in self.current_tags:
            return
        
        # Ajouter le tag
        self.current_tags.append(tag)
        self.update_tags_display()
        
        # Vider le champ de saisie
        self.txt_tag_input.clear()
        
        # Émettre le signal
        self.tag_added.emit(tag)
        self.metadata_changed.emit(self.get_metadata())
    
    def remove_tag(self, tag):
        """
        Suppression d'un tag de la liste
        
        Args:
            tag (str): Tag à supprimer
        """
        if tag in self.current_tags:
            self.current_tags.remove(tag)
            self.update_tags_display()
            
            # Émettre le signal
            self.tag_removed.emit(tag)
            self.metadata_changed.emit(self.get_metadata())
    
    def update_tags_display(self):
        """Mise à jour de l'affichage des tags"""
        # Supprimer tous les widgets existants
        for i in reversed(range(self.tags_container_layout.count())):
            widget = self.tags_container_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Ajouter les nouveaux boutons de tags
        for tag in self.current_tags:
            tag_btn = TagButton(tag)
            tag_btn.remove_requested.connect(self.remove_tag)
            self.tags_container_layout.addWidget(tag_btn)
        
        # Ajouter un widget extensible à la fin pour que les tags s'alignent à gauche
        spacer = QWidget()
        spacer.setSizePolicy(0, 0)
        self.tags_container_layout.addWidget(spacer, 1)
    
    def set_rating(self):
        """Définition de la note du projet"""
        # Récupération du bouton qui a émis le signal
        sender = self.sender()
        if not sender:
            return
        
        # Récupération de la note
        rating = sender.property("rating")
        if rating is None:
            return
        
        # Mise à jour de la note
        self.current_rating = rating
        self.update_rating_buttons()
        
        # Émettre le signal
        self.rating_changed.emit(rating)
        self.metadata_changed.emit(self.get_metadata())
    
    def update_rating_buttons(self):
        """Mise à jour de l'apparence des boutons de notation"""
        for i, btn in enumerate(self.rating_buttons):
            if i <= self.current_rating:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f39c12;
                        color: white;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setStyleSheet("")
    
    def _on_notes_changed(self):
        """Gestion du changement des notes"""
        self.notes_changed.emit(self.txt_notes.toPlainText())
        self.metadata_changed.emit(self.get_metadata())
    
    def _on_save_clicked(self):
        """Gestion du clic sur le bouton de sauvegarde"""
        self.save_requested.emit()
