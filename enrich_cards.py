#!/usr/bin/env python3
"""
MTG Card Enrichment Script

This script reads a ManaBox CSV export, enriches it with data from Scryfall API,
and outputs an enriched CSV with additional card information.

Features:
- Progress tracking with resume capability
- Configurable rate limiting
- Comprehensive error handling
- File and console logging
- Configuration file support

Usage:
    python enrich_cards.py --input manabox-db.csv --output enriched.csv
    python enrich_cards.py -i manabox-db.csv -o enriched.csv --resume --log-level DEBUG
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from tqdm import tqdm

from src.data_ingest import read_manabox_csv, validate_card_data
from src.scryfall_client import ScryfallClient
from src.transformer import extract_card_fields, get_required_fields


class EnrichmentProgress:
   """Track enrichment progress for resume capability."""
   
   def __init__(self, progress_file: str):
       self.progress_file = progress_file
       self.completed_cards = set()
       self.load_progress()
   
   def load_progress(self) -> None:
       """Load progress from file if it exists."""
       if Path(self.progress_file).exists():
           try:
               with open(self.progress_file, 'r') as f:
                   data = json.load(f)
                   self.completed_cards = set(data.get('completed_cards', []))
                   logging.info(f"Loaded progress: {len(self.completed_cards)} cards already processed")
           except Exception as e:
               logging.warning(f"Could not load progress file: {e}")
               self.completed_cards = set()
   
   def save_progress(self) -> None:
       """Save current progress to file."""
       try:
           with open(self.progress_file, 'w') as f:
               json.dump({
                   'completed_cards': list(self.completed_cards),
                   'timestamp': time.time()
               }, f, indent=2)
       except Exception as e:
           logging.error(f"Could not save progress: {e}")
   
   def mark_completed(self, card_id: str) -> None:
       """Mark a card as completed."""
       self.completed_cards.add(card_id)
   
   def is_completed(self, card_id: str) -> bool:
       """Check if a card is already completed."""
       return card_id in self.completed_cards


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
   """Set up logging configuration with both console and file output."""
   # Create formatter
   formatter = logging.Formatter(
       '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       datefmt='%d-%m %H:%M'
   )
   
   # Set up root logger
   root_logger = logging.getLogger()
   root_logger.setLevel(getattr(logging, level.upper()))
   
   # Clear existing handlers
   root_logger.handlers.clear()
   
   # Console handler
   console_handler = logging.StreamHandler(sys.stdout)
   console_handler.setFormatter(formatter)
   root_logger.addHandler(console_handler)
   
   # File handler (if specified)
   if log_file:
       file_handler = logging.FileHandler(log_file)
       file_handler.setFormatter(formatter)
       root_logger.addHandler(file_handler)


def enrich_card_data(
   df: pd.DataFrame, 
   client: ScryfallClient, 
   progress: EnrichmentProgress,
   rate_limit: float = 0.1,
   max_retries: int = 3
) -> pd.DataFrame:
   """
   Enrich the DataFrame with data from Scryfall API.
   
   Args:
       df: Input DataFrame with card data
       client: ScryfallClient instance
       progress: Progress tracker for resume capability
       rate_limit: Delay between requests in seconds
       max_retries: Maximum number of retries for failed requests
       
   Returns:
       Enriched DataFrame with additional columns
   """
   enriched_df = df.copy()
   
   # Add new columns for enriched data
   for field in get_required_fields():
       enriched_df[field] = ''
   
   total_cards = len(df)
   successful_fetches = 0
   failed_fetches = 0
   skipped_cards = 0
   
   # Filter out already completed cards if resuming
   cards_to_process = []
   for index, row in df.iterrows():
       scryfall_id = row['Scryfall ID']
       if not progress.is_completed(scryfall_id):
           cards_to_process.append((index, row))
       else:
           skipped_cards += 1
   
   if skipped_cards > 0:
       logging.info(f"Skipping {skipped_cards} already processed cards")
   
   logging.info(f"Starting enrichment of {len(cards_to_process)} cards...")
   
   # Process cards with progress bar
   for index, row in tqdm(cards_to_process, desc="Enriching cards"):
       scryfall_id = row['Scryfall ID']
       card_name = row['Name']
       
       # Retry logic for failed requests
       card_data = None
       for attempt in range(max_retries):
           try:
               card_data = client.get_card_by_id(scryfall_id)
               if card_data:
                   break
               elif attempt < max_retries - 1:
                   logging.warning(f"Attempt {attempt + 1} failed for {card_name}, retrying...")
                   time.sleep(rate_limit * 2)  # Longer delay on retry
           except Exception as e:
               if attempt < max_retries - 1:
                   logging.warning(f"Error fetching {card_name} (attempt {attempt + 1}): {e}")
                   time.sleep(rate_limit * 2)
               else:
                   logging.error(f"Failed to fetch {card_name} after {max_retries} attempts: {e}")
       
       if card_data:
           # Extract the fields we want
           try:
               extracted_fields = extract_card_fields(card_data)
               
               # Add the extracted fields to the DataFrame
               for field, value in extracted_fields.items():
                   enriched_df.at[index, field] = value
               
               successful_fetches += 1
               progress.mark_completed(scryfall_id)
               
               # Save progress periodically
               if successful_fetches % 10 == 0:
                   progress.save_progress()
                   
           except Exception as e:
               logging.error(f"Error processing data for {card_name}: {e}")
               failed_fetches += 1
       else:
           failed_fetches += 1
           logging.warning(f"Failed to fetch data for: {card_name}")
       
       # Rate limiting
       time.sleep(rate_limit)
   
   # Final progress save
   progress.save_progress()
   
   logging.info(f"Enrichment complete. Success: {successful_fetches}, Failed: {failed_fetches}, Skipped: {skipped_cards}")
   
   return enriched_df


def load_config(config_file: str) -> Dict:
   """Load configuration from JSON file."""
   try:
       with open(config_file, 'r') as f:
           return json.load(f)
   except Exception as e:
       logging.warning(f"Could not load config file {config_file}: {e}")
       return {}


def main():
   """Main function to run the enrichment process."""
   parser = argparse.ArgumentParser(
       description="Enrich ManaBox CSV with Scryfall data",
       formatter_class=argparse.RawDescriptionHelpFormatter,
       epilog="""
