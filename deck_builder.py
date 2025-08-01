import pandas as pd
import logging
import argparse
from typing import List, Dict, Optional
from src.llm_client import chat_prompt, parse_card_suggestions, parse_card_pairs, parse_card_triplets

# Set up logging (will be configured in main())
logger = logging.getLogger(__name__)

def load_collection(path: str = "enriched.csv") -> pd.DataFrame:
   """
   Load the enriched collection from CSV
   
   Args:
      path: Path to the enriched CSV file
   
   Returns:
      DataFrame containing the enriched collection
   """
   try:
      df = pd.read_csv(path)
      logger.info(f"Loaded {len(df)} cards from {path}")
      return df
   except FileNotFoundError:
      logger.error(f"Collection file not found: {path}")
      raise

def suggest_complements(seed_names: List[str], df: pd.DataFrame, n: int = 8, model: str = 'gpt-4o-mini', temperature: float = 0.7) -> List[str]:
   """
   Suggest complementary cards using LLM
   
   Args:
      seed_names: List of card names to build around
      df: DataFrame containing the collection
      n: Number of suggestions to request
   
   Returns:
      List of suggested card names
   """
   # 1) Gather oracle text snippets for seed cards
   seeds = []
   for name in seed_names:
      # Find the card in the collection (case-insensitive)
      matches = df[df['Name'].str.lower() == name.lower()]
      if matches.empty:
         logger.warning(f"Card not found in collection: {name}")
         continue
      
      row = matches.iloc[0]
      oracle_text = row.get('oracle_text', 'No oracle text available')
      mana_cost = row.get('mana_cost', '')
      type_line = row.get('type_line', '')
      
      # Create a comprehensive card description
      card_desc = f"{name}"
      if mana_cost:
         card_desc += f" ({mana_cost})"
      if type_line:
         card_desc += f" — {type_line}"
      card_desc += f": {oracle_text}"
      
      seeds.append(card_desc)
   
   if not seeds:
      logger.error("No valid seed cards found in collection")
      return []
   
   # 2) Get a sample of cards from the collection to suggest from
   # Filter to white cards and creatures/instants/sorceries that might work well
   white_cards = df[df['colors'].str.contains('W', na=False)]
   potential_cards = white_cards[
      (white_cards['type_line'].str.contains('Creature', na=False)) |
      (white_cards['type_line'].str.contains('Instant', na=False)) |
      (white_cards['type_line'].str.contains('Sorcery', na=False)) |
      (white_cards['type_line'].str.contains('Enchantment', na=False))
   ]
   
   # Get a sample of cards (up to 50) to suggest from
   sample_cards = potential_cards.sample(min(50, len(potential_cards)))[['Name', 'mana_cost', 'type_line', 'oracle_text']]
   
   # 3) Build prompt with available cards
   available_cards_text = "\n".join([
      f"• {row['Name']} ({row['mana_cost']}) — {row['type_line']}: {str(row['oracle_text'])[:100]}..."
      for _, row in sample_cards.iterrows()
   ])
   
   messages = [
      {"role": "system", "content": 
         "You are an expert Magic: the Gathering deck-builder. Given a partial decklist or a list of seed cards, "
         "you will suggest cards that synergize with them to form a coherent strategy. "
         "IMPORTANT: You must ONLY suggest cards from the provided list of available cards."
      },
      {"role": "user", "content":
         f"I'm building around these cards:\n" + "\n".join(f"• {s}" for s in seeds) +
         f"\n\nAvailable cards in my collection:\n{available_cards_text}\n\n"
         f"Suggest {n} cards from the available list that complement the seed cards. "
         f"For each suggestion, provide:\n"
         f"1. The exact card name (must match one from the available list)\n"
         f"2. A brief one-sentence rationale explaining why it works well with the seed cards\n\n"
         f"Format your response as a numbered list with each card name followed by a dash and the rationale."
      },
   ]
   
   # 3) Call LLM
   try:
      response = chat_prompt(messages, model=model, temperature=temperature)
      logger.info("Received suggestions from LLM")
      
      # 4) Parse numbered list of names
      suggestions = parse_card_suggestions(response)
      logger.info(f"Parsed {len(suggestions)} card suggestions")
      
      return suggestions
   except Exception as e:
      logger.error(f"Failed to get suggestions: {str(e)}")
      return []

