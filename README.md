# ViDrive

A CLI application designed to strip away the guesswork for drivers in Vietnam. ViDrive looks at the long game — registration fees, maintenance, fuel, and the hidden costs of keeping a car on Vietnamese roads — providing insights beyond the sticker price.

## Current Functionality

> [!NOTE]
> Having to balance the time with school and other projects, I am unsure of my ability to commit the data-entry for all models without generative intelligence or professional data solutions. Therefore, for the foreseeable future, ViDrive will focus on providing precision for **mainstream and popular vehicles** sold in the Vietnamese market. For niche models, use the wizard with discretion.

* **Lifecycle TCO Analysis**: Generate a granular financial breakdown including acquisition, maintenance, and resale to uncover the true monthly cost of car ownership. Including:
* **True Opportunity Costs**: Optionally account for the "Lost Bank Interest" on your invested capital through an average compound interest model.
* **Tax Resolution**: Automated 3-tier registration fee detection across all Vietnamese administrative zones (Cities, towns, and rural districts).
* **City vs. Highway Physics**: Fuel costs estimation for ICE, HEV, and EV powertrains that accounts for non-linear consumption in urban gridlock vs. open-road drag.
* **Market-Linked Depreciation -> Resale**: Value retention predicted by geometric decay curves, validated against real-world 2026 used car market data. Now with ML.
* **Decision Support**: Conduct side-by-side comparisons of any two vehicles or use the **New Car Wizard** to test custom parameters for niche or future models.

## Installation & Setup

It is recommended to use a virtual environment:

```bash
# Clone the repository
git clone https://github.com/PearTr0191/ViDrive.git
cd ViDrive

# Setup environment
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Or if you have no need to be as conscious about your developer environment, just download and extract the .zip :\

## Usage

Run the application directly from your terminal:

```bash
python main.py
```

Follow the on-screen prompts to select/add your vehicle and input your variables. Use shorthands like `500m`, `1.2b`, or `15k` for easy value entry.

> [Version History moved to tag notes, see changelog for newest version at CHANGELOG.md]
