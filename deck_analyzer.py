#!/usr/bin/env python3
"""
Deck Analyzer - Comprehensive MTG Deck Analysis Tool

This script analyzes a deck CSV file and uses OpenAI's LLM to provide detailed
strategy analysis, strengths, weaknesses, and usage tips for the deck.
"""

import argparse
import logging
import pandas as pd
import sys
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from llm_client import chat_prompt


def setup_logging(verbose: bool = False) -> None:
   """Set up logging configuration"""
   log_level = logging.DEBUG if verbose else logging.INFO
   log_format = '%(asctime)s - %(levelname)s - %(message)s'
   date_format = '%d-%m %H:%M'
   
   logging.basicConfig(
      level=log_level,
      format=log_format,
      datefmt=date_format,
      handlers=[
         logging.StreamHandler(sys.stdout)
      ]
   )


def read_deck_csv(file_path: str) -> pd.DataFrame:
   """
   Read a deck CSV file and return a DataFrame
   
   Args:
      file_path: Path to the deck CSV file
      
   Returns:
      DataFrame containing the deck data
   """
   try:
      logging.info(f"Reading deck CSV from {file_path}")
      
      # Read CSV and skip comment lines
      df = pd.read_csv(file_path, comment='#')
      
      # Validate required columns
      required_columns = ['Name', 'Quantity', 'Mana Cost', 'Type', 'CMC', 'Colors', 'Category']
      missing_columns = [col for col in required_columns if col not in df.columns]
      
      if missing_columns:
         raise ValueError(f"Missing required columns: {missing_columns}")
      
      # Convert Quantity to numeric, handling any non-numeric values
      df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(1).astype(int)
      
      # Convert CMC to numeric, handling any non-numeric values
      df['CMC'] = pd.to_numeric(df['CMC'], errors='coerce').fillna(0)
      
      logging.info(f"Successfully loaded {len(df)} cards from deck CSV")
      return df
      
   except FileNotFoundError:
      logging.error(f"Deck CSV file not found: {file_path}")
      raise
   except Exception as e:
      logging.error(f"Error reading deck CSV file: {e}")
      raise


def analyze_deck_structure(df: pd.DataFrame) -> Dict[str, Any]:
   """
   Analyze the deck structure and statistics
   
   Args:
      df: DataFrame containing deck data
      
   Returns:
      Dictionary with deck analysis statistics
   """
   analysis = {}
   
   # Basic deck info
   analysis['total_cards'] = df['Quantity'].sum()
   analysis['unique_cards'] = len(df)
   
   # Color analysis
   color_counts = {}
   for colors in df['Colors'].dropna():
      if pd.isna(colors) or colors == 'nan' or str(colors).lower() == 'nan':
         continue
      for color in str(colors).split(','):
         color = color.strip()
         if color:  # Only add non-empty colors
            color_counts[color] = color_counts.get(color, 0) + 1
   
   analysis['colors'] = color_counts
   analysis['color_identity'] = list(color_counts.keys())
   
   # Mana curve analysis
   cmc_data = df[df['CMC'] > 0]  # Exclude lands
   cmc_counts = cmc_data.groupby('CMC')['Quantity'].sum().to_dict()
   analysis['mana_curve'] = cmc_counts
   analysis['avg_cmc'] = (cmc_data['CMC'] * cmc_data['Quantity']).sum() / cmc_data['Quantity'].sum()
   
   # Category analysis
   category_counts = df.groupby('Category')['Quantity'].sum().to_dict()
   analysis['categories'] = category_counts
   
   # Rarity analysis
   rarity_counts = df.groupby('Rarity')['Quantity'].sum().to_dict()
   analysis['rarities'] = rarity_counts
   
   # Land count
   land_df = df[df['Category'] == 'lands']
   analysis['land_count'] = land_df['Quantity'].sum() if not land_df.empty else 0
   analysis['land_ratio'] = analysis['land_count'] / analysis['total_cards']
   
   # Creature analysis
   creature_df = df[df['Category'] == 'creatures']
   analysis['creature_count'] = creature_df['Quantity'].sum() if not creature_df.empty else 0
   analysis['creature_ratio'] = analysis['creature_count'] / analysis['total_cards']
   
   return analysis


