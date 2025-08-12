Football Betting Strategy Dashboard
This repository contains the code for a web-based performance dashboard designed to visualize and analyze the results of an automated football betting strategy. The dashboard provides key performance metrics (KPIs), advanced analytics, and detailed bet history, all powered by data stored in a Firebase Firestore database.
The core logic for placing and tracking bets is handled by a separate bot (not included in this repository) that populates the Firestore database. This web application's sole purpose is to provide a user-friendly interface for monitoring and evaluating the strategy's effectiveness.
Features
Key Performance Metrics (KPIs)
 * Total Bets Placed: The total number of bets made within a selected time frame.
 * Win Rate (%): The percentage of winning bets.
 * Profit/Loss (Net & ROI%): Total profit/loss in monetary units and Return on Investment (ROI).
 * Biggest Win/Loss Streak: Identifies the longest consecutive winning or losing streaks.
Advanced Analytics
 * Performance by League: A breakdown of profit/loss and win rate for each football league tracked.
 * Performance by Bet Type: Analyzes the effectiveness of different bet types (e.g., regular, chase).
Trend & Time-Based Analysis
 * Daily/Weekly/Monthly Profit Trends: A visual representation of performance over time using line or bar charts.
 * Running P&L Graph: A cumulative graph showing the progression of profit and loss.
Bet Tracking & History
 * Recent Bets Log: A filterable table displaying a list of recent bets with their outcomes.
 * Data Export: The ability to export bet data for further analysis in CSV or Excel formats (planned feature).
Technology Stack
 * Backend: Flask (Python)
 * Database: Google Firebase Firestore
 * Frontend: HTML, CSS, JavaScript
 * Charting: Chart.js for data visualization
 * Deployment: Railway
Prerequisites
To run this application, you need to have the following:
 * A Google Firebase project with a Firestore database.
 * A Firebase Service Account JSON file.
 * The FIREBASE_CREDENTIALS_JSON environment variable set with the contents of your service account file.
 * Python 3.8+ installed.
Installation and Setup
1. Clone the Repository
git clone https://github.com/your-username/your-dashboard-repo.git
cd your-dashboard-repo

2. Set Up a Python Virtual Environment
It is recommended to use a virtual environment to manage dependencies.
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

3. Install Dependencies
Install the required Python packages using pip.
pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the root of the project to store your Firebase credentials.
# .env file
FIREBASE_CREDENTIALS_JSON='{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "firebase-adminsdk...iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "...",
  "token_uri": "...",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}'

> Note: The entire JSON string must be on a single line and enclosed in single quotes.
> 
5. Run the Application Locally
Start the Flask development server.
flask run

The dashboard will be available at http://127.0.0.1:5000.
Deployment
This application is designed to be easily deployed on Railway. The platform automatically detects the requirements.txt and app.py files and configures the deployment.
 * Push to GitHub: Ensure your code is pushed to a GitHub repository.
 * Create a New Railway Project: Log in to Railway, create a new project, and link it to your GitHub repository.
 * Configure Environment Variables: Go to the project settings on Railway and add the FIREBASE_CREDENTIALS_JSON variable.
 * Deploy: Railway will automatically build and deploy your application. You can then generate a public domain to access it.
   
File Structure
/web-dashboard
|-- app.py                   # Main Flask application
|-- requirements.txt         # Python dependencies
|-- /templates
|   |-- index.html           # The main dashboard page
|-- /static
|   |-- /css
|   |   |-- style.css        # Custom CSS for styling
|   |-- /js
|   |   |-- dashboard.js     # JavaScript for API calls and chart rendering
|-- .env                     # Environment variables (for local development)

Contributing
Feel free to open issues or submit pull requests to improve the dashboard's features, visuals, or performance.
