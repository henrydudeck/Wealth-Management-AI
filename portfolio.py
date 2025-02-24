import yfinance as yf
import pandas as pd
import numpy as np
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt.risk_models import risk_matrix
from pypfopt.expected_returns import mean_historical_return
from statsmodels.tsa.arima.model import ARIMA
from forecasting import forecast_stock_prices, fetch_stock_data

def get_stocks_from_selected_sectors(selected_sectors):
    """Returns a list of stock tickers based on user-selected sectors, including ETFs."""
    sector_to_tickers = {
        "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "AMD", "META", "CRM"],
        "Healthcare": ["JNJ", "PFE"],
        "Finance": ["JPM", "GS"],
        "Energy": ["XOM", "CVX"],
        "Consumer Goods": ["PG", "WMT"],
        "Industrials": ["TSLA"],
        "ETFs": ["VOO", "QQQ", "IWM"]  
    }

    selected_tickers = []
    for sector in selected_sectors:
        selected_tickers.extend(sector_to_tickers.get(sector, []))

    if not selected_tickers:
        selected_tickers = sum(sector_to_tickers.values(), [])

    return selected_tickers


def fetch_stock_data(tickers, period="3y", interval="1wk"):
    """Fetch historical closing prices for selected stocks from Yahoo Finance."""
    try:
        df = yf.download(tickers, period=period, interval=interval)
        if df.empty:
            raise ValueError("Yahoo Finance returned an empty DataFrame.")
        return df["Close"] if "Close" in df else df
    except Exception as e:
        print(f"⚠️ Error fetching stock data: {e}")
        return pd.DataFrame()

def generate_portfolio(investment_amount, risk_tolerance, selected_sectors, use_forecast=True):
    """Generates an optimized portfolio using both ETFs and stocks."""
    
    # Step 1️⃣: Get Selected Stocks + ETFs
    filtered_tickers = get_stocks_from_selected_sectors(selected_sectors)
    if not filtered_tickers:
        return pd.DataFrame()

    # Step 2️⃣: Fetch Stock + ETF Data
    data = fetch_stock_data(filtered_tickers)
    if data.empty:
        return pd.DataFrame()

    # Step 3️⃣: Choose Return Estimation Method
    if use_forecast:
        forecasted_returns = forecast_stock_prices(data)
        expected_returns = pd.Series(forecasted_returns).dropna()
        if expected_returns.empty:
            expected_returns = mean_historical_return(data)
    else:
        expected_returns = expected_returns.reindex(data.columns).dropna()

    # Step 4️⃣: Compute Risk (Covariance Matrix)
    covariance = risk_matrix(data)

    # Step 5️⃣: Optimize Portfolio (Favor ETFs for Low-Risk Profiles)
    ef = EfficientFrontier(expected_returns, covariance)
    
    if risk_tolerance == "Low":
        weights = ef.min_volatility()  # Prioritize ETFs for stability
    elif risk_tolerance == "High":
        weights = ef.max_sharpe()  # Prioritize growth
    else:
        try:
         weights = ef.efficient_return(target_return=0.12)
        except Exception:
            weights = ef.max_sharpe()



    cleaned_weights = ef.clean_weights()

    # **Step 6️⃣: Adjust ETF Allocations**  
    # Increase ETF weight for low-risk users, decrease for high-risk
    if "ETFs" in selected_sectors:
        etf_tickers = ["VOO", "QQQ", "IWM"]
        for ticker in etf_tickers:
            if ticker in cleaned_weights:
                if risk_tolerance == "Low" and cleaned_weights[ticker] < 0.5:  # Prevent 50%+ ETF dominance
                    cleaned_weights[ticker] += 0.1
            elif risk_tolerance == "High" and cleaned_weights[ticker] > 0.1:  # Prevent ETFs from going to 0
                cleaned_weights[ticker] -= 0.05
            cleaned_weights[ticker] = max(0, cleaned_weights[ticker])  


    # **Step 7️⃣: Convert to Investment Allocation**
    portfolio_df = pd.DataFrame(cleaned_weights.items(), columns=["Ticker", "Allocation"])
    portfolio_df["Investment ($)"] = portfolio_df["Allocation"] * investment_amount
    portfolio_df["Allocation (%)"] = portfolio_df["Allocation"] * 100

    return portfolio_df
