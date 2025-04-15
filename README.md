# Tri Morceaux Cubase

## 📝 Description

Application pour **trier, comparer et sauvegarder** vos projets Cubase (`.cpr`, `.bak`, `.wav`) répartis dans plusieurs dossiers. L'objectif est de faire le ménage et centraliser les bons fichiers sans rien perdre d'important.

Cette application vous permet de visualiser clairement les différentes versions de vos projets provenant de différentes sources et de choisir lesquelles conserver en fonction de critères objectifs comme la date de modification et la taille des fichiers.

## 🔍 Contexte

Les projets Cubase sont souvent répartis dans plusieurs dossiers et contiennent différents types de fichiers :
- Fichiers projet (`.cpr`)
- Sauvegardes automatiques (`.bak`)
- Fichiers audio (`.wav`)
- Dossiers comme `Audio`, `Images`, etc.

Il devient difficile de s'y retrouver lorsque plusieurs versions d'un même projet existent à différents endroits.

## ✨ Fonctionnalités principales

### 1. Scan intelligent
- Parcours récursif de plusieurs dossiers racines
- Regroupement des fichiers par nom de projet
- Identification des fichiers `.cpr`, `.bak`, et `.wav`
- Suivi de la source (dossier d'origine) de chaque fichier

### 2. Visualisation multi-sources
- Tableau des projets avec indication de leur source
- **Deux modes d'affichage** : par projet ou par dossier
- **Coloration des sources** pour une meilleure distinction visuelle
- Regroupement des fichiers par source dans la vue détaillée
- Mise en évidence des fichiers les plus récents
- Comparaison facile des différentes versions d'un même projet

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

### 6. Personnalisation de l'interface
- **Mode sombre** pour réduire la fatigue visuelle
- Sauvegarde des préférences utilisateur
- Interface adaptative

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
   - Cliquez sur "Sauvegarder le projet sélectionné" pour copier les fichiers

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
- ✅ Mode sombre pour réduire la fatigue visuelle

## 🔮 Évolutions prioritaires

- ajout d'une option pour supprimer les fichiers commençant par "._"
- ajout d'une option pour renomer le repertoire du projet de destination
- ajout d'une option pour ajouter une note au format txt integrer au repertoire de sauvegarde
- ajout de la possibilité de lancer le projet dans cubase a partir de l'application
- ajout d'un système de tags et notes pour les projets


## 🔮 Évolutions possibles secondaires


- Versioning avancé des projets
- Analyse du contenu des fichiers CPR (si possible)
- Intégration avec des services cloud pour la sauvegarde
- Synchronisation automatique entre plusieurs sources


## 📄 Licence

Ce projet est distribué sous licence libre. Vous êtes libre de l'utiliser, le modifier et le distribuer selon vos besoins.
