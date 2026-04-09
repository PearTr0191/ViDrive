# ViDrive

A CLI application designed to strip away the guesswork for drivers in Vietnam. ViDrive looks at the long game — registration fees, maintenance, fuel, and the hidden costs of keeping a car on Vietnamese roads — providing insights beyond the sticker price.

## Current Functionality

> [!NOTE]
> Having to balance the time with school and other projects, I am unsure of my ability to commit the data-entry for all models without generative intelligence or professional data solutions. Therefore, for the foreseeable future, ViDrive will focus on providing precision for **mainstream and popular vehicles** sold in the Vietnamese market. For niche models, use the wizard with discretion.

* **Lifecycle TCO Analysis**: Generate a granular financial breakdown including acquisition, maintenance, and resale to uncover the true monthly cost of car ownership. Including:
*    **True Opportunity Costs**: Accounts for the "Lost Bank Interest" on your invested capital through an average compound interest model.
*    **Tax Resolution**: Automated 3-tier registration fee detection across all Vietnamese administrative zones (Cities, towns, and rural districts).
*    **City vs. Highway Physics**: Fuel costs estimation for ICE, HEV, and EV powertrains that accounts for non-linear consumption in urban gridlock vs. open-road drag.
*    **Market-Linked Depreciation**: Value retention predicted by geometric decay curves, validated against real-world 2026 used car market data.
*    **Flood Risk Provisions**: Built-in environmental risk assessment for flood-prone metropolitan areas.
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
* **CSV/PDF Export:** Generation of raw data or reports for non-technical users.
* **Vietnamese support:** This app is as close to ready as the casual buyer needs now, so it's time I finally make it accessible to the right people

---

## Version History

### [v0.4.0] - 2026-04-09
* **Schema-Driven Architecture**: Decoupled vehicle logic from code. Model-specific heuristics (segments, liquidity premiums) are now offloaded to `cars.json` metadata.
* **Pythonic Refactor (with Copilot)**: Rethought CLI middleware using modern idioms, `pathlib` integration, and a unified input pipeline.
* **Flood Risk Assessment**: Added potential repair risk costs/provision estimates for flood-prone metropolitan areas (Hanoi/HCMC).
* **True Cost of Opportunities**: Integrated a compound interest modeling for **Capital Opportunity Cost** calculations.
* **2026 Fleet Expansion**: Integrated 34+ mainstream models.
* **City v Highway**: Modeled energy consumption for ICE, HEV, and EV based on urban gridlock vs. open-road drag after basic physics.
* **Variables Fine-tuning**: Tailored parameters and constants for the mainstream vehicles, achieved **93.10% validation success** via 5-year back-testing against April 2026 market benchmarks (<5% variance).

### [v0.3.1] - 2026-04-04
* **Fuel Costs**: Implemented 9-month weighted average constants (Petrol: 23,850 VND, EV: 2,150 VND) for imminent precision.
* **Provincial Differentiation**: Added interactive Area 2/3 (City/Town vs. Rural District) selector.

### [v0.3.0] - 2026-03-30
* Initial 3-tier regional fee system, automated area-tier detection, and parametric depreciation curves.

### [v0.2.0] - 2026-03-15
* **Depreciation**: Replaced linear model with parametric decay (`DEPRECIATION_EQ_PARAMS`).
* **Wizard**: Improved the Custom Car Wizard with smart input parsing.
* **EV Logic**: Added registration discount handling post-exemption (50% rate); removed deprecated battery rent policy for VinFast EVs.

### [v0.1.0] - 2026-02-22
* **Initial Release**: Baseline TCO calculation with hardcoded standard fees and basic fuel/maintenance projections.
