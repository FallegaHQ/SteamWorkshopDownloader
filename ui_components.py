import os
import tempfile
import tkinter as tk
import webbrowser
from tkinter import ttk
import config


class WindowHelper:
    """Helper functions for window positioning and management."""

    @staticmethod
    def center_window(window, width, height):
        """Center a window on the screen."""
        window.update_idletasks()

        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        window.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def center_window_relative(child_window, parent_window, width, height):
        """Center a child window relative to its parent."""
        parent_window.update_idletasks()

        parent_x = parent_window.winfo_x()
        parent_y = parent_window.winfo_y()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()

        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        child_window.geometry(f"{width}x{height}+{x}+{y}")


class LogPopup:
    """Modal popup window for displaying download logs with progress bar."""

    def __init__(self, parent, total_mods):
        self.popup = tk.Toplevel(parent)
        self.popup.title("SteamCMD Download Log")

        WindowHelper.center_window_relative(
            self.popup, parent,
            config.LOG_WINDOW_WIDTH,
            config.LOG_WINDOW_HEIGHT
        )

        self.popup.transient(parent)
        self.popup.grab_set()
        self.popup.protocol("WM_DELETE_WINDOW", lambda: None)
        self.popup.resizable(False, False)

        self._setup_ui(total_mods)

        self.current_download = 0
        self.total_downloads = total_mods

    def _setup_ui(self, total_mods):
        """Setup the UI components."""

        progress_frame = tk.Frame(self.popup)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        self.progress_label = tk.Label(progress_frame, text=f"Progress: 0/{total_mods} mods")
        self.progress_label.pack(anchor="w")

        progress_width = config.LOG_WINDOW_WIDTH - 20
        self.progress_bar = ttk.Progressbar(progress_frame, length=progress_width, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        self.progress_bar["maximum"] = 100

        log_frame = tk.Frame(self.popup)
        log_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=(0, 5))

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED, bg="black", fg="lightgrey",
                                font=("Courier New", 9))
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    def update_progress(self, current, total):
        """Update the progress bar and label."""
        self.current_download = current
        self.total_downloads = total
        progress_percentage = (current / total) * 100 if total > 0 else 0
        self.progress_bar["value"] = progress_percentage
        self.progress_label.config(text=f"Progress: {current}/{total} mods")

    def add_log(self, message):
        """Add a message to the log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def destroy(self):
        """Destroy the popup window."""
        self.popup.destroy()


class DescriptionPopup:
    """Popup window for displaying mod descriptions with BBCode parsing."""

    def __init__(self, parent, title, description, bbcode_parser):
        self.popup = tk.Toplevel(parent)
        self.popup.title(f"Description - {title}")

        WindowHelper.center_window_relative(
            self.popup, parent,
            config.DESCRIPTION_WINDOW_WIDTH,
            config.DESCRIPTION_WINDOW_HEIGHT
        )

        self.popup.transient(parent)
        self.popup.grab_set()

        self.description = description
        self.bbcode_parser = bbcode_parser
        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI components."""

        frame = tk.Frame(self.popup)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        webview_created = False

        if config.TKINTERWEB_AVAILABLE:
            try:
                html_view = config.tkweb.HtmlFrame(frame)
                html_view.pack(fill=tk.BOTH, expand=True)

                parsed_html = self.bbcode_parser.parse(self.description)
                html_view.load_html(parsed_html)
                webview_created = True
            except Exception as e:
                print(f"tkinterweb failed: {e}")

        if not webview_created:
            self._create_text_fallback(frame)

        self._create_buttons()

    def _create_text_fallback(self, frame):
        """Create a text widget fallback when webview is not available."""

        info_label = tk.Label(frame,
                              text="HTML webview not available. Install 'tkinterweb' for better formatting:\npip install tkinterweb",
                              fg="orange", justify=tk.LEFT)
        info_label.pack(pady=(0, 10))

        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_widget = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Helvetica", 10))
        scrollbar = tk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        text_widget.config(state=tk.NORMAL)
        if self.description:
            text_widget.insert(tk.END, self.description)
        else:
            text_widget.insert(tk.END, "No description available.")
        text_widget.config(state=tk.DISABLED)

    def _create_buttons(self):
        """Create the button frame with action buttons."""
        button_frame = tk.Frame(self.popup)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        def open_in_browser():
            """Save HTML to temp file and open in browser."""
            parsed_html = self.bbcode_parser.parse(self.description)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(parsed_html)
                temp_file = f.name

            webbrowser.open(f'file://{temp_file}')

            def cleanup():
                try:
                    os.unlink(temp_file)
                except:
                    pass

            self.popup.after(5000, cleanup)

        open_browser_button = tk.Button(button_frame, text="Open in Browser", command=open_in_browser)
        open_browser_button.pack(side=tk.LEFT, padx=(0, 5))

        close_button = tk.Button(button_frame, text="Close", command=self.popup.destroy)
        close_button.pack(side=tk.RIGHT)


