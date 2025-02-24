import yfinance as yf
import pandas as pd
from forecasting import fetch_stock_data, forecast_stock_prices
from portfolio import generate_portfolio

def generate_backtest_portfolio(investment_amount, risk_tolerance, selected_sectors):
    """Creates a backtest portfolio using only 2010-2015 data."""
    return generate_portfolio(investment_amount, risk_tolerance, selected_sectors, use_forecast=True)

import matplotlib.pyplot as plt

def evaluate_backtest_performance(portfolio_df):
    """Compare AI portfolio performance against S&P 500 (2015-2020)."""
    tickers = portfolio_df["Ticker"].tolist()
    
    # Fetch actual performance (2015-2020)
    historical_data = fetch_stock_data(tickers, start="2015-01-01", end="2020-01-01")
    
    # Ensure tickers in data match portfolio tickers
    portfolio_tickers = portfolio_df["Ticker"].tolist()
    historical_data = historical_data[portfolio_tickers].dropna(axis=1, how="all")  

    # Normalize stock data
    normalized_prices = historical_data / historical_data.iloc[0]  

    # Compute weighted portfolio return
    weights = portfolio_df.set_index("Ticker")["Allocation"]
    weights = weights.reindex(normalized_prices.columns).fillna(0)  
    portfolio_returns = (normalized_prices * weights).sum(axis=1)  

    # Fetch actual S&P 500 performance
    sp500_data = yf.download("^GSPC", start="2015-01-01", end="2020-01-01")["Close"]
    sp500_growth = sp500_data / sp500_data.iloc[0]  

    # Plot AI Portfolio vs. S&P 500
    plt.figure(figsize=(10,5))
    plt.plot(portfolio_returns.index, portfolio_returns, label="AI Portfolio", color="blue")
    plt.plot(sp500_growth.index, sp500_growth, label="S&P 500", color="red", linestyle="dashed")
    plt.xlabel("Date")
    plt.ylabel("Normalized Growth (Base 100%)")
    plt.title("Backtest: AI Portfolio vs. S&P 500 (2015-2020)")
    plt.legend()
    plt.grid()
    plt.show()


def benchmark_against_indices(portfolio_df, start="2015-01-01", end="2020-01-01"):
    """Compare AI portfolio returns against S&P 500, Nasdaq-100, and Russell 2000."""
    indices = {
        "S&P 500": "^GSPC",
        "Nasdaq-100": "^NDX",
        "Russell 2000": "^RUT"
    }
    
    try:
        for index_name, ticker in indices.items():
            index_data = yf.download(ticker, start=start, end=end, interval="1wk")["Close"]
            index_return = (index_data.iloc[-1] - index_data.iloc[0]) / index_data.iloc[0]
            portfolio_df[f"{index_name} Return (%)"] = index_return * 100

        return portfolio_df
    except Exception as e:
        print(f"⚠️ Error fetching benchmark data: {e}")
        return portfolio_df

