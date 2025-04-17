# Tri Morceaux Cubase

Application de gestion de projets Cubase permettant de trier, comparer, sauvegarder et organiser vos projets.

## État du Projet

Le projet a été restructuré selon l'architecture proposée dans le cahier des charges. Les deux modes de fonctionnement (Tri et Espace de Travail) sont maintenant clairement séparés et utilisent des composants communs réutilisables.

### Problèmes Résolus

1. **Gestion des métadonnées en mode local** : 
   - Ajout du champ `project_dir` dans le scanner pour stocker correctement le chemin du dossier de chaque projet
   - Amélioration de la gestion des erreurs dans le service de métadonnées
   - Meilleure résilience face aux chemins manquants ou invalides

2. **Nettoyage de la structure du projet** :
   - Suppression des fichiers obsolètes de l'ancienne structure
   - Refactorisation complète selon l'architecture modulaire proposée

### Structure Implémentée

```
.
├── main.py                      # Point d'entrée, parsing des arguments, lancement du mode approprié
├── config/                      # Configuration de l'application
│   ├── __init__.py
│   ├── settings.py              # Gestion des paramètres utilisateur
│   └── constants.py             # Constantes globales
├── gui/                         # Interface utilisateur
│   ├── __init__.py
│   ├── base/
│   │   ├── __init__.py
│   │   └── base_window.py       # Classe de base pour les fenêtres principales
│   ├── components/              # Composants d'UI réutilisables
│   │   ├── __init__.py
│   │   ├── audio_player.py      # Lecteur audio unifié
│   │   ├── file_tree.py         # Arborescence de fichiers
│   │   ├── metadata_editor.py   # Éditeur de métadonnées (tags, notes)
│   │   └── project_table.py     # Table des projets
│   ├── sort_mode/               # Mode Tri (multi-sources)
│   │   ├── __init__.py
│   │   └── sort_window.py       # Fenêtre principale du mode tri
│   └── workspace_mode/          # Mode Espace de Travail
│       ├── __init__.py
│       └── workspace_window.py  # Fenêtre principale du mode workspace
├── models/                      # Modèles de données
│   ├── __init__.py
│   └── project_model.py         # Modèle pour l'affichage des projets
├── services/                    # Services métier
│   ├── __init__.py
│   ├── scanner.py               # Scanner de projets Cubase
│   ├── metadata_service.py      # Gestion des métadonnées
│   ├── audio_service.py         # Service audio unifié
│   ├── file_service.py          # Opérations sur les fichiers
│   └── cubase_service.py        # Interactions avec Cubase
└── styles/                      # Feuilles de style
    └── dark_theme.qss          
```

### Utilisation

L'application peut être lancée dans deux modes :

- **Mode Espace de Travail** (par défaut) : `python main.py`
- **Mode Tri** (multi-sources) : `python main.py --mode tri`

## Recommandations pour les Évolutions Futures

### 1. Améliorations Techniques

1. **Tests unitaires** :
   - Implémenter des tests unitaires pour les services et composants principaux
   - Mettre en place une intégration continue pour exécuter les tests automatiquement

2. **Gestion des exceptions** :
   - Améliorer la gestion des exceptions dans tous les services
   - Implémenter un système de journalisation (logging) centralisé

3. **Optimisation des performances** :
   - Optimiser le scan des dossiers volumineux avec un threading plus avancé
   - Implémenter un système de mise en cache des métadonnées

### 2. Améliorations Fonctionnelles

1. **Interface utilisateur** :
   - Ajouter des raccourcis clavier pour les actions fréquentes
   - Améliorer l'expérience utilisateur avec des animations et transitions
   - Implémenter un système de thèmes plus complet

2. **Gestion des métadonnées** :
   - Implémenter un système de tags hiérarchiques
   - Ajouter la possibilité d'importer/exporter les métadonnées
   - Synchronisation avec des services cloud

3. **Fonctionnalités avancées** :
   - Intégration plus poussée avec l'API de Cubase
   - Analyse audio avancée (détection de BPM, tonalité, etc.)
   - Gestion des versions et historique des modifications

### 3. Documentation

1. **Documentation utilisateur** :
   - Créer un guide utilisateur complet avec captures d'écran
   - Ajouter des tutoriels vidéo pour les fonctionnalités complexes

2. **Documentation technique** :
   - Documenter l'architecture et les choix de conception
   - Ajouter des diagrammes UML pour les composants principaux
   - Créer un guide de contribution pour les développeurs

## Cahier des Charges Initial

### 1. Introduction

L'application "Tri Morceaux Cubase" est un outil de gestion de projets Cubase avec deux fonctionnalités principales distinctes :

