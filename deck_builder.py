import pandas as pd
import logging
import argparse
import csv
from typing import List, Dict, Optional, Tuple
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

def select_archetype(colors: List[str], df: pd.DataFrame, model: str = 'gpt-4o-mini', temperature: float = 0.7) -> str:
   """
   Select a viable deck archetype for the given colors
   
   Args:
      colors: List of colors to build with (e.g., ['W', 'U'])
      df: DataFrame containing the collection
      model: OpenAI model to use
      temperature: Temperature setting for LLM
   
   Returns:
      Selected archetype name
   """
   # Filter collection to cards with the specified colors
   color_filter = df['colors'].str.contains('|'.join(colors), na=False)
   available_cards = df[color_filter]
   
   # Get a sample of cards to show what's available
   sample_cards = available_cards.sample(min(50, len(available_cards)))[['Name', 'mana_cost', 'type_line', 'colors']]
   
   available_cards_text = "\n".join([
      f"• {row['Name']} ({row['mana_cost']}) — {row['type_line']} [{row['colors']}]"
      for _, row in sample_cards.iterrows()
   ])
   
   color_names = {
      'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'
   }
   color_display = ' + '.join([color_names.get(c, c) for c in colors])
   
   messages = [
      {"role": "system", "content": 
         "You are an expert Magic: the Gathering deck-builder. Given a collection and color constraints, "
         "you will suggest viable deck archetypes that can be built from the available cards."
      },
      {"role": "user", "content":
         f"I want to build a {color_display} deck from my collection.\n\n"
         f"Available cards in my collection:\n{available_cards_text}\n\n"
         f"Suggest 3 viable deck archetypes for these colors. For each archetype, provide:\n"
         f"1. Archetype name (e.g., 'White Weenie Aggro', 'Azorius Control')\n"
         f"2. Brief strategy description\n"
         f"3. Key card types needed\n"
         f"4. Approximate mana curve target\n\n"
         f"Format your response as a numbered list. I will choose the first archetype."
      },
   ]
   
   try:
      response = chat_prompt(messages, model=model, temperature=temperature)
      logger.info("Received archetype suggestions from LLM")
      
      # Extract the first archetype name from the response
      lines = response.split('\n')
      for line in lines:
         if line.strip() and line[0].isdigit():
            # Look for the archetype name after the number
            parts = line.split('.', 1)
            if len(parts) > 1:
               archetype_part = parts[1].strip()
               # Extract the archetype name (usually the first part before any description)
               archetype = archetype_part.split('—')[0].strip()
               return archetype
      
      # Fallback: return a generic archetype
      return f"{color_display} Midrange"
      
   except Exception as e:
      logger.error(f"Failed to select archetype: {str(e)}")
      return f"{color_display} Midrange"

