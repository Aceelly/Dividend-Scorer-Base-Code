import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

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

def calculate_dividend_score_metrics(dividend_payout, net_income, long_term_debt, total_shareholder_equity, operating_cashflow, capital_expenditures, short_term_debt_repayments, long_term_debt_issuance):
    # Calculate payout ratio and its corresponding score
    payout_ratio = dividend_payout / net_income if net_income != 0 else 0

    payout_score = payout_ratio / 100
    if payout_score < 0:
        payout_score = 0
    elif payout_score >= 1:
        payout_score = (-0.1 * payout_score) + 20
    else:
        payout_score = (-38 * payout_ratio) + 100 # Corrected to use payout_ratio here

    # Calculate debt ratio and its corresponding score
    debt_ratio = long_term_debt / total_shareholder_equity if total_shareholder_equity != 0 else 0

    debt_score = (debt_ratio * -26) + 100
    if debt_score < 0:
        debt_score = 0
    elif debt_score > 100:
        debt_score = 100

    # Calculate Net Debt Repayments
    net_debt_repayments = (short_term_debt_repayments or 0) + (long_term_debt_issuance or 0)

    # Calculate LFCF (Levered Free Cash Flow)
    lfcf = operating_cashflow - capital_expenditures - net_debt_repayments

    # Calculate LFCF Ratio and Free Cash Flow Score
    lfcf_ratio = dividend_payout / lfcf if lfcf != 0 else 'N/A'
    free_cashflow_score = -50 * (lfcf_ratio if isinstance(lfcf_ratio, (int, float)) else 0) + 100
    if free_cashflow_score < 0:
        free_cashflow_score = 0

    # Calculate the weighted dividend score (1/3 weight for each metric)
    weighted_dividend_score = (payout_score / 3) + (debt_score / 3) + (free_cashflow_score / 3)

    return {
        'dividend_score': weighted_dividend_score, 
        'payout_ratio': payout_ratio, 
        'debt_ratio': debt_ratio, 
        'operatingCashflow': operating_cashflow,
        'capitalExpenditures': capital_expenditures,
        'shortTermDebtRepayments': short_term_debt_repayments,
        'longTermDebtIssuance': long_term_debt_issuance,
        'netDebtRepayments': net_debt_repayments,
        'lfcf': lfcf,
        'lfcf_ratio': lfcf_ratio,
        'payout_score': payout_score,
        'debt_score': debt_score,
        'free_cashflow_score': free_cashflow_score
    }

