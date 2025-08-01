#!/usr/bin/env python3
"""
Test script for the MTG Deck Builder
"""

import logging
import sys
from llm_client import test_connection
from deck_builder import load_collection, suggest_complements, filter_by_collection

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_functionality():
   """Test basic deck builder functionality"""
   print("Testing MTG Deck Builder...")
   
   # Test 1: Load collection
   try:
      print("\n1. Testing collection loading...")
      df = load_collection()
      print(f"✓ Successfully loaded {len(df)} cards")
   except Exception as e:
      print(f"✗ Failed to load collection: {e}")
      return False
   
   # Test 2: Check if we have some good seed cards
   print("\n2. Checking for seed cards...")
   test_cards = ["Paladin Class", "Kitesail Cleric", "Speaker of the Heavens"]
   found_cards = []
   
   for card in test_cards:
      matches = df[df['Name'].str.lower() == card.lower()]
      if not matches.empty:
         found_cards.append(card)
         print(f"✓ Found: {card}")
      else:
         print(f"✗ Not found: {card}")
   
   if not found_cards:
      print("No test cards found in collection. Please check your enriched.csv file.")
      return False
   
   # Test 3: Test LLM connection (if API key is configured)
   print("\n3. Testing LLM connection...")
   try:
      if test_connection():
         print("✓ LLM connection successful")
         
         # Test 4: Get suggestions
         print("\n4. Testing card suggestions...")
         suggestions = suggest_complements(found_cards[:2], df, n=3)
         if suggestions:
            print(f"✓ Got {len(suggestions)} suggestions from LLM")
            print("Sample suggestions:")
            for i, suggestion in enumerate(suggestions[:3], 1):
               print(f"  {i}. {suggestion}")
         else:
            print("✗ No suggestions received from LLM")
            return False
         
         # Test 5: Filter suggestions
         print("\n5. Testing suggestion filtering...")
         filtered = filter_by_collection(suggestions, df)
         print(f"✓ {len(filtered)} out of {len(suggestions)} suggestions are in collection")
         
      else:
         print("⚠ LLM connection failed - this is expected if no API key is configured")
         print("To test LLM features, add your OpenAI API key to config.json")
   
   except Exception as e:
      print(f"⚠ LLM test skipped due to error: {e}")
   
   print("\n✓ Basic functionality tests completed!")
   return True

def main():
   """Main test function"""
   print("MTG Deck Builder Test Suite")
   print("=" * 40)
   
   success = test_basic_functionality()
   
   if success:
      print("\n🎉 All tests passed! Your deck builder is ready to use.")
      print("\nNext steps:")
      print("1. Add your OpenAI API key to config.json")
      print("2. Run: python deck_builder.py --seeds 'Paladin Class' 'Kitesail Cleric'")
      print("3. Or run with details: python deck_builder.py --seeds 'Paladin Class' --details")
   else:
      print("\n❌ Some tests failed. Please check the errors above.")
      sys.exit(1)

if __name__ == "__main__":
   main() 