Examples:
  python enrich_cards.py --input manabox-db.csv --output enriched.csv
  python enrich_cards.py -i manabox-db.csv -o enriched.csv --resume --log-level DEBUG
  python enrich_cards.py -i manabox-db.csv -o enriched.csv --config config.json
       """
   )
   
   parser.add_argument(
       '-i', '--input',
       required=True,
       help='Input ManaBox CSV file path'
   )
   
   parser.add_argument(
       '-o', '--output',
       required=True,
       help='Output enriched CSV file path'
   )
   
   parser.add_argument(
       '--log-level',
       default='INFO',
       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
       help='Logging level (default: INFO)'
   )
   
   parser.add_argument(
       '--log-file',
       help='Log file path (optional)'
   )
   
   parser.add_argument(
       '--resume',
       action='store_true',
       help='Resume from previous run using progress file'
   )
   
   parser.add_argument(
       '--progress-file',
       default='enrichment_progress.json',
       help='Progress file path (default: enrichment_progress.json)'
   )
   
   parser.add_argument(
       '--rate-limit',
       type=float,
       default=0.1,
       help='Rate limit delay in seconds (default: 0.1)'
   )
   
   parser.add_argument(
       '--max-retries',
       type=int,
       default=3,
       help='Maximum retries for failed requests (default: 3)'
   )
   
   parser.add_argument(
       '--config',
       help='Configuration file path (JSON format)'
   )
   
   args = parser.parse_args()
   
   # Load configuration if provided
   config = {}
   if args.config:
       config = load_config(args.config)
   
   # Override config with command line arguments
   log_level = args.log_level or config.get('log_level', 'INFO')
   log_file = args.log_file or config.get('log_file')
   rate_limit = args.rate_limit or config.get('rate_limit', 0.1)
   max_retries = args.max_retries or config.get('max_retries', 3)
   
   # Set up logging
   setup_logging(log_level, log_file)
   logger = logging.getLogger(__name__)
   
   # Validate input file exists
   input_path = Path(args.input)
   if not input_path.exists():
       logger.error(f"Input file not found: {args.input}")
       sys.exit(1)
   
   # Create output directory if it doesn't exist
   output_path = Path(args.output)
   output_path.parent.mkdir(parents=True, exist_ok=True)
   
   try:
       # Read the CSV file
       logger.info("Reading input CSV file...")
       df = read_manabox_csv(args.input)
       
       # Validate the data
       logger.info("Validating card data...")
       validate_card_data(df)
       
       # Initialize progress tracker
       progress = EnrichmentProgress(args.progress_file)
       
       # Create Scryfall client
       logger.info("Initializing Scryfall client...")
       with ScryfallClient() as client:
           # Enrich the data
           enriched_df = enrich_card_data(
               df, client, progress, 
               rate_limit=rate_limit, 
               max_retries=max_retries
           )
           
           # Write the enriched data to output file
           logger.info(f"Writing enriched data to {args.output}...")
           enriched_df.to_csv(args.output, index=False)
           
           logger.info(f"Successfully created enriched CSV: {args.output}")
           logger.info(f"Original columns: {list(df.columns)}")
           logger.info(f"New columns added: {get_required_fields()}")
           
           # Clean up progress file if successful
           if Path(args.progress_file).exists():
               Path(args.progress_file).unlink()
               logger.info("Progress file cleaned up")
           
   except KeyboardInterrupt:
       logger.info("Process interrupted by user")
       logger.info("Progress has been saved. Use --resume to continue later.")
       sys.exit(1)
   except Exception as e:
       logger.error(f"Error during enrichment: {e}")
       sys.exit(1)


if __name__ == "__main__":
   main() 