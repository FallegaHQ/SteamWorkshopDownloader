import queue
import threading
import tkinter as tk
from tkinter import messagebox

import config
from bbcode_parser import BBCodeParser
from config import STEAMCMD_PATH
from download_completion_dialog import DownloadCompletionDialog
from mod_manager import ModManager
from steam_api import SteamAPI
from steamcmd_downloader import SteamCMDDownloader
from ui_components import WindowHelper, LogPopup, DescriptionPopup, ModInfoWidget



class SteamWorkshopDownloader:
    """Main application class for the Steam Workshop Downloader."""

    def __init__(self, root):
        self.root = root
        self.root.title("Steam Workshop Downloader")
        self.root.geometry(config.MAIN_WINDOW_DIMS)

        WindowHelper.center_window(self.root, config.MAIN_WINDOW_WIDTH, config.MAIN_WINDOW_HEIGHT)

        self.mod_manager = ModManager()
        self.bbcode_parser = BBCodeParser()
        self.steamcmd_downloader = SteamCMDDownloader(STEAMCMD_PATH)
        self.steam_api = SteamAPI()

        self.log_popup = None
        self.listbox_to_mod_index = {}
        self.filtered_mods = []
        self.current_filter = ""
        self.filter_show_dependencies = True
        self.filter_show_main_mods = True
        self.current_selection = []

        self.download_queue = queue.Queue()
        self.is_downloading = False

        self.process_queue()

        self._setup_ui()

        self.refresh_listbox()

        self.active_threads = []
        self.shutdown_event = threading.Event()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui(self):
        """Setup the user interface."""
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        filter_frame = tk.Frame(self.root)
        filter_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        list_frame = tk.Frame(self.root)
        list_frame.pack(expand=True, fill=tk.BOTH, padx=10)

        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        info_frame = tk.Frame(self.root, relief=tk.GROOVE, borderwidth=2)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        tk.Label(top_frame, text="Steam Workshop URL:").pack(side=tk.LEFT)

        self.entry = tk.Entry(top_frame, width=50)
        self.entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0), ipady=2)
        self.entry.bind('<Return>', lambda e: self.add_mod())
        self.entry.bind('<KP_Enter>', lambda e: self.add_mod())

        self.add_button = tk.Button(top_frame, text="Add Mod", command=self.add_mod)
        self.add_button.pack(side=tk.LEFT, padx=(5, 0))

        tk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)

        self.filter_entry = tk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=(5, 0))
        self.filter_entry.bind('<KeyRelease>', self._on_filter_change)
        self.filter_entry.bind('<Return>', lambda e: self._apply_filter())
        self.filter_entry.bind('<KP_Enter>', lambda e: self._apply_filter())

        self.clear_filter_button = tk.Button(filter_frame, text="Clear", command=self._clear_filter)
        self.clear_filter_button.pack(side=tk.LEFT, padx=(5, 0))

        self.show_main_var = tk.BooleanVar(value=True)
        self.show_deps_var = tk.BooleanVar(value=True)

        tk.Checkbutton(filter_frame, text="Main Mods", variable=self.show_main_var, command=self._apply_filter).pack(
            side=tk.LEFT, padx=(10, 0))
        tk.Checkbutton(filter_frame, text="Dependencies", variable=self.show_deps_var, command=self._apply_filter).pack(
            side=tk.LEFT, padx=(5, 0))

        self.filter_info_label = tk.Label(filter_frame, text="", fg="gray")
        self.filter_info_label.pack(side=tk.RIGHT)

        self.listbox = tk.Listbox(list_frame, width=80, height=15, selectmode=tk.EXTENDED)
        list_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=list_scrollbar.set)
        self.listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.execute_button = tk.Button(button_frame, text="Download Selected", command=self.download_selected)
        self.execute_button.pack(side=tk.LEFT)

        self.download_all_button = tk.Button(button_frame, text="Download All", command=self.download_all)
        self.download_all_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(button_frame, text="Delete Selected", command=self.delete_selected)
        self.delete_button.pack(side=tk.RIGHT)

        self.mod_info_widget = ModInfoWidget(info_frame)
        self.mod_info_widget.set_view_description_callback(self.show_description_popup)

        self.status_label = tk.Label(self.root, text="", bd=1, relief=tk.SUNKEN, anchor="w")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        self.mod_info_widget.bind_selection_preservation(self._preserve_selection)

    def _preserve_selection(self):
        """Preserve the current listbox selection."""
        self.current_selection = list(self.listbox.curselection())

    def _on_listbox_select(self, event):
        """Handle listbox selection change."""
        self.current_selection = list(self.listbox.curselection())
        self.show_mod_info(event)

    def _restore_selection(self):
        """Restore the preserved selection."""
        if self.current_selection:
            self.listbox.selection_clear(0, tk.END)
            for index in self.current_selection:
                if index < self.listbox.size():
                    self.listbox.selection_set(index)

    def _on_filter_change(self, event=None):
        """Called when filter text changes."""
        self.root.after_idle(self._apply_filter)

    def _apply_filter(self):
        """Apply the current filter settings."""
        filter_text = self.filter_entry.get().lower().strip()
        show_main = self.show_main_var.get()
        show_deps = self.show_deps_var.get()

        all_mods = self.mod_manager.get_all_mods()

        filtered_mods = []
        for mod in all_mods:
            is_dependency = mod.get('is_dependency', False)
            if is_dependency and not show_deps:
                continue
            if not is_dependency and not show_main:
                continue

            if filter_text:
                title = mod.get('info', {}).get('title', '').lower()
                mod_id = mod['id'].lower()
                url = mod['url'].lower()

                if (filter_text not in title and filter_text not in mod_id and filter_text not in url):
                    continue

            filtered_mods.append(mod)

        self.filtered_mods = filtered_mods
        self.current_filter = filter_text
        self.filter_show_dependencies = show_deps
        self.filter_show_main_mods = show_main

        total_mods = len(all_mods)
        filtered_count = len(filtered_mods)
        if filtered_count == total_mods:
            self.filter_info_label.config(text=f"Showing all {total_mods} mods")
        else:
            self.filter_info_label.config(text=f"Showing {filtered_count} of {total_mods} mods")

        self._refresh_filtered_listbox()

    def _clear_filter(self):
        """Clear all filters."""
        self.filter_entry.delete(0, tk.END)
        self.show_main_var.set(True)
        self.show_deps_var.set(True)
        self._apply_filter()

    def _refresh_filtered_listbox(self):
        """Refresh the listbox with filtered mod data."""
        selected_mod_ids = []
        for listbox_index in self.current_selection:
            if listbox_index in self.listbox_to_mod_index:
                mod_index = self.listbox_to_mod_index[listbox_index]
                all_mods = self.mod_manager.get_all_mods()
                if 0 <= mod_index < len(all_mods):
                    selected_mod_ids.append(all_mods[mod_index]['id'])

        self.listbox.delete(0, tk.END)

        hierarchical_list = self._build_filtered_hierarchical_list()

        self.listbox_to_mod_index = {}
        new_selected_indices = []

        all_mods = self.mod_manager.get_all_mods()
        for listbox_index, (mod, indent_level) in enumerate(hierarchical_list):
            info = mod.get("info") or {}
            title = info.get("title", mod["url"])

            indent = "  " * indent_level
            if mod.get("is_dependency") or indent_level > 0:
                title = f"{indent}├─ {title} (dependency)"
            else:
                title = f"{indent}{title}"

            self.listbox.insert(tk.END, title)

            original_index = all_mods.index(mod)
            self.listbox_to_mod_index[listbox_index] = original_index

            if mod['id'] in selected_mod_ids:
                new_selected_indices.append(listbox_index)

        self.current_selection = new_selected_indices
        for index in new_selected_indices:
            self.listbox.selection_set(index)

        if new_selected_indices:
            self.listbox.see(new_selected_indices[0])
        elif len(hierarchical_list) > 0:
            self.listbox.see(tk.END)

    def _build_filtered_hierarchical_list(self):
        """Build a hierarchical list for filtered mods, maintaining dependency relationships."""
        all_mods_by_id = {mod['id']: mod for mod in self.mod_manager.get_all_mods()}
        filtered_mods_ids = {mod['id'] for mod in self.filtered_mods}

        root_mods = []
        dependency_mods = set()

        for mod in self.filtered_mods:
            dependencies = mod.get('info', {}).get('dependencies', [])
            dependency_mods.update(dependencies)

        for mod in self.filtered_mods:
            if not mod.get('is_dependency', False):
                root_mods.append(mod)
            elif mod['id'] not in dependency_mods:
                root_mods.append(mod)

        hierarchical_list = []
        processed_mods = set()

        def add_mod_with_dependencies(mod, indent_level=0):
            if mod['id'] in processed_mods:
                return

            processed_mods.add(mod['id'])
            hierarchical_list.append((mod, indent_level))

            m_dependencies = mod.get('info', {}).get('dependencies', [])
            for dep_id in m_dependencies:
                if dep_id in filtered_mods_ids and dep_id in all_mods_by_id:
                    dep_mod = all_mods_by_id[dep_id]
                    add_mod_with_dependencies(dep_mod, indent_level + 1)

        for mod in root_mods:
            add_mod_with_dependencies(mod)

        for mod in self.filtered_mods:
            if mod['id'] not in processed_mods:
                add_mod_with_dependencies(mod)

        return hierarchical_list

    def process_queue(self):
        """Process messages from the background thread queue."""
        try:
            messages_processed = 0
            max_messages = 50 if self.is_downloading else 10

            while messages_processed < max_messages:
                try:
                    message_type, data = self.download_queue.get_nowait()
                    messages_processed += 1

                    if message_type == "status":
                        self.status_label.config(text=data)
                    elif message_type == "log":
                        if self.log_popup:
                            self.log_popup.add_log(data)
                    elif message_type == "progress":
                        if self.log_popup:
                            self.log_popup.update_progress(data["current"], data["total"])
                    elif message_type == "info_updated":
                        self.mod_manager.save_mods()
                        self.refresh_listbox()
                        if self.current_selection:
                            self.show_mod_info(None)
                    elif message_type == "description_updated":
                        mod_id = data
                        if self._is_mod_selected(mod_id):
                            self.show_mod_info(None)
                        self.mod_manager.save_mods()
                    elif message_type == "download_finished":
                        result = data
                        if self.log_popup:
                            self.log_popup.destroy()
                            self.log_popup = None

                        completed = result['completed']
                        successful = result['successful']
                        failed_count = len(result['failed_ids'])

                        if failed_count == 0:
                            self.status_label.config(text=f"Successfully downloaded all {successful} mod(s).")
                        else:
                            self.status_label.config(text=f"Downloaded {successful} mod(s). {failed_count} failed.")

                        DownloadCompletionDialog(self.root, result)
                        self.is_downloading = False
                        self.toggle_buttons(tk.NORMAL)

                except queue.Empty:
                    break

        except Exception as e:
            print(f"Error processing queue: {e}")
        finally:
            interval = 20 if self.is_downloading else 100
            self.root.after(interval, self.process_queue)

    def _is_mod_selected(self, mod_id):
        """Check if a specific mod is currently selected."""
        all_mods = self.mod_manager.get_all_mods()
        for listbox_index in self.current_selection:
            if listbox_index in self.listbox_to_mod_index:
                mod_index = self.listbox_to_mod_index[listbox_index]
                if 0 <= mod_index < len(all_mods):
                    if all_mods[mod_index]['id'] == mod_id:
                        return True
        return False

    def refresh_listbox(self):
        """Refresh the listbox with current mod data, applying current filter."""
        self._apply_filter()

    def add_mod(self):
        """Add a mod from the URL entry field."""
        url = self.entry.get().strip()
        if not url:
            return

        mod_id = self.mod_manager.add_mod_by_url(url)
        if not mod_id:
            messagebox.showerror("Invalid URL",
                                 "Please enter a valid Steam Workshop URL containing an ID (e.g., ...?id=12345).")
            return

        self.entry.delete(0, tk.END)
        self.status_label.config(text=f"Added mod {mod_id}, fetching info...")
        self.mod_manager.save_mods()
        self.refresh_listbox()

        self._start_info_fetch(mod_id)

    def _start_info_fetch(self, mod_id):
        """Start background info fetching for a mod with proper thread tracking."""
        fetch_thread = threading.Thread(target=self._fetch_info_worker, args=(mod_id,), daemon=True)
        self.active_threads.append(fetch_thread)
        fetch_thread.start()

        self.active_threads = [t for t in self.active_threads if t.is_alive()]

    def _fetch_info_worker(self, mod_id):
        """Fetches info and then triggers dependency checks with shutdown check."""
        try:
            if self.shutdown_event.is_set():
                return

            fetched_info = self.steam_api.fetch_mod_info(mod_id)

            if self.shutdown_event.is_set():
                return

            self.mod_manager.update_mod_info(mod_id, fetched_info)
            self.download_queue.put(("info_updated", None))

            dependency_ids = fetched_info.get("dependencies", [])
            for dep_id in dependency_ids:
                if self.shutdown_event.is_set():
                    return

                existing_mod = self.mod_manager.get_mod_by_id(dep_id)
                if existing_mod and not existing_mod.get("is_dependency", False):
                    self.mod_manager.mark_as_dependency(dep_id)
                    self.download_queue.put(("info_updated", None))

                if self.mod_manager.add_mod_by_id(dep_id, is_dependency=True):
                    self._start_info_fetch(dep_id)

        except Exception as e:
            if not self.shutdown_event.is_set():
                print(f"Error fetching info for mod {mod_id}: {e}")
                self.download_queue.put(("status", f"Error fetching info for mod {mod_id}: {e}"))

    def _fetch_description_worker(self, mod_id):
        """Fetches only the description for a mod using the Steam API."""
        try:
            description = self.steam_api.fetch_mod_description(mod_id)
            if description:
                self.mod_manager.update_mod_description(mod_id, description)
                self.download_queue.put(("description_updated", mod_id))
        except Exception as e:
            print(f"Error fetching description for mod {mod_id}: {e}")

    def delete_selected(self):
        """Delete the selected mod(s)."""
        if not self.current_selection:
            return

        mods_to_delete = []
        for listbox_index in self.current_selection:
            if listbox_index in self.listbox_to_mod_index:
                mod_index = self.listbox_to_mod_index[listbox_index]
                mod = self.mod_manager.get_mod_by_index(mod_index)
                if mod:
                    mods_to_delete.append((mod_index, mod))

        if not mods_to_delete:
            return

        mod_ids_to_delete = {mod['id'] for _, mod in mods_to_delete}
        dependency_warnings = []

        for _, mod in mods_to_delete:
            dependents = self.mod_manager.find_dependents(mod['id'])
            remaining_dependents = [dep for dep in dependents if dep['id'] not in mod_ids_to_delete]
            if remaining_dependents:
                dependent_titles = [dep.get('info', {}).get('title', dep['id']) for dep in remaining_dependents]
                title = mod.get('info', {}).get('title', mod['id'])
                dependency_warnings.append(f"'{title}' is required by: {', '.join(dependent_titles)}")

        if dependency_warnings:
            msg = "The following mods have dependencies:\n\n"
            msg += "\n".join(dependency_warnings)
            msg += "\n\nAre you sure you want to delete them?"
            if not messagebox.askyesno("Dependency Warning", msg):
                return

        mods_to_delete.sort(key=lambda x: x[0], reverse=True)
        for mod_index, mod in mods_to_delete:
            self.mod_manager.remove_mod_by_index(mod_index)

        self.mod_manager.save_mods()
        self.current_selection = []
        self.refresh_listbox()
        self.mod_info_widget.clear()

    def toggle_buttons(self, state):
        """Enable or disable main action buttons."""
        if self.is_downloading and state == tk.NORMAL:
            return

        self.add_button.config(state=state)
        self.execute_button.config(state=state)
        self.delete_button.config(state=state)

        all_state = state if self.mod_manager.get_mods_count() > 0 else tk.DISABLED
        self.download_all_button.config(state=all_state)

    def download_selected(self):
        """Download selected mods and their dependencies."""
        if self.is_downloading:
            messagebox.showinfo("Download in Progress", "Please wait for the current download to complete.")
            return

        if not self.current_selection:
            messagebox.showinfo("No Selection", "Please select one or more mods to download.")
            return

        if not self.steamcmd_downloader.is_steamcmd_available():
            messagebox.showerror("SteamCMD Not Found", f"SteamCMD not found at '{STEAMCMD_PATH}'.\n"
                                                       "Please ensure SteamCMD is installed and the path is correct.")
            return

        initial_mod_indices = []
        for listbox_index in self.current_selection:
            if listbox_index in self.listbox_to_mod_index:
                initial_mod_indices.append(self.listbox_to_mod_index[listbox_index])

        if not initial_mod_indices:
            return

        self.status_label.config(text="Preparing download - resolving dependencies...")
        self.toggle_buttons(tk.DISABLED)

        prep_thread = threading.Thread(target=self._prepare_download_worker, args=(initial_mod_indices,), daemon=True)
        prep_thread.start()

    def _prepare_download_worker(self, initial_mod_indices):
        """Background worker to resolve dependencies and prepare download."""
        try:
            all_mods = self.mod_manager.get_all_mods()
            initial_mod_ids = {all_mods[i]['id'] for i in initial_mod_indices}

            all_dependencies = self.mod_manager.get_all_dependencies_efficient(initial_mod_ids)
            final_mod_ids_to_download = initial_mod_ids.union(all_dependencies)

            added_deps_ids = all_dependencies - initial_mod_ids

            self.root.after(0, self._handle_dependencies_resolved, initial_mod_ids, final_mod_ids_to_download,
                            added_deps_ids)

        except Exception as e:
            error_msg = f"Error resolving dependencies: {e}"
            print(f"Dependency resolution error: {e}")
            self.root.after(0, self._handle_dependency_resolution_error, error_msg)

    def _handle_dependency_resolution_error(self, error_msg):
        """Handle dependency resolution errors on the main thread."""
        self.status_label.config(text="Ready")
        self.toggle_buttons(tk.NORMAL)
        messagebox.showerror("Dependency Resolution Error", error_msg)

    def _handle_dependencies_resolved(self, initial_mod_ids, final_mod_ids_to_download, added_deps_ids):
        """Handle dependency resolution completion on the main thread."""
        try:
            all_mods = self.mod_manager.get_all_mods()

            if added_deps_ids:
                added_deps_titles = []
                for dep_id in added_deps_ids:
                    mod = self.mod_manager.get_mod_by_id(dep_id)
                    if mod:
                        title = mod.get('info', {}).get('title', dep_id)
                        added_deps_titles.append(title)

                if added_deps_titles:
                    msg = "This download requires the following dependencies, which will also be selected:\n\n"
                    msg += "\n".join(f"- {title}" for title in added_deps_titles)
                    msg += "\n\nDo you want to continue?"

                    self.toggle_buttons(tk.NORMAL)
                    self.status_label.config(text="Ready")

                    if not messagebox.askyesno("Dependencies Found", msg):
                        return

            self._update_selection_with_dependencies(final_mod_ids_to_download)

            mods_to_download = []
            for mod in all_mods:
                if mod['id'] in final_mod_ids_to_download:
                    mods_to_download.append(mod)

            if not mods_to_download:
                self.status_label.config(text="Ready")
                self.toggle_buttons(tk.NORMAL)
                return

            self._start_download(mods_to_download)

        except Exception as e:
            error_msg = f"Error preparing download: {e}"
            print(f"Download preparation error: {e}")
            self.status_label.config(text="Ready")
            self.toggle_buttons(tk.NORMAL)
            messagebox.showerror("Download Preparation Error", error_msg)

    def _update_selection_with_dependencies(self, final_mod_ids_to_download):
        """Update the listbox selection to include dependencies."""
        self.listbox.selection_clear(0, tk.END)
        hierarchical_list = self._build_filtered_hierarchical_list()
        new_selection = []

        for listbox_index, (mod, indent_level) in enumerate(hierarchical_list):
            if mod['id'] in final_mod_ids_to_download:
                self.listbox.selection_set(listbox_index)
                new_selection.append(listbox_index)

        self.current_selection = new_selection

    def download_all(self):
        """Download all mods in the list (respecting current filter)."""
        if self.is_downloading:
            messagebox.showinfo("Download in Progress", "Please wait for the current download to complete.")
            return

        if not self.filtered_mods:
            messagebox.showinfo("No Mods", "There are no mods to download (check your filters).")
            return

        if not self.steamcmd_downloader.is_steamcmd_available():
            messagebox.showerror("SteamCMD Not Found", f"SteamCMD not found at '{STEAMCMD_PATH}'.\n"
                                                       "Please ensure SteamCMD is installed and the path is correct.")
            return

        total_mods = self.mod_manager.get_mods_count()
        if len(self.filtered_mods) < total_mods:
            msg = f"Download only the {len(self.filtered_mods)} filtered mods, or all {total_mods} mods?"
            result = messagebox.askyesnocancel("Download All",
                                               f"Yes = Download {len(self.filtered_mods)} filtered mods\n"
                                               f"No = Download all {total_mods} mods\n"
                                               f"Cancel = Cancel download")

            if result is None:
                return
            elif result:
                mods_to_download = self.filtered_mods
            else:
                mods_to_download = self.mod_manager.get_all_mods()
        else:
            if not messagebox.askyesno("Confirm Download All",
                                       f"Are you sure you want to download all {len(self.filtered_mods)} mod(s)?"):
                return
            mods_to_download = self.filtered_mods

        self._start_download(mods_to_download)

    def _start_download(self, mods_to_download):
        """Start the download process for the given mods."""
        print(f"Starting download for {len(mods_to_download)} mods...")

        self.is_downloading = True
        self.toggle_buttons(tk.DISABLED)
        self.status_label.config(text="Starting download...")

        self.root.update_idletasks()

        try:
            self.log_popup = LogPopup(self.root, len(mods_to_download))
            print("Log popup created successfully")
        except Exception as e:
            print(f"Error creating log popup: {e}")
            self.is_downloading = False
            self.toggle_buttons(tk.NORMAL)
            messagebox.showerror("Error", f"Failed to create download window: {e}")
            return

        self.root.update_idletasks()

        try:
            download_thread = threading.Thread(target=self._download_worker, args=(mods_to_download,), daemon=True)
            download_thread.start()
            print("Download thread started")
        except Exception as e:
            print(f"Error starting download thread: {e}")
            if self.log_popup:
                self.log_popup.destroy()
                self.log_popup = None
            self.is_downloading = False
            self.toggle_buttons(tk.NORMAL)
            messagebox.showerror("Error", f"Failed to start download: {e}")

    def _download_worker(self, mods_to_download):
        """Download worker with proper shutdown handling."""
        try:
            if self.shutdown_event.is_set():
                return

            print(f"Download worker started with {len(mods_to_download)} mods")

            valid_mods = []
            for i, mod in enumerate(mods_to_download):
                if self.shutdown_event.is_set():
                    return

                try:
                    mod_id = mod["id"]
                    mod_info = mod.get("info", {})

                    self.download_queue.put(("status", f"Checking mod {i + 1}/{len(mods_to_download)}: {mod_id}"))

                    if not mod_info.get("app_id"):
                        if self.shutdown_event.is_set():
                            return

                        self.download_queue.put(("status", f"Fetching info for mod {mod_id}..."))
                        self.download_queue.put(("log", f"Fetching info for mod {mod_id}...\n"))

                        fetched_info = self.steam_api.fetch_mod_info(mod_id)

                        if self.shutdown_event.is_set():
                            return

                        if "error" in fetched_info:
                            error_msg = f"Error fetching info for {mod_id}: {fetched_info['error']}"
                            self.download_queue.put(("status", error_msg))
                            self.download_queue.put(("log", f"{error_msg}\n"))
                            continue

                        self.mod_manager.update_mod_info(mod_id, fetched_info)
                        self.download_queue.put(("info_updated", None))
                        mod["info"] = fetched_info

                    app_id = mod["info"].get("app_id")
                    if not app_id:
                        error_msg = f"⚠️ Could not find App ID for mod {mod_id}. Skipping."
                        self.download_queue.put(("status", error_msg))
                        self.download_queue.put(("log", f"{error_msg}\n"))
                        continue

                    valid_mods.append(mod)

                except Exception as e:
                    if not self.shutdown_event.is_set():
                        error_msg = f"Error processing mod {mod.get('id', 'unknown')}: {e}"
                        self.download_queue.put(("log", f"{error_msg}\n"))
                        print(f"Error processing mod: {e}")

            if self.shutdown_event.is_set():
                return

            if not valid_mods:
                self.download_queue.put(("log", "No valid mods found for download.\n"))
                error_result = {'completed': 0, 'successful': 0, 'failed_ids': [], 'failed_details': []}
                self.download_queue.put(("download_finished", error_result))
                return

            self.download_queue.put(("status", f"Starting download of {len(valid_mods)} valid mods..."))
            self.download_queue.put(("log", f"Starting download of {len(valid_mods)} valid mods...\n"))

            def progress_callback(current, total):
                if not self.shutdown_event.is_set():
                    self.download_queue.put(("progress", {"current": current, "total": total}))

            def log_callback(message):
                if not self.shutdown_event.is_set():
                    self.download_queue.put(("log", message))

            def status_callback(status):
                if not self.shutdown_event.is_set():
                    self.download_queue.put(("status", status))

            download_result = self.steamcmd_downloader.download_mods(valid_mods, progress_callback, log_callback,
                status_callback)

            if not self.shutdown_event.is_set():
                self.download_queue.put(("download_finished", download_result))

        except Exception as e:
            if not self.shutdown_event.is_set():
                error_msg = f"Unexpected error during download: {e}"
                print(f"Download worker error: {e}")
                self.download_queue.put(("log", error_msg + "\n"))
                self.download_queue.put(("status", error_msg))

                error_result = {'completed': 0, 'successful': 0, 'failed_ids': [], 'failed_details': []}
                self.download_queue.put(("download_finished", error_result))

    def show_description_popup(self):
        """Shows the description in a webview popup with BBCode parsing."""
        if not self.current_selection:
            return

        listbox_index = self.current_selection[0]
        if listbox_index not in self.listbox_to_mod_index:
            return

        mod_index = self.listbox_to_mod_index[listbox_index]
        mod = self.mod_manager.get_mod_by_index(mod_index)
        if not mod:
            return

        info = mod.get("info", {})
        description = info.get('description', '')
        title = info.get('title', f"Mod {mod['id']}")

        DescriptionPopup(self.root, title, description, self.bbcode_parser)

    def show_mod_info(self, event):
        """Show information for the selected mod(s)."""
        if not self.current_selection:
            self.mod_info_widget.clear()
            return

        if len(self.current_selection) > 1:
            self._show_multiple_mod_info()
        else:
            self._show_single_mod_info()

    def _show_single_mod_info(self):
        """Show info for a single selected mod."""
        listbox_index = self.current_selection[0]
        if listbox_index not in self.listbox_to_mod_index:
            self.mod_info_widget.clear()
            return

        mod_index = self.listbox_to_mod_index[listbox_index]
        mod = self.mod_manager.get_mod_by_index(mod_index)
        all_mods = self.mod_manager.get_all_mods()

        self.mod_info_widget.update_info(mod, all_mods)

        if mod:
            info = mod.get("info", {})
            description = info.get('description', '')
            if (not description or not description.strip()) and not info.get("title", "").startswith(
                    "Fetching info for") and "error" not in info:
                fetch_thread = threading.Thread(target=self._fetch_description_worker, args=(mod['id'],), daemon=True)
                fetch_thread.start()

    def _show_multiple_mod_info(self):
        """Show summary info for multiple selected mods."""
        selected_mods = []
        all_mods = self.mod_manager.get_all_mods()

        for listbox_index in self.current_selection:
            if listbox_index in self.listbox_to_mod_index:
                mod_index = self.listbox_to_mod_index[listbox_index]
                mod = self.mod_manager.get_mod_by_index(mod_index)
                if mod:
                    selected_mods.append(mod)

        if not selected_mods:
            self.mod_info_widget.clear()
            return

        self.mod_info_widget.update_multiple_info(selected_mods)

    def on_closing(self):
        """Handle application closing with proper thread cleanup."""
        try:
            self.shutdown_event.set()

            if hasattr(self, 'steamcmd_downloader'):
                self.steamcmd_downloader.stop_download()

            if self.log_popup:
                try:
                    self.log_popup.destroy()
                except:
                    pass
                self.log_popup = None

            for thread in self.active_threads:
                if thread.is_alive():
                    thread.join(timeout=1.0)

            active_threads = [t for t in threading.enumerate() if t != threading.current_thread()]
            for thread in active_threads:
                if hasattr(thread, 'daemon') and not thread.daemon:
                    continue

        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            self.root.destroy()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = SteamWorkshopDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
