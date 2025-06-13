# Dividend-Scorer-Base-Code
 This project represents a unique opportunity to address a specific need within the investment community, and we invite anyone with an interest in stock analysis, programming, or data visualization to join us in bringing this vision to life. Together, we can create a powerful tool that enhances the investment decision-making process. 

TO RUN THE APP USING VS CODE
1. Open ".env_sample" file and type in Alpha Vantage API key.
2. Rename ".env_sample" file to ".env"
3. Open Terminal in VS CODE and Type "python app.py"
4. CTRL CLICK the website address that pops up. You should see something like "Running on http://126.0.1.2:5000"
5. Your Browser will display the App.


Update  |  11/6/2024  |  3:53pm
- Make sure that when you open the index.html file, that you are using vscode and that you also have already downloaded file into your vscode environment.

Update | 11/14/2024 | 12:02pm
- Added the Metrics for Levered free Cash flow (LCFC), Payout Ratio, Debt Levels. Only Payout Ratio and Debt Levels are calculated in the dividend score 50/50. 

Update | 11/19/2024 | 18:41pm
- Formatted numbers displayed on the dashboard for everything except LCFC and Debt Ratio.

Update | 11/20/2024 | 16:42pm
- Replaced LCFC with EPS
- Replaced Debt Ratio Display with Company Name
- Changed chart look and size
- Made Logout button look better
- Added the Username to display on Dashboard

Update | 11/22/2014 | 21:41pm
- Hide the API key
- When pull the updated code from GitHub, change the name .env_sample file to .env
- In the .env file replace the YOUR_API_KEY_HERE with the actual API key with NO quotation marks or anything
- Do not push the .env file into GitHub, save it locally

Update | 11/24/2024 | 4:00pm
- Added a cashflow chart in the dashboard. The chart is interactive and you can hover over the data points to see the exact value.

Update | 11/25/2024 | 10:03am
- Added some error handling

Update | 12/4/2024 | 11:11pm
- Added dynamic coloring to the dividend Score display
- Changed dashboard layout