def plan_deck_strategy(archetype: str, colors: List[str], df: pd.DataFrame, model: str = 'gpt-4o-mini', temperature: float = 0.7) -> Dict[str, int]:
   """
   Plan the deck strategy and define card counts by category
   
   Args:
      archetype: The selected archetype
      colors: List of colors to build with
      df: DataFrame containing the collection
      model: OpenAI model to use
      temperature: Temperature setting for LLM
   
   Returns:
      Dictionary mapping card categories to target counts
   """
   color_names = {
      'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'
   }
   color_display = ' + '.join([color_names.get(c, c) for c in colors])
   
   messages = [
      {"role": "system", "content": 
         "You are an expert Magic: the Gathering deck-builder. Given an archetype, "
         "you will define the optimal card distribution for a 60-card deck."
      },
      {"role": "user", "content":
         f"I'm building a {archetype} deck with {color_display} colors.\n\n"
         f"Define the optimal card distribution for this archetype. Provide:\n"
         f"1. Number of creatures\n"
         f"2. Number of removal/interaction spells\n"
         f"3. Number of card draw/selection spells\n"
         f"4. Number of utility/protection spells\n"
         f"5. Number of lands\n\n"
         f"Format your response as a simple list with just the numbers, "
         f"e.g., 'Creatures: 15, Removal: 10, Card Draw: 6, Utility: 4, Lands: 25'"
      },
   ]
   
   try:
      response = chat_prompt(messages, model=model, temperature=temperature)
      logger.info("Received deck strategy from LLM")
      
      # Parse the response to extract numbers
      strategy = {}
      lines = response.split('\n')
      for line in lines:
         if ':' in line:
            parts = line.split(':')
            if len(parts) == 2:
               category = parts[0].strip().lower()
               count_str = parts[1].strip().split(',')[0]  # Take first number if multiple
               try:
                  count = int(count_str)
                  strategy[category] = count
               except ValueError:
                  continue
      
      # Ensure we have reasonable defaults if parsing failed
      if not strategy:
         strategy = {
            'creatures': 15,
            'removal': 10,
            'card draw': 6,
            'utility': 4,
            'lands': 25
         }
      
      return strategy
      
   except Exception as e:
      logger.error(f"Failed to plan deck strategy: {str(e)}")
      # Return reasonable defaults
      return {
         'creatures': 15,
         'removal': 10,
         'card draw': 6,
         'utility': 4,
         'lands': 25
      }

def build_category(category: str, count: int, existing_cards: List[str], archetype: str, 
                  colors: List[str], df: pd.DataFrame, model: str = 'gpt-4o-mini', temperature: float = 0.7) -> List[str]:
   """
   Build a specific category of cards for the deck
   
   Args:
      category: Category to build (creatures, removal, card draw, utility)
      count: Number of cards to select
      existing_cards: Cards already in the deck
      archetype: The deck archetype
      colors: List of colors to build with
      df: DataFrame containing the collection
      model: OpenAI model to use
      temperature: Temperature setting for LLM
   
   Returns:
      List of selected card names
   """
   # Filter collection to cards with the specified colors
   color_filter = df['colors'].str.contains('|'.join(colors), na=False)
   available_cards = df[color_filter]
   
   # Filter out cards already in the deck
   existing_lower = [card.lower() for card in existing_cards]
   available_cards = available_cards[~available_cards['Name'].str.lower().isin(existing_lower)]
   
   # Filter by category type
   if category == 'creatures':
      category_filter = available_cards['type_line'].str.contains('Creature', na=False)
   elif category == 'removal':
      # Look for cards that can remove threats
      removal_keywords = ['destroy', 'exile', 'damage', 'return to owner', 'counter']
      category_filter = available_cards['oracle_text'].str.lower().str.contains('|'.join(removal_keywords), na=False)
   elif category == 'card draw':
      # Look for cards that draw cards
      draw_keywords = ['draw', 'scry', 'look at the top']
      category_filter = available_cards['oracle_text'].str.lower().str.contains('|'.join(draw_keywords), na=False)
   elif category == 'utility':
      # Look for utility cards (enchantments, artifacts, etc.)
      utility_filter = (
         available_cards['type_line'].str.contains('Enchantment', na=False) |
         available_cards['type_line'].str.contains('Artifact', na=False) |
         available_cards['type_line'].str.contains('Planeswalker', na=False)
      )
      category_filter = utility_filter
   else:
      # Default to all cards
      category_filter = pd.Series([True] * len(available_cards))
   
   category_cards = available_cards[category_filter]
   
   if len(category_cards) == 0:
      logger.warning(f"No {category} cards found in collection")
      return []
   
   # Get a sample of cards to suggest from
   sample_cards = category_cards.sample(min(50, len(category_cards)))[['Name', 'mana_cost', 'type_line', 'oracle_text']]
   
   available_cards_text = "\n".join([
      f"• {row['Name']} ({row['mana_cost']}) — {row['type_line']}: {str(row['oracle_text'])[:100]}..."
      for _, row in sample_cards.iterrows()
   ])
   
   color_names = {
      'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'
   }
   color_display = ' + '.join([color_names.get(c, c) for c in colors])
   
   category_descriptions = {
      'creatures': 'creature cards that can attack and block',
      'removal': 'removal and interaction spells that can deal with threats',
      'card draw': 'card draw and selection spells',
      'utility': 'utility and protection spells'
   }
   
   category_desc = category_descriptions.get(category, category)
   
   messages = [
      {"role": "system", "content": 
         "You are an expert Magic: the Gathering deck-builder. You will select the best cards "
         "for a specific category in a deck."
      },
      {"role": "user", "content":
         f"I'm building a {archetype} deck with {color_display} colors.\n\n"
         f"Current deck: {', '.join(existing_cards) if existing_cards else 'Empty'}\n\n"
         f"I need {count} {category_desc} for this deck.\n\n"
         f"Available cards:\n{available_cards_text}\n\n"
         f"Select exactly {count} cards from the available list that work best in this {archetype} deck. "
         f"Focus on cards that support the deck's strategy and work well together.\n\n"
         f"Format your response as a numbered list with just the card names."
      },
   ]
   
   try:
      response = chat_prompt(messages, model=model, temperature=temperature)
      logger.info(f"Received {category} suggestions from LLM")
      
      # Parse the response to extract card names
      suggestions = parse_card_suggestions(response)
      
      # Filter to collection and limit to requested count
      filtered_suggestions = filter_by_collection(suggestions, df)
      return filtered_suggestions[:count]
      
   except Exception as e:
      logger.error(f"Failed to build {category}: {str(e)}")
      return []

