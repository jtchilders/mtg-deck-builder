# MTG Deck Analyzer

A comprehensive Magic: The Gathering deck analysis tool that uses OpenAI's LLM to provide detailed strategy analysis, strengths, weaknesses, and usage tips for your decks.

## Features

- **Comprehensive Deck Analysis**: Analyzes deck structure, mana curve, color distribution, and card synergies
- **LLM-Powered Insights**: Uses OpenAI's GPT models to provide expert-level strategy analysis
- **Detailed Reports**: Generates 10-section analysis covering archetype, strengths, weaknesses, matchups, and more
- **CSV Support**: Works with deck CSV files exported from ManaBox or similar tools
- **Flexible Output**: Saves analysis to files and displays results in console

## Scripts

### 1. `deck_analyzer.py` (Full Version)
The main script that uses OpenAI's LLM for comprehensive analysis.

**Requirements:**
- OpenAI API key set as environment variable `OPENAI_API_KEY`
- Python 3.7+
- Required packages: `pandas`, `openai`

**Usage:**
```bash
# Basic usage
python deck_analyzer.py deck.csv

# Save to specific file
python deck_analyzer.py deck.csv -o analysis.txt

# Verbose logging
python deck_analyzer.py deck.csv -v --output detailed_analysis.txt
```

### 2. `deck_analyzer_demo.py` (Demo Version)
A demo version that shows the analysis structure without requiring an OpenAI API key.

**Usage:**
```bash
# Basic usage
python deck_analyzer_demo.py deck.csv

# Save to specific file
python deck_analyzer_demo.py deck.csv -o demo_analysis.txt
```

## Input Format

The analyzer expects a CSV file with the following columns:
- `Name`: Card name
- `Quantity`: Number of copies
- `Mana Cost`: Mana cost (e.g., `{2}{W}`)
- `Type`: Card type (e.g., `Creature — Human Soldier`)
- `CMC`: Converted mana cost (numeric)
- `Colors`: Color identity (e.g., `W,U`)
- `Category`: Card category (e.g., `creatures`, `removal`, `lands`)
- `Rarity`: Card rarity
- `Set`: Set name
- `Oracle Text`: Card rules text
- `Power`: Creature power (if applicable)
- `Toughness`: Creature toughness (if applicable)

## Analysis Sections

The LLM generates a comprehensive 10-section analysis:

1. **Deck Archetype & Strategy**: Identifies the deck's primary strategy and win conditions
2. **Strengths**: Lists 5-7 key strengths and powerful card combinations
3. **Weaknesses & Vulnerabilities**: Identifies potential weaknesses and exploitable gaps
4. **Mana Base & Curve Analysis**: Evaluates mana curve, land count, and color distribution
5. **Key Card Interactions**: Highlights important synergies and optimal sequencing
6. **Sideboard Considerations**: Suggests sideboard strategies and problematic matchups
7. **Playing Tips & Strategy**: Provides specific piloting advice and mulligan strategies
8. **Matchup Analysis**: Rates performance against common archetypes (Aggro, Control, Midrange, Combo)
9. **Potential Improvements**: Suggests cards that could improve the deck
10. **Overall Assessment**: Final rating and competitive viability assessment

## Example Output

```
DECK ANALYSIS REQUEST

Deck Statistics:
- Total Cards: 60
- Unique Cards: 37
- Colors: W, U
- Average CMC: 3.11
- Lands: 25 (41.7%)
- Creatures: 19 (31.7%)

Mana Curve:
- CMC 1.0: 2 cards
- CMC 2.0: 12 cards
- CMC 3.0: 10 cards
...

=== ANALYSIS RESULTS ===

1. **DECK ARCHETYPE & STRATEGY**
   This appears to be an Azorius (White/Blue) Control deck...

2. **STRENGTHS**
   - Strong removal suite with exile effects...
   ...
```

## Setup

1. **Install Dependencies:**
   ```bash
   pip install pandas openai
   ```

2. **Set OpenAI API Key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

3. **Run the Analyzer:**
   ```bash
   python deck_analyzer.py your_deck.csv
   ```

## CSV Export from ManaBox

To export a deck from ManaBox:
1. Open your deck in ManaBox
2. Go to Export → CSV
3. Include all card details (Oracle text, mana cost, etc.)
4. Save the CSV file
5. Run the analyzer on the exported file

## Tips for Best Results

1. **Complete Card Data**: Ensure your CSV includes Oracle text and all card details
2. **Proper Categorization**: Categorize cards accurately (creatures, removal, lands, etc.)
3. **Accurate Mana Costs**: Include proper mana cost formatting
4. **Full Deck**: Include all 60 cards (or 100 for Commander)

## Troubleshooting

**"OpenAI API key not found"**
- Set the `OPENAI_API_KEY` environment variable
- Or use the demo version: `deck_analyzer_demo.py`

**"Missing required columns"**
- Ensure your CSV has all required columns
- Check column names match exactly (case-sensitive)

**"Error reading CSV file"**
- Verify the file path is correct
- Check that the CSV file is not corrupted
- Ensure the file has proper formatting

## Example Deck CSV Structure

```csv
Name,Quantity,Mana Cost,Type,CMC,Colors,Rarity,Set,Oracle Text,Power,Toughness,Category
Swords to Plowshares,1,{W},Instant,1.0,W,uncommon,March of the Machine Commander,Exile target creature. Its controller gains life equal to its power.,nan,nan,removal
Blade Splicer,1,{2}{W},Creature — Phyrexian Human Artificer,3.0,W,rare,March of the Machine Commander,When this creature enters, create a 3/3 colorless Phyrexian Golem artifact creature token. Golems you control have first strike.,1,1,creatures
Island,12,nan,Basic Land — Island,0.0,nan,common,Bloomburrow,({T}: Add {U}.),nan,nan,lands
```

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the deck analyzer!

## License

This project is open source and available under the MIT License. 