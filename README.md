# MTG Deck Builder - Production Enrichment Tool

A production-ready Python tool to enrich ManaBox CSV exports with additional card data from the Scryfall API.

## Overview

This project takes your ManaBox collection export and enriches it with additional card information such as:
- Mana cost
- Type line
- Oracle text
- Power/Toughness
- Converted mana cost (CMC)
- Colors and color identity
- Rarity
- Loyalty (for planeswalkers)
- Set information
- Image URLs

## Installation

1. **Activate your virtual environment:**
   ```bash
   source ./venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Enrich your ManaBox CSV with Scryfall data:

```bash
python enrich_cards.py --input manabox-db.csv --output enriched.csv
```

### Advanced Usage

With debug logging and progress tracking:

```bash
python enrich_cards.py -i manabox-db.csv -o enriched.csv --log-level DEBUG
```

Resume from a previous run:

```bash
python enrich_cards.py -i manabox-db.csv -o enriched.csv --resume
```

Using a configuration file:

```bash
python enrich_cards.py -i manabox-db.csv -o enriched.csv --config config.json
```

### Command Line Options

- `-i, --input`: Input ManaBox CSV file path (required)
- `-o, --output`: Output enriched CSV file path (required)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, default: INFO)
- `--log-file`: Log file path (optional)
- `--resume`: Resume from previous run using progress file
- `--progress-file`: Progress file path (default: enrichment_progress.json)
- `--rate-limit`: Rate limit delay in seconds (default: 0.1)
- `--max-retries`: Maximum retries for failed requests (default: 3)
- `--config`: Configuration file path (JSON format)

## Project Structure

```
mtg-deck-builder/
├── src/                    # Source modules
│   ├── __init__.py         # Package initialization
│   ├── data_ingest.py      # CSV reading and validation
│   ├── scryfall_client.py  # Scryfall API client
│   ├── transformer.py      # Data extraction and transformation
│   ├── llm_client.py       # OpenAI API client for deck building
│   └── collection_filter.py # Collection filtering and exploration utility
├── enrich_cards.py         # Main enrichment script (production-ready)
├── deck_builder.py         # Deck building assistant with LLM integration
├── example_usage.py        # Example usage script
├── test_deck_builder.py    # Test script for deck builder functionality
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── manabox-db.csv          # Your ManaBox export
├── enriched.csv            # Enriched collection data
└── README.md              # This file
```

## Architecture

The production-ready implementation follows a robust architecture:

1. **src/data_ingest.py**: Reads ManaBox CSV into pandas DataFrame and validates the data
2. **src/scryfall_client.py**: Handles HTTP calls to Scryfall API with proper error handling
3. **src/transformer.py**: Extracts desired fields from Scryfall JSON responses
4. **enrich_cards.py**: Orchestrates the entire enrichment process with production features

## Features

- **Rate Limiting**: Respects Scryfall's 10 requests/second limit with configurable delays
- **Error Handling**: Graceful handling of network errors and missing cards with retry logic
- **Logging**: Comprehensive logging with configurable levels and file output
- **Validation**: Input data validation and error reporting
- **Progress Tracking**: Visual progress bars with tqdm and resume capability
- **Resume Capability**: Can resume interrupted runs from where they left off
- **Configuration Files**: Support for JSON configuration files
- **Retry Logic**: Configurable retry attempts for failed requests
- **Progress Persistence**: Saves progress to JSON file for recovery

## Output

The enriched CSV will contain all original columns plus the following new columns:

- `mana_cost`: The card's mana cost (e.g., "{1}{W}")
- `type_line`: Card type (e.g., "Creature — Human Cleric")
- `oracle_text`: The card's rules text
- `power`: Power (for creatures)
- `toughness`: Toughness (for creatures)
- `cmc`: Converted mana cost
- `colors`: Card colors (comma-separated)
- `color_identity`: Color identity (comma-separated)
- `rarity`: Card rarity
- `loyalty`: Loyalty (for planeswalkers)
- `set_name`: Full set name
- `collector_number`: Collector number in the set
- `image_uris`: Image URLs (comma-separated)

## Phase 2: Deck Building Assistant

The deck building assistant uses OpenAI's LLM to suggest complementary cards from your collection.

### Setup

1. **Set your OpenAI API key as an environment variable:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Or add it to your shell profile (e.g., `~/.bashrc`, `~/.zshrc`):
   ```bash
   echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
   source ~/.bashrc
   ```
   
   **Note:** The API key can also be added to `config.json` as a fallback, but environment variables are preferred for security.
   
   **Alternative:** Create a `.env` file in the project root and export it:
   ```bash
   echo 'OPENAI_API_KEY="your-api-key-here"' > .env
   export $(cat .env | xargs)
   ```

2. **Test the setup:**
   ```bash
   python test_deck_builder.py
   ```

### Usage

**Basic deck suggestions:**
```bash
python deck_builder.py --seeds "Paladin Class" "Kitesail Cleric"
```

**Get more suggestions:**
```bash
python deck_builder.py --seeds "Speaker of the Heavens" --count 12
```

**Show detailed card information:**
```bash
python deck_builder.py --seeds "Paladin Class" --details
```

**Find synergistic card pairs:**
```bash
python deck_builder.py --pairs 5
```

**Find synergistic card triplets:**
```bash
python deck_builder.py --triplets 3
```

**Find pairs with detailed information:**
```bash
python deck_builder.py --pairs 3 --details
```

### Collection Filtering

**Show collection statistics:**
```bash
python collection_filter.py --stats
```

**Filter by color and type:**
```bash
python collection_filter.py --colors W --types Creature --cmc-max 2
```

**Search by name:**
```bash
python collection_filter.py --search "Paladin"
```

### Command Line Options

**Deck Builder:**
- `--seeds, -s`: Seed card names to build around
- `--count, -c`: Number of suggestions to request (default: 8)
- `--collection`: Path to enriched collection CSV (default: enriched.csv)
- `--details, -d`: Show detailed information for suggested cards
- `--pairs, -p`: Find N synergistic card pairs
- `--triplets, -t`: Find N synergistic card triplets

**Collection Filter:**
- `--colors, -c`: Filter by colors (W, U, B, R, G)
- `--types, -t`: Filter by card types (Creature, Instant, Sorcery, etc.)
- `--cmc-min/--cmc-max`: Filter by converted mana cost range
- `--rarities, -r`: Filter by rarities (common, uncommon, rare, mythic)
- `--sets, -s`: Filter by set names
- `--search`: Search by card name
- `--limit, -l`: Maximum number of results to show (default: 20)
- `--details, -d`: Show detailed card information
- `--stats`: Show collection statistics

### Features

- **LLM-Powered Suggestions**: Uses OpenAI's GPT models to suggest synergistic cards
- **Synergistic Pairs & Triplets**: Find powerful card combinations in your collection
- **Collection Filtering**: Only suggests cards you actually own
- **Detailed Card Info**: View mana costs, oracle text, and other card details
- **Error Handling**: Graceful handling of API errors and missing cards
- **Logging**: Comprehensive logging for debugging

## Next Steps

Future phases will add:

- **Phase 3**: Web UI and advanced deck analysis
- **Phase 4**: Performance optimizations and caching
- **Phase 5**: Advanced deck-building algorithms and recommendations

## Troubleshooting

### Common Issues

1. **Network errors**: Check your internet connection and try again
2. **Rate limiting**: The script includes built-in rate limiting, but if you get errors, try running with fewer cards
3. **Missing cards**: Some cards might not be found in Scryfall - these will be logged as warnings

### Debug Mode

Run with debug logging to see detailed information:

```bash
python enrich_cards.py -i manabox-db.csv -o enriched.csv --log-level DEBUG
```

### Configuration File

Create a `config.json` file to set default options:

```json
{
   "log_level": "INFO",
   "log_file": "enrichment.log",
   "rate_limit": 0.1,
   "max_retries": 3,
   "progress_file": "enrichment_progress.json"
}
```

## License

This project is for personal use. Please respect Scryfall's API terms of service. 