def analyze_deck_curve(deck_cards: List[str], df: pd.DataFrame) -> Dict[str, int]:
   """
   Analyze the mana curve of the deck
   
   Args:
      deck_cards: List of card names in the deck
      df: DataFrame containing the collection
   
   Returns:
      Dictionary mapping CMC to count
   """
   curve = {}
   total_nonland = 0
   
   for card_name in deck_cards:
      matches = df[df['Name'].str.lower() == card_name.lower()]
      if not matches.empty:
         row = matches.iloc[0]
         cmc = row.get('cmc', 0)
         type_line = row.get('type_line', '')
         
         # Skip lands for curve analysis
         if 'Land' not in type_line:
            cmc_key = f"CMC {cmc}"
            curve[cmc_key] = curve.get(cmc_key, 0) + 1
            total_nonland += 1
   
   curve['Total Non-Land'] = total_nonland
   return curve

def add_basic_lands(deck_cards: List[str], colors: List[str], target_land_count: int) -> List[str]:
   """
   Add basic lands to reach the target land count
   
   Args:
      deck_cards: Current deck cards
      colors: Colors in the deck
      target_land_count: Target number of lands
   
   Returns:
      Updated deck with basic lands added
   """
   # Count current lands
   current_lands = sum(1 for card in deck_cards if 'Land' in card)
   lands_needed = target_land_count - current_lands
   
   if lands_needed <= 0:
      return deck_cards
   
   # Add basic lands based on colors
   basic_lands = {
      'W': 'Plains',
      'U': 'Island', 
      'B': 'Swamp',
      'R': 'Mountain',
      'G': 'Forest'
   }
   
   # Distribute lands evenly among colors
   lands_per_color = max(1, lands_needed // len(colors))
   remaining_lands = lands_needed % len(colors)
   
   new_deck = deck_cards.copy()
   
   for i, color in enumerate(colors):
      land_name = basic_lands.get(color, f"{color} Land")
      lands_to_add = lands_per_color + (1 if i < remaining_lands else 0)
      
      for _ in range(lands_to_add):
         new_deck.append(land_name)
   
   return new_deck

def build_deck(colors: List[str], df: pd.DataFrame, model: str = 'gpt-4o-mini', temperature: float = 0.7) -> Tuple[List[str], Dict]:
   """
   Build a complete 60-card deck for the specified colors
   
   Args:
      colors: List of colors to build with (e.g., ['W', 'U'])
      df: DataFrame containing the collection
      model: OpenAI model to use
      temperature: Temperature setting for LLM
   
   Returns:
      Tuple of (deck_cards, deck_info)
   """
   logger.info(f"Building deck for colors: {colors}")
   
   # Stage 1: Select archetype
   archetype = select_archetype(colors, df, model, temperature)
   logger.info(f"Selected archetype: {archetype}")
   
   # Stage 2: Plan deck strategy
   strategy = plan_deck_strategy(archetype, colors, df, model, temperature)
   logger.info(f"Deck strategy: {strategy}")
   
   # Stage 3: Build deck by category
   deck_cards = []
   
   # Build each category
   categories = ['creatures', 'removal', 'card draw', 'utility']
   for category in categories:
      if category in strategy:
         count = strategy[category]
         logger.info(f"Building {category} category with {count} cards")
         category_cards = build_category(category, count, deck_cards, archetype, colors, df, model, temperature)
         deck_cards.extend(category_cards)
         logger.info(f"Added {len(category_cards)} {category} cards")
   
   # Stage 4: Add lands
   land_count = strategy.get('lands', 25)
   deck_cards = add_basic_lands(deck_cards, colors, land_count)
   
   # Stage 5: Analyze final deck
   curve = analyze_deck_curve(deck_cards, df)
   
   deck_info = {
      'archetype': archetype,
      'colors': colors,
      'strategy': strategy,
      'curve': curve,
      'total_cards': len(deck_cards)
   }
   
   logger.info(f"Built deck with {len(deck_cards)} cards")
   return deck_cards, deck_info

def print_deck(deck_cards: List[str], deck_info: Dict, df: pd.DataFrame):
   """
   Print a formatted deck list with analysis
   
   Args:
      deck_cards: List of card names in the deck
      deck_info: Dictionary with deck information
      df: DataFrame containing the collection
   """
   print(f"\n{'='*60}")
   print(f"DECK: {deck_info['archetype']}")
   print(f"Colors: {', '.join(deck_info['colors'])}")
   print(f"Total Cards: {deck_info['total_cards']}")
   print(f"{'='*60}")
   
   # Print cards by category
   categories = ['creatures', 'removal', 'card draw', 'utility', 'lands']
   category_cards = {cat: [] for cat in categories}
   
   for card_name in deck_cards:
      matches = df[df['Name'].str.lower() == card_name.lower()]
      if not matches.empty:
         row = matches.iloc[0]
         type_line = row.get('type_line', '')
         
         if 'Land' in type_line:
            category_cards['lands'].append(card_name)
         elif 'Creature' in type_line:
            category_cards['creatures'].append(card_name)
         elif any(keyword in row.get('oracle_text', '').lower() for keyword in ['destroy', 'exile', 'damage', 'counter']):
            category_cards['removal'].append(card_name)
         elif any(keyword in row.get('oracle_text', '').lower() for keyword in ['draw', 'scry']):
            category_cards['card draw'].append(card_name)
         else:
            category_cards['utility'].append(card_name)
   
   for category in categories:
      if category_cards[category]:
         print(f"\n{category.upper()} ({len(category_cards[category])}):")
         for card in sorted(category_cards[category]):
            print(f"  {card}")
   
   # Print curve analysis
   print(f"\nMANA CURVE:")
   curve = deck_info['curve']
   for cmc in sorted([k for k in curve.keys() if k.startswith('CMC')], key=lambda x: float(x.split()[1])):
      print(f"  {cmc}: {curve[cmc]}")
   print(f"  Total Non-Land: {curve.get('Total Non-Land', 0)}")

def export_deck_to_csv(deck_cards: List[str], deck_info: Dict, df: pd.DataFrame, output_file: str = "deck_export.csv"):
   """
   Export the deck to a CSV file
   
   Args:
      deck_cards: List of card names in the deck
      deck_info: Dictionary with deck information
      df: DataFrame containing the collection
      output_file: Output CSV file path
   """
   # Create a list to store deck data
   deck_data = []
   
   # Count cards (handle duplicates)
   card_counts = {}
   for card in deck_cards:
      card_counts[card] = card_counts.get(card, 0) + 1
   
   # Get card details from collection
   for card_name, count in card_counts.items():
      matches = df[df['Name'].str.lower() == card_name.lower()]
      if not matches.empty:
         row = matches.iloc[0]
         deck_data.append({
            'Name': row['Name'],
            'Quantity': count,
            'Mana Cost': row.get('mana_cost', ''),
            'Type': row.get('type_line', ''),
            'CMC': row.get('cmc', ''),
            'Colors': row.get('colors', ''),
            'Rarity': row.get('rarity', ''),
            'Set': row.get('set_name', ''),
            'Oracle Text': row.get('oracle_text', '').replace('\n', ' '),
            'Power': row.get('power', ''),
            'Toughness': row.get('toughness', ''),
            'Category': get_card_category(card_name, df)
         })
      else:
         # Handle basic lands that might not be in the collection
         deck_data.append({
            'Name': card_name,
            'Quantity': count,
            'Mana Cost': '',
            'Type': 'Basic Land',
            'CMC': '0',
            'Colors': '',
            'Rarity': 'Common',
            'Set': '',
            'Oracle Text': '',
            'Power': '',
            'Toughness': '',
            'Category': 'lands'
         })
   
   # Sort by category and then by name
   category_order = {'creatures': 1, 'removal': 2, 'card draw': 3, 'utility': 4, 'lands': 5}
   deck_data.sort(key=lambda x: (category_order.get(x['Category'], 6), x['Name']))
   
   # Write to CSV
   try:
      with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
         fieldnames = ['Name', 'Quantity', 'Mana Cost', 'Type', 'CMC', 'Colors', 'Rarity', 'Set', 'Oracle Text', 'Power', 'Toughness', 'Category']
         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
         
         # Write header
         writer.writeheader()
         
         # Write card data
         writer.writerows(deck_data)
      
      logger.info(f"Deck exported to {output_file}")
      print(f"✓ Deck exported to {output_file}")
      
   except Exception as e:
      logger.error(f"Failed to export deck to CSV: {str(e)}")
      print(f"✗ Failed to export deck to CSV: {str(e)}")

def get_card_category(card_name: str, df: pd.DataFrame) -> str:
   """
   Determine the category of a card
   
   Args:
      card_name: Name of the card
      df: DataFrame containing the collection
   
   Returns:
      Category string (creatures, removal, card draw, utility, lands)
   """
   matches = df[df['Name'].str.lower() == card_name.lower()]
   if not matches.empty:
      row = matches.iloc[0]
      type_line = row.get('type_line', '')
      oracle_text = row.get('oracle_text', '').lower()
      
      if 'Land' in type_line:
         return 'lands'
      elif 'Creature' in type_line:
         return 'creatures'
      elif any(keyword in oracle_text for keyword in ['destroy', 'exile', 'damage', 'return to owner', 'counter']):
         return 'removal'
      elif any(keyword in oracle_text for keyword in ['draw', 'scry', 'look at the top']):
         return 'card draw'
      else:
         return 'utility'
   else:
      # Handle basic lands
      if card_name in ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest']:
         return 'lands'
      return 'utility'

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
       description='MTG Deck Builder - Suggest complementary cards, find synergies, and build complete decks',
       formatter_class=argparse.RawDescriptionHelpFormatter,
       epilog="""
Examples:
  python deck_builder.py --seeds "Paladin Class" "Kitesail Cleric" --count 10
  python deck_builder.py --pairs 5 --details
  python deck_builder.py --triplets 3 -v --openai-temperature 0.8
  python deck_builder.py --build-deck W U --details
  python deck_builder.py --build-deck R G -v
  python deck_builder.py --build-deck W U --export-csv my_deck.csv
  python deck_builder.py --seeds "Paladin Class" --export-csv suggestions.csv
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
   parser.add_argument('--build-deck', '-b', nargs='+', metavar='COLORS',
                      help='Build a complete 60-card deck for specified colors (e.g., W U for Azorius)')
   parser.add_argument('--export-csv', '-e', type=str, metavar='FILE',
                      help='Export deck to CSV file (e.g., --export-csv my_deck.csv)')
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
   if not args.seeds and not args.pairs and not args.triplets and not args.build_deck:
      parser.error("Must specify either --seeds, --pairs, --triplets, or --build-deck")
   
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
         
         # Export to CSV if requested
         if args.export_csv:
            # Create a simple deck info for suggestions
            suggestions_info = {
               'archetype': f"Suggestions for {', '.join(args.seeds)}",
               'colors': [],
               'strategy': {'suggestions': len(final_suggestions)},
               'curve': {},
               'total_cards': len(final_suggestions)
            }
            export_deck_to_csv(final_suggestions, suggestions_info, df, args.export_csv)
      
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
         
         # Export to CSV if requested
         if args.export_csv:
            # Create a simple deck info for pairs
            pairs_info = {
               'archetype': f"Synergistic Pairs ({args.pairs} pairs)",
               'colors': [],
               'strategy': {'pairs': len(final_pairs)},
               'curve': {},
               'total_cards': len(final_pairs) * 2
            }
            # Flatten pairs into a single list
            pairs_cards = []
            for pair_tuple in final_pairs:
               pairs_cards.extend(pair_tuple[0])
            export_deck_to_csv(pairs_cards, pairs_info, df, args.export_csv)
      
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
         
         # Export to CSV if requested
         if args.export_csv:
            # Create a simple deck info for triplets
            triplets_info = {
               'archetype': f"Synergistic Triplets ({args.triplets} triplets)",
               'colors': [],
               'strategy': {'triplets': len(final_triplets)},
               'curve': {},
               'total_cards': len(final_triplets) * 3
            }
            # Flatten triplets into a single list
            triplets_cards = []
            for triplet_tuple in final_triplets:
               triplets_cards.extend(triplet_tuple[0])
            export_deck_to_csv(triplets_cards, triplets_info, df, args.export_csv)
      
      elif args.build_deck:
         # Build a complete deck
         colors = args.build_deck
         logger.info(f"Building deck for colors: {colors}")
         
         # Validate colors
         valid_colors = ['W', 'U', 'B', 'R', 'G']
         invalid_colors = [c for c in colors if c not in valid_colors]
         if invalid_colors:
            print(f"Invalid colors: {invalid_colors}. Valid colors are: {', '.join(valid_colors)}")
            return
         
         # Build the deck
         deck_cards, deck_info = build_deck(colors, df, args.openai_model, args.openai_temperature)
         
         if not deck_cards:
            print("Failed to build deck")
            return
         
         # Display the deck
         print_deck(deck_cards, deck_info, df)
         
         # Export to CSV if requested
         if args.export_csv:
            export_deck_to_csv(deck_cards, deck_info, df, args.export_csv)
         
         if args.details:
            print(f"\nDECK ANALYSIS:")
            print(f"Archetype: {deck_info['archetype']}")
            print(f"Strategy: {deck_info['strategy']}")
            print(f"Total Cards: {deck_info['total_cards']}")
            if deck_info['total_cards'] != 60:
               print(f"WARNING: Deck has {deck_info['total_cards']} cards (should be 60)")
      
   except Exception as e:
      logger.error(f"Error: {str(e)}")
      print(f"Error: {str(e)}")

if __name__ == "__main__":
   main() 