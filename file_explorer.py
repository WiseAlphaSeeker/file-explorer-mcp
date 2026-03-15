"""
Serveur MCP Explorateur de fichiers
====================================
Permet a Claude de naviguer dans les fichiers de ton ordinateur.

Tools exposes :
  - list_directory   : lister le contenu d un dossier
  - read_text_file   : lire un fichier texte
  - search_files     : chercher des fichiers par nom
  - file_info        : informations sur un fichier ou dossier
  - tree_view        : arborescence d un dossier
"""

import os
import datetime
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

server = FastMCP("file_explorer")


def format_size(size_bytes: int) -> str:
    """Convertit des bytes en taille lisible."""
    if size_bytes < 1024:
        return f"{size_bytes} o"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} Ko"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} Mo"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} Go"


def format_date(timestamp: float) -> str:
    """Convertit un timestamp en date lisible."""
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%d/%m/%Y %H:%M")


# --- Tool 1 : Lister un dossier ---

class ListDirectoryInput(BaseModel):
    path: str = Field(
        default="~",
        description="Chemin du dossier a lister (ex: C:\\Users\\efbl\\Documents, ~/Desktop, .)"
    )
    show_hidden: bool = Field(default=False, description="Afficher les fichiers caches")


@server.tool(name="list_directory")
async def list_directory(params: ListDirectoryInput) -> str:
    """Liste les fichiers et dossiers dans un repertoire.

    Affiche le nom, le type (dossier/fichier), la taille et la date de modification.
    """
    target = Path(params.path).expanduser().resolve()

    if not target.exists():
        return f"Erreur : Le chemin '{params.path}' n'existe pas."
    if not target.is_dir():
        return f"Erreur : '{params.path}' n'est pas un dossier."

    try:
        entries = sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        return f"Erreur : Acces refuse a '{target}'."

    if not params.show_hidden:
        entries = [e for e in entries if not e.name.startswith(".")]

    if not entries:
        return f"Le dossier '{target}' est vide."

    lines = [f"Contenu de {target} ({len(entries)} elements) :\n"]
    lines.append(f"  {'Type':<8} {'Taille':>10}  {'Modifie le':<18} Nom")
    lines.append(f"  {'----':<8} {'------':>10}  {'----------':<18} ---")

    for entry in entries:
        try:
            stat = entry.stat()
            date = format_date(stat.st_mtime)
            if entry.is_dir():
                lines.append(f"  {'DOSSIER':<8} {'':>10}  {date:<18} {entry.name}/")
            else:
                size = format_size(stat.st_size)
                lines.append(f"  {'FICHIER':<8} {size:>10}  {date:<18} {entry.name}")
        except (PermissionError, OSError):
            lines.append(f"  {'?':<8} {'?':>10}  {'?':<18} {entry.name}")

    return "\n".join(lines)


# --- Tool 2 : Lire un fichier texte ---

class ReadTextFileInput(BaseModel):
    path: str = Field(..., description="Chemin du fichier a lire", min_length=1)
    max_lines: Optional[int] = Field(default=100, description="Nombre max de lignes a afficher", ge=1, le=1000)


@server.tool(name="read_text_file")
async def read_text_file(params: ReadTextFileInput) -> str:
    """Lit le contenu d'un fichier texte (.txt, .py, .json, .csv, .md, etc.)."""
    filepath = Path(params.path).expanduser().resolve()

    if not filepath.exists():
        return f"Erreur : Fichier '{params.path}' introuvable."
    if not filepath.is_file():
        return f"Erreur : '{params.path}' n'est pas un fichier."
    if filepath.stat().st_size > 5 * 1024 * 1024:
        return f"Erreur : Fichier trop volumineux ({format_size(filepath.stat().st_size)}). Limite : 5 Mo."

    try:
        text = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = filepath.read_text(encoding="latin-1")
        except Exception:
            return f"Erreur : Impossible de lire '{filepath.name}' (fichier binaire ?)."

    lines = text.splitlines()
    total = len(lines)
    truncated = False

    if total > params.max_lines:
        lines = lines[:params.max_lines]
        truncated = True

    result = [f"Fichier : {filepath.name} ({format_size(filepath.stat().st_size)}, {total} lignes)\n"]
    for i, line in enumerate(lines, 1):
        result.append(f"  {i:>4} | {line}")

    if truncated:
        result.append(f"\n  ... ({total - params.max_lines} lignes restantes, utilisez max_lines pour en voir plus)")

    return "\n".join(result)


# --- Tool 3 : Chercher des fichiers ---