def format_deck_for_llm(df: pd.DataFrame, analysis: Dict[str, Any]) -> str:
   """
   Format the deck data for LLM analysis
   
   Args:
      df: DataFrame containing deck data
      analysis: Deck analysis statistics
      
   Returns:
      Formatted string for LLM prompt
   """
   # Header with deck statistics
   header = f"""DECK ANALYSIS REQUEST

Deck Statistics:
- Total Cards: {analysis['total_cards']}
- Unique Cards: {analysis['unique_cards']}
- Colors: {', '.join(analysis['color_identity'])}
- Average CMC: {analysis['avg_cmc']:.2f}
- Lands: {analysis['land_count']} ({analysis['land_ratio']:.1%})
- Creatures: {analysis['creature_count']} ({analysis['creature_ratio']:.1%})

Mana Curve:
"""
   
   # Add mana curve
   for cmc in sorted(analysis['mana_curve'].keys()):
      header += f"- CMC {cmc}: {analysis['mana_curve'][cmc]} cards\n"
   
   header += f"""
Category Breakdown:
"""
   
   # Add category breakdown
   for category, count in analysis['categories'].items():
      header += f"- {category}: {count} cards\n"
   
   header += f"""
Rarity Breakdown:
"""
   
   # Add rarity breakdown
   for rarity, count in analysis['rarities'].items():
      header += f"- {rarity}: {count} cards\n"
   
   # Card list by category
   card_list = "\nCARD LIST BY CATEGORY:\n"
   
   for category in sorted(df['Category'].unique()):
      category_df = df[df['Category'] == category]
      card_list += f"\n{category.upper()}:\n"
      
      for _, row in category_df.iterrows():
         card_list += f"- {row['Quantity']}x {row['Name']} ({row['Mana Cost']}) - {row['Type']}"
         if pd.notna(row['Power']) and pd.notna(row['Toughness']):
            card_list += f" - {row['Power']}/{row['Toughness']}"
         card_list += f"\n  Oracle Text: {row['Oracle Text']}\n"
   
   return header + card_list


def generate_deck_analysis(df: pd.DataFrame, analysis: Dict[str, Any]) -> str:
   """
   Generate comprehensive deck analysis using LLM
   
   Args:
      df: DataFrame containing deck data
      analysis: Deck analysis statistics
      
   Returns:
      LLM-generated deck analysis
   """
   deck_info = format_deck_for_llm(df, analysis)
   
   system_prompt = """You are an expert Magic: The Gathering deck analyst and strategist. You have deep knowledge of deck building, meta analysis, and competitive play. When analyzing a deck, provide comprehensive insights that would be valuable to both casual and competitive players."""

   user_prompt = f"""Please provide a comprehensive analysis of this Magic: The Gathering deck. Your analysis should include:

1. **DECK ARCHETYPE & STRATEGY**
   - Identify the deck's primary archetype and strategy
   - Explain the core game plan and win conditions
   - Describe how the deck aims to achieve victory

2. **STRENGTHS**
   - List 5-7 key strengths of this deck
   - Explain why these elements work well together
   - Highlight any particularly powerful card combinations

3. **WEAKNESSES & VULNERABILITIES**
   - Identify 5-7 potential weaknesses or vulnerabilities
   - Explain what types of decks or strategies could exploit these weaknesses
   - Discuss any gaps in the deck's game plan

4. **MANA BASE & CURVE ANALYSIS**
   - Evaluate the mana curve and land count
   - Assess color distribution and mana fixing
   - Identify any potential mana issues

5. **KEY CARD INTERACTIONS**
   - Highlight 3-5 important card synergies or combinations
   - Explain how these cards work together
   - Suggest optimal sequencing for these interactions

6. **SIDEBOARD CONSIDERATIONS**
   - Suggest potential sideboard strategies
   - Identify cards that could be problematic in certain matchups
   - Recommend cards to bring in against different archetypes

7. **PLAYING TIPS & STRATEGY**
   - Provide 5-7 specific tips for piloting this deck
   - Explain key decision points and sequencing
   - Discuss mulligan strategies

8. **MATCHUP ANALYSIS**
   - Rate the deck's performance against common archetypes (Aggro, Control, Midrange, Combo)
   - Explain why certain matchups are favorable or unfavorable
   - Suggest specific strategies for difficult matchups

9. **POTENTIAL IMPROVEMENTS**
   - Suggest 3-5 cards that could improve the deck
   - Explain what problems these cards would solve
   - Consider both budget and competitive options

10. **OVERALL ASSESSMENT**
    - Provide a final rating and assessment
    - Summarize the deck's competitive viability
    - Give recommendations for different play environments

Please be detailed and specific in your analysis. Use the card names and explain how they contribute to the deck's strategy. Focus on practical advice that would help a player understand and improve their gameplay with this deck.

Here is the deck to analyze:

{deck_info}"""

   messages = [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_prompt}
   ]
   
   logging.info("Generating deck analysis with LLM...")
   response = chat_prompt(messages, temperature=0.7)
   
   return response


