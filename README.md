# ViDrive

A CLI application designed to strip away the guesswork for drivers in Vietnam. Most people look at the sticker price; ViDrive looks at the long game—registration fees, maintenance, fuel, and the hidden costs of keeping a car on Vietnamese roads.

## Current Functionality
* **Baseline Fees:** Estimates for registration (Lệ phí trước bạ) and licensing based on standard local rates.
* **Running Costs:** Rough fuel and maintenance projections based on user-provided mileage.
* **Vehicle Data:** Basic specifications pulled from a local `data/cars.json` for consistent comparisons.

## Installation & Setup
It is recommended to use a virtual environment to keep your global Python installation clean:

```bash
# Clone the repository
git clone [https://github.com/PearTr0191/ViDrive.git](https://github.com/PearTr0191/ViDrive.git)
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
Follow the on-screen prompts to select/add your vehicle and input your variables.

## Coming Soon
We are moving beyond basic arithmetic to provide deeper financial insights:
* **Resale Value Engine:** Logarithmic depreciation curves specific to the VN market (accounting for the "Toyota vs. the rest" value retention).

* **Opportunity Cost (TVM):** Calculation of lost gains if the capital was kept in a standard VN savings account (~6-8%) instead of a depreciating asset.

* **Urban Stress Factor:** Multipliers for engine hours in HCMC/Hanoi traffic vs. open road mileage to reflect real-world wear.

* **Regional Fee Differentiation:** Adjusting registration tax specifically for Hanoi (12%) vs. other provinces (10%).

* **CSV Export:** For when you need to show your not-(tech-savvy) spouse why the car is a bad idea.
