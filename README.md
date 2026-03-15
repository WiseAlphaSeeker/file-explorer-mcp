![Python](https://img.shields.io/badge/Python-3.12-blue)
![MCP](https://img.shields.io/badge/MCP-Server-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Outils](https://img.shields.io/badge/Outils-5-orange)
# 🗂️ MCP File Explorer

Un serveur MCP (Model Context Protocol) qui permet à Claude d'explorer et d'interagir avec vos fichiers locaux. Ce serveur expose 5 outils puissants pour naviguer dans le système de fichiers.

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Server-green)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Outils](https://img.shields.io/badge/Outils-5-orange)]()

## ✨ Fonctionnalités

- **`list_directory`** : Liste le contenu d'un dossier (type, taille, date de modification).
- **`read_text_file`** : Lit un fichier texte avec limitation du nombre de lignes.
- **`search_files`** : Recherche des fichiers par motif (ex: `*.py`, `rapport*`).
- **`file_info`** : Affiche les métadonnées détaillées d'un fichier ou dossier.
- **`tree_view`** : Affiche l'arborescence d'un dossier (comme la commande `tree`).

## ⚙️ Installation

### Prérequis
- Python 3.12 ou supérieur
- [Claude Desktop](https://claude.ai/download) installé

### Étapes

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/WiseAlphaSeeker/file-explorer-mcp.git
   cd file-explorer-mcp
