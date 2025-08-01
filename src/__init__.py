"""
MTG Deck Builder Source Package

This package contains the core modules for the MTG Deck Builder application.
"""

__version__ = "1.0.0"
__author__ = "MTG Deck Builder Team"

# Import key modules for easier access
from .llm_client import chat_prompt, parse_card_suggestions, test_connection
from .scryfall_client import ScryfallClient
from .data_ingest import read_manabox_csv, validate_card_data
from .transformer import extract_card_fields, get_required_fields

__all__ = [
   'chat_prompt',
   'parse_card_suggestions', 
   'test_connection',
   'ScryfallClient',
   'read_manabox_csv',
   'validate_card_data',
   'extract_card_fields',
   'get_required_fields'
] 