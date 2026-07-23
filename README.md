# ViDrive

A CLI application designed to strip away the guesswork for drivers in Vietnam. ViDrive looks at the long game — registration fees, maintenance, fuel, and the hidden costs of keeping a car on Vietnamese roads — providing insights beyond the sticker price.

## Current Functionality

> [!NOTE]
> As of 2:41am, 24/07/2026, ViDrive, as a CLI application, has reached the end of its active development timeline. The app will work fine as long as new data is pulled in on the user's end, but as a student project, this is it. I will seek field experts' advice and discuss initiatives to potentially bring ViDrive to more people, ideally in a more user-friendly and visually satisfying form factor, even though the code-ish font and sheer simplicity of Interactive Mode has grown on me hard.

> [!NOTE]
> Having to balance the time with school and other projects, I am unsure of my ability to commit the data-entry for all models without generative intelligence or professional data solutions. Therefore, for the foreseeable future, ViDrive will focus on providing precision for **mainstream and popular vehicles** sold in the Vietnamese market. For niche models, use the wizard with discretion.

* **Lifecycle TCO Analysis**: Generate a granular financial breakdown including acquisition, maintenance, and resale to uncover the true monthly cost of car ownership. Including:
* **True Opportunity Costs**: Optionally account for the "Lost Bank Interest" on your invested capital through an average compound interest model.
* **Tax Resolution**: Automated 3-tier registration fee detection across all Vietnamese administrative zones (Cities, towns, and rural districts).
* **City vs. Highway Physics**: Fuel costs estimation for ICE, HEV, and EV powertrains that accounts for non-linear consumption in urban gridlock vs. open-road drag.
* **Market-Linked Depreciation → Resale**: Value retention predicted by geometric decay curves, validated against real-world 2026 used car market data. Now with ML.
* **Decision Support**: Conduct side-by-side comparisons of any two vehicles or use the **New Car Wizard** to test custom parameters for niche or future models.

## Installation & Setup

It is recommended to use a virtual environment:

```bash
# Clone the repository (Git LFS required for ML models)
git clone https://github.com/PearTr0191/ViDrive.git
cd ViDrive

# Ensure Git LFS is initialized (install from https://git-lfs.com if needed)
git lfs install

# Pull the ML model files (resale_rf.pkl, resale_gb.pkl), internet connection required.
git lfs pull

# Setup environment
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Or if you have no need to be as conscious about your developer environment, just download and extract the .zip:

> ViDrive uses Git LFS to version the ML model files (`data/models/*.pkl`). Without Git LFS, you will receive pointer files instead of the actual models, and the app will fall back to parametric resale estimation.

## Usage

### Interactive Mode

Simply run the application and follow the on-screen prompts:

```bash
python main.py
```

Select from 9 options:

| # | Option | Description |
|---|--------|-------------|
| 1 | Single car | Analyze one vehicle |
| 2 | Compare | Side-by-side comparison (2–10 cars) |
| 3 | Wizard | Build a custom car with manual parameters |
| 4 | List cars | Browse all available vehicles |
| 5 | Search | Find cars by keyword |
| 6 | Saved results | View, delete, or re-calculate saved results |
| 7 | Cities | List supported cities and area tiers |
| 8 | Demo | Run a randomized pre-filled calculation |
| 9 | Exit | Quit the application |

Use shorthands like `500m`, `1.2b`, or `15k` for easy value entry.

### CLI Arguments

Besides the signature interactive mode, ViDrive supports a full CLI as-is for scripting and automation:

```bash
# Single car analysis
python main.py --car vios_2026 --city hanoi --km 15000 --years 5

# Compare 2–10 cars
python main.py --compare vios_2026 city_2026 accent_2026 --city hanoi

# Run randomized demo
python main.py --demo --lang en

# Search cars by keyword
python main.py --search SUV

# List all cars or cities
python main.py --list-cars
python main.py --list-cities

# View saved results
python main.py --history

# Save a result and export to CSV
python main.py --car vios_2026 --csv --save my_result

# Include opportunity cost and show calculation breakdown
python main.py --car vios_2026 --opp-cost --verbose
```

| Flag | Description |
|------|-------------|
| `--car` | Single car ID to analyze |
| `--compare` | 2–10 car IDs for comparison |
| `--city` | City/Province (default: `hanoi`) |
| `--km` | Annual kilometers (default: `15000`) |
| `--years` | Years of ownership (default: `5`) |
| `--area` | Area tier: 1 (Central), 2 (Provincial), 3 (Rural) |
| `--city-ratio` | City driving percent, 0–100 (default: `30`) |
| `--opp-cost` | Include opportunity cost |
| `--verbose` | Show calculation breakdown with formulas |
| `--lang` | Language: `en` or `vi` |
| `--list-cities` | List supported cities and exit |
| `--list-cars` | List all cars and exit |
| `--search` | Search cars by keyword and exit |
| `--demo` | Run randomized demo calculation |
| `--save` | Save result to history with given name |
| `--history` | List saved results and exit |
| `--csv` | Export single result to CSV |
| `--csv-compare` | Export comparison to CSV |

## Project Structure

```
ViDrive/
├── main.py                    # Entry point (interactive + CLI)
├── src/
│   ├── __init__.py
│   ├── calculations.py        # TCO, loan, fuel, registration, resale
│   ├── cli.py                 # Display, input, menu, search, history
│   ├── config.py              # Constants, fees, rates, maps
│   ├── export.py              # CSV export
│   ├── i18n.py                # Bilingual translations (en/vi)
│   ├── ml_model.py            # Resale predictor (RF + GB ensemble)
│   ├── pdf_export.py          # PDF/plain-text report generation
│   ├── persistence.py         # Save/load/delete history
│   └── wizard.py              # Interactive custom car wizard
├── data/
│   ├── cars.json              # Vehicle database
│   └── models/                # ML model artifacts (Git LFS)
├── CHANGELOG.md               # Full change history
├── requirements.txt
└── README.md
```

## Requirements

* Python 3.10+
* Git LFS (for ML model files)
* `pdflatex` (optional, for PDF export — falls back to plain text if unavailable)

## License

See the [GitHub repository](https://github.com/PearTr0191/ViDrive) for license information.
