
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt.risk_models import risk_matrix
from pypfopt.expected_returns import mean_historical_return



# Streamlit App Title
st.set_page_config(page_title="AI-Powered Portfolio Generator", layout="wide")
st.title("📈 AI-Powered Portfolio Generator")

# Sidebar - User Inputs
st.sidebar.header("Investment Preferences")
investment_amount = st.sidebar.number_input("💰 Investment Amount ($)", min_value=1000, step=500, key="investment")
risk_tolerance = st.sidebar.selectbox("📉 Risk Tolerance", ["Low", "Medium", "High"], key="risk")
selected_sectors = st.sidebar.multiselect("📊 Preferred Sectors", ["Technology", "Healthcare", "Finance", "Energy", "Consumer Goods", "Industrials"], key="sectors")

# Stock Tickers and Company Names Mapping
ticker_to_company = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "TSLA": "Tesla Inc.",
    "XOM": "Exxon Mobil Corporation",
    "JNJ": "Johnson & Johnson",
    "PG": "Procter & Gamble Co.",
    "NVDA": "NVIDIA Corporation",
    "META": "Meta Platforms Inc.",
    "AMD": "Advanced Micro Devices",
    "CRM": "Salesforce Inc.",
    "GS": "Goldman Sachs Group",
    "PFE": "Pfizer Inc.",
    "CVX": "Chevron Corp.",
    "WMT": "Walmart Inc."
}

# Stock tickers for portfolio optimization
stock_tickers = list(ticker_to_company.keys())

def fetch_stock_data(tickers):
    """Fetch historical closing prices for 17 selected stocks from Yahoo Finance with optimized memory usage."""
    try:
        df = yf.download(tickers, period="3y", interval="1wk")  # Use 3 years of weekly data to reduce memory load
        if df.empty:
            st.error("⚠️ Error: Yahoo Finance returned an empty DataFrame. Check tickers or connection.")
            return pd.DataFrame()
        return df["Close"] if ("Close", tickers[0]) in df.columns else df
    except Exception as e:
        st.error(f"⚠️ An error occurred: {e}")
        return pd.DataFrame()
    
# Map stocks to their respective sectors
sector_to_tickers = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "AMD", "META", "CRM"],
    "Healthcare": ["JNJ", "PFE"],
    "Finance": ["JPM", "GS"],
    "Energy": ["XOM", "CVX"],
    "Consumer Goods": ["PG", "WMT"],
    "Industrials": ["TSLA"]
}

def get_stocks_from_selected_sectors(selected_sectors):
    """Returns a list of stocks based on user-selected sectors."""
    selected_tickers = []
    for sector in selected_sectors:
        selected_tickers.extend(sector_to_tickers.get(sector, []))
    
    if not selected_tickers:  # If no sectors are selected, default to all stocks
        selected_tickers = sum(sector_to_tickers.values(), [])
    
    return selected_tickers


@st.cache_data(ttl=3600, max_entries=1)
def generate_portfolio(investment_amount, risk_tolerance, selected_sectors):
    """Generates an optimized portfolio using historical returns and risk models."""
    
    # 1️⃣ **Filter Stocks by Selected Sectors**
    filtered_tickers = get_stocks_from_selected_sectors(selected_sectors)
    if not filtered_tickers:
        st.error("⚠️ No stocks available for selected sectors!")
        return pd.DataFrame()

    # 2️⃣ **Fetch Stock Data**
    data = fetch_stock_data(filtered_tickers)
    if data.empty:
        st.error("⚠️ Could not retrieve stock data!")
        return pd.DataFrame()

    # 3️⃣ **Calculate Expected Returns and Risk**
    expected_returns = mean_historical_return(data)
    covariance = risk_matrix(data)

    # 4️⃣ **Optimize Portfolio Using Efficient Frontier**
    ef = EfficientFrontier(expected_returns, covariance)
    
    if risk_tolerance == "Low":
        weights = ef.min_volatility()  # Prioritize stability
    elif risk_tolerance == "High":
        weights = ef.max_sharpe()  # Prioritize growth
    else:
        try:
            weights = ef.efficient_return(target_return=0.15)  # Balanced risk-return
        except:
            weights = ef.max_sharpe()  # Fallback to max Sharpe

    cleaned_weights = ef.clean_weights()

    # 5️⃣ **Convert Weights into an Investment Allocation Table**
    portfolio_df = pd.DataFrame(cleaned_weights.items(), columns=["Ticker", "Allocation"])
    portfolio_df["Company"] = portfolio_df["Ticker"].map(ticker_to_company)
    portfolio_df["Investment ($)"] = portfolio_df["Allocation"] * investment_amount
    portfolio_df["Allocation (%)"] = portfolio_df["Allocation"] * 100

    return portfolio_df


