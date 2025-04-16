#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de gestion des métadonnées des projets (tags et notes)
"""

import os
import json
from pathlib import Path

class MetadataManager:
    """
    Gestionnaire de métadonnées pour les projets Cubase.
    Supporte deux modes :
    - mode centralisé (legacy)
    - mode local (metadata.json dans chaque dossier de projet)
    """
    def __init__(self, mode='centralized'):
        """
        Initialisation du gestionnaire de métadonnées
        Args:
            mode (str): 'centralized' (défaut) ou 'local'
        """
        self.mode = mode  # 'centralized' ou 'local'
        self.metadata_dir = Path.home() / '.trie_morceaux' / 'metadata'
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / 'projects_metadata.json'
        self.metadata = self._load_metadata() if self.mode == 'centralized' else None
        self.local_filename = 'metadata.json'
    
    def _get_local_metadata_path(self, project_dir):
        """Retourne le chemin du fichier metadata.json local pour un projet"""
        return Path(project_dir) / self.local_filename
    
    def _load_local_metadata(self, project_dir):
        """Charge les métadonnées locales d'un projet (metadata.json)"""
        meta_path = self._get_local_metadata_path(project_dir)
        if meta_path.exists():
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement des métadonnées locales: {e}")
                return {}
        else:
            return {}
    
    def _save_local_metadata(self, project_dir, metadata):
        """Sauvegarde les métadonnées locales d'un projet (metadata.json)"""
        meta_path = self._get_local_metadata_path(project_dir)
        try:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des métadonnées locales: {e}")
            return False
    
    def _load_metadata(self):
        """Chargement des métadonnées depuis le fichier"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement des métadonnées: {e}")
                return {}
        else:
            return {}
    
    def _save_metadata(self):
        """Sauvegarde des métadonnées dans le fichier"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des métadonnées: {e}")
            return False
    
    def get_project_metadata(self, project_name, project_dir=None):
        """
        Récupération des métadonnées d'un projet
        Args:
            project_name (str): Nom du projet
            project_dir (str): Chemin du dossier projet (requis en mode local)
        Returns:
            dict: Métadonnées du projet
        """
        if self.mode == 'centralized':
            if project_name not in self.metadata:
                self.metadata[project_name] = {
                    'tags': [],
                    'rating': 0
                }
                self._save_metadata()
            return self.metadata[project_name]
        else:
            if not project_dir:
                raise ValueError("project_dir est requis en mode local")
            metadata = self._load_local_metadata(project_dir)
            if not metadata:
                metadata = {
                    "name": project_name,
                    "styles": [],
                    "bpm": 0,
                    "rating": 0,
                    "tags": [],
                    "versions": [],
                    "notes": "",
                    "last_modified": None
                }
                self._save_local_metadata(project_dir, metadata)
            return metadata
    
    def set_project_metadata(self, project_name, metadata, project_dir=None):
        """
        Sauvegarde des métadonnées d'un projet (tous les champs)
        Args:
            project_name (str): Nom du projet
            metadata (dict): Métadonnées à sauvegarder
            project_dir (str): Chemin du dossier projet (requis en mode local)
        Returns:
            bool: Succès
        """
        if self.mode == 'centralized':
            self.metadata[project_name] = metadata
            return self._save_metadata()
        else:
            if not project_dir:
                raise ValueError("project_dir est requis en mode local")
            return self._save_local_metadata(project_dir, metadata)
    
    def set_project_tags(self, project_name, tags, project_dir=None):
        """
        Définition des tags d'un projet
        Args:
            project_name (str): Nom du projet
            tags (list): Liste des tags
            project_dir (str): Chemin du dossier projet (requis en mode local)
        Returns:
            bool: Succès
        """
        if self.mode == 'centralized':
            if project_name not in self.metadata:
                self.metadata[project_name] = {'tags': [], 'rating': 0}
            self.metadata[project_name]['tags'] = tags
            return self._save_metadata()
        else:
            if not project_dir:
                raise ValueError("project_dir est requis en mode local")
            metadata = self.get_project_metadata(project_name, project_dir)
            metadata['tags'] = tags
            return self._save_local_metadata(project_dir, metadata)
    
    def set_project_rating(self, project_name, rating, project_dir=None):
        """
        Définition de la note en étoiles d'un projet
        Args:
            project_name (str): Nom du projet
            rating (int): Note de 0 à 5 étoiles
            project_dir (str): Chemin du dossier projet (requis en mode local)
        Returns:
            bool: Succès
        """
        if not isinstance(rating, int) or rating < 0 or rating > 5:
            print(f"Note invalide: {rating}. Doit être un entier entre 0 et 5.")
            return False
        if self.mode == 'centralized':
            if project_name not in self.metadata:
                self.metadata[project_name] = {'tags': [], 'rating': 0}
            self.metadata[project_name]['rating'] = rating
            return self._save_metadata()
        else:
            if not project_dir:
                raise ValueError("project_dir est requis en mode local")
            metadata = self.get_project_metadata(project_name, project_dir)
            metadata['rating'] = rating
            return self._save_local_metadata(project_dir, metadata)

    
    def set_project_tags(self, project_name, tags):
        """
        Définition des tags d'un projet
        
        Args:
            project_name (str): Nom du projet
            tags (list): Liste des tags
            
        Returns:
            bool: Succès de l'opération
        """
        # Récupération des métadonnées existantes ou création si nécessaire
        if project_name not in self.metadata:
            self.metadata[project_name] = {'tags': [], 'rating': 0}
        
        # Mise à jour des tags
        self.metadata[project_name]['tags'] = tags
        
        # Sauvegarde des modifications
        return self._save_metadata()
    
    def set_project_rating(self, project_name, rating):
        """
        Définition de la note en étoiles d'un projet
        
        Args:
            project_name (str): Nom du projet
            rating (int): Note de 0 à 5 étoiles
            
        Returns:
            bool: Succès de l'opération
        """
        # Vérification que la note est valide (entre 0 et 5)
        if not isinstance(rating, int) or rating < 0 or rating > 5:
            print(f"Note invalide: {rating}. Doit être un entier entre 0 et 5.")
            return False
        
        # Récupération des métadonnées existantes ou création si nécessaire
        if project_name not in self.metadata:
            self.metadata[project_name] = {'tags': [], 'rating': 0}
        
        # Mise à jour de la note
        self.metadata[project_name]['rating'] = rating
        
        # Sauvegarde des modifications
        return self._save_metadata()
    
    def get_project_rating(self, project_name):
        """
        Récupération de la note en étoiles d'un projet
        
        Args:
            project_name (str): Nom du projet
            
        Returns:
            int: Note de 0 à 5 étoiles
        """
        metadata = self.get_project_metadata(project_name)
        return metadata.get('rating', 0)
    
    def get_all_tags(self):
        """
        Récupération de tous les tags utilisés
        
        Returns:
            list: Liste de tous les tags uniques
        """
        all_tags = set()
        for project_data in self.metadata.values():
            all_tags.update(project_data.get('tags', []))
        
        return sorted(list(all_tags))
    
    def search_projects_by_tag(self, tag):
        """
        Recherche de projets par tag
        
        Args:
            tag (str): Tag à rechercher
            
        Returns:
            list: Liste des noms de projets ayant ce tag
        """
        matching_projects = []
        for project_name, project_data in self.metadata.items():
            if tag in project_data.get('tags', []):
                matching_projects.append(project_name)
        
        return matching_projects