def find_synergistic_pairs(df: pd.DataFrame, n_pairs: int = 5, model: str = 'gpt-4o-mini', temperature: float = 0.7) -> List[List[str]]:
   """
   Find synergistic card pairs using LLM
   
   Args:
      df: DataFrame containing the collection
      n_pairs: Number of pairs to find
   
   Returns:
      List of card pairs (each pair is a list of 2 card names)
   """
   # Get a sample of cards from the collection to work with
   # Focus on creatures, instants, sorceries, and enchantments
   potential_cards = df[
      (df['type_line'].str.contains('Creature', na=False)) |
      (df['type_line'].str.contains('Instant', na=False)) |
      (df['type_line'].str.contains('Sorcery', na=False)) |
      (df['type_line'].str.contains('Enchantment', na=False))
   ]
   
   # Get a sample of cards (up to 100) to work with
   sample_cards = potential_cards.sample(min(100, len(potential_cards)))[['Name', 'mana_cost', 'type_line', 'oracle_text', 'colors']]
   
   # Build prompt with available cards
   available_cards_text = "\n".join([
      f"• {row['Name']} ({row['mana_cost']}) — {row['type_line']} [{row['colors']}]: {str(row['oracle_text'])[:80]}..."
      for _, row in sample_cards.iterrows()
   ])
   
   messages = [
      {"role": "system", "content": 
         "You are an expert Magic: the Gathering deck-builder. You will find synergistic card pairs "
         "that work exceptionally well together. Look for cards that have strong interactions, "
         "combo potential, or synergistic abilities. IMPORTANT: You must ONLY suggest cards from the provided list."
      },
      {"role": "user", "content":
         f"Available cards in my collection:\n{available_cards_text}\n\n"
         f"Find {n_pairs} synergistic card pairs from the available list. "
         f"For each pair, provide:\n"
         f"1. The exact card names (must match ones from the available list)\n"
         f"2. A brief explanation of how they synergize together\n\n"
         f"Format your response as a numbered list with each pair followed by the synergy explanation. "
         f"Example format:\n"
         f"1. Card A + Card B - Explanation of synergy\n"
         f"2. Card C + Card D - Explanation of synergy"
      },
   ]
   
   try:
      response = chat_prompt(messages, model=model, temperature=temperature)
      logger.info("Received synergistic pairs from LLM")
      
      # Parse the response to extract pairs
      pairs = parse_card_pairs(response)
      logger.info(f"Parsed {len(pairs)} card pairs")
      
      return pairs
   except Exception as e:
      logger.error(f"Failed to get synergistic pairs: {str(e)}")
      return []

def find_synergistic_triplets(df: pd.DataFrame, n_triplets: int = 3, model: str = 'gpt-4o-mini', temperature: float = 0.7) -> List[List[str]]:
   """
   Find synergistic card triplets using LLM
   
   Args:
      df: DataFrame containing the collection
      n_triplets: Number of triplets to find
   
   Returns:
      List of card triplets (each triplet is a list of 3 card names)
   """
   # Get a sample of cards from the collection to work with
   # Focus on creatures, instants, sorceries, and enchantments
   potential_cards = df[
      (df['type_line'].str.contains('Creature', na=False)) |
      (df['type_line'].str.contains('Instant', na=False)) |
      (df['type_line'].str.contains('Sorcery', na=False)) |
      (df['type_line'].str.contains('Enchantment', na=False))
   ]
   
   # Get a sample of cards (up to 100) to work with
   sample_cards = potential_cards.sample(min(100, len(potential_cards)))[['Name', 'mana_cost', 'type_line', 'oracle_text', 'colors']]
   
   # Build prompt with available cards
   available_cards_text = "\n".join([
      f"• {row['Name']} ({row['mana_cost']}) — {row['type_line']} [{row['colors']}]: {str(row['oracle_text'])[:80]}..."
      for _, row in sample_cards.iterrows()
   ])
   
   messages = [
      {"role": "system", "content": 
         "You are an expert Magic: the Gathering deck-builder. You will find synergistic card triplets "
         "that work exceptionally well together. Look for three cards that form a powerful combination, "
         "combo, or synergistic engine. IMPORTANT: You must ONLY suggest cards from the provided list."
      },
      {"role": "user", "content":
         f"Available cards in my collection:\n{available_cards_text}\n\n"
         f"Find {n_triplets} synergistic card triplets from the available list. "
         f"For each triplet, provide:\n"
         f"1. The exact card names (must match ones from the available list)\n"
         f"2. A brief explanation of how they synergize together\n\n"
         f"Format your response as a numbered list with each triplet followed by the synergy explanation. "
         f"Example format:\n"
         f"1. Card A + Card B + Card C - Explanation of synergy\n"
         f"2. Card D + Card E + Card F - Explanation of synergy"
      },
   ]
   
   try:
      response = chat_prompt(messages, model=model, temperature=temperature)
      logger.info("Received synergistic triplets from LLM")
      
      # Parse the response to extract triplets
      triplets = parse_card_triplets(response)
      logger.info(f"Parsed {len(triplets)} card triplets")
      
      return triplets
   except Exception as e:
      logger.error(f"Failed to get synergistic triplets: {str(e)}")
      return []

