import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import datetime
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_secret_key_that_should_be_changed') # Use a strong secret key from .env
CORS(app, resources={r"/*": {"origins": "*"}}) 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Specify the login view

USERS_FILE = 'users.json'

# User management functions
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        users = load_users()
        for username, user_data in users.items():
            if user_data['id'] == int(user_id): # Ensure type consistency
                return User(user_data['id'], username, user_data['password_hash'])
        return None

    @staticmethod
    def get_by_username(username):
        users = load_users()
        user_data = users.get(username)
        if user_data:
            return User(user_data['id'], username, user_data['password_hash'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def get_industry_cyclicality_score(sector):
    non_cyclical_sectors = ["Consumer Defensive", "Healthcare", "Utilities","Energy", "Consumer Staples", "Trade & Services","Life Sciences"]
    cyclical_sectors = ["Manufacturing", "Consumer Cyclical", "Industrials", "Materials", "Real Estate", "Financial Services", "Technology","Communication Services"]

    if sector in non_cyclical_sectors:
        return "Not Cyclical", 85
    elif sector in cyclical_sectors:
        return "Cyclical", 50
    else:
        return "Highly Cyclical or Unknown", 30

def calculate_recession_performance(time_series_data):
    if not time_series_data:
        return 50, "Neutral"

    dividends = {}
    for date_str, values in time_series_data.items():
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        year_month = date.strftime("%Y-%m")
        
        if year_month in ["2019-12", "2020-12"]:
            dividends[year_month] = float(values.get("7. dividend amount", 0))

    div_2019 = dividends.get("2019-12", 0)
    div_2020 = dividends.get("2020-12", 0)

    if div_2019 == 0 and div_2020 == 0:
        return 50, "Neutral"
    elif div_2020 >= div_2019:
        return 85, "Good"
    else: # div_2020 < div_2019
        return 25, "Bad"

def calculate_dividend_longevity(time_series_data):
    if not time_series_data:
        return 0, 0

    dividends_by_year = {}
    for date_str, values in time_series_data.items():
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        year = date.year
        dividend = float(values.get("7. dividend amount", 0))

        if dividend > 0:
            dividends_by_year.setdefault(year, 0)
            dividends_by_year[year] += 1

    if not dividends_by_year:
        return 0, 0

    min_year = min(dividends_by_year)
    consistent_years = {
        year for year, count in dividends_by_year.items()
        if count >= 4 or (year == min_year and count >= 2)
    }

    if not consistent_years:
        return 0, 0

    current_year = datetime.datetime.now().year
    year = current_year
    while year not in consistent_years and year >= min(consistent_years):
        year -= 1

    streak = 0
    while year in consistent_years:
        streak += 1
        year -= 1

    dividend_longevity_score = min(int(streak * 4.99), 100)
    return streak, dividend_longevity_score

def calculate_growth_score(income_statement_data):
    if not income_statement_data or 'annualReports' not in income_statement_data or len(income_statement_data['annualReports']) < 2:
        return 0, 0

    annual_reports = sorted(income_statement_data['annualReports'], key=lambda x: x['fiscalDateEnding'])
    
    recent_reports = annual_reports[-5:]
    
    growth_rates = []
    for i in range(1, len(recent_reports)):
        try:
            prev_ebitda = float(recent_reports[i-1]['ebitda'])
            curr_ebitda = float(recent_reports[i]['ebitda'])
            if prev_ebitda > 0:
                growth = (curr_ebitda - prev_ebitda) / prev_ebitda
                growth_rates.append(growth)
        except (ValueError, TypeError):
            continue  # Skip invalid EBITDA data

    if not growth_rates:
        return 0, 0

    average_growth = sum(growth_rates) / len(growth_rates)
    
    # If average YoY growth is negative, return score of 0
    if average_growth < 0:
        return 0, average_growth
    
    # Apply scoring formula for non-negative growth
    score_input = average_growth
    if score_input > 1:
        score_input = 1
    elif score_input < 0:
        score_input = 0
    
    score = (475 * score_input) + 5
    score = min(score, 100)  # Cap the final score at 100
    
    return score, average_growth

def calculate_payout_score(dividend_payout, net_income):
    payout_ratio = dividend_payout / net_income if net_income != 0 else 0
    
    if payout_ratio < 0:
        score = 0
    elif payout_ratio >= 1:  # 100% or more payout ratio
        score = (-2 * (payout_ratio ** 8)) + 22
    else:  # payout_ratio < 1
        score = (-53 * (payout_ratio ** 2)) + 100
    
    # Clamp score between 0 and 100
    score = max(0, min(score, 100))
    
    return score, payout_ratio


def calculate_debt_score(long_term_debt, total_shareholder_equity):
    debt_ratio = long_term_debt / total_shareholder_equity if total_shareholder_equity != 0 else 0
    score = (debt_ratio * -26) + 100
    if score < 0:
        score = 0
    elif score > 100:
        score = 100

    print(f"Debt Ratio: {debt_ratio:.2f}, Score: {score:.2f}")    
    return score, debt_ratio

def calculate_free_cashflow_score(dividend_payout, operating_cashflow, capital_expenditures, net_debt_repayments):
    # Calculate LFCF (Levered Free Cash Flow)
    lfcf = operating_cashflow - capital_expenditures - net_debt_repayments

    lfcf_ratio = None  # Define upfront to avoid local variable error

    # Handle zero or negative LFCF to avoid invalid calculations
    if lfcf <= 0:
        free_cashflow_score = 0
    else:
        # Calculate LFCF Ratio
        lfcf_ratio = dividend_payout / lfcf

        # Calculate Free Cash Flow Score
        # free_cashflow_score = -50 * lfcf_ratio + 100
        free_cashflow_score = (-81 * lfcf_ratio * lfcf_ratio) - 5 * lfcf_ratio + 100

        # Clamp score between 0 and 100
        if free_cashflow_score < 0:
            free_cashflow_score = 0
        elif free_cashflow_score > 100:
            free_cashflow_score = 100
        
    return free_cashflow_score, lfcf_ratio

def calculate_dividend_score_metrics(payout_score, debt_score, recession_score, dividend_longevity_score, industry_cyclicality_score, growth_score, free_cashflow_score):
    weighted_dividend_score = (payout_score * 0.303) + (debt_score * 0.197) + (recession_score * 0.013) + (dividend_longevity_score * 0.026) + (industry_cyclicality_score * 0.039) + (free_cashflow_score * 0.289) + (growth_score * 0.133)

    print(f"Calculated Scores:")
    print(f"  Payout Score: {payout_score:.2f}")
    print(f"  Debt Score: {debt_score:.2f}")
    print(f"  Recession Score: {recession_score}")
    print(f"  Dividend Longevity Score: {dividend_longevity_score}")
    print(f"  Industry Cyclicality Score: {industry_cyclicality_score}")
    print(f"  Growth Score: {growth_score:.2f}")
    print(f"  Weighted Dividend Score: {weighted_dividend_score:.2f}")
    print(f"  Free Cashflow Score: {free_cashflow_score}")

    return weighted_dividend_score

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users:
            flash('Username already exists')
        else:
            user_id = len(users) + 1
            hashed_password = generate_password_hash(password)
            users[username] = {'id': user_id, 'password_hash': hashed_password}
            save_users(users)
            user = User(user_id, username, hashed_password)
            login_user(user)
            return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/get_stock_data', methods=['GET', 'POST']) 
@login_required
def get_stock_data():
    ticker = request.form.get('ticker')
    api_key = os.getenv('API_KEY')
    if not api_key:
        return jsonify({'error':'API key is missing'}), 500
    
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()

    if 'Error Message' in data:
        return jsonify({'error': data['Error Message']}), 500

    sector = data.get("Sector", "").title()
    industry_cyclicality_label, _ = get_industry_cyclicality_score(sector)

    return jsonify({
        'DividendYield': data.get('DividendYield', 'N/A'),
        'MarketCapitalization': data.get('MarketCapitalization', 'N/A'),
        'Name': data.get('Name', 'N/A'),
        'EPS': data.get('EPS', 'N/A'),
        'ExDividendDate': data.get('ExDividendDate', 'N/A'),
        'industry_cyclicality_label': industry_cyclicality_label
    })

@app.route('/get_dividend_score', methods=['GET', 'POST'])
@login_required
def get_dividend_score():
    ticker = request.form.get('ticker')
    api_key = os.getenv('API_KEY') 
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 500
    
    url_ts = f'https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={ticker}&apikey={api_key}'
    url_overview = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'
    url_income = f'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={api_key}'
    url_cf = f'https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={api_key}'
    url_bs = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={api_key}'

    # Helper function to make API calls with rate limit handling
    def fetch_with_retry(url, label, max_retries=3):
        for attempt in range(max_retries):
            response = requests.get(url)
            data = response.json()
            
            # Check if we got rate limited
            if "Information" in data or "Note" in data:
                msg = data.get("Information") or data.get("Note", "")
                print(f"⏳ {label} rate limited (attempt {attempt+1}/{max_retries}). Waiting 15s...")
                time.sleep(15)
                continue
            
            print(f"✅ {label} received")
            return data
        
        # If all retries exhausted, return the last response anyway
        print(f"❌ {label} failed after {max_retries} attempts")
        return data

    try:
        data_ts = fetch_with_retry(url_ts, "TIME_SERIES_MONTHLY_ADJUSTED")
        time.sleep(13)
        data_overview = fetch_with_retry(url_overview, "OVERVIEW")
        time.sleep(13)
        data_income = fetch_with_retry(url_income, "INCOME_STATEMENT")
        time.sleep(13)
        data_cf = fetch_with_retry(url_cf, "CASH_FLOW")
        time.sleep(13)
        data_bs = fetch_with_retry(url_bs, "BALANCE_SHEET")

        time_series_data = data_ts.get("Monthly Adjusted Time Series")
        
        recession_score, recession_label = calculate_recession_performance(time_series_data)
        dividend_longevity_streak, dividend_longevity_score = calculate_dividend_longevity(time_series_data)
        
        sector = data_overview.get("Sector", "").title()
        _, industry_cyclicality_score = get_industry_cyclicality_score(sector)

        growth_score, average_growth_rate = calculate_growth_score(data_income)

        if 'annualReports' not in data_cf or not data_cf['annualReports'] or 'annualReports' not in data_bs or not data_bs['annualReports']:
            return jsonify({'error': 'Insufficient financial data to calculate score'}), 500

        latest_cashflow = data_cf['annualReports'][0]
        dividend_payout = float(latest_cashflow.get('dividendPayout', '0').replace('None', '0'))
        net_income = float(latest_cashflow.get('netIncome', '0').replace('None', '0'))

        latest_balancesheet = data_bs['annualReports'][0]
        long_term_debt = float(latest_balancesheet.get('longTermDebt', '0').replace('None', '0'))
        total_shareholder_equity = float(latest_balancesheet.get('totalShareholderEquity', '0').replace('None', '0'))

        print(f"Long Term Debt: {long_term_debt}, Total Shareholder Equity: {total_shareholder_equity}")

        operating_cashflow = float(latest_cashflow.get('operatingCashflow', '0').replace('None', '0'))
        capital_expenditures = float(latest_cashflow.get('capitalExpenditures', '0').replace('None', '0'))
        short_term_debt_repayments = float(latest_cashflow.get('proceedsFromRepaymentsOfShortTermDebt', '0').replace('None', '0'))
        long_term_debt_issuance = float(latest_cashflow.get('proceedsFromIssuanceOfLongTermDebtAndCapitalSecuritiesNet', '0').replace('None', '0'))

        net_debt_repayments = (short_term_debt_repayments or 0) + (long_term_debt_issuance or 0)
        
        payout_score, payout_ratio = calculate_payout_score(dividend_payout, net_income)
        debt_score, debt_ratio = calculate_debt_score(long_term_debt, total_shareholder_equity)
        free_cashflow_score, lfcf_ratio = calculate_free_cashflow_score(dividend_payout, operating_cashflow, capital_expenditures, net_debt_repayments)

        weighted_dividend_score = calculate_dividend_score_metrics(
            payout_score, debt_score, recession_score, dividend_longevity_score, 
            industry_cyclicality_score, growth_score, free_cashflow_score
        )
        
        return jsonify({
            'dividend_score': weighted_dividend_score,
            'payout_ratio': payout_ratio,
            'debt_ratio': debt_ratio,
            'recession_label': recession_label,
            'dividend_longevity_streak': dividend_longevity_streak,
            'average_growth_rate': average_growth_rate,
            'lfcf_ratio': lfcf_ratio
        })

    except Exception as e:
        print(f"An unexpected error occurred in get_dividend_score: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/api/cashflow/<symbol>')
@login_required
def get_cashflow_data(symbol):
    api_key = os.getenv('API_KEY')
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 500
    
    url = f'https://www.alphavantage.co/query?function=CASH_FLOW&symbol={symbol}&apikey={api_key}'
    
    # Add retry logic for rate limiting
    max_retries = 3
    data = None
    for attempt in range(max_retries):
        response = requests.get(url)
        data = response.json()
        
        if "Information" in data or "Note" in data:
            print(f"⏳ Cashflow API rate limited (attempt {attempt+1}/{max_retries}). Waiting 15s...")
            time.sleep(15)
            continue
        
        break
    
    if not data or 'annualReports' not in data:
        print(f"❌ No cashflow data available for {symbol}. Response keys: {list(data.keys()) if data else 'None'}")
        return jsonify({'error': 'No data available'})

    annual_reports = data['annualReports']

    cashflow_data = {
        'labels': [],
        'operatingCashflow': [],
        'capitalExpenditures': [],
        'freeCashflow': []
    }

    for report in annual_reports:
        cashflow_data['labels'].append(report['fiscalDateEnding'])
        cashflow_data['operatingCashflow'].append(float(report['operatingCashflow']) / 1e9)
        cashflow_data['capitalExpenditures'].append(float(report['capitalExpenditures']) / 1e9)
        cashflow_data['freeCashflow'].append(
            float(report['operatingCashflow']) / 1e9 + float(report['capitalExpenditures']) / 1e9
        )

    for key in cashflow_data:
        cashflow_data[key].reverse()

    return jsonify(cashflow_data)

if __name__ == '__main__':
    app.run(debug=True)
