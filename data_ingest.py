"""
Data ingestion module for MTG deck builder.
Reads ManaBox CSV exports into pandas DataFrames.
"""

import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def read_manabox_csv(file_path: str) -> pd.DataFrame:
   """
   Read a ManaBox CSV export into a pandas DataFrame.
   
   Args:
       file_path: Path to the ManaBox CSV file
       
   Returns:
       DataFrame containing the card data
   """
   try:
       logger.info(f"Reading ManaBox CSV from {file_path}")
       df = pd.read_csv(file_path)
       
       # Validate required columns
       required_columns = ['Name', 'Set code', 'Scryfall ID']
       missing_columns = [col for col in required_columns if col not in df.columns]
       
       if missing_columns:
           raise ValueError(f"Missing required columns: {missing_columns}")
       
       logger.info(f"Successfully loaded {len(df)} cards from CSV")
       return df
       
   except FileNotFoundError:
       logger.error(f"CSV file not found: {file_path}")
       raise
   except Exception as e:
       logger.error(f"Error reading CSV file: {e}")
       raise


def validate_card_data(df: pd.DataFrame) -> bool:
   """
   Validate that the DataFrame contains valid card data.
   
   Args:
       df: DataFrame to validate
       
   Returns:
       True if valid, raises exception if not
   """
   # Check for required columns
   required_columns = ['Name', 'Set code', 'Scryfall ID']
   for col in required_columns:
       if col not in df.columns:
           raise ValueError(f"Missing required column: {col}")
   
   # Check for non-empty values in key columns
   if df['Name'].isna().any():
       logger.warning("Found cards with missing names")
   
   if df['Scryfall ID'].isna().any():
       logger.warning("Found cards with missing Scryfall IDs")
   
   # Check for duplicate Scryfall IDs (should be unique)
   duplicate_ids = df['Scryfall ID'].duplicated().sum()
   if duplicate_ids > 0:
       logger.warning(f"Found {duplicate_ids} duplicate Scryfall IDs")
   
   return True 