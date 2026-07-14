# ViDrive

A CLI application designed to strip away the guesswork for drivers in Vietnam. ViDrive looks at the long game — registration fees, maintenance, fuel, and the hidden costs of keeping a car on Vietnamese roads — providing insights beyond the sticker price.

## Current Functionality

> [!NOTE]
> Having to balance the time with school and other projects, I am unsure of my ability to commit the data-entry for all models without generative intelligence or professional data solutions. Therefore, for the foreseeable future, ViDrive will focus on providing precision for **mainstream and popular vehicles** sold in the Vietnamese market. For niche models, use the wizard with discretion.

* **Lifecycle TCO Analysis**: Generate a granular financial breakdown including acquisition, maintenance, and resale to uncover the true monthly cost of car ownership. Including:
* **True Opportunity Costs**: Accounts for the "Lost Bank Interest" on your invested capital through an average compound interest model.
* **Tax Resolution**: Automated 3-tier registration fee detection across all Vietnamese administrative zones (Cities, towns, and rural districts).
* **City vs. Highway Physics**: Fuel costs estimation for ICE, HEV, and EV powertrains that accounts for non-linear consumption in urban gridlock vs. open-road drag.
* **Market-Linked Depreciation**: Value retention predicted by geometric decay curves, validated against real-world 2026 used car market data.
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

## Usage

Run the application directly from your terminal:

```bash
python main.py
```

Follow the on-screen prompts to select/add your vehicle and input your variables. Use shorthands like `500m`, `1.2b`, or `15k` for easy value entry.

## Coming Soon

* **ML resale:** The current resale algorithms are parametric, leaving room for sufficient MAE, even if by the percent, that will hurt owner's pocket considerably. I'm thinking of using ML to predict resale values based on market data, but then I will need to learn much more.
* **CSV/PDF Export:** Generation of raw data or reports for non-technical users.

---

## Version History

### [v0.4.2] - 2026-07-02

* **Added Vietnamese support**: Không giải thích gì thêm;>
* **More intuitive default**: While the lost opportunity costs feature provides an insightful data point, defaulting to including them in the final calculations (TCO -> True Financial Impact) is causing confusion among the testers. Therefore, this option now defaults to no.
* **Removed Flood Risk Assessment**: Damage of this nature can vary widely, and as I've found out the hard way at 1am, can't be predicted reliably. The 120M VND placeholder is as useless as what I intend to replace it with, so it goes away.