def explain_stock_choice(ticker):
    """In-depth logic behind why the stock is included in the portfolio."""
    explanations = {
        "AAPL": "📱 Apple dominates consumer electronics with iPhones, MacBooks, and a growing services segment, ensuring high margins and stability.",
        "MSFT": "💻 Microsoft excels in cloud computing (Azure), software, and AI investments (OpenAI, LinkedIn), making it a diversified tech leader.",
        "GOOGL": "🔎 Google leads in search, digital ads, and cloud computing, with AI-driven growth in Bard and DeepMind.",
        "AMZN": "📦 Amazon dominates e-commerce and cloud computing (AWS), ensuring high revenue diversification and logistics strength.",
        "JPM": "🏦 JPMorgan benefits from rising interest rates, strong financial stability, and a diversified banking business.",
        "TSLA": "🚗 Tesla leads in EVs, AI-driven self-driving technology, and energy storage, making it a high-growth stock with high volatility.",
        "XOM": "⛽ ExxonMobil benefits from oil price fluctuations and is investing in renewable energy for long-term sustainability.",
        "JNJ": "🩺 Johnson & Johnson is a defensive healthcare giant with strong pharmaceuticals and medical device businesses.",
        "PG": "🏠 Procter & Gamble is a consumer staple with essential household goods, making it a strong defensive investment.",
        "NVDA": "🎮 NVIDIA dominates AI chip manufacturing and GPU markets, making it a leader in AI and gaming tech."
    }
    return explanations.get(ticker, "No specific rationale available.")

# Fetch S&P 500 data for comparison
def fetch_sp500_data():
    try:
        sp500 = yf.download("^GSPC", period="3y", interval="1wk")["Close"]
        return sp500
    except Exception as e:
        st.error(f"⚠️ Error fetching S&P 500 data: {e}")
        return pd.Series()

# Compute Portfolio Growth Over Time
def calculate_portfolio_growth(portfolio, data):
    """Simulates portfolio performance using historical stock prices and compares it to the S&P 500."""
    if data.empty or portfolio.empty:
        return pd.DataFrame()

    # Ensure tickers in data match portfolio tickers
    portfolio_tickers = portfolio["Ticker"].tolist()
    data = data[portfolio_tickers].dropna(axis=1, how="all")  # Drop stocks with no data


    # Normalize stock data for comparison
    normalized_prices = data / data.iloc[0]  # Start from 1 (base 100%)

    # Get portfolio allocations (adjusted for missing tickers)
    weights = portfolio.set_index("Ticker")["Allocation"]
    weights = weights.reindex(normalized_prices.columns).fillna(0)  # Handle missing tickers safely

    # Compute weighted returns
    portfolio_returns = (normalized_prices * weights).sum(axis=1)  # Weighted sum of stock returns

    return portfolio_returns

# Maintain portfolio persistence across tabs
if "portfolio" not in st.session_state:
    st.session_state["portfolio"] = pd.DataFrame()

# --- Multi-tab layout ---
tab1, tab2, tab3 = st.tabs(["📊 Portfolio Results", "🤖 AI Investment Logic", "📜 How the AI Works"])

with tab1:
    if st.sidebar.button("🚀 Generate Portfolio"):
        st.session_state["portfolio"] = generate_portfolio(investment_amount, risk_tolerance, selected_sectors)


    portfolio = st.session_state["portfolio"]

    if not portfolio.empty:
        st.subheader("📊 Recommended Portfolio Allocation")
        st.dataframe(portfolio[["Company", "Ticker", "Allocation (%)", "Investment ($)"]])

        # **Improved Bar Chart**
        st.subheader("📊 Portfolio Allocation Breakdown")
        fig, ax = plt.subplots(figsize=(8, 5))
        portfolio = portfolio.sort_values(by="Allocation", ascending=True)
        colors = sns.color_palette("muted", len(portfolio))
        ax.barh(portfolio["Ticker"], portfolio["Allocation"], color=colors, edgecolor="black")
        ax.set_xlabel("Allocation (%)", fontsize=12)
        ax.set_title("📊 Portfolio Allocation Breakdown", fontsize=14, fontweight="bold")
        ax.grid(axis="x", linestyle="--", alpha=0.7)
        st.pyplot(fig)

        # --- Add Performance Chart in Tab 1 ---
        st.subheader("📈 Portfolio Growth vs. S&P 500")

        # Fetch data and compute performance
        filtered_tickers = get_stocks_from_selected_sectors(selected_sectors)  # Get sector-specific stocks
        historical_data = fetch_stock_data(filtered_tickers)  # Fetch data only for chosen stocks
  # Use selected 17 stocks
        sp500_data = fetch_sp500_data()

        if not historical_data.empty and not sp500_data.empty:
            portfolio_growth = calculate_portfolio_growth(portfolio, historical_data)
            sp500_growth = sp500_data / sp500_data.iloc[0]  # Normalize S&P 500 to start at 1

            # Plot Performance Comparison
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.plot(portfolio_growth.index, portfolio_growth, label="AI-Powered Portfolio", color="blue", linewidth=2)
            ax.plot(sp500_growth.index, sp500_growth, label="S&P 500", color="red", linestyle="dashed", linewidth=2)
            ax.set_xlabel("Date", fontsize=12)
            ax.set_ylabel("Normalized Growth (Base 100%)", fontsize=12)
            ax.set_title("📊 Portfolio Performance vs. S&P 500", fontsize=14, fontweight="bold")
            ax.legend()
            ax.grid(alpha=0.3)

            st.pyplot(fig)
        else:
            st.warning("⚠️ Portfolio or S&P 500 data is unavailable. Generate a portfolio first.")

        