def filter_by_collection(names: List[str], df: pd.DataFrame) -> List[str]:
   """
   Filter card names to only those in the collection
   
   Args:
      names: List of card names to filter
      df: DataFrame containing the collection
   
   Returns:
      List of card names that exist in the collection
   """
   collection_names = set(df['Name'].str.lower())
   filtered = []
   
   for name in names:
      if name.lower() in collection_names:
         # Find the exact case from the collection
         exact_match = df[df['Name'].str.lower() == name.lower()]['Name'].iloc[0]
         filtered.append(exact_match)
      else:
         logger.warning(f"Card not in collection: {name}")
   
   return filtered

def filter_pairs_by_collection(pairs: List[tuple], df: pd.DataFrame) -> List[tuple]:
   """
   Filter card pairs to only those where all cards are in the collection
   
   Args:
      pairs: List of tuples (card_pair, explanation) where card_pair is a list of 2 card names
      df: DataFrame containing the collection
   
   Returns:
      List of tuples (card_pair, explanation) where all cards exist in the collection
   """
   collection_names = set(df['Name'].str.lower())
   filtered_pairs = []
   
   for pair_tuple in pairs:
      pair, explanation = pair_tuple
      if len(pair) == 2:
         card1, card2 = pair
         if (card1.lower() in collection_names and card2.lower() in collection_names):
            # Find the exact case from the collection
            exact_card1 = df[df['Name'].str.lower() == card1.lower()]['Name'].iloc[0]
            exact_card2 = df[df['Name'].str.lower() == card2.lower()]['Name'].iloc[0]
            filtered_pairs.append(([exact_card1, exact_card2], explanation))
         else:
            logger.warning(f"Pair not fully in collection: {card1} + {card2}")
   
   return filtered_pairs

def filter_triplets_by_collection(triplets: List[tuple], df: pd.DataFrame) -> List[tuple]:
   """
   Filter card triplets to only those where all cards are in the collection
   
   Args:
      triplets: List of tuples (card_triplet, explanation) where card_triplet is a list of 3 card names
      df: DataFrame containing the collection
   
   Returns:
      List of tuples (card_triplet, explanation) where all cards exist in the collection
   """
   collection_names = set(df['Name'].str.lower())
   filtered_triplets = []
   
   for triplet_tuple in triplets:
      triplet, explanation = triplet_tuple
      if len(triplet) == 3:
         card1, card2, card3 = triplet
         if (card1.lower() in collection_names and 
             card2.lower() in collection_names and 
             card3.lower() in collection_names):
            # Find the exact case from the collection
            exact_card1 = df[df['Name'].str.lower() == card1.lower()]['Name'].iloc[0]
            exact_card2 = df[df['Name'].str.lower() == card2.lower()]['Name'].iloc[0]
            exact_card3 = df[df['Name'].str.lower() == card3.lower()]['Name'].iloc[0]
            filtered_triplets.append(([exact_card1, exact_card2, exact_card3], explanation))
         else:
            logger.warning(f"Triplet not fully in collection: {card1} + {card2} + {card3}")
   
   return filtered_triplets