class SearchFilesInput(BaseModel):
    path: str = Field(default="~", description="Dossier de depart pour la recherche")
    pattern: str = Field(..., description="Motif de recherche (ex: *.py, rapport*, *.txt)", min_length=1)
    max_results: Optional[int] = Field(default=20, description="Nombre max de resultats", ge=1, le=100)


@server.tool(name="search_files")
async def search_files(params: SearchFilesInput) -> str:
    """Cherche des fichiers par nom dans un dossier et ses sous-dossiers.

    Supporte les wildcards : *.py pour tous les Python, rapport* pour les fichiers commencant par rapport.
    """
    start = Path(params.path).expanduser().resolve()

    if not start.exists():
        return f"Erreur : Le chemin '{params.path}' n'existe pas."

    results = []
    try:
        for match in start.rglob(params.pattern):
            if len(results) >= params.max_results:
                break
            try:
                stat = match.stat()
                size = format_size(stat.st_size) if match.is_file() else "DOSSIER"
                date = format_date(stat.st_mtime)
                results.append(f"  {size:>10}  {date}  {match}")
            except (PermissionError, OSError):
                continue
    except PermissionError:
        return f"Erreur : Acces refuse a '{start}'."

    if not results:
        return f"Aucun fichier correspondant a '{params.pattern}' dans '{start}'."

    header = f"Recherche '{params.pattern}' dans {start} : {len(results)} resultat(s)\n"
    return header + "\n".join(results)


# --- Tool 4 : Informations sur un fichier ---

class FileInfoInput(BaseModel):
    path: str = Field(..., description="Chemin du fichier ou dossier", min_length=1)


@server.tool(name="file_info")
async def file_info(params: FileInfoInput) -> str:
    """Donne les informations detaillees sur un fichier ou dossier."""
    target = Path(params.path).expanduser().resolve()

    if not target.exists():
        return f"Erreur : '{params.path}' n'existe pas."

    try:
        stat = target.stat()
    except PermissionError:
        return f"Erreur : Acces refuse a '{target}'."

    info = [f"Informations sur : {target}\n"]
    info.append(f"  Nom         : {target.name}")
    info.append(f"  Type        : {'Dossier' if target.is_dir() else 'Fichier'}")
    info.append(f"  Extension   : {target.suffix if target.suffix else '(aucune)'}")
    info.append(f"  Taille      : {format_size(stat.st_size)}")
    info.append(f"  Modifie le  : {format_date(stat.st_mtime)}")
    info.append(f"  Cree le     : {format_date(stat.st_ctime)}")
    info.append(f"  Chemin abs. : {target}")
    info.append(f"  Parent      : {target.parent}")

    if target.is_dir():
        try:
            children = list(target.iterdir())
            nb_files = sum(1 for c in children if c.is_file())
            nb_dirs = sum(1 for c in children if c.is_dir())
            info.append(f"  Contenu     : {nb_files} fichier(s), {nb_dirs} dossier(s)")
        except PermissionError:
            info.append(f"  Contenu     : acces refuse")

    return "\n".join(info)


# --- Tool 5 : Arborescence ---

class TreeViewInput(BaseModel):
    path: str = Field(default="~", description="Dossier racine")
    max_depth: Optional[int] = Field(default=2, description="Profondeur max (1 a 5)", ge=1, le=5)


@server.tool(name="tree_view")
async def tree_view(params: TreeViewInput) -> str:
    """Affiche l'arborescence d'un dossier sous forme d'arbre.

    Comme la commande 'tree' sous Windows.
    """
    start = Path(params.path).expanduser().resolve()

    if not start.exists():
        return f"Erreur : Le chemin '{params.path}' n'existe pas."
    if not start.is_dir():
        return f"Erreur : '{params.path}' n'est pas un dossier."

    lines = [f"{start}/"]
    count = {"files": 0, "dirs": 0}

    def _tree(directory: Path, prefix: str, depth: int):
        if depth > params.max_depth:
            return
        try:
            entries = sorted(directory.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
            entries = [e for e in entries if not e.name.startswith(".")]
        except PermissionError:
            lines.append(f"{prefix}[acces refuse]")
            return

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                count["dirs"] += 1
                _tree(entry, next_prefix, depth + 1)
            else:
                size = format_size(entry.stat().st_size)
                lines.append(f"{prefix}{connector}{entry.name} ({size})")
                count["files"] += 1

    _tree(start, "", 1)
    lines.append(f"\n{count['dirs']} dossier(s), {count['files']} fichier(s)")

    return "\n".join(lines)


# --- Point d'entree ---

if __name__ == "__main__":
    server.run()
