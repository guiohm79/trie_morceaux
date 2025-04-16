# Tri Morceaux Cubase

## 📝 Description

Application pour **trier, comparer et sauvegarder** vos projets Cubase (`.cpr`, `.bak`, `.wav`) répartis dans plusieurs dossiers. L'objectif est de faire le ménage et centraliser les bons fichiers sans rien perdre d'important.

Cette application vous permet de visualiser clairement les différentes versions de vos projets provenant de différentes sources et de choisir lesquelles conserver en fonction de critères objectifs comme la date de modification et la taille des fichiers.

Une deuxieme fonction de cette application permet la gestion des projets, metadonnées, tags, notes (etoiles)...

## 🔍 Contexte

Les projets Cubase sont souvent répartis dans plusieurs dossiers et contiennent différents types de fichiers :
- Fichiers projet (`.cpr`)
- Sauvegardes automatiques (`.bak`)
- Fichiers audio (`.wav`)
- Dossiers comme `Audio`, `Images`, etc.

Il devient difficile de s'y retrouver lorsque plusieurs versions d'un même projet existent à différents endroits.

## ✨ Fonctionnalités principales du mode tri

### 1. Scan intelligent du mode tri
- Parcours récursif de plusieurs dossiers racines
- Regroupement des fichiers par nom de projet
- Identification des fichiers `.cpr`, `.bak`, et `.wav`
- Suivi de la source (dossier d'origine) de chaque fichier

### 2. Visualisation multi-sources et mode workspace
- Tableau des projets avec indication de leur source
- **Deux modes d'affichage** : par projet ou par dossier
- **Mode "espace de travail unique" (workspace)** :
  - Dès qu'un dossier workspace est sélectionné, un scan complet est lancé automatiquement
  - Affichage de l'arborescence complète du dossier sélectionné dans les deux vues
  - Organisation des résultats par dossier plutôt que par projet
  - Toutes les fonctionnalités avancées (détails, tags, tri, aperçu audio, etc.) sont disponibles sans limitation
- **Coloration des sources** pour une meilleure distinction visuelle
- Regroupement des fichiers par source dans la vue détaillée
- Mise en évidence des fichiers les plus récents
- Comparaison facile des différentes versions d'un même projet
- **Système de notation** avec étoiles (0-5) pour évaluer vos projets

### 3. Aperçu audio intégré
- Lecture des fichiers WAV directement dans l'application
- Contrôles de lecture (play, pause, stop)
- Double-clic sur un fichier WAV pour le prévisualiser

### 4. Filtrage et tri
- Filtre par nom pour retrouver rapidement un projet spécifique
- Tri par nom, date de modification ou taille
- Option pour inverser l'ordre de tri

### 5. Gestion manuelle
- Choix de ce que vous souhaitez conserver
- Sélection d'un dossier de destination propre
- Option pour ne garder que le `.cpr` le plus récent et ignorer les `.bak`
- Structure de dossiers Cubase lors de la sauvegarde (Audio, Auto Saves, etc.)

### 6. Organisation et métadonnées
- **Système de tags** pour catégoriser vos projets
- **Notation à étoiles** (0-5) pour évaluer l'importance ou la qualité
- Auto-complétion des tags basée sur les tags existants
- Sauvegarde persistante des métadonnées

### 7. Personnalisation de l'interface
- **Mode sombre** optimisé pour réduire la fatigue visuelle
- Sauvegarde des préférences utilisateur
- Interface adaptative et intuitive

## ✨ Fonctionnalités principales du mode unique

A completer

## 🛠️ Installation

### Prérequis
- Python 3.7 ou supérieur
- PyQt5
- pygame (pour la lecture audio)
- mutagen (pour l'analyse des fichiers audio)

### Étapes d'installation

1. Clonez ou téléchargez ce dépôt
2. Installez les dépendances :

```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

1. Lancez l'application :

```bash
python main.py
```

2. **Sélection des sources** : Ajoutez les différents dossiers contenant vos projets Cubase en cliquant sur "Ajouter un dossier"

3. **Scan** : Cliquez sur "Scanner les dossiers" pour analyser vos projets

4. **Choix du mode d'affichage** :
   - Basculez entre la vue "Par projet" et "Par dossier" avec le sélecteur dans la barre d'outils
   - Activez le mode sombre si vous préférez une interface plus sombre
   - En mode "espace de travail unique", sélectionnez simplement votre dossier : le scan démarre automatiquement et toutes les fonctionnalités (tri, tags, détails, aperçu audio...) sont accessibles comme en mode multi-sources

5. **Exploration** : 
   - Utilisez le champ de recherche pour filtrer les projets par nom
   - Triez les projets par nom, date ou taille
   - Consultez la liste des projets trouvés dans le tableau avec code couleur par source

6. **Comparaison** : 
   - Sélectionnez un projet pour voir ses détails
   - Examinez les fichiers regroupés par source et type (CPR, BAK, WAV)
   - Identifiez les versions les plus récentes (mises en évidence)

7. **Aperçu audio** :
   - Double-cliquez sur un fichier WAV pour le prévisualiser
   - Utilisez les contrôles de lecture pour gérer l'audio

8. **Sauvegarde** : 
   - Choisissez un dossier de destination en cliquant sur "Dossier de destination"
   - Cochez ou décochez l'option "Conserver les fichiers .bak" selon vos préférences
   - Activez l'option "Supprimer les fichiers commençant par ._" pour nettoyer les fichiers temporaires
   - Renommez le projet de destination si nécessaire
   - Ajoutez des notes textuelles qui seront sauvegardées avec le projet
   - Cliquez sur "Sauvegarder le projet sélectionné" pour copier les fichiers

9. **Organisation** :
   - Attribuez des tags à vos projets pour une meilleure organisation
   - Notez vos projets avec un système d'étoiles (0-5)
   - Utilisez l'auto-complétion pour ajouter rapidement des tags existants

10. **Intégration Cubase** :
    - Ouvrez directement vos projets dans Cubase depuis l'application

## 📁 Structure du projet

```
.
├── main.py                 # Point d'entrée de l'application
├── requirements.txt        # Dépendances Python
├── gui/                    # Modules d'interface utilisateur
│   ├── __init__.py
│   └── main_window.py      # Fenêtre principale de l'application
├── models/                 # Modèles de données
│   ├── __init__.py
│   └── project_model.py    # Modèle pour l'affichage des projets
├── utils/                  # Utilitaires
│   ├── __init__.py
│   ├── scanner.py          # Scanner de projets Cubase
│   ├── metadata_manager.py # Gestionnaire de métadonnées (tags et notes)
│   ├── audio_player.py     # Interface pour la lecture audio
│   ├── pygame_audio_player.py # Lecteur audio basé sur pygame
│   └── system_audio_player.py # Lecteur audio utilisant le système
└── styles/                 # Feuilles de style
    └── dark_theme.qss      # Thème sombre pour l'application
```

## ⚠️ Remarques importantes

- L'application ne supprime **jamais** vos fichiers originaux, elle ne fait que les copier
- Pour chaque projet, seul le fichier CPR le plus récent est copié par défaut
- Les fichiers sont organisés selon la structure standard de Cubase lors de la sauvegarde :
  - Fichiers `.cpr` dans le dossier principal du projet
  - Fichiers `.bak` dans le sous-dossier "Auto Saves"
  - Fichiers `.wav` dans le sous-dossier "Audio"
  - Création automatique des dossiers standards Cubase (Images, Edits, etc.)
- L'application est conçue pour fonctionner avec des projets Cubase, mais pourrait être adaptée pour d'autres logiciels de production musicale

## ✅ Fonctionnalités implémentées

- ✅ Visualisation des projets par dossier
- ✅ Coloration des différentes sources et fichiers pour une meilleure visibilité
- ✅ Aperçu audio des fichiers WAV
- ✅ Structure de dossiers Cubase lors de la sauvegarde
- ✅ Mode sombre optimisé pour réduire la fatigue visuelle
- ✅ Option pour supprimer les fichiers commençant par "._"
- ✅ Option pour renommer le répertoire du projet de destination
- ✅ Option pour ajouter une note au format txt intégrée au répertoire de sauvegarde
- ✅ Possibilité de lancer le projet dans Cubase à partir de l'application
- ✅ Système de tags et notation à étoiles pour les projets
- ✅ Ouvrir l'application directement en mode "unique"
- ✅ Garder en mémoire le chemin de cubase.exe (demande d'emplacement au premier lancement)
- ✅ Affichage de l'arborescence du projet/dossier sélectionné dans la deuxième fenêtre
- ✅ Mode workspace amélioré avec organisation par dossier

## 🔮 Évolutions futures

- Redefinition du mode unique:
  - ce mode permet la gestion des projets Cubase:
   - personnalisation des metadonnées
   - ajout d'un mode de scan du repertoire de travail, 

- division du code en plusieurs modules, un module pour le mode tri et un module pour le mode unique

- (100%) Ajout d'une fenêtre à côté du détail du projet dans les deux modes pour afficher l'arborescence du dossier du projet et permettre la manipulation des éléments (ajout, déplacement, suppression)
- redimensionnement des fenetres
- Amélioration continue de l'interface utilisateur (lecteur audio, interface utilisateur, etc.)
- Exportation/importation des métadonnées (tags et notes) et sauvegardes dans un fichier json inclut dans le répertoire du projet
- Optimisation des performances pour les collections de projets très volumineuses
- Support multiplateforme amélioré (macOS, Linux)

## 🔮 Problèmes résolus

- ~~La deuxième fenêtre d'arborescence n'affiche pas l'arborescence du projet sélectionné dans la fenêtre résultats~~ : **Résolu**
  - En mode multi-sources : Affiche maintenant correctement l'arborescence du projet sélectionné en utilisant plusieurs stratégies de recherche
  - En mode workspace : Affiche directement l'arborescence du dossier sélectionné

## 🔮 Évolutions possibles secondaires
- ajouter une option (case a cocher) pour garder en memoire le repertoire de travail du mode unique lors des futures ouverture de l'application
- afficher la liste des plugins et VSTi utilisé dans le projet
- versioning avancé des projets 
- en mode unique, pouvoir supprimer des éléments d'un projet et d'enregistrer les modifications directement dans le répertoire de travail
- Intégration avec des services cloud pour la sauvegarde
- Synchronisation automatique entre plusieurs sources
- Statistiques d'utilisation et rapports sur vos projets


## 📄 Licence

Ce projet est distribué sous licence libre. Vous êtes libre de l'utiliser, le modifier et le distribuer selon vos besoins.
