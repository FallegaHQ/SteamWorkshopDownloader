import json
import os
import re
import threading
from typing import List, Dict, Optional, Set

import config


class ModManager:
    """Handles mod data management and persistence with improved dependency resolution."""

    def __init__(self, data_file: str = config.DATA_FILE):
        self.data_file = data_file
        self.mods = self._load_mods()
        self.mods_lock = threading.Lock()

    def _load_mods(self) -> List[Dict]:
        """Load mods from the JSON data file."""

        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f:
                content = f.read()
                mods = json.loads(content)

            for m in mods:
                if m.get("info") is None:
                    m["info"] = {}
                if "is_dependency" not in m:
                    m["is_dependency"] = False
            return mods
        return []

    def save_mods(self) -> None:
        """Save mods to the JSON data file."""
        with self.mods_lock:
            with open(self.data_file, "w") as f:
                json.dump(self.mods, f, indent=2)

    def add_mod_by_url(self, url: str) -> Optional[str]:
        """
        Add a mod by URL, extracting the ID from various Steam Workshop URL formats.
        Returns the mod_id if successful, None if invalid URL.
        """

        pattern = r"steamcommunity\.com/(?:sharedfiles|workshop)/filedetails/\?.*id=(\d+)"
        match = re.search(pattern, url)

        if not match:
            return None

        mod_id = match.group(1)
        self.add_mod_by_id(mod_id)
        return mod_id

    def add_mod_by_id(self, mod_id: str, is_dependency: bool = False) -> bool:
        """
        Add a mod to the list by its ID, checking for duplicates.
        Returns True if mod was added or updated, False if already exists unchanged.
        """
        with self.mods_lock:
            existing_mod = next((m for m in self.mods if m['id'] == mod_id), None)

            if existing_mod:

                if existing_mod.get("is_dependency") and not is_dependency:
                    existing_mod["is_dependency"] = False
                    return True

                return False

            url = f"https://steamcommunity.com/workshop/filedetails/?id={mod_id}"
            title = f"Fetching info for {mod_id}..." if not is_dependency else f"Fetching dependency {mod_id}..."
            mod = {"id": mod_id, "url": url, "info": {"title": title}, "is_dependency": is_dependency}
            self.mods.append(mod)
            return True

    def remove_mod(self, mod_id: str) -> bool:
        """Remove a mod by its ID. Returns True if removed, False if not found."""
        with self.mods_lock:
            for i, mod in enumerate(self.mods):
                if mod['id'] == mod_id:
                    del self.mods[i]
                    return True
            return False

    def remove_mod_by_index(self, index: int) -> bool:
        """Remove a mod by its index. Returns True if removed, False if invalid index."""
        with self.mods_lock:
            if 0 <= index < len(self.mods):
                del self.mods[index]
                return True
            return False

    def get_mod_by_id(self, mod_id: str) -> Optional[Dict]:
        """Get a mod by its ID."""
        with self.mods_lock:
            return next((m for m in self.mods if m['id'] == mod_id), None)

    def get_mod_by_index(self, index: int) -> Optional[Dict]:
        """Get a mod by its index."""
        with self.mods_lock:
            if 0 <= index < len(self.mods):
                return self.mods[index]
            return None

    def update_mod_info(self, mod_id: str, info: Dict) -> bool:
        """Update mod info. Returns True if updated, False if mod not found."""
        with self.mods_lock:
            mod = next((m for m in self.mods if m['id'] == mod_id), None)
            if mod:
                mod["info"] = info
                return True
            return False

    def update_mod_description(self, mod_id: str, description: str) -> bool:
        """Update only the description of a mod. Returns True if updated, False if mod not found."""
        with self.mods_lock:
            mod = next((m for m in self.mods if m['id'] == mod_id), None)
            if mod:
                if "info" not in mod:
                    mod["info"] = {}
                mod["info"]["description"] = description
                return True
            return False

    def get_all_mods(self) -> List[Dict]:
        """Get all mods (returns a copy to prevent external modifications)."""
        with self.mods_lock:
            return self.mods.copy()

    def get_mods_count(self) -> int:
        """Get the total number of mods."""
        with self.mods_lock:
            return len(self.mods)

    def find_dependents(self, mod_id: str) -> List[Dict]:
        """Find all mods that depend on the given mod_id."""
        dependents = []
        with self.mods_lock:
            for mod in self.mods:
                dependencies = mod.get('info', {}).get('dependencies', [])
                if mod_id in dependencies:
                    dependents.append(mod)
        return dependents

    def get_all_dependencies_efficient(self, mod_ids: Set[str]) -> Set[str]:
        """
        Efficiently find all dependencies for a set of mod IDs using iterative approach.
        This prevents infinite recursion and is much faster for large dependency trees.
        """
        all_dependencies = set()
        to_process = set(mod_ids)
        processed = set()

        with self.mods_lock:
            mods_dict = {mod['id']: mod for mod in self.mods}

        while to_process:
            current_id = to_process.pop()

            if current_id in processed:
                continue

            processed.add(current_id)

            if current_id in mods_dict:
                mod = mods_dict[current_id]
                dependencies = mod.get('info', {}).get('dependencies', [])

                for dep_id in dependencies:
                    all_dependencies.add(dep_id)

                    if dep_id not in processed:
                        to_process.add(dep_id)

        return all_dependencies

    def get_all_dependencies(self, mod_id: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """
        DEPRECATED: Use get_all_dependencies_efficient instead.
        Kept for backward compatibility but now uses the efficient method.
        """
        return self.get_all_dependencies_efficient({mod_id})

    def build_hierarchical_list(self) -> List[tuple]:
        """Build a hierarchical list where dependencies appear directly under their parents."""
        with self.mods_lock:

            mods_by_id = {mod['id']: mod for mod in self.mods}

            root_mods = []
            dependency_mods = set()

            for mod in self.mods:
                dependencies = mod.get('info', {}).get('dependencies', [])
                dependency_mods.update(dependencies)

            for mod in self.mods:
                if not mod.get('is_dependency', False):
                    root_mods.append(mod)
                elif mod['id'] not in dependency_mods:

                    root_mods.append(mod)

            hierarchical_list = []
            processed_mods = set()

            def add_mod_with_dependencies(mod, indent_level=0, visited=None):
                if visited is None:
                    visited = set()

                if mod['id'] in visited or mod['id'] in processed_mods:
                    return

                visited.add(mod['id'])
                processed_mods.add(mod['id'])
                hierarchical_list.append((mod, indent_level))

                dependencies = mod.get('info', {}).get('dependencies', [])
                for dep_id in dependencies:
                    if dep_id in mods_by_id and dep_id not in visited:
                        dep_mod = mods_by_id[dep_id]
                        add_mod_with_dependencies(dep_mod, indent_level + 1, visited.copy())

            for mod in root_mods:
                add_mod_with_dependencies(mod)

            for mod in self.mods:
                if mod['id'] not in processed_mods:
                    add_mod_with_dependencies(mod)

            return hierarchical_list

    def mark_as_dependency(self, mod_id: str) -> bool:
        """Mark a mod as a dependency. Returns True if updated, False if mod not found."""
        with self.mods_lock:
            mod = next((m for m in self.mods if m['id'] == mod_id), None)
            if mod:
                mod["is_dependency"] = True
                return True
            return False

    def mark_as_main_mod(self, mod_id: str) -> bool:
        """Mark a mod as a main mod (not a dependency). Returns True if updated, False if mod not found."""
        with self.mods_lock:
            mod = next((m for m in self.mods if m['id'] == mod_id), None)
            if mod:
                mod["is_dependency"] = False
                return True
            return False
