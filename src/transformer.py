"""
Data transformer module for MTG deck builder.
Extracts desired fields from Scryfall JSON responses.
"""

import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


def extract_card_fields(card_data: Dict) -> Dict:
   """
   Extract the desired fields from Scryfall card data.
   
   Args:
       card_data: Dictionary containing Scryfall card data
       
   Returns:
       Dictionary with extracted fields
   """
   extracted = {}
   
   try:
       # Basic card information
       extracted['mana_cost'] = card_data.get('mana_cost', '')
       extracted['type_line'] = card_data.get('type_line', '')
       extracted['oracle_text'] = card_data.get('oracle_text', '')
       
       # Power and toughness (for creatures)
       extracted['power'] = card_data.get('power', '')
       extracted['toughness'] = card_data.get('toughness', '')
       
       # Additional useful fields
       extracted['cmc'] = card_data.get('cmc', '')
       extracted['colors'] = ','.join(card_data.get('colors', []))
       extracted['color_identity'] = ','.join(card_data.get('color_identity', []))
       extracted['rarity'] = card_data.get('rarity', '')
       extracted['loyalty'] = card_data.get('loyalty', '')
       
       # Set information
       extracted['set_name'] = card_data.get('set_name', '')
       extracted['collector_number'] = card_data.get('collector_number', '')
       
       # Image URLs
       extracted['image_uris'] = _extract_image_urls(card_data)
       
       logger.debug(f"Extracted fields for card: {card_data.get('name', 'Unknown')}")
       
   except Exception as e:
       logger.error(f"Error extracting fields from card data: {e}")
       # Return empty fields on error
       extracted = {
           'mana_cost': '', 'type_line': '', 'oracle_text': '',
           'power': '', 'toughness': '', 'cmc': '', 'colors': '',
           'color_identity': '', 'rarity': '', 'loyalty': '',
           'set_name': '', 'collector_number': '', 'image_uris': ''
       }
   
   return extracted


def _extract_image_urls(card_data: Dict) -> str:
   """
   Extract image URLs from card data.
   
   Args:
       card_data: Dictionary containing Scryfall card data
       
   Returns:
       Comma-separated string of image URLs
   """
   image_urls = []
   
   # Check for image_uris field
   if 'image_uris' in card_data:
       image_uris = card_data['image_uris']
       if 'normal' in image_uris:
           image_urls.append(image_uris['normal'])
       if 'small' in image_uris:
           image_urls.append(image_uris['small'])
   
   # Check for card_faces (for double-faced cards)
   elif 'card_faces' in card_data:
       for face in card_data['card_faces']:
           if 'image_uris' in face:
               image_uris = face['image_uris']
               if 'normal' in image_uris:
                   image_urls.append(image_uris['normal'])
               if 'small' in image_uris:
                   image_urls.append(image_uris['small'])
   
   return ','.join(image_urls)


def get_required_fields() -> List[str]:
   """
   Get the list of fields that will be extracted from Scryfall data.
   
   Returns:
       List of field names
   """
   return [
       'mana_cost', 'type_line', 'oracle_text', 'power', 'toughness',
       'cmc', 'colors', 'color_identity', 'rarity', 'loyalty',
       'set_name', 'collector_number', 'image_uris'
   ]


def validate_extracted_data(extracted_data: Dict) -> bool:
   """
   Validate that extracted data contains expected fields.
   
   Args:
       extracted_data: Dictionary of extracted card data
       
   Returns:
       True if valid, False otherwise
   """
   required_fields = get_required_fields()
   
   for field in required_fields:
       if field not in extracted_data:
           logger.warning(f"Missing required field: {field}")
           return False
   
   return True 