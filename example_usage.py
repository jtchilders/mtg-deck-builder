#!/usr/bin/env python3
"""
Example usage of the MTG Deck Builder
This script demonstrates how to use the deck builder programmatically.
"""

import pandas as pd
from deck_builder import load_collection, get_card_details, print_card_details

def main():
   """Demonstrate basic deck builder functionality"""
   print("MTG Deck Builder - Example Usage")
   print("=" * 40)
   
   # Load the collection
   try:
      df = load_collection()
      print(f"✓ Loaded {len(df)} cards from collection")
   except Exception as e:
      print(f"✗ Failed to load collection: {e}")
      return
   
   # Example 1: Find cards by name
   print("\n1. Finding specific cards:")
   test_cards = ["Paladin Class", "Kitesail Cleric", "Speaker of the Heavens"]
   
   for card_name in test_cards:
      details = get_card_details(card_name, df)
      if details:
         print(f"✓ Found: {details['name']} ({details['mana_cost']}) - {details['type_line']}")
      else:
         print(f"✗ Not found: {card_name}")
   
   # Example 2: Show detailed card information
   print("\n2. Detailed card information:")
   if test_cards:
      print_card_details(test_cards[0], df)
   
   # Example 3: Find cards by type
   print("\n3. Finding all Cleric creatures:")
   clerics = df[
      (df['type_line'].str.contains('Cleric', na=False)) & 
      (df['type_line'].str.contains('Creature', na=False))
   ]
   print(f"Found {len(clerics)} Cleric creatures:")
   for _, card in clerics.head(5).iterrows():
      print(f"  • {card['Name']} ({card['mana_cost']})")
   
   # Example 4: Find cards by CMC
   print("\n4. Finding 1-mana white cards:")
   one_mana_white = df[
      (df['cmc'] == 1.0) & 
      (df['colors'].str.contains('W', na=False))
   ]
   print(f"Found {len(one_mana_white)} 1-mana white cards:")
   for _, card in one_mana_white.head(5).iterrows():
      print(f"  • {card['Name']} ({card['mana_cost']}) - {card['type_line']}")
   
   # Example 5: Find cards by rarity
   print("\n5. Finding rare cards:")
   rares = df[df['rarity'] == 'rare']
   print(f"Found {len(rares)} rare cards:")
   for _, card in rares.head(5).iterrows():
      print(f"  • {card['Name']} ({card['mana_cost']}) - {card['set_name']}")
   
   print("\n" + "=" * 40)
   print("Example completed! To use LLM features:")
   print("1. Add your OpenAI API key to config.json")
   print("2. Run: python deck_builder.py --seeds 'Paladin Class' 'Kitesail Cleric'")

if __name__ == "__main__":
   main() 