def save_analysis_to_file(analysis_text: str, output_file: str) -> None:
   """
   Save the analysis to a text file
   
   Args:
      analysis_text: The analysis text to save
      output_file: Path to the output file
   """
   try:
      with open(output_file, 'w', encoding='utf-8') as f:
         f.write(analysis_text)
      logging.info(f"Analysis saved to {output_file}")
   except Exception as e:
      logging.error(f"Error saving analysis to file: {e}")
      raise


def main():
   """Main function"""
   parser = argparse.ArgumentParser(
      description="Analyze a Magic: The Gathering deck CSV and provide detailed strategy analysis",
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog="""
Examples:
   python deck_analyzer.py deck.csv
   python deck_analyzer.py deck.csv -o analysis.txt
   python deck_analyzer.py deck.csv -v --output detailed_analysis.txt
      """
   )
   
   parser.add_argument(
      'deck_file',
      help='Path to the deck CSV file to analyze'
   )
   
   parser.add_argument(
      '-o', '--output',
      help='Output file for the analysis (default: deck_analysis_YYYY-MM-DD_HH-MM.txt)'
   )
   
   parser.add_argument(
      '-v', '--verbose',
      action='store_true',
      help='Enable verbose logging'
   )
   
   args = parser.parse_args()
   
   # Setup logging
   setup_logging(args.verbose)
   
   try:
      # Read deck CSV
      df = read_deck_csv(args.deck_file)
      
      # Analyze deck structure
      logging.info("Analyzing deck structure...")
      analysis = analyze_deck_structure(df)
      
      # Print basic statistics
      logging.info(f"Deck Analysis Summary:")
      logging.info(f"  Total Cards: {analysis['total_cards']}")
      logging.info(f"  Colors: {', '.join(analysis['color_identity'])}")
      logging.info(f"  Average CMC: {analysis['avg_cmc']:.2f}")
      logging.info(f"  Lands: {analysis['land_count']} ({analysis['land_ratio']:.1%})")
      logging.info(f"  Creatures: {analysis['creature_count']} ({analysis['creature_ratio']:.1%})")
      
      # Generate LLM analysis
      logging.info("Generating comprehensive deck analysis...")
      deck_analysis = generate_deck_analysis(df, analysis)
      
      # Determine output file
      if args.output:
         output_file = args.output
      else:
         timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
         deck_name = os.path.splitext(os.path.basename(args.deck_file))[0]
         output_file = f"{deck_name}_analysis_{timestamp}.txt"
      
      # Save analysis
      save_analysis_to_file(deck_analysis, output_file)
      
      # Print analysis to console
      print("\n" + "="*80)
      print("DECK ANALYSIS")
      print("="*80)
      print(deck_analysis)
      print("="*80)
      print(f"\nAnalysis also saved to: {output_file}")
      
   except KeyboardInterrupt:
      logging.info("Analysis interrupted by user")
      sys.exit(1)
   except Exception as e:
      logging.error(f"Error during deck analysis: {e}")
      sys.exit(1)


if __name__ == "__main__":
   main() 