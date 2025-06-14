# Dividend-Scorer-Base-Code
 This project represents a unique opportunity to address a specific need within the investment community, and we invite anyone with an interest in stock analysis, programming, or data visualization to join us in bringing this vision to life. Together, we can create a powerful tool that enhances the investment decision-making process. 

TO RUN THE APP USING VS CODE
1. Create a .env file and add your Alpha Vantage API key and a secret key:
```env
API_KEY=ALPHA_VANTAGE_API_KEY
SECRET_KEY=GENERATED_SECRET_KEY
```

2. Open the Terminal in VS Code and run:
```env
python app.py
```

3. CTRL+Click the address that appears (e.g., http://127.0.0.1:5000).
3. Your browser will open and display the app!





📅 Update Log:

🗓️ 11/06/2024 – 3:53 PM
Make sure to open index.html using VS Code.
Ensure all files are downloaded and opened within your VS Code environment.

🗓️ 11/14/2024 – 12:02 PM
Added new metrics:
Levered Free Cash Flow (LCFC)
Payout Ratio
Debt Levels
Only Payout Ratio and Debt Levels are used in the Dividend Score (weighted 50/50).

🗓️ 11/19/2024 – 6:41 PM
Formatted number displays across the dashboard (except for LCFC and Debt Ratio).

🗓️ 11/20/2024 – 4:42 PM
Replaced LCFC with EPS.
Replaced Debt Ratio display with Company Name.
Updated chart appearance and size.
Improved the look of the Logout button.
Displayed username on the dashboard.

🗓️ 11/22/2024 – 9:41 PM
Hid the API key from public view.
After pulling the latest code from GitHub:
Rename .env_sample to .env.
Replace YOUR_API_KEY_HERE with your actual API key (no quotes).
Do not push the .env file to GitHub—keep it local.

🗓️ 11/24/2024 – 4:00 PM
Added an interactive cashflow chart to the dashboard.
You can hover over data points to see exact values.

🗓️ 11/25/2024 – 10:03 AM
Added basic error handling.

🗓️ 12/04/2024 – 11:11 PM
Added dynamic coloring to the Dividend Score display.
Updated the dashboard layout.

🗓️ 6/13/2025 – 11:13 PM
Fixed Error when some stock tickers where not displaying payout ratio and dividend score
Dashboard redesign
Separated login overlay into seperate html files