class ModInfoWidget:
    """Widget for displaying mod information with selection preservation."""

    def __init__(self, parent):
        self.parent = parent
        self.selection_preserve_callback = None
        self._setup_ui()
        self.view_desc_callback = None

    def _setup_ui(self):
        """Setup the UI components."""

        info_title_label = tk.Label(self.parent, text="Mod Info:", anchor="w", justify="left",
                                    font=("Helvetica", 10, "bold"))
        info_title_label.pack(fill="x", padx=5, pady=(2, 0))

        desc_frame = tk.Frame(self.parent)
        desc_frame.pack(fill="x", padx=5, pady=(0, 2))

        self.view_desc_button = tk.Button(desc_frame, text="View Description", command=self._on_view_description,
                                          state=tk.DISABLED)
        self.view_desc_button.pack(side=tk.LEFT)

        self.info_text = tk.Text(self.parent, height=8, wrap=tk.WORD, state=tk.DISABLED, bg=self.parent.cget('bg'),
                                 relief=tk.FLAT, font=("Helvetica", 9))
        self.info_text.pack(fill="x", expand=True, padx=5, pady=(0, 5))

        self.info_text.bind("<Button-1>", self._on_text_click)
        self.info_text.bind("<Control-a>", self._on_select_all)
        self.info_text.bind("<Control-c>", self._on_copy)

    def _on_text_click(self, event):
        """Handle clicks on the text widget."""
        if self.selection_preserve_callback:
            self.selection_preserve_callback()

        return

    def _on_select_all(self, event):
        """Handle Ctrl+A in text widget."""
        if self.selection_preserve_callback:
            self.selection_preserve_callback()
        self.info_text.tag_add(tk.SEL, "1.0", tk.END)
        return "break"

    def _on_copy(self, event):
        """Handle Ctrl+C in text widget."""
        if self.selection_preserve_callback:
            self.selection_preserve_callback()
        try:

            selected_text = self.info_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.parent.clipboard_clear()
                self.parent.clipboard_append(selected_text)
        except tk.TclError:

            all_text = self.info_text.get("1.0", tk.END).strip()
            if all_text:
                self.parent.clipboard_clear()
                self.parent.clipboard_append(all_text)
        return "break"

    def bind_selection_preservation(self, callback):
        """Bind a callback to preserve selection when interacting with the widget."""
        self.selection_preserve_callback = callback

    def set_view_description_callback(self, callback):
        """Set the callback for the view description button."""
        self.view_desc_callback = callback

    def _on_view_description(self):
        """Handle view description button click."""
        if self.view_desc_callback:
            self.view_desc_callback()

    def update_info(self, mod, all_mods):
        """Update the displayed mod information."""
        if not mod:
            self.view_desc_button.config(state=tk.DISABLED)
            self._set_text("")
            return

        info = mod.get("info", {})

        if info.get("title", "").startswith("Fetching info for"):
            text = "Fetching details..."
            self.view_desc_button.config(state=tk.DISABLED)
        elif "error" in info:
            text = f"Error fetching info: {info['error']}"
            self.view_desc_button.config(state=tk.DISABLED)
        else:
            text = self._build_info_text(mod, all_mods)

            description = info.get('description', '')
            if description and description.strip():
                self.view_desc_button.config(state=tk.NORMAL)
                text += "\n\n[Description available - click 'View Description' to see it]"
            else:
                self.view_desc_button.config(state=tk.DISABLED)
                text += "\n\n[No description available]"

        self._set_text(text)

    def update_multiple_info(self, selected_mods):
        """Update the displayed information for multiple selected mods."""
        if not selected_mods:
            self.view_desc_button.config(state=tk.DISABLED)
            self._set_text("")
            return

        self.view_desc_button.config(state=tk.DISABLED)

        total_size = 0
        valid_size_count = 0
        main_mods = 0
        dependencies = 0

        for mod in selected_mods:

            if mod.get('is_dependency', False):
                dependencies += 1
            else:
                main_mods += 1

            info = mod.get("info", {})
            try:
                file_size = int(info.get("file_size", 0))
                if file_size > 0:
                    total_size += file_size
                    valid_size_count += 1
            except (ValueError, TypeError):
                pass

        if total_size > 0:
            total_size_mb = total_size / (1024 * 1024)
            if total_size_mb >= 1024:
                size_str = f"{total_size_mb / 1024:.2f} GB"
            else:
                size_str = f"{total_size_mb:.2f} MB"
        else:
            size_str = "Unknown"

        text = f"Multiple mods selected: {len(selected_mods)} total\n"

        if main_mods > 0 and dependencies > 0:
            text += f"├─ Main mods: {main_mods}\n"
            text += f"├─ Dependencies: {dependencies}\n"
        elif dependencies > 0:
            text += f"├─ All dependencies\n"
        else:
            text += f"├─ All main mods\n"

        text += f"├─ Total size: {size_str}"

        if valid_size_count < len(selected_mods):
            text += f" ({valid_size_count}/{len(selected_mods)} mods have size info)"

        text += "\n\n[Select a single mod to view detailed information]"

        self._set_text(text)

    def _build_info_text(self, mod, all_mods):
        """Build the info text for a mod."""
        info = mod.get("info", {})

        try:
            size_mb = int(info.get("file_size", 0)) / (1024 * 1024)
            if size_mb >= 1024:
                size_str = f"{size_mb / 1024:.2f} GB"
            else:
                size_str = f"{size_mb:.2f} MB"
        except (ValueError, TypeError):
            size_str = "N/A"

        text = (f"Title: {info.get('title', 'N/A')}\n"
                f"ID: {mod['id']}\n"
                f"App ID: {info.get('app_id', 'N/A')}\n"
                f"URL: {mod['url']}\n"
                f"Size: {size_str}\n")

        all_mods_by_id = {m['id']: m for m in all_mods}
        dependencies = info.get("dependencies", [])
        if dependencies:
            dep_titles = [all_mods_by_id.get(dep_id, {}).get('info', {}).get('title', dep_id) for dep_id in
                          dependencies]
            text += f"\nRequires: {', '.join(dep_titles)}"

        requiring_mods = []
        for other_mod in all_mods:
            if mod['id'] in other_mod.get('info', {}).get('dependencies', []):
                requiring_mods.append(other_mod.get('info', {}).get('title', other_mod['id']))

        if requiring_mods:
            text += f"\nRequired by: {', '.join(requiring_mods)}"

        return text

    def _set_text(self, text):
        """Set the text in the info widget."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, text)
        self.info_text.config(state=tk.DISABLED)

    def clear(self):
        """Clear the info display."""
        self.view_desc_button.config(state=tk.DISABLED)
        self._set_text("")
