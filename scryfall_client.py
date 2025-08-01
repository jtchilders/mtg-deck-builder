"""
Scryfall API client for MTG deck builder.
Handles HTTP calls to Scryfall API to fetch card data.
"""

import requests
import logging
import time
from typing import Dict, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

# Scryfall API base URL
SCRYFALL_BASE_URL = "https://api.scryfall.com"


class ScryfallClient:
   """
   Client for interacting with the Scryfall API.
   """
   
   def __init__(self, base_url: str = SCRYFALL_BASE_URL, timeout: int = 30):
       """
       Initialize the Scryfall client.
       
       Args:
           base_url: Base URL for Scryfall API
           timeout: Request timeout in seconds
       """
       self.base_url = base_url
       self.timeout = timeout
       self.session = requests.Session()
       
       # Set user agent to identify our application
       self.session.headers.update({
           'User-Agent': 'MTG-Deck-Builder/1.0 (https://github.com/your-repo)'
       })
   
   def get_card_by_id(self, scryfall_id: str) -> Optional[Dict]:
       """
       Fetch card data by Scryfall ID.
       
       Args:
           scryfall_id: The Scryfall ID of the card
           
       Returns:
           Dictionary containing card data, or None if not found
       """
       url = urljoin(self.base_url, f"/cards/{scryfall_id}")
       
       try:
           logger.debug(f"Fetching card with ID: {scryfall_id}")
           response = self.session.get(url, timeout=self.timeout)
           
           if response.status_code == 200:
               card_data = response.json()
               logger.debug(f"Successfully fetched card: {card_data.get('name', 'Unknown')}")
               return card_data
           elif response.status_code == 404:
               logger.warning(f"Card not found with ID: {scryfall_id}")
               return None
           else:
               logger.error(f"HTTP {response.status_code} error fetching card {scryfall_id}")
               return None
               
       except requests.exceptions.Timeout:
           logger.error(f"Timeout fetching card {scryfall_id}")
           return None
       except requests.exceptions.RequestException as e:
           logger.error(f"Request error fetching card {scryfall_id}: {e}")
           return None
       except Exception as e:
           logger.error(f"Unexpected error fetching card {scryfall_id}: {e}")
           return None
   
   def get_card_by_name(self, card_name: str, set_code: Optional[str] = None) -> Optional[Dict]:
       """
       Fetch card data by name and optionally set code.
       
       Args:
           card_name: The name of the card
           set_code: Optional set code to narrow down the search
           
       Returns:
           Dictionary containing card data, or None if not found
       """
       # Build the search query
       query = f'!"{card_name}"'
       if set_code:
           query += f' set:{set_code}'
       
       url = urljoin(self.base_url, "/cards/search")
       params = {'q': query}
       
       try:
           logger.debug(f"Searching for card: {card_name} (set: {set_code})")
           response = self.session.get(url, params=params, timeout=self.timeout)
           
           if response.status_code == 200:
               data = response.json()
               if data.get('data') and len(data['data']) > 0:
                   card_data = data['data'][0]  # Take the first match
                   logger.debug(f"Successfully found card: {card_data.get('name', 'Unknown')}")
                   return card_data
               else:
                   logger.warning(f"No cards found for: {card_name}")
                   return None
           elif response.status_code == 404:
               logger.warning(f"No cards found for: {card_name}")
               return None
           else:
               logger.error(f"HTTP {response.status_code} error searching for card {card_name}")
               return None
               
       except requests.exceptions.Timeout:
           logger.error(f"Timeout searching for card {card_name}")
           return None
       except requests.exceptions.RequestException as e:
           logger.error(f"Request error searching for card {card_name}: {e}")
           return None
       except Exception as e:
           logger.error(f"Unexpected error searching for card {card_name}: {e}")
           return None
   
   def close(self):
       """Close the session."""
       self.session.close()
   
   def __enter__(self):
       return self
   
   def __exit__(self, exc_type, exc_val, exc_tb):
       self.close() 