document.addEventListener('DOMContentLoaded', function() {
    const stockTickerInput = document.getElementById('stock-ticker-input');
    const payoutRatioValue = document.getElementById('payout-ratio-value');
    const dividendYieldValue = document.getElementById('dividend-yield-value');
    const dividendScoreValue = document.getElementById('dividend-score-value');
    const companyNameValue = document.getElementById('company-name-value'); 
    const epsValue = document.getElementById('eps-value');
    const marketCapValue = document.getElementById('market-cap-value');
    const recessionPerformanceValue = document.getElementById('recession-performance-value');
    const dividendLongevityValue = document.getElementById('dividend-longevity-value');
    const industryCyclicalityValue = document.getElementById('industry-cyclicality-value');
    const ebitdaGrowthValue = document.getElementById('ebitda-growth-value');
    const mainScoreCard = document.querySelector('.main-score-card');
    const safetyLabel = document.getElementById('safety-label');
    const scoreIndicator = document.querySelector('.score-indicator');

    // Debounce function to limit API calls
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }

    stockTickerInput.addEventListener('input', debounce(function(e) {
        const ticker = e.target.value;
        if (ticker.length > 0) {
            fetchStockData(ticker);
            fetchCashflowData(ticker);
        } else {
            payoutRatioValue.textContent = 'N/A';
            dividendYieldValue.textContent = 'N/A';
            dividendScoreValue.textContent = 'N/A';
            companyNameValue.textContent = 'N/A'; 
            epsValue.textContent = 'N/A';
            marketCapValue.textContent = 'N/A';
            recessionPerformanceValue.textContent = 'N/A';
            dividendLongevityValue.textContent = 'N/A';
            industryCyclicalityValue.textContent = 'N/A';
            ebitdaGrowthValue.textContent = 'N/A';
            safetyLabel.textContent = 'N/A';
            scoreIndicator.style.setProperty('--score-width', '0%');
        }
    }, 700));

    async function fetchStockData(ticker) {
        try {
            const response = await fetch(`/get_stock_data`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `ticker=${ticker}`
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            if (data.error) throw new Error(data.error);

            marketCapValue.textContent = formatMarketCap(data.MarketCapitalization);
            companyNameValue.textContent = data.Name;
            epsValue.textContent = data.EPS;
            industryCyclicalityValue.textContent = data.industry_cyclicality_label;

            const dividendYield = parseFloat(data.DividendYield);
            if (dividendYield === 0 || isNaN(dividendYield)) {
                dividendScoreValue.textContent = 'No Dividend';
                payoutRatioValue.textContent = 'N/A';
                dividendYieldValue.textContent = 'N/A';
                recessionPerformanceValue.textContent = 'N/A';
                dividendLongevityValue.textContent = 'N/A';
                ebitdaGrowthValue.textContent = 'N/A';
                safetyLabel.textContent = 'N/A';
                scoreIndicator.style.setProperty('--score-width', '0%');
            } else {
                dividendYieldValue.textContent = `${(dividendYield * 100).toFixed(2)}%`; 
                fetchDividendScore(ticker);
            }
        } catch (error) {
            console.error('Error fetching stock data:', error);
            const fields = [marketCapValue, companyNameValue, epsValue, industryCyclicalityValue, dividendYieldValue, dividendScoreValue, payoutRatioValue, recessionPerformanceValue, dividendLongevityValue, ebitdaGrowthValue, safetyLabel];
            fields.forEach(field => field.textContent = 'Error');
        }
    }

    async function fetchDividendScore(ticker) {
        try {
            const response = await fetch(`/get_dividend_score`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `ticker=${ticker}`
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            if (data.error) throw new Error(data.error);

            const score = Math.round(data.dividend_score);
            dividendScoreValue.textContent = score;
            payoutRatioValue.textContent = `${(data.payout_ratio * 100).toFixed(1)}%`;
            recessionPerformanceValue.textContent = data.recession_label;
            dividendLongevityValue.textContent = `${data.dividend_longevity_streak} years`;
            ebitdaGrowthValue.textContent = `${(data.average_growth_rate * 100).toFixed(1)}%`;
            
            scoreIndicator.style.setProperty('--score-width', `${score}%`);

            if (score >= 78) {
                safetyLabel.textContent = 'Extremely Safe';
                safetyLabel.className = 'bg-emerald-100 text-emerald-800 px-4 py-2 rounded-full text-sm font-medium shadow-inner';
            } else if (score >= 60) {
                safetyLabel.textContent = 'Safe';
                safetyLabel.className = 'bg-green-100 text-green-800 px-4 py-2 rounded-full text-sm font-medium shadow-inner';
            } else if (score >= 36) {
                safetyLabel.textContent = 'Unsafe';
                safetyLabel.className = 'bg-yellow-100 text-yellow-800 px-4 py-2 rounded-full text-sm font-medium shadow-inner';
            } else {
                safetyLabel.textContent = 'Extremely Unsafe';
                safetyLabel.className = 'bg-red-100 text-red-800 px-4 py-2 rounded-full text-sm font-medium shadow-inner';
            }
        } catch (error) {
            console.error('Error fetching dividend score:', error);
            const fields = [dividendScoreValue, payoutRatioValue, recessionPerformanceValue, dividendLongevityValue, ebitdaGrowthValue, safetyLabel];
            fields.forEach(field => field.textContent = 'Error');
        }
    }

    function formatMarketCap(marketCap) {
        let value = parseFloat(marketCap);
        if (isNaN(value)) return 'N/A';
        let suffix = '';
        if (value >= 1e12) {
            value /= 1e12;
            suffix = 'T';
        } else if (value >= 1e9) {
            value /= 1e9;
            suffix = 'B';
        } else if (value >= 1e6) {
            value /= 1e6;
            suffix = 'M';
        }
        return `$${value.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 2})}${suffix}`;
    }
});
