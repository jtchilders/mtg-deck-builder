# MTG Deck Builder

A Python tool to enrich ManaBox CSV exports with Scryfall data and build decks using AI suggestions.

## Setup

```bash
# Activate virtual environment
source ./venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Phase 1: Enrich Collection

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

### Setup OpenAI API

```bash
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
```

## Command Options

**Deck Builder:**
- `--seeds, -s`: Seed card names
- `--count, -c`: Number of suggestions (default: 8)
- `--details, -d`: Show detailed card info
- `--pairs, -p`: Find N synergistic pairs
- `--triplets, -t`: Find N synergistic triplets

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

## Troubleshooting

- **"OpenAI API key not found"**: Set `OPENAI_API_KEY` environment variable
- **"Card not found"**: Check spelling or use collection filter to search
- **Network errors**: Check internet connection and try again 