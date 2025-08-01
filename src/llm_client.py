from openai import OpenAI
import time
import json
import logging
import os
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
   """Load configuration from config.json and environment variables"""
   config = {}
   
   # Load from config.json
   try:
      with open('config.json', 'r') as f:
         config = json.load(f)
   except FileNotFoundError:
      logger.warning("config.json not found, using environment variables only")
   
   # Override with environment variables (environment takes precedence)
   if 'OPENAI_API_KEY' in os.environ:
      config['openai_api_key'] = os.environ['OPENAI_API_KEY']
   
   return config

def chat_prompt(messages: List[Dict[str, str]], retries: int = 3, backoff: float = 1.0) -> str:
   """
   Send a chat prompt to OpenAI API with retry logic
   
   Args:
      messages: List of message dictionaries with 'role' and 'content'
      retries: Number of retry attempts
      backoff: Initial backoff time in seconds
   
   Returns:
      The response content from the API
   
   Raises:
      Exception: If all retries are exhausted
   """
   config = load_config()
   api_key = config.get('openai_api_key')
   model = config.get('openai_model', 'gpt-4o-mini')
   temperature = config.get('openai_temperature', 0.7)
   
   if not api_key:
      raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable or add it to config.json.")
   
   # Create OpenAI client
   client = OpenAI(api_key=api_key)
   
   for attempt in range(retries):
      try:
         logger.info(f"Sending chat prompt to OpenAI (attempt {attempt + 1}/{retries})")
         response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
         )
         response_content = response.choices[0].message.content
         logger.info("Successfully received response from OpenAI")
         return response_content
      except Exception as e:
         logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
         if attempt + 1 == retries:
            logger.error(f"All {retries} attempts failed. Last error: {str(e)}")
            raise
         sleep_time = backoff * (2 ** attempt)
         logger.info(f"Waiting {sleep_time} seconds before retry...")
         time.sleep(sleep_time)

def parse_card_suggestions(response: str) -> List[str]:
   """
   Parse card names from LLM response
   
   Args:
      response: The raw response from the LLM
   
   Returns:
      List of card names extracted from the response
   """
   suggestions = []
   for line in response.splitlines():
      line = line.strip()
      if line and line[0].isdigit():
         # Try to extract card name after the number
         parts = line.split(".", 1)
         if len(parts) > 1:
            # Remove the number and any rationale text
            name_part = parts[1].strip()
            # Remove markdown formatting (** **)
            name_part = name_part.replace("**", "").strip()
            # Split on common separators and take the first part
            for separator in [" — ", " - ", ":", " (", " [", " - "]:
               if separator in name_part:
                  name_part = name_part.split(separator)[0]
            suggestions.append(name_part.strip())
   
   return suggestions

def parse_card_pairs(response: str) -> List[tuple]:
   """
   Parse card pairs and their explanations from LLM response
   
   Args:
      response: The raw response from the LLM
   
   Returns:
      List of tuples: (card_pair, explanation) where card_pair is a list of 2 card names
   """
   pairs = []
   for line in response.splitlines():
      line = line.strip()
      if line and line[0].isdigit():
         # Try to extract card names after the number
         parts = line.split(".", 1)
         if len(parts) > 1:
            content = parts[1].strip()
            # Look for the pattern "Card A + Card B - Explanation"
            if " + " in content and " - " in content:
               # Split on " - " to separate cards from explanation
               cards_part = content.split(" - ")[0].strip()
               explanation = content.split(" - ", 1)[1].strip() if " - " in content else ""
               # Split on " + " to get individual cards
               card_names = [card.strip() for card in cards_part.split(" + ")]
               # Remove markdown formatting
               card_names = [name.replace("**", "").strip() for name in card_names]
               if len(card_names) == 2:
                  pairs.append((card_names, explanation))
   
   return pairs

def parse_card_triplets(response: str) -> List[tuple]:
   """
   Parse card triplets and their explanations from LLM response
   
   Args:
      response: The raw response from the LLM
   
   Returns:
      List of tuples: (card_triplet, explanation) where card_triplet is a list of 3 card names
   """
   triplets = []
   for line in response.splitlines():
      line = line.strip()
      if line and line[0].isdigit():
         # Try to extract card names after the number
         parts = line.split(".", 1)
         if len(parts) > 1:
            content = parts[1].strip()
            # Look for the pattern "Card A + Card B + Card C - Explanation"
            if " + " in content and " - " in content:
               # Split on " - " to separate cards from explanation
               cards_part = content.split(" - ")[0].strip()
               explanation = content.split(" - ", 1)[1].strip() if " - " in content else ""
               # Split on " + " to get individual cards
               card_names = [card.strip() for card in cards_part.split(" + ")]
               # Remove markdown formatting
               card_names = [name.replace("**", "").strip() for name in card_names]
               if len(card_names) == 3:
                  triplets.append((card_names, explanation))
   
   return triplets

def test_connection() -> bool:
   """
   Test the OpenAI API connection
   
   Returns:
      True if connection successful, False otherwise
   """
   try:
      messages = [
         {"role": "system", "content": "You are a helpful assistant."},
         {"role": "user", "content": "Hello! Please respond with 'Connection successful' if you can see this message."}
      ]
      response = chat_prompt(messages)
      logger.info(f"Connection test response: {response}")
      return "Connection successful" in response
   except Exception as e:
      logger.error(f"Connection test failed: {str(e)}")
      return False 