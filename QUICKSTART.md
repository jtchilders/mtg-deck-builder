# MTG Deck Builder - Quick Start Guide

## Overview

This project helps you build Magic: The Gathering decks from your collection using AI-powered suggestions. It consists of two main phases:

1. **Phase 1**: Enrich your ManaBox collection with detailed card data
2. **Phase 2**: Use AI to suggest complementary cards for deck building

## Quick Setup

### 1. Environment Setup

```bash
# Activate virtual environment
source ./venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Enrich Your Collection (Phase 1)

If you haven't already enriched your collection:

```bash
# Enrich your ManaBox CSV with Scryfall data
python enrich_cards.py --input manabox-db.csv --output enriched.csv
```

### 3. Explore Your Collection

```bash
# See collection statistics
python collection_filter.py --stats

# Find white creatures with CMC 2 or less
python collection_filter.py --colors W --types Creature --cmc-max 2

# Search for specific cards
python collection_filter.py --search "Paladin"
```

### 4. Get AI Deck Suggestions (Phase 2)

**Setup OpenAI API:**
1. Get an OpenAI API key from [OpenAI](https://platform.openai.com/)
2. Set it as an environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Or add it to your shell profile for persistence:
   ```bash
   echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
   source ~/.bashrc
   ```
   
   **Alternative:** Create a `.env` file in the project root and export it:
   ```bash
   echo 'OPENAI_API_KEY="your-api-key-here"' > .env
   export $(cat .env | xargs)
   ```

**Get deck suggestions:**
```bash
# Basic suggestions
python deck_builder.py --seeds "Paladin Class" "Kitesail Cleric"

# More suggestions with details
python deck_builder.py --seeds "Speaker of the Heavens" --count 12 --details

# Find synergistic pairs
python deck_builder.py --pairs 5

# Find synergistic triplets
python deck_builder.py --triplets 3
```

## Example Workflow

1. **Start with a card you like:**
   ```bash
   python collection_filter.py --search "Paladin"
   ```

2. **Find complementary cards:**
   ```bash
   python deck_builder.py --seeds "Paladin Class" "Kitesail Cleric"
   ```

3. **Find synergistic pairs:**
   ```bash
   python deck_builder.py --pairs 5
   ```

4. **Explore your options:**
   ```bash
   python collection_filter.py --colors W --types Creature --cmc-max 3
   ```

5. **Get more suggestions:**
   ```bash
   python deck_builder.py --seeds "Paladin Class" "Speaker of the Heavens" --count 15
   ```

6. **Find powerful triplets:**
   ```bash
   python deck_builder.py --triplets 3 --details
   ```

## Key Features

- **Collection Enrichment**: Adds mana costs, oracle text, and other details to your ManaBox export
- **AI-Powered Suggestions**: Uses OpenAI's GPT models to suggest synergistic cards
- **Synergistic Pairs & Triplets**: Find powerful card combinations in your collection
- **Collection Filtering**: Explore your collection by color, type, CMC, rarity, and more
- **Detailed Card Info**: View full card details including oracle text and stats
- **Error Handling**: Graceful handling of missing cards and API errors

## Troubleshooting

**"OpenAI API key not found"**: Set the `OPENAI_API_KEY` environment variable

**"Card not found"**: Check the card name spelling or use the collection filter to search

**"No suggestions received"**: Check your internet connection and OpenAI API key

## Next Steps

- Try different seed card combinations
- Use the collection filter to explore your options
- Build multiple deck variations
- Experiment with different archetypes (aggro, control, etc.)

For more detailed information, see the main [README.md](README.md). 