def get_card_details(card_name: str, df: pd.DataFrame) -> Optional[Dict]:
   """
   Get detailed information about a card
   
   Args:
      card_name: Name of the card
      df: DataFrame containing the collection
   
   Returns:
      Dictionary with card details or None if not found
   """
   matches = df[df['Name'].str.lower() == card_name.lower()]
   if matches.empty:
      return None
   
   row = matches.iloc[0]
   return {
      'name': row['Name'],
      'mana_cost': row.get('mana_cost', ''),
      'type_line': row.get('type_line', ''),
      'oracle_text': row.get('oracle_text', ''),
      'power': row.get('power', ''),
      'toughness': row.get('toughness', ''),
      'cmc': row.get('cmc', ''),
      'colors': row.get('colors', ''),
      'rarity': row.get('rarity', ''),
      'set_name': row.get('set_name', ''),
      'quantity': row.get('Quantity', 1)
   }

def print_card_details(card_name: str, df: pd.DataFrame):
   """
   Print formatted card details
   
   Args:
      card_name: Name of the card
      df: DataFrame containing the collection
   """
   details = get_card_details(card_name, df)
   if not details:
      print(f"Card not found: {card_name}")
      return
   
   print(f"\n{details['name']}")
   print(f"Mana Cost: {details['mana_cost']}")
   print(f"Type: {details['type_line']}")
   print(f"CMC: {details['cmc']}")
   print(f"Colors: {details['colors']}")
   print(f"Rarity: {details['rarity']}")
   print(f"Set: {details['set_name']}")
   print(f"Quantity: {details['quantity']}")
   print(f"Text: {details['oracle_text']}")
   if details['power'] and details['toughness']:
      print(f"Power/Toughness: {details['power']}/{details['toughness']}")