1. **Mode Tri (multi-sources)** : Pour trier, comparer et consolider des projets Cubase provenant de plusieurs sources
2. **Mode Espace de Travail (unique)** : Pour gérer et organiser un répertoire unique contenant des projets Cubase

Le code actuel nécessite une refonte pour clarifier la structure et séparer proprement ces deux modes.

### 2. Architecture proposée

```
.
├── main.py                      # Point d'entrée, parsing des arguments, lancement du mode approprié
├── config/                      # Configuration de l'application
│   ├── __init__.py
│   ├── settings.py              # Gestion des paramètres utilisateur
│   └── constants.py             # Constantes globales
├── gui/                         # Interface utilisateur
│   ├── __init__.py
│   ├── base/
│   │   ├── __init__.py
│   │   └── base_window.py       # Classe de base pour les fenêtres principales
│   ├── components/              # Composants d'UI réutilisables
│   │   ├── __init__.py
│   │   ├── audio_player.py      # Lecteur audio unifié
│   │   ├── file_tree.py         # Arborescence de fichiers
│   │   ├── metadata_editor.py   # Éditeur de métadonnées (tags, notes)
│   │   └── project_table.py     # Table des projets
│   ├── sort_mode/               # Mode Tri (multi-sources)
│   │   ├── __init__.py
│   │   └── sort_window.py       # Fenêtre principale du mode tri
│   └── workspace_mode/          # Mode Espace de Travail
│       ├── __init__.py
│       └── workspace_window.py  # Fenêtre principale du mode workspace
├── models/                      # Modèles de données
│   ├── __init__.py
│   └── project_model.py         # Modèle pour l'affichage des projets
├── services/                    # Services métier
│   ├── __init__.py
│   ├── scanner.py               # Scanner de projets Cubase
│   ├── metadata_service.py      # Gestion des métadonnées
│   ├── audio_service.py         # Service audio unifié
│   ├── file_service.py          # Opérations sur les fichiers
│   └── cubase_service.py        # Interactions avec Cubase
└── styles/                      # Feuilles de style
    └── dark_theme.qss          
```

### 3. Spécifications détaillées des modes

#### 3.1. Mode Tri (multi-sources)

**Objectif** : Permettre de consolider des projets dispersés dans plusieurs dossiers en triant et comparant leurs fichiers.

**Fonctionnalités** :
- Sélection de plusieurs dossiers sources
- Scan récursif des dossiers
- Regroupement des fichiers par projet
- Visualisation des projets avec leur contenu
- Comparaison des versions de fichiers (.cpr, .bak, .wav)
- Sélection des fichiers à conserver
- Copie structurée des fichiers sélectionnés vers un dossier de destination

**Interface utilisateur** :
1. Zone de sélection des dossiers sources
2. Tableau des projets trouvés
3. Détails du projet sélectionné (fichiers, taille, date)
4. Arborescence des fichiers du projet
5. Prévisualisation audio
6. Options de sauvegarde (dossier de destination, options)

#### 3.2. Mode Espace de Travail (unique)

**Objectif** : Gérer un répertoire de travail contenant des projets Cubase, avec organisation, tagging et gestion des fichiers.

**Fonctionnalités** :
- Sélection d'un dossier de travail unique
- Navigation dans l'arborescence des projets
- Gestion des métadonnées (tags, notes, notation)
- Gestion des fichiers (création, renommage, suppression)
- Prévisualisation audio
- Lancement des projets dans Cubase

**Interface utilisateur** :
1. Sélection du dossier de travail
2. Double arborescence :
   - Vue globale des projets (gauche)
   - Vue détaillée du projet sélectionné (droite)
3. Zone de métadonnées (tags, notes, étoiles)
4. Contrôles de manipulation de fichiers

### 4. Composants techniques communs

#### 4.1. Scanner de projets
- Détection et analyse des projets Cubase
- Identification des fichiers par type (.cpr, .bak, .wav)
- Extraction des métadonnées (date, taille)

#### 4.2. Gestionnaire de métadonnées
- Stockage et récupération des métadonnées (tags, notes, notation)
- Persistance locale (JSON dans chaque dossier projet)
- Prise en charge des deux modes (centralisé/local)

#### 4.3. Lecteur audio
- Prévisualisation des fichiers WAV
- Interface unifiée (contrôles de lecture)
- Implémentation unique et stable

#### 4.4. Modèle de données
- Représentation unifiée des projets
- Prise en charge des différentes vues (par projet, par dossier)
- Support du mode sombre/clair

### 5. Propositions d'amélioration

#### 5.1. Refactorisation prioritaire

