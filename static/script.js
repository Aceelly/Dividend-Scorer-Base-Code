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
    const mainScoreCard = document.querySelector('.main-score-card');

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
            fetchAllData(ticker);
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
            mainScoreCard.className = 'metric-card main-score-card';
        }
    }, 600));

    async function fetchAllData(ticker) {
        try {
            const response = await fetch(`/api/get_all_data/${ticker}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }

            // Populate overview data
            const overview = data.overview;
            marketCapValue.textContent = formatMarketCap(overview.MarketCapitalization);
            companyNameValue.textContent = overview.Name;
            epsValue.textContent = overview.EPS;
            
            const dividendYield = parseFloat(overview.DividendYield);
            if (dividendYield === 0 || isNaN(dividendYield)) {
                dividendScoreValue.textContent = 'No Dividend';
                payoutRatioValue.textContent = 'N/A';
                dividendYieldValue.textContent = 'N/A';
                recessionPerformanceValue.textContent = 'N/A';
                dividendLongevityValue.textContent = 'N/A';
                industryCyclicalityValue.textContent = 'N/A';
                mainScoreCard.className = 'metric-card main-score-card';
            } else {
                dividendYieldValue.textContent = `${(dividendYield * 100).toFixed(2)}%`;
                
                // Populate scores and labels
                const scores = data.scores;
                const labels = data.labels;

                dividendScoreValue.textContent = Math.round(scores.dividend_score);
                payoutRatioValue.textContent = `${(scores.payout_ratio * 100).toFixed(1)}%`;
                recessionPerformanceValue.textContent = labels.recession_label;
                dividendLongevityValue.textContent = `${labels.dividend_longevity_streak} years`;
                industryCyclicalityValue.textContent = labels.industry_cyclicality_label;

                // Apply color class based on dividend score
                const score = Math.round(scores.dividend_score);
                mainScoreCard.className = 'metric-card main-score-card';
                if (score >= 78) {
                    mainScoreCard.classList.add('extremely-safe');
                } else if (score >= 60) {
                    mainScoreCard.classList.add('safe');
                } else if (score >= 36) {
                    mainScoreCard.classList.add('unsafe');
                } else {
                    mainScoreCard.classList.add('extremely-unsafe');
                }
            }

        } catch (error) {
            console.error('Error fetching all data:', error);
            // Set all fields to 'Error'
            const fields = [dividendYieldValue, marketCapValue, companyNameValue, epsValue, dividendScoreValue, payoutRatioValue, recessionPerformanceValue, dividendLongevityValue, industryCyclicalityValue];
            fields.forEach(field => field.textContent = 'Error');
        }
    }

    // Function to format market cap
    function formatMarketCap(marketCap) {
        let value = parseFloat(marketCap);
        let suffix = '';

        if (value >= 1000000000000) {
            value /= 1000000000000;
            suffix = 'T';
        } else if (value >= 1000000000) {
            value /= 1000000000;
            suffix = 'B';
        } else if (value >= 1000000) {
            value /= 1000000;
            suffix = 'M';
        }

        return `$${value.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 2})}${suffix}`;
    }
});