def main():
   """Main function for command-line usage"""
   parser = argparse.ArgumentParser(
       description='MTG Deck Builder - Suggest complementary cards and find synergies',
       formatter_class=argparse.RawDescriptionHelpFormatter,
       epilog="""
Examples:
  python deck_builder.py --seeds "Paladin Class" "Kitesail Cleric" --count 10
  python deck_builder.py --pairs 5 --details
  python deck_builder.py --triplets 3 -v --openai-temperature 0.8
       """
   )
   parser.add_argument('--seeds', '-s', nargs='+',
                      help='Seed card names to build around')
   parser.add_argument('--count', '-c', type=int, default=8,
                      help='Number of suggestions to request (default: 8)')
   parser.add_argument('--collection', type=str, default='enriched.csv',
                      help='Path to enriched collection CSV (default: enriched.csv)')
   parser.add_argument('--details', '-d', action='store_true',
                      help='Show detailed information for suggested cards')
   parser.add_argument('--pairs', '-p', type=int, metavar='N',
                      help='Find N synergistic card pairs')
   parser.add_argument('--triplets', '-t', type=int, metavar='N',
                      help='Find N synergistic card triplets')
   parser.add_argument('-v', '--verbose',
                      action='store_true',
                      help='Enable verbose (DEBUG) logging')
   parser.add_argument('--openai-model',
                      default='gpt-4o-mini',
                      help='OpenAI model to use (default: gpt-4o-mini)')
   parser.add_argument('--openai-temperature',
                      type=float,
                      default=0.7,
                      help='OpenAI temperature setting (default: 0.7)')
   
   args = parser.parse_args()
   
   # Set up logging based on verbose flag
   log_level = 'DEBUG' if args.verbose else 'INFO'
   logging.basicConfig(
       level=getattr(logging, log_level),
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       datefmt='%d-%m %H:%M'
   )
   
   # Check that at least one mode is specified
   if not args.seeds and not args.pairs and not args.triplets:
      parser.error("Must specify either --seeds, --pairs, or --triplets")
   
   try:
      # Load collection
      df = load_collection(args.collection)
      
      # Handle different modes
      if args.seeds:
         # Get suggestions for seed cards
         logger.info(f"Getting {args.count} suggestions for seed cards: {args.seeds}")
         raw_suggestions = suggest_complements(args.seeds, df, args.count, args.openai_model, args.openai_temperature)
         
         if not raw_suggestions:
            print("No suggestions received from LLM")
            return
         
         # Filter to collection
         final_suggestions = filter_by_collection(raw_suggestions, df)
         
         if not final_suggestions:
            print("None of the suggested cards are in your collection")
            return
         
         # Display results
         print(f"\nSuggested complementary cards for {', '.join(args.seeds)}:")
         print("=" * 60)
         
         for i, card_name in enumerate(final_suggestions, 1):
            if args.details:
               print_card_details(card_name, df)
            else:
               print(f"{i}. {card_name}")
         
         print(f"\nFound {len(final_suggestions)} cards in your collection")
      
      elif args.pairs:
         # Find synergistic pairs
         logger.info(f"Finding {args.pairs} synergistic card pairs")
         raw_pairs = find_synergistic_pairs(df, args.pairs, args.openai_model, args.openai_temperature)
         
         if not raw_pairs:
            print("No synergistic pairs found")
            return
         
         # Filter to collection
         final_pairs = filter_pairs_by_collection(raw_pairs, df)
         
         if not final_pairs:
            print("None of the suggested pairs are fully in your collection")
            return
         
         # Display results
         print(f"\nSynergistic card pairs found:")
         print("=" * 60)
         
         for i, pair_tuple in enumerate(final_pairs, 1):
            pair, explanation = pair_tuple
            print(f"{i}. {pair[0]} + {pair[1]}")
            print(f"   Synergy: {explanation}")
            if args.details:
               card1_details = get_card_details(pair[0], df)
               card2_details = get_card_details(pair[1], df)
               print(f"   {pair[0]} ({card1_details['mana_cost']}) [{card1_details['colors']}]")
               print(f"      Type: {card1_details['type_line']}")
               print(f"      Text: {card1_details['oracle_text']}")
               print(f"   {pair[1]} ({card2_details['mana_cost']}) [{card2_details['colors']}]")
               print(f"      Type: {card2_details['type_line']}")
               print(f"      Text: {card2_details['oracle_text']}")
            print()
         
         print(f"\nFound {len(final_pairs)} synergistic pairs in your collection")
      
      elif args.triplets:
         # Find synergistic triplets
         logger.info(f"Finding {args.triplets} synergistic card triplets")
         raw_triplets = find_synergistic_triplets(df, args.triplets, args.openai_model, args.openai_temperature)
         
         if not raw_triplets:
            print("No synergistic triplets found")
            return
         
         # Filter to collection
         final_triplets = filter_triplets_by_collection(raw_triplets, df)
         
         if not final_triplets:
            print("None of the suggested triplets are fully in your collection")
            return
         
         # Display results
         print(f"\nSynergistic card triplets found:")
         print("=" * 60)
         
         for i, triplet_tuple in enumerate(final_triplets, 1):
            triplet, explanation = triplet_tuple
            print(f"{i}. {triplet[0]} + {triplet[1]} + {triplet[2]}")
            print(f"   Synergy: {explanation}")
            if args.details:
               card1_details = get_card_details(triplet[0], df)
               card2_details = get_card_details(triplet[1], df)
               card3_details = get_card_details(triplet[2], df)
               print(f"   {triplet[0]} ({card1_details['mana_cost']}) [{card1_details['colors']}]")
               print(f"      Type: {card1_details['type_line']}")
               print(f"      Text: {card1_details['oracle_text']}")
               print(f"   {triplet[1]} ({card2_details['mana_cost']}) [{card2_details['colors']}]")
               print(f"      Type: {card2_details['type_line']}")
               print(f"      Text: {card2_details['oracle_text']}")
               print(f"   {triplet[2]} ({card3_details['mana_cost']}) [{card3_details['colors']}]")
               print(f"      Type: {card3_details['type_line']}")
               print(f"      Text: {card3_details['oracle_text']}")
            print()
         
         print(f"\nFound {len(final_triplets)} synergistic triplets in your collection")
      
   except Exception as e:
      logger.error(f"Error: {str(e)}")
      print(f"Error: {str(e)}")

if __name__ == "__main__":
   main() 