with tab2:
    st.subheader("🤖 AI Investment Logic")
    selected_stock = st.selectbox("📌 Select a stock to understand its rationale:", options=list(ticker_to_company.keys()))
    explanation = explain_stock_choice(selected_stock)
    st.write(f"**{ticker_to_company[selected_stock]} ({selected_stock})**")
    st.write(f"💡 **Reasoning:** {explanation}")

with tab3:
    st.subheader("📜 How the AI Works")

    st.write("""
    ## **What Data Does the AI Use?**
    - **Stock prices & historical returns** (5 years of data)
    - **Risk calculations** (volatility, standard deviation)
    - **Stock correlations** (diversification matrix)

    ## **How Does the AI Decide Allocations?**
    - Uses **expected return, risk, and Sharpe ratio** to determine stock weights.
    - Diversifies investments across **uncorrelated stocks** to reduce risk.
    """)

    # Expandable sections for each strategy
    with st.expander("📉 **Low Risk Strategy – Minimum Volatility Portfolio (MVP)**"):
        st.write("""
        **Goal:** Minimize portfolio risk while maintaining diversification.

        **How It Works:**  
        - This model looks for the **smallest possible variance** in returns.
        - Stocks with **lower volatility** receive **higher allocations**.
        - Diversification is maximized to **reduce exposure to individual stock risks**.

        **Mathematical Model:**
        - The AI **minimizes portfolio variance**:
        \[
        \min_w w^T \Sigma w
        \]
        - Subject to:
        \[
        \sum w_i = 1
        \]
        - Where:
          - \( w \) = stock weight vector
          - \( \Sigma \) = covariance matrix (risk relationships between stocks)

        **Real-Life Example:**
        - A low-risk portfolio would include **stable, defensive stocks like JNJ, PG, JPM**.
        """)

    with st.expander("⚖️ **Medium Risk Strategy – Efficient Return Portfolio**"):
        st.write("""
        **Goal:** Balance risk and return while achieving a **target return**.

        **How It Works:**  
        - Instead of minimizing risk or maximizing return, this model **finds the best trade-off**.
        - AI **sets a target return** (e.g., 15%) and **optimizes allocations** to meet that goal with the least possible risk.

        **Mathematical Model:**
        - The AI solves for:
        \[
        \min_w w^T \Sigma w
        \]
        - Subject to:
        \[
        w^T \mu \geq R_{target}
        \]
        \[
        \sum w_i = 1
        \]
        - Where:
          - \( R_{target} \) = desired return
          - \( w \) = stock weights
          - \( \mu \) = expected return vector

        **Real-Life Example:**
        - A balanced portfolio might include **a mix of stable stocks (MSFT, JPM) and high-growth stocks (NVDA, TSLA)**.
        """)

    with st.expander("🚀 **High Risk Strategy – Maximum Sharpe Ratio Portfolio**"):
        st.write("""
        **Goal:** Maximize the Sharpe ratio to achieve the **highest return per unit of risk**.

        **How It Works:**  
        - AI **chooses stocks with the best return-to-risk tradeoff**.
        - More money goes into **high-growth stocks with strong historical performance**.

        **Mathematical Model:**
        - The AI **maximizes the Sharpe Ratio**:
        \[
        \max_w \frac{w^T \mu - r_f}{\sqrt{w^T \Sigma w}}
        \]
        - Where:
          - \( w \) = stock weights
          - \( \mu \) = expected return vector
          - \( \Sigma \) = covariance matrix
          - \( r_f \) = risk-free rate (usually treasury bonds)

        **Real-Life Example:**
        - A high-risk portfolio would be **heavily weighted in high-growth tech stocks like NVDA, TSLA, AMZN**.
        """)

    st.write("""
    ## **Why Are Some Stocks Weighted More?**
    - AI allocates more money to **high-growth stocks in high-risk portfolios**.
    - In **low-risk portfolios**, AI favors **dividend stocks and stable companies**.
    - AI ensures **diversification to reduce exposure to a single sector**.

    ## **Final Takeaway**
    - **Mathematical optimization ensures the best balance between risk & return.**
    - **AI continuously adjusts portfolios based on user risk preferences.**
    """)