@app.route('/calculate', methods=['POST'])
@login_required
def calculate():
    # This route is currently not used by the frontend for dividend scoring based on ticker
    # It was previously used for manual input calculation.
    # Keeping it for now, but the primary calculation happens via get_dividend_score
    data = request.json
    try:
        # Placeholder for the actual dividend score calculation logic
        # This function needs to be updated if it's intended for manual input calculation
        # For now, it's a simplified version.
        score = (float(data['payout_ratio']) + float(data['debt_levels']) + float(data['dividend_longevity']) + float(data['free_cash_flow']) + float(data['recent_growth'])) / 5
        return jsonify({'score': round(score, 2)})
    except ValueError as e:
        return jsonify({'error': f'Invalid input. Please check your values. Error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/')
@login_required
def index():
    # Render the main page (index.html) for the application
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
            user_id = len(users) + 1 # Simple ID generation
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
    # Retrieve the stock ticker from the form data
    ticker = request.form.get('ticker')
    api_key = os.getenv ('API_KEY') # Load the API key securely from the environment
    if not api_key:
        return jsonify({'error':'API key is missing'}), 500
    # Create API URL to get stock data
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()

    print(f"Raw API Response (get_stock_data): {data}")

    # Handle cases where the API returns an error
    if 'Error Message' in data:
        return jsonify({'error': data['Error Message']}), 500

    # Return relevant stock data (Dividend Yield and Market Capitalization)
    return jsonify({
        'DividendYield': data.get('DividendYield', 'N/A'),
        'MarketCapitalization': data.get('MarketCapitalization', 'N/A'),
        'Name': data.get('Name', 'N/A'), # Include stock name in response
        'EPS': data.get('EPS', 'N/A'), # Include EPS in response
        'ExDividendDate': data.get('ExDividendDate', 'N/A') # Include Ex-Dividend Date in response
    })

@app.route('/get_dividend_score', methods=['GET', 'POST'])
@login_required
def get_dividend_score():
    # Retrieve the stock ticker from the form data
    ticker = request.form.get('ticker')
    api_key = os.getenv ('API_KEY') 
    if not api_key:
        return jsonify({'error': 'API key is missing'}), 500 # Load the API key securely from the environment
    # URLs to get cash flow and balance sheet data
    url_cf = f'https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={api_key}'
    url_bs = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={api_key}'
    response_cf = requests.get(url_cf)
    response_bs = requests.get(url_bs)
    data_cf = response_cf.json()
    data_bs = response_bs.json()

    print(f"Raw API Response (CASH_FLOW): {data_cf}")
    print(f"Raw API Response (BALANCE_SHEET): {data_bs}")

    try:
        # Check for API error messages in cash flow data
        if 'Error Message' in data_cf:
            return jsonify({'error': f"Cash Flow API Error: {data_cf['Error Message']}"}), 500
        if 'Error Message' in data_bs:
            return jsonify({'error': f"Balance Sheet API Error: {data_bs['Error Message']}"}), 500
        
        # Check if cash flow data is available and 'annualReports' is not empty
        if 'annualReports' not in data_cf or not data_cf['annualReports']:
            return jsonify({'error': 'No cash flow data available for this ticker'}), 500
        if 'annualReports' not in data_bs or not data_bs['annualReports']:
            return jsonify({'error': 'No balance sheet data available for this ticker'}), 500

        # Extract latest annual dividend payout and net income from cash flow data
        latest_cashflow = data_cf['annualReports'][0]
        dividend_payout_str = latest_cashflow.get('dividendPayout', '0')
        net_income_str = latest_cashflow.get('netIncome', '0')

        # Convert 'None' string to '0' before float conversion
        dividend_payout = float(dividend_payout_str if dividend_payout_str != 'None' else '0')
        net_income = float(net_income_str if net_income_str != 'None' else '0')

        # Extract latest annual long-term debt and total shareholder equity from balance sheet data
        latest_balancesheet = data_bs['annualReports'][0]
        long_term_debt_str = latest_balancesheet.get('longTermDebt', '0')
        total_shareholder_equity_str = latest_balancesheet.get('totalShareholderEquity', '0')

        # Convert 'None' string to '0' before float conversion
        long_term_debt = float(long_term_debt_str if long_term_debt_str != 'None' else '0')
        total_shareholder_equity = float(total_shareholder_equity_str if total_shareholder_equity_str != 'None' else '0')

        # Fetch data for LFCF calculation
        operating_cashflow_str = latest_cashflow.get('operatingCashflow', '0')
        capital_expenditures_str = latest_cashflow.get('capitalExpenditures', '0')
        short_term_debt_repayments_str = latest_cashflow.get('proceedsFromRepaymentsOfShortTermDebt', '0')
        long_term_debt_issuance_str = latest_cashflow.get('proceedsFromIssuanceOfLongTermDebtAndCapitalSecuritiesNet', '0')

        # Convert 'None' string to '0' before float conversion
        operating_cashflow = float(operating_cashflow_str if operating_cashflow_str != 'None' else '0')
        capital_expenditures = float(capital_expenditures_str if capital_expenditures_str != 'None' else '0')
        short_term_debt_repayments = float(short_term_debt_repayments_str if short_term_debt_repayments_str != 'None' else '0')
        long_term_debt_issuance = float(long_term_debt_issuance_str if long_term_debt_issuance_str != 'None' else '0')

        print(f"Metrics for calculate_dividend_score_metrics:")
        print(f"  dividend_payout: {dividend_payout}")
        print(f"  net_income: {net_income}")
        print(f"  long_term_debt: {long_term_debt}")
        print(f"  total_shareholder_equity: {total_shareholder_equity}")
        print(f"  operating_cashflow: {operating_cashflow}")
        print(f"  capital_expenditures: {capital_expenditures}")
        print(f"  short_term_debt_repayments: {short_term_debt_repayments}")
        print(f"  long_term_debt_issuance: {long_term_debt_issuance}")

        # Calculate all scores using the dedicated function
        calculated_data = calculate_dividend_score_metrics(
            dividend_payout, net_income, long_term_debt, total_shareholder_equity,
            operating_cashflow, capital_expenditures, short_term_debt_repayments, long_term_debt_issuance
        )

        # Return all calculated data as JSON response
        return jsonify(calculated_data)

    except (KeyError, ValueError, ZeroDivisionError) as e:
        # Handle errors in calculation or missing data
        print(f"Error in get_dividend_score: {e}")
        return jsonify({'error': f'Error calculating dividend score: {str(e)}'}), 500
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
    response = requests.get(url)
    data = response.json()

    if 'annualReports' not in data:
        return jsonify({'error': 'No data available'})

    annual_reports = data['annualReports']

    # Extract relevant data
    cashflow_data = {
        'labels': [],
        'operatingCashflow': [],
        'capitalExpenditures': [],
        'freeCashflow': []
    }

    for report in annual_reports:
        cashflow_data['labels'].append(report['fiscalDateEnding'])
        cashflow_data['operatingCashflow'].append(float(report['operatingCashflow']) / 1e9)  # Convert to billions
        cashflow_data['capitalExpenditures'].append(float(report['capitalExpenditures']) / 1e9)  # Convert to billions
        cashflow_data['freeCashflow'].append(
            float(report['operatingCashflow']) / 1e9 + float(report['capitalExpenditures']) / 1e9
        )

    # Reverse the data to show chronological order
    for key in cashflow_data:
        cashflow_data[key].reverse()

    return jsonify(cashflow_data)

if __name__ == '__main__':
    app.run(debug=True)  # Run the application in debug mode
