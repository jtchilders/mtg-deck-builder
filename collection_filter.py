#!/usr/bin/env python3
"""
Collection Filter Utility
Filter and explore your MTG collection by various criteria.
"""

import pandas as pd
import argparse
import logging
from typing import List, Optional
from deck_builder import load_collection, print_card_details

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def filter_by_color(df: pd.DataFrame, colors: List[str]) -> pd.DataFrame:
   """Filter cards by color"""
   if not colors:
      return df
   
   # Create a mask for each color
   mask = pd.Series([False] * len(df), index=df.index)
   for color in colors:
      mask |= df['colors'].str.contains(color, na=False)
   
   return df[mask]

def filter_by_cmc(df: pd.DataFrame, min_cmc: Optional[float] = None, max_cmc: Optional[float] = None) -> pd.DataFrame:
   """Filter cards by converted mana cost"""
   if min_cmc is not None:
      df = df[df['cmc'] >= min_cmc]
   if max_cmc is not None:
      df = df[df['cmc'] <= max_cmc]
   return df

def filter_by_type(df: pd.DataFrame, card_types: List[str]) -> pd.DataFrame:
   """Filter cards by type"""
   if not card_types:
      return df
   
   mask = pd.Series([False] * len(df), index=df.index)
   for card_type in card_types:
      mask |= df['type_line'].str.contains(card_type, case=False, na=False)
   
   return df[mask]

def filter_by_rarity(df: pd.DataFrame, rarities: List[str]) -> pd.DataFrame:
   """Filter cards by rarity"""
   if not rarities:
      return df
   
   return df[df['rarity'].isin(rarities)]

def filter_by_set(df: pd.DataFrame, sets: List[str]) -> pd.DataFrame:
   """Filter cards by set"""
   if not sets:
      return df
   
   mask = pd.Series([False] * len(df), index=df.index)
   for set_name in sets:
      mask |= df['set_name'].str.contains(set_name, case=False, na=False)
   
   return df[mask]

def search_by_name(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
   """Search cards by name"""
   if not search_term:
      return df
   
   return df[df['Name'].str.contains(search_term, case=False, na=False)]

def print_results(df: pd.DataFrame, limit: int = 20, show_details: bool = False):
   """Print filtered results"""
   if df.empty:
      print("No cards found matching the criteria.")
      return
   
   print(f"\nFound {len(df)} cards:")
   print("=" * 60)
   
   # Sort by name for consistent output
   df_sorted = df.sort_values('Name')
   
   for i, (_, card) in enumerate(df_sorted.head(limit).iterrows(), 1):
      if show_details:
         print_card_details(card['Name'], df)
      else:
         mana_cost = card.get('mana_cost', '')
         type_line = card.get('type_line', '')
         cmc = card.get('cmc', '')
         print(f"{i:2d}. {card['Name']} ({mana_cost}) - {type_line} [CMC: {cmc}]")
   
   if len(df) > limit:
      print(f"\n... and {len(df) - limit} more cards")

def main():
   """Main function for command-line usage"""
   parser = argparse.ArgumentParser(description='Filter and explore your MTG collection')
   parser.add_argument('--collection', type=str, default='enriched.csv',
                      help='Path to enriched collection CSV (default: enriched.csv)')
   parser.add_argument('--colors', '-c', nargs='+', choices=['W', 'U', 'B', 'R', 'G'],
                      help='Filter by colors')
   parser.add_argument('--cmc-min', type=float, help='Minimum CMC')
   parser.add_argument('--cmc-max', type=float, help='Maximum CMC')
   parser.add_argument('--types', '-t', nargs='+', 
                      choices=['Creature', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Planeswalker', 'Land'],
                      help='Filter by card types')
   parser.add_argument('--rarities', '-r', nargs='+', 
                      choices=['common', 'uncommon', 'rare', 'mythic'],
                      help='Filter by rarities')
   parser.add_argument('--sets', '-s', nargs='+', help='Filter by set names')
   parser.add_argument('--search', type=str, help='Search by card name')
   parser.add_argument('--limit', '-l', type=int, default=20, help='Maximum number of results to show')
   parser.add_argument('--details', '-d', action='store_true', help='Show detailed card information')
   parser.add_argument('--stats', action='store_true', help='Show collection statistics')
   
   args = parser.parse_args()
   
   try:
      # Load collection
      df = load_collection(args.collection)
      
      # Apply filters
      filtered_df = df.copy()
      
      if args.colors:
         filtered_df = filter_by_color(filtered_df, args.colors)
      
      if args.cmc_min is not None or args.cmc_max is not None:
         filtered_df = filter_by_cmc(filtered_df, args.cmc_min, args.cmc_max)
      
      if args.types:
         filtered_df = filter_by_type(filtered_df, args.types)
      
      if args.rarities:
         filtered_df = filter_by_rarity(filtered_df, args.rarities)
      
      if args.sets:
         filtered_df = filter_by_set(filtered_df, args.sets)
      
      if args.search:
         filtered_df = search_by_name(filtered_df, args.search)
      
      # Show statistics if requested
      if args.stats:
         print("Collection Statistics:")
         print("=" * 40)
         print(f"Total cards: {len(df)}")
         print(f"Creatures: {len(df[df['type_line'].str.contains('Creature', na=False)])}")
         print(f"Instants: {len(df[df['type_line'].str.contains('Instant', na=False)])}")
         print(f"Sorceries: {len(df[df['type_line'].str.contains('Sorcery', na=False)])}")
         print(f"Enchantments: {len(df[df['type_line'].str.contains('Enchantment', na=False)])}")
         print(f"Artifacts: {len(df[df['type_line'].str.contains('Artifact', na=False)])}")
         print(f"Lands: {len(df[df['type_line'].str.contains('Land', na=False)])}")
         
         print(f"\nBy color:")
         for color in ['W', 'U', 'B', 'R', 'G']:
            count = len(df[df['colors'].str.contains(color, na=False)])
            print(f"  {color}: {count}")
         
         print(f"\nBy CMC:")
         for cmc in range(0, 8):
            count = len(df[df['cmc'] == cmc])
            print(f"  {cmc}: {count}")
      
      # Print results
      print_results(filtered_df, args.limit, args.details)
      
   except Exception as e:
      logger.error(f"Error: {str(e)}")
      print(f"Error: {str(e)}")

if __name__ == "__main__":
   main() 