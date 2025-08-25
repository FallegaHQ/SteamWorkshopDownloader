import tkinter as tk
from tkinter import messagebox


class DownloadCompletionDialog:
    """Custom dialog for showing download completion results with copy functionality."""

    def __init__(self, parent, download_result):
        self.parent = parent
        self.result = download_result
        self.dialog = None
        self._show_dialog()

    def _show_dialog(self):
        """Show the completion dialog."""
        completed = self.result['completed']
        successful = self.result['successful']
        failed_count = len(self.result['failed_ids'])

        if failed_count == 0:
            title = "Download Complete"
            message = f"Successfully downloaded all {successful} mod(s)!"
            icon = "info"
        else:
            title = "Download Complete with Errors"
            message = f"Downloaded {successful} mod(s) successfully.\n{failed_count} mod(s) failed to download."
            icon = "warning"

        if failed_count == 0:
            messagebox.showinfo(title, message)
            return

        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")

        message_label = tk.Label(self.dialog, text=message, font=("Helvetica", 10, "bold"))
        message_label.pack(pady=10)

        if failed_count > 0:
            failed_label = tk.Label(self.dialog, text="Failed Downloads:", font=("Helvetica", 9, "bold"))
            failed_label.pack(anchor="w", padx=20, pady=(10, 5))

            list_frame = tk.Frame(self.dialog)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

            self.failed_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
            scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.failed_listbox.yview)
            self.failed_listbox.config(yscrollcommand=scrollbar.set)

            for failed_mod in self.result['failed_details']:
                mod_id = failed_mod['id']
                title = failed_mod['title']
                reason = failed_mod['reason']
                display_text = f"{mod_id} - {title} ({reason})"
                self.failed_listbox.insert(tk.END, display_text)

            self.failed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        if failed_count > 0:
            copy_button = tk.Button(button_frame, text="Copy Failed Mod IDs", command=self._copy_failed_ids)
            copy_button.pack(side=tk.LEFT)

            copy_details_button = tk.Button(button_frame, text="Copy Failed Mod Details",
                                            command=self._copy_failed_details)
            copy_details_button.pack(side=tk.LEFT, padx=(10, 0))

        close_button = tk.Button(button_frame, text="Close", command=self.dialog.destroy)
        close_button.pack(side=tk.RIGHT)

        self.dialog.bind('<Return>', lambda e: self.dialog.destroy())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())

    def _copy_failed_ids(self):
        """Copy the list of failed mod IDs to clipboard."""
        failed_ids = self.result['failed_ids']
        if failed_ids:
            ids_text = '\n'.join(failed_ids)
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(ids_text)

            messagebox.showinfo("Copied", f"Copied {len(failed_ids)} failed mod IDs to clipboard.")

    def _copy_failed_details(self):
        """Copy the detailed list of failed mods to clipboard."""
        failed_details = self.result['failed_details']
        if failed_details:
            details_lines = []
            for failed_mod in failed_details:
                mod_id = failed_mod['id']
                title = failed_mod['title']
                reason = failed_mod['reason']
                details_lines.append(f"{mod_id} - {title} ({reason})")

            details_text = '\n'.join(details_lines)
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(details_text)

            messagebox.showinfo("Copied", f"Copied {len(failed_details)} failed mod details to clipboard.")
