#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de scan pour le mode TRI (multi-sources)
"""

from pathlib import Path
from datetime import datetime
import shutil
from collections import defaultdict

class TriScanner:
    """Classe pour scanner et analyser les projets Cubase en mode TRI (multi-dossiers)"""
    def __init__(self):
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
        """
        root_path = Path(root_dir)
        print(f"Scan du dossier: {root_path} (existe: {root_path.exists()})")
        if not root_path.exists():
            print(f"Le dossier {root_path} n'existe pas!")
            return self.projects
        file_count = 0
        for path in root_path.rglob('*'):
            if path.is_file():
                file_count += 1
                ext = path.suffix.lower()
                parent_dir = path.parent.name
                project_dir = path.parent
                project_name = project_dir.name
                print(f"Fichier trouvé: {path.name}, ext: {ext}, projet: {project_name}")
                if 'source' not in self.projects[project_name]:
                    self.projects[project_name]['source'] = str(root_path)
                elif self.projects[project_name]['source'] != str(root_path):
                    self.projects[project_name]['source'] = "Plusieurs sources"
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
        self._create_dataframe()
        return self.projects

    def scan_multiple_directories(self, dir_list):
        """
        Scan de plusieurs dossiers racines (mode tri)
        """
        for directory in dir_list:
            self.scan_directory(directory)
        return self.projects

    def copy_project(self, project_name, destination, keep_bak=False, remove_dotunderscore=False, new_project_name="", project_notes=""):
        """
        Copie d'un projet vers un dossier de destination selon la structure Cubase
        """
        project = self.projects.get(project_name)
        if not project:
            return False
        target_name = new_project_name if new_project_name else project_name
        dest_dir = Path(destination) / target_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"Sauvegarde du projet '{project_name}' vers '{dest_dir}'")
        if project['cpr_files']:
            latest_cpr = max(project['cpr_files'], key=lambda x: x['modified'])
            cpr_path = Path(latest_cpr['path'])
            if remove_dotunderscore and cpr_path.name.startswith('._'):
                print(f"Ignoré fichier CPR commençant par ._: {cpr_path}")
            else:
                shutil.copy2(latest_cpr['path'], dest_dir)
                print(f"Copié fichier CPR: {latest_cpr['path']} vers {dest_dir}")
        if keep_bak and project['bak_files']:
            auto_saves_dir = dest_dir / 'Auto Saves'
            auto_saves_dir.mkdir(exist_ok=True)
            for bak_file in project['bak_files']:
                bak_path = Path(bak_file['path'])
                if remove_dotunderscore and bak_path.name.startswith('._'):
                    print(f"Ignoré fichier BAK commençant par ._: {bak_path}")
                else:
                    shutil.copy2(bak_file['path'], auto_saves_dir)
                    print(f"Copié fichier BAK: {bak_file['path']} vers {auto_saves_dir}")
        audio_dir = dest_dir / 'Audio'
        audio_dir.mkdir(exist_ok=True)
        for wav_file in project['wav_files']:
            wav_path = Path(wav_file['path'])
            wav_name = wav_path.name.lower()
            is_preview = project_name.lower() in wav_name
            if is_preview:
                target_dir = audio_dir
            else:
                samples_dir = audio_dir / 'Samples'
                samples_dir.mkdir(exist_ok=True)
                target_dir = samples_dir
            if remove_dotunderscore and wav_path.name.startswith('._'):
                preview_text = "(aperçu)" if is_preview else "(sample)"
                print(f"Ignoré fichier WAV {preview_text} commençant par ._: {wav_path}")
            else:
                shutil.copy2(wav_file['path'], target_dir)
                preview_text = "(aperçu)" if is_preview else "(sample)"
                print(f"Copié fichier WAV {preview_text}: {wav_file['path']} vers {target_dir}")
        for folder in ['Edits', 'Images', 'Track Pictures']:
            folder_path = dest_dir / folder
            folder_path.mkdir(exist_ok=True)
        if project_notes:
            notes_file = dest_dir / 'notes.txt'
            try:
                from datetime import datetime
                header = f"Notes pour le projet '{project_name}' - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                header += "-" * 80 + "\n\n"
                with open(notes_file, 'w', encoding='utf-8') as f:
                    f.write(header + project_notes)
                print(f"Fichier de notes créé: {notes_file}")
            except Exception as e:
                print(f"Erreur lors de la création du fichier de notes: {e}")
        return True

    def _create_dataframe(self):
        """
        Création d'une liste de dictionnaires à partir des projets trouvés
        """
        data = []
        for project_name, project_data in self.projects.items():
            latest_cpr = None
            if project_data['cpr_files']:
                latest_cpr = max(project_data['cpr_files'], key=lambda x: x['modified'])
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
        """
        return self.projects.get(project_name, None)