1. **Séparation de main_window.py** :
   - Extraire les bases communes dans une classe abstraite BaseWindow
   - Créer SortWindow et WorkspaceWindow héritant de BaseWindow
   - Déplacer les fonctionnalités spécifiques dans les classes respectives

2. **Extraction des composants** :
   - Créer des classes dédiées pour les composants réutilisables
   - AudioPlayer unifié qui remplace les multiples implémentations
   - FileTreeWidget pour la gestion de l'arborescence
   - MetadataEditor pour les tags, notes, etc.

3. **Nettoyage du code** :
   - Suppression des duplications
   - Standardisation des noms de méthodes et variables
   - Documentation améliorée

#### 5.2. Améliorations fonctionnelles

1. **Mode Tri** :
   - Interface simplifiée et plus intuitive
   - Amélioration de la visualisation des différences entre fichiers
   - Prévisualisation des modifications avant sauvegarde

2. **Mode Espace de Travail** :
   - Gestion de métadonnées avancée (exportation/importation)
   - Intégration complète avec Cubase
   - Navigation améliorée dans les projets

3. **Commun** :
   - Système de recherche avancée
   - Historique des actions (undo/redo)
   - Exportation de rapports sur les projets

### 6. Plan d'implémentation

#### Phase 1: Restructuration du code
1. Établir la nouvelle structure de répertoires
2. Extraire les composants communs
3. Séparer les modes Tri et Espace de Travail

#### Phase 2: Stabilisation des fonctionnalités
1. Corriger les bugs dans le mode Tri
2. Finaliser le mode Espace de Travail
3. Unifier l'expérience utilisateur

#### Phase 3: Améliorations
1. Ajouter les nouvelles fonctionnalités
2. Optimiser les performances
3. Améliorer l'interface utilisateur

## Prérequis et Installation

### Prérequis
- Python 3.7 ou supérieur
- PyQt5
- pygame (pour la lecture audio)
- mutagen (pour l'analyse des fichiers audio)

### Installation

1. Clonez ou téléchargez ce dépôt
2. Installez les dépendances :

```bash
pip install -r requirements.txt
```

## Utilisation

### Lancement de l'application

Pour lancer l'application dans le mode Espace de Travail (par défaut) :
```bash
python main.py
```

Pour lancer l'application dans le mode Tri (multi-sources) :
```bash
python main.py --mode tri
```

### Mode Espace de Travail

Ce mode permet de gérer un répertoire unique contenant des projets Cubase :

1. Sélectionnez un dossier de travail via le bouton "Choisir dossier de travail..." dans la barre d'outils
2. Naviguez dans l'arborescence des projets à gauche
3. Visualisez les détails du projet sélectionné à droite
4. Gérez les métadonnées (tags, notes, notation) dans l'onglet "Tags & Notes"
5. Prévisualisez les fichiers audio en double-cliquant sur un fichier WAV

### Mode Tri (multi-sources)

Ce mode permet de consolider des projets dispersés dans plusieurs dossiers :

1. Ajoutez des dossiers à scanner via le bouton "Ajouter un dossier"
2. Lancez le scan avec le bouton "Scanner les dossiers"
3. Filtrez et triez les projets trouvés
4. Sélectionnez un projet pour voir ses détails et fichiers
5. Choisissez un dossier de destination
6. Sauvegardez le projet sélectionné avec les options souhaitées

Options disponibles:
- `--mode tri` : Lance directement en mode tri (multi-sources)
- `--mode workspace` : Lance directement en mode espace de travail (unique)
- `--workspace [chemin]` : Définit directement le dossier de travail

## Captures d'écran
### Mode Tri
1. Sélectionnez les dossiers sources contenant vos projets Cubase
2. Lancez l'analyse
3. Explorez les projets détectés
4. Sélectionnez les fichiers à conserver
5. Choisissez un dossier de destination
6. Sauvegardez le projet

### Mode Espace de Travail
1. Sélectionnez un dossier de travail contenant vos projets
2. Parcourez l'arborescence des projets
3. Gérez les métadonnées (tags, notes)
4. Manipulez les fichiers selon vos besoins
5. Lancez directement les projets dans Cubase

## 📷 Captures d'écran

*(À ajouter)*

## 📝 Conventions de code

- Utilisez PEP 8 pour le style de code Python
- Préfixez les attributs privés avec `_`
- Utilisez des noms explicites pour les méthodes et variables
- Ajoutez des docstrings pour toutes les classes et méthodes
- Organisez le code selon l'architecture proposée

## 📄 Licence

Ce projet est distribué sous licence libre. Vous êtes libre de l'utiliser, le modifier et le distribuer selon vos besoins.