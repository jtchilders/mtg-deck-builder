# MTG Deck Builder
Author: J. Taylor Childers with the help of Cursor AI.
A Python tool to enrich ManaBox CSV exports with Scryfall data and build decks using AI suggestions.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt
```

## Phase 1: Enrich Collection

I have a collection of cards that I had added to my ManaBox collection. I can export the collection as a CSV file, however it doesn't include card details for deck building, but it does uniquely identify each card. So the first step is to use Scryfall to add the card details to the CSV file.

Enrich your ManaBox CSV with card details from Scryfall:

```bash
python enrich_cards.py --input manabox-db.csv --output enriched.csv
```

**Options:**
- `-i, --input`: Input ManaBox CSV file (required)
- `-o, --output`: Output enriched CSV file (required)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--resume`: Resume from previous run

## Phase 2: Deck Building

The deck builder now supports building complete 60-card decks using a multi-stage AI approach:

1. **Archetype Selection**: AI suggests viable deck archetypes for your colors
2. **Strategy Planning**: Defines optimal card distribution by category
3. **Category Building**: Selects the best cards for each category (creatures, removal, etc.)
4. **Land Addition**: Automatically adds appropriate basic lands
5. **Curve Analysis**: Analyzes and displays the deck's mana curve

### Setup OpenAI API Key

```bash
export OPENAI_API_BASE="https://api.openai.com/v1"
export OPENAI_API_KEY="your-api-key-here"
```

### Explore Collection

```bash
# Show collection stats
python collection_filter.py --stats

# Filter by color and type
python collection_filter.py --colors W --types Creature --cmc-max 2

# Search by name
python collection_filter.py --search "Paladin"
```

### Get AI Suggestions

```bash
# Basic suggestions
python deck_builder.py --seeds "Paladin Class" "Kitesail Cleric"

# More suggestions with details
python deck_builder.py --seeds "Speaker of the Heavens" --count 12 --details

# Find synergistic pairs
python deck_builder.py --pairs 5

# Find synergistic triplets
python deck_builder.py --triplets 3

# Build a complete 60-card deck
python deck_builder.py --build-deck W U --details

# Build deck with different colors
python deck_builder.py --build-deck R G -v

# Export deck to CSV
python deck_builder.py --build-deck W U --export-csv my_deck.csv
```

## Command Options

**Deck Builder:**
- `--seeds, -s`: Seed card names
- `--count, -c`: Number of suggestions (default: 8)
- `--details, -d`: Show detailed card info
- `--pairs, -p`: Find N synergistic pairs
- `--triplets, -t`: Find N synergistic triplets
- `--build-deck, -b`: Build a complete 60-card deck for specified colors
- `--export-csv, -e`: Export deck/suggestions to CSV file

**Collection Filter:**
- `--colors, -c`: Filter by colors (W, U, B, R, G)
- `--types, -t`: Filter by card types
- `--cmc-min/--cmc-max`: Filter by CMC range
- `--search`: Search by card name
- `--stats`: Show collection statistics

## Example Workflow

1. Enrich your collection: `python enrich_cards.py -i manabox-db.csv -o enriched.csv`
2. Explore options: `python collection_filter.py --search "Paladin"`
3. Get suggestions: `python deck_builder.py --seeds "Paladin Class" --count 10`
4. Find synergies: `python deck_builder.py --pairs 5 --details`
5. Build complete deck: `python deck_builder.py --build-deck W U --details`
6. Export deck: `python deck_builder.py --build-deck W U --export-csv my_deck.csv`

## CSV Export

The deck builder can export decks and suggestions to CSV format for easy import into other tools:

```bash
# Export a complete deck
python deck_builder.py --build-deck W U --export-csv my_deck.csv

# Export card suggestions
python deck_builder.py --seeds "Paladin Class" --export-csv suggestions.csv

# Export synergistic pairs
python deck_builder.py --pairs 5 --export-csv pairs.csv
```

The CSV includes:
- Card details (name, mana cost, type, CMC, colors, rarity, set, oracle text)
- Quantity of each card
- Card categories (creatures, removal, card draw, utility, lands)
- Deck metadata (archetype, colors, strategy, mana curve)

## Testing Without API Key

To test the deck building functionality without setting up the OpenAI API key:

```bash
# Run the demo to see how deck building works
python demo_deck_builder.py
```

This will create a sample deck using your collection data and show the deck building process in action.

## Troubleshooting

- **"OpenAI API key not found"**: Set `OPENAI_API_KEY` environment variable
- **"Card not found"**: Check spelling or use collection filter to search
- **Network errors**: Check internet connection and try again 