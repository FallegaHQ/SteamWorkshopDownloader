import html
import re

import requests
from bs4 import BeautifulSoup, FeatureNotFound

import config


class SteamAPI:
    """Handles communication with Steam API and workshop page scraping."""

    @staticmethod
    def fetch_mod_info(mod_id):
        """Fetch title, app_id & other details from Steam API and scrape page for dependencies."""
        try:

            response = requests.post(config.STEAM_API_URL, data={"itemcount": 1, "publishedfileids[0]": mod_id}, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("response", {}).get("publishedfiledetails"):
                return {"title": f"Mod {mod_id}", "error": "No details in API response."}

            details = data["response"]["publishedfiledetails"][0]

            if details.get("result") != 1:
                return {"title": f"Mod {mod_id}", "error": f"API result not OK (result code: {details.get('result')})"}

            dependencies = []
            workshop_url = f"https://steamcommunity.com/workshop/filedetails/?id={mod_id}"
            try:
                page_response = requests.get(workshop_url, timeout=10)
                page_response.raise_for_status()
                try:

                    soup = BeautifulSoup(page_response.text, 'lxml')
                except FeatureNotFound:

                    print(
                        "Warning: 'lxml' parser not found. Falling back to 'html.parser'. For better performance, run: pip install lxml")
                    soup = BeautifulSoup(page_response.text, 'html.parser')

                required_items_div = soup.find('div', id='RequiredItems')
                if required_items_div:
                    for link in required_items_div.find_all('a'):
                        href = link.get('href')
                        if href and (match := re.search(r"id=(\d+)", href)):
                            dependencies.append(match.group(1))
            except Exception as scrape_error:

                print(f"Warning: Could not scrape dependencies for {mod_id}: {scrape_error}")

            description = details.get("description", "")
            if description:
                description = html.unescape(description)

            return {"title": details.get("title", "Unknown"), "app_id": details.get("consumer_app_id"),
                    "preview_url": details.get("preview_url", ""), "file_size": details.get("file_size", 0),
                    "description": description, "dependencies": dependencies, }
        except requests.exceptions.RequestException as e:
            return {"title": f"Mod {mod_id}", "error": f"Network error: {e}"}
        except Exception as e:
            return {"title": f"Mod {mod_id}", "error": str(e)}

    @staticmethod
    def fetch_mod_description(mod_id):
        """Fetch only the description for a mod using the Steam API."""
        try:
            response = requests.post(config.STEAM_API_URL, data={"itemcount": 1, "publishedfileids[0]": mod_id}, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("response", {}).get("publishedfiledetails"):
                details = data["response"]["publishedfiledetails"][0]
                if details.get("result") == 1:
                    description = details.get("description", "")
                    if description:
                        return html.unescape(description)
            return None
        except Exception as e:
            print(f"Warning: Could not fetch description for {mod_id}: {e}")
            return None
