#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de scan et d'analyse des projets Cubase
"""

import os
from pathlib import Path
from datetime import datetime
import shutil
from collections import defaultdict

class CubaseScanner:
    """Classe pour scanner et analyser les projets Cubase"""
    
    def __init__(self):
        """Initialisation du scanner"""
        self.projects = defaultdict(lambda: {
            'cpr_files': [],
            'bak_files': [],
            'wav_files': [],
            'other_files': [],
            'directories': [],
            'source': ''
        })
        self.df_projects = []
    
    def scan_directory(self, root_dir):
        """
        Parcours récursif d'un dossier pour trouver les projets Cubase
        
        Args:
            root_dir (str): Chemin du dossier racine à scanner
        
        Returns:
            dict: Dictionnaire des projets trouvés
        """
        root_path = Path(root_dir)
        print(f"Scan du dossier: {root_path} (existe: {root_path.exists()})")
        
        if not root_path.exists():
            print(f"Le dossier {root_path} n'existe pas!")
            return self.projects
        
        # Parcours récursif du dossier
        file_count = 0
        for path in root_path.rglob('*'):
            if path.is_file():
                file_count += 1
                # Récupération de l'extension et du nom du dossier parent
                ext = path.suffix.lower()
                parent_dir = path.parent.name
                project_dir = path.parent
                
                # Détermination du nom du projet (nom du dossier parent)
                project_name = project_dir.name
                
                print(f"Fichier trouvé: {path.name}, ext: {ext}, projet: {project_name}")
                
                # Si le projet n'a pas encore de source, on l'initialise
                if 'source' not in self.projects[project_name]:
                    self.projects[project_name]['source'] = str(root_path)
                # Si le projet existe déjà mais vient d'une autre source, on le marque comme multi-source
                elif self.projects[project_name]['source'] != str(root_path):
                    self.projects[project_name]['source'] = "Plusieurs sources"
                
                # Ajout du fichier à la catégorie correspondante
                if ext == '.cpr':
                    self.projects[project_name]['cpr_files'].append({
                        'path': str(path),
                        'size': path.stat().st_size,
                        'modified': datetime.fromtimestamp(path.stat().st_mtime),
                        'created': datetime.fromtimestamp(path.stat().st_ctime),
                        'source': str(root_path)
                    })
                    print(f"Ajouté fichier CPR: {path.name} au projet {project_name}")
                elif ext == '.bak':
                    self.projects[project_name]['bak_files'].append({
                        'path': str(path),
                        'size': path.stat().st_size,
                        'modified': datetime.fromtimestamp(path.stat().st_mtime),
                        'created': datetime.fromtimestamp(path.stat().st_ctime),
                        'source': str(root_path)
                    })
                    print(f"Ajouté fichier BAK: {path.name} au projet {project_name}")
                elif ext == '.wav':
                    self.projects[project_name]['wav_files'].append({
                        'path': str(path),
                        'size': path.stat().st_size,
                        'modified': datetime.fromtimestamp(path.stat().st_mtime),
                        'created': datetime.fromtimestamp(path.stat().st_ctime),
                        'source': str(root_path)
                    })
                    print(f"Ajouté fichier WAV: {path.name} au projet {project_name}")
                else:
                    self.projects[project_name]['other_files'].append({
                        'path': str(path),
                        'size': path.stat().st_size,
                        'modified': datetime.fromtimestamp(path.stat().st_mtime),
                        'created': datetime.fromtimestamp(path.stat().st_ctime),
                        'source': str(root_path)
                    })
            elif path.is_dir() and path.name not in ['.', '..']:
                project_name = path.parent.name
                self.projects[project_name]['directories'].append({
                    'path': str(path),
                    'name': path.name,
                    'source': str(root_path)
                })
        
        print(f"Scan terminé pour {root_path}, {file_count} fichiers trouvés")
        
        # Conversion en DataFrame pour faciliter l'analyse
        self._create_dataframe()
        
        return self.projects
    
    def scan_multiple_directories(self, dir_list):
        """
        Scan de plusieurs dossiers racines
        
        Args:
            dir_list (list): Liste des chemins des dossiers à scanner
            
        Returns:
            dict: Dictionnaire des projets trouvés
        """
        for directory in dir_list:
            self.scan_directory(directory)
        
        return self.projects
    
    def _create_dataframe(self):
        """
        Création d'une liste de dictionnaires à partir des projets trouvés
        """
        data = []
        
        for project_name, project_data in self.projects.items():
            # Trouver le fichier CPR le plus récent
            latest_cpr = None
            if project_data['cpr_files']:
                latest_cpr = max(project_data['cpr_files'], 
                                key=lambda x: x['modified'])
            
            # Calculer les statistiques
            total_size = sum(f['size'] for files in [
                project_data['cpr_files'], 
                project_data['bak_files'],
                project_data['wav_files'],
                project_data['other_files']
            ] for f in files)
            
            data.append({
                'project_name': project_name,
                'source': project_data.get('source', ''),
                'latest_cpr': latest_cpr['path'] if latest_cpr else None,
                'latest_cpr_date': latest_cpr['modified'] if latest_cpr else None,
                'cpr_count': len(project_data['cpr_files']),
                'bak_count': len(project_data['bak_files']),
                'wav_count': len(project_data['wav_files']),
                'other_count': len(project_data['other_files']),
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            })
        
        self.df_projects = data
        return self.df_projects
    
    def get_project_details(self, project_name):
        """
        Récupération des détails d'un projet spécifique
        
        Args:
            project_name (str): Nom du projet
            
        Returns:
            dict: Détails du projet
        """
        return self.projects.get(project_name, None)
    
    def copy_project(self, project_name, destination, keep_bak=False, remove_dotunderscore=False):
        """
        Copie d'un projet vers un dossier de destination selon la structure Cubase
        
        Args:
            project_name (str): Nom du projet
            destination (str): Chemin du dossier de destination
            keep_bak (bool): Conserver les fichiers .bak
            
        Returns:
            bool: Succès de l'opération
        """
        project = self.projects.get(project_name)
        if not project:
            return False
        
        # Création du dossier de destination principal
        dest_dir = Path(destination) / project_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Copie du fichier CPR le plus récent
        if project['cpr_files']:
            latest_cpr = max(project['cpr_files'], key=lambda x: x['modified'])
            cpr_path = Path(latest_cpr['path'])
            
            # Vérifier si le fichier commence par ._ et si l'option est activée
            if remove_dotunderscore and cpr_path.name.startswith('._'):
                print(f"Ignoré fichier CPR commençant par ._: {cpr_path}")
            else:
                shutil.copy2(latest_cpr['path'], dest_dir)
                print(f"Copié fichier CPR: {latest_cpr['path']} vers {dest_dir}")
        
        # Copie des fichiers BAK si demandé
        if keep_bak and project['bak_files']:
            # Création du dossier Auto Saves
            auto_saves_dir = dest_dir / 'Auto Saves'
            auto_saves_dir.mkdir(exist_ok=True)
            
            for bak_file in project['bak_files']:
                bak_path = Path(bak_file['path'])
                
                # Vérifier si le fichier commence par ._ et si l'option est activée
                if remove_dotunderscore and bak_path.name.startswith('._'):
                    print(f"Ignoré fichier BAK commençant par ._: {bak_path}")
                else:
                    shutil.copy2(bak_file['path'], auto_saves_dir)
                    print(f"Copié fichier BAK: {bak_file['path']} vers {auto_saves_dir}")
        
        # Création du dossier Audio si nécessaire
        audio_dir = dest_dir / 'Audio'
        audio_dir.mkdir(exist_ok=True)
        
        # Copie des fichiers WAV avec distinction entre aperçus et samples
        for wav_file in project['wav_files']:
            wav_path = Path(wav_file['path'])
            wav_name = wav_path.name.lower()
            
            # Vérifier si c'est un aperçu du projet (nom proche du projet)
            # On considère que c'est un aperçu si le nom du projet est contenu dans le nom du fichier WAV
            is_preview = project_name.lower() in wav_name
            
            # Destination du fichier WAV
            if is_preview:
                # Les aperçus vont directement dans le dossier Audio
                target_dir = audio_dir
            else:
                # Les samples vont dans un sous-dossier Samples du dossier Audio
                samples_dir = audio_dir / 'Samples'
                samples_dir.mkdir(exist_ok=True)
                target_dir = samples_dir
            
            # Vérifier si le fichier commence par ._ et si l'option est activée
            if remove_dotunderscore and wav_path.name.startswith('._'):
                preview_text = "(aperçu)" if is_preview else "(sample)"
                print(f"Ignoré fichier WAV {preview_text} commençant par ._: {wav_path}")
            else:
                # Copie du fichier WAV
                shutil.copy2(wav_file['path'], target_dir)
                preview_text = "(aperçu)" if is_preview else "(sample)"
                print(f"Copié fichier WAV {preview_text}: {wav_file['path']} vers {target_dir}")
        
        # Création des autres dossiers standard de Cubase s'ils n'existent pas déjà
        for folder in ['Edits', 'Images', 'Track Pictures']:
            folder_path = dest_dir / folder
            folder_path.mkdir(exist_ok=True)
        
        return True
