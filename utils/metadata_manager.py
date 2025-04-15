#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de gestion des métadonnées des projets (tags et notes)
"""

import os
import json
from pathlib import Path

class MetadataManager:
    """Gestionnaire de métadonnées pour les projets"""
    
    def __init__(self):
        """Initialisation du gestionnaire de métadonnées"""
        self.metadata_dir = Path.home() / '.trie_morceaux' / 'metadata'
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / 'projects_metadata.json'
        self.metadata = self._load_metadata()
    
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
    
    def get_project_metadata(self, project_name):
        """
        Récupération des métadonnées d'un projet
        
        Args:
            project_name (str): Nom du projet
            
        Returns:
            dict: Métadonnées du projet (tags et notes)
        """
        if project_name not in self.metadata:
            # Initialisation des métadonnées pour un nouveau projet
            self.metadata[project_name] = {
                'tags': [],
                'rating': 0  # Note de 0 à 5 étoiles
            }
            self._save_metadata()
        
        return self.metadata[project_name]
    
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
