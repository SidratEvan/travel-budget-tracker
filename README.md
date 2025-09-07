🌍 Travel Budget Planner

A Python + Streamlit web app that helps travelers plan trips within their budget.
It compares destinations by estimating flights, bus, or driving costs, plus accommodation, food, local mobility (own car vs rental), and even generates a day-by-day itinerary.

✨ Features

Budget-based suggestions
Enter your budget and the app filters destinations you can afford.

Multiple transport modes

✈️ Flight (cheapest airline auto-selected)

🚌 Bus

🚗 Drive (own car or rental)

Local mobility inside the destination

None

Public transit

Rent a car

Use own car

Cost breakdown
Transparent breakdown of primary transport, local mobility, stay, food, activities.

Sensitivity analysis
See how your plan changes if you add or remove ±$10, $20, $100, $200.

Day-by-day itinerary
Auto-generated schedule with activities for each day.

🛠️ Tech Stack

Python 3.13

Streamlit
 for the web app

Pandas
 for data handling

JSON for destination dataset

📂 Project Structure
travel-budget-tracker/
│
├── app.py                 # Main Streamlit app
├── requirements.txt       # Dependencies
├── data/
│   └── destinations.json  # Destination dataset (10 Canadian cities)
└── src/
    ├── cost.py            # Cost models (flights, bus, drive, local mobility)
    └── plan.py            # Itinerary planning

🚀 Getting Started
1. Clone the repo
git clone https://github.com/SidratEvan/travel-budget-tracker.git
cd travel-budget-tracker

2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # On Windows
# or
source .venv/bin/activate  # On Mac/Linux

3. Install dependencies
pip install -r requirements.txt

4. Run the app
streamlit run app.py


The app will open at:
👉 http://localhost:8501

🌆 Current Destinations

Calgary

Edmonton

Winnipeg

Regina

Banff

Vancouver

Victoria

Toronto

Ottawa

Montreal

(All costs are rule-of-thumb estimates; extendable with live APIs for flights/hotels/activities.)

🎯 Future Improvements

Airline selection inside each destination card

Export itinerary as CSV or PDF

More destinations (USA, Europe, Asia)

Live data integration (Skyscanner, Expedia, TripAdvisor APIs)
