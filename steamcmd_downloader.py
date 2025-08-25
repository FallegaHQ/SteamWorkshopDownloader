import os
import re
import subprocess
import threading
import time
from typing import List, Dict, Callable, Optional

from config import STEAMCMD_PATH


class SteamCMDDownloader:
    """Handles SteamCMD download operations with improved threading and error handling."""

    def __init__(self, steamcmd_path: str = STEAMCMD_PATH):
        self.steamcmd_path = steamcmd_path
        self._stop_requested = False

    def download_mods(self, mods: List[Dict], progress_callback: Optional[Callable] = None,
                      log_callback: Optional[Callable] = None, status_callback: Optional[Callable] = None) -> Dict:
        """
        Download multiple mods using SteamCMD with improved error handling.

        Args:
            mods: List of mod dictionaries containing 'id' and 'info' with 'app_id'
            progress_callback: Called with (current, total) progress
            log_callback: Called with log messages
            status_callback: Called with status updates

        Returns:
            Dict with 'completed', 'successful', 'failed_ids', and 'failed_details' keys
        """
        if not mods:
            return {'completed': 0, 'successful': 0, 'failed_ids': [], 'failed_details': []}

        self._stop_requested = False

        if not self.is_steamcmd_available():
            error_msg = f"SteamCMD not found at '{self.steamcmd_path}'"
            if log_callback:
                log_callback(error_msg + "\n")
            if status_callback:
                status_callback(error_msg)
            return {'completed': 0, 'successful': 0, 'failed_ids': [], 'failed_details': []}

        valid_mods = []
        failed_ids = []
        failed_details = []

        for mod in mods:
            app_id = mod.get("info", {}).get("app_id")
            if not app_id:
                failed_id = mod['id']
                failed_title = mod.get('info', {}).get('title', failed_id)
                failed_ids.append(failed_id)
                failed_details.append({'id': failed_id, 'title': failed_title, 'reason': 'No App ID found'})
                if log_callback:
                    log_callback(f"Could not find App ID for mod {failed_id}. Skipping.\n")
                continue
            valid_mods.append(mod)

        if not valid_mods:
            if log_callback:
                log_callback("No valid mods to download.\n")
            return {'completed': len(failed_ids), 'successful': 0, 'failed_ids': failed_ids,
                    'failed_details': failed_details}

        if status_callback:
            status_callback("Starting batch download...")
        if log_callback:
            log_callback(f"--- Starting batch download for {len(valid_mods)} mod(s) ---\n")

        command = [self.steamcmd_path, "+login", "anonymous"]

        for mod in valid_mods:
            app_id = mod["info"]["app_id"]
            mod_id = mod["id"]
            title = mod["info"].get('title', mod_id)
            if log_callback:
                log_callback(f"Queuing: {title} ({mod_id})\n")
            command.extend(["+workshop_download_item", str(app_id), mod_id])

        command.append("+quit")

        try:

            result = self._execute_steamcmd_with_monitoring(command, valid_mods, progress_callback, log_callback,
                                                            status_callback)

            result['failed_ids'].extend(failed_ids)
            result['failed_details'].extend(failed_details)
            result['completed'] += len(failed_ids)

            return result

        except FileNotFoundError:
            error_msg = f"Error: '{self.steamcmd_path}' not found. Please check the path."
            if log_callback:
                log_callback(error_msg + "\n")
            if status_callback:
                status_callback(error_msg)
            return {'completed': 0, 'successful': 0, 'failed_ids': failed_ids, 'failed_details': failed_details}
        except Exception as e:
            error_msg = f"Unexpected error during download: {e}"
            if log_callback:
                log_callback(error_msg + "\n")
            if status_callback:
                status_callback(error_msg)
            return {'completed': 0, 'successful': 0, 'failed_ids': failed_ids, 'failed_details': failed_details}

    def _execute_steamcmd_with_monitoring(self, command, valid_mods, progress_callback, log_callback, status_callback):
        """Execute SteamCMD with improved monitoring and timeout handling."""

        failed_ids = []
        failed_details = []

        try:

            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            if log_callback:
                log_callback(f"Executing command: {' '.join(command[:5])}... [truncated]\n")

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                       encoding='utf-8', errors='replace', creationflags=flags, bufsize=1,
                                       universal_newlines=True)

            completed_downloads = 0
            successful_downloads = 0
            current_mod_info = None
            last_activity = time.time()
            timeout_seconds = 300

            download_patterns = {'start': re.compile(r'downloading item (\d+)', re.IGNORECASE),
                                 'success': re.compile(r'success\.', re.IGNORECASE),
                                 'error': re.compile(r'error|failed|timeout', re.IGNORECASE),
                                 'progress': re.compile(r'(\d+)%', re.IGNORECASE),
                                 'downloading': re.compile(r'downloading', re.IGNORECASE),
                                 'login': re.compile(r'logged in OK', re.IGNORECASE),
                                 'workshop': re.compile(r'workshop', re.IGNORECASE)}

            mods_by_id = {mod['id']: mod for mod in valid_mods}

            if progress_callback:
                progress_callback(0, len(valid_mods))

            output_lines = []
            process_finished = False

            def read_output():
                """Read output in a separate thread to prevent blocking."""
                try:
                    for line in iter(process.stdout.readline, ''):
                        if not line:
                            break
                        output_lines.append(line)
                        if len(output_lines) > 1000:
                            output_lines.pop(0)
                except Exception as e:
                    if log_callback:
                        log_callback(f"Error reading output: {e}\n")

            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()

            processed_lines = 0
            startup_grace_period = 30
            startup_time = time.time()

            while process.poll() is None and not self._stop_requested:
                current_time = time.time()

                while processed_lines < len(output_lines):
                    line = output_lines[processed_lines]
                    processed_lines += 1
                    last_activity = current_time

                    if "-- type 'quit' to exit --" not in line.lower():
                        if log_callback:
                            log_callback(line)

                    if any(pattern.search(line) for pattern in download_patterns.values()):
                        last_activity = current_time

                    start_match = download_patterns['start'].search(line)
                    if start_match:
                        downloading_id = start_match.group(1)
                        if downloading_id in mods_by_id:
                            current_mod_info = mods_by_id[downloading_id]
                            title = current_mod_info["info"].get('title', downloading_id)
                            if status_callback:
                                status_callback(f"Downloading: {title}")
                            if log_callback:
                                log_callback(f"--- Starting download: {title} ({downloading_id}) ---\n")

                    if current_mod_info:
                        is_success = download_patterns['success'].search(line)
                        is_error = download_patterns['error'].search(line)

                        if is_success or is_error:
                            completed_downloads += 1
                            title = current_mod_info["info"].get('title', current_mod_info["id"])
                            mod_id = current_mod_info["id"]

                            if is_success:
                                successful_downloads += 1
                                if status_callback:
                                    status_callback(f"Downloaded: {title}")
                                if log_callback:
                                    log_callback(f"--- Successfully downloaded {title} ---\n")
                            else:
                                failed_ids.append(mod_id)
                                failed_details.append({'id': mod_id, 'title': title, 'reason': 'Download failed'})
                                if status_callback:
                                    status_callback(f"Failed to download: {title}")
                                if log_callback:
                                    log_callback(f"--- Failed to download {title} ---\n")

                            if progress_callback:
                                progress_callback(completed_downloads, len(valid_mods))

                            current_mod_info = None


                    elif not current_mod_info and (
                            download_patterns['success'].search(line) or download_patterns['error'].search(line)):

                        if completed_downloads < len(valid_mods):
                            completed_downloads += 1

                            successful_downloads += 1
                            if progress_callback:
                                progress_callback(completed_downloads, len(valid_mods))

                if current_time - startup_time > startup_grace_period:
                    if current_time - last_activity > timeout_seconds:
                        if log_callback:
                            log_callback("--- Timeout: No activity detected for 5 minutes, terminating process ---\n")
                        if status_callback:
                            status_callback("Download timeout - terminating process")
                        try:
                            process.terminate()
                            process.wait(timeout=10)
                        except:
                            try:
                                process.kill()
                            except:
                                pass
                        break

                time.sleep(0.02)

            output_thread.join(timeout=5)

            while processed_lines < len(output_lines):
                line = output_lines[processed_lines]
                processed_lines += 1
                if log_callback and "-- type 'quit' to exit --" not in line.lower():
                    log_callback(line)

            try:
                return_code = process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                if log_callback:
                    log_callback("--- Process did not terminate gracefully, forcing termination ---\n")
                try:
                    process.kill()
                    return_code = process.wait(timeout=10)
                except:
                    return_code = -1

            if completed_downloads < len(valid_mods):
                if log_callback:
                    log_callback(
                        f"--- Adjusting completion count from {completed_downloads} to {len(valid_mods)} ---\n")

                remaining = len(valid_mods) - completed_downloads
                successful_downloads += remaining
                completed_downloads = len(valid_mods)
                if progress_callback:
                    progress_callback(completed_downloads, len(valid_mods))

            if return_code == 0:
                if log_callback:
                    log_callback("--- Batch download completed successfully ---\n")
                if status_callback:
                    status_callback("Batch download completed")
            else:
                if log_callback:
                    log_callback(f"--- Batch download completed with errors (exit code: {return_code}) ---\n")
                if status_callback:
                    status_callback("Batch download completed with errors")

            return {'completed': completed_downloads, 'successful': successful_downloads, 'failed_ids': failed_ids,
                    'failed_details': failed_details}

        except Exception as e:
            error_msg = f"Error during SteamCMD execution: {e}"
            if log_callback:
                log_callback(error_msg + "\n")
            if status_callback:
                status_callback(error_msg)
            return {'completed': 0, 'successful': 0, 'failed_ids': failed_ids, 'failed_details': failed_details}

    def stop_download(self):
        """Request to stop the current download."""
        self._stop_requested = True

    def is_steamcmd_available(self) -> bool:
        """Check if SteamCMD is available at the specified path."""
        return os.path.exists(self.steamcmd_path)
