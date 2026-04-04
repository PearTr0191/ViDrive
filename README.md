# ViDrive

A CLI application designed to strip away the guesswork for drivers in Vietnam. ViDrive looks at the long game — registration fees, maintenance, fuel, and the hidden costs of keeping a car on Vietnamese roads — providing insights beyond the sticker price.

## Current Functionality
* **Calculate Total Cost of Ownership (TCO):** Generate a detailed financial breakdown to uncover the true price of keeping a car.
* **Resolve Registration Fees by Location:** Enter your city or province to automatically identify the correct 3-tier registration costs for any vehicle.
* **Project Your Car's Resale Value:** Predict future trade-in prices using logarithmic decay models specifically tuned for the Vietnamese market.
* **Model Custom Vehicle Profiles:** Input your own pricing, fuel efficiency, and maintenance data to analyze cars not found in the standard database using the interactive wizard.
* **Compare Costs Side-by-Side:** Benchmark any two vehicles—such as a petrol-powered model vs. an electric alternative—to see which one is more cost-effective for your specific mileage and region.

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
* **Opportunity Cost (TVM):** Lost gains if capital was kept in a savings account (~6-8%) vs. a depreciating asset.
* **Urban Stress Factor:** Multipliers for engine hours in gridlocked HCMC/Hanoi traffic vs. open road mileage.
* **CSV/PDF Export:** Generation of raw data or reports for non-technical users.

---

## Version History

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
