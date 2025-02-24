import streamlit as st
import pandas as pd
from portfolio import generate_portfolio
from forecasting import fetch_sp500_data, calculate_portfolio_growth
from forecasting import fetch_stock_data
from config import TICKER_TO_COMPANY
from db import get_stocks_from_selected_sectors, fetch_stock_data
from explainability import explain_stock_choice
from explainability import build_ticker_info
from auth import authentication, save_portfolio, load_portfolio
from forecasting import forecast_stock_prices

st.subheader("🔮 Forecasted Portfolio Growth Over Time")

# Ensure authentication before anything else
if "user" not in st.session_state or not st.session_state["user"]:
    authentication()
    st.stop()  # Prevents the rest of the app from running until user logs in

# Sidebar - User Inputs
st.sidebar.header("Investment Preferences")
investment_amount = st.sidebar.number_input("💰 Investment Amount ($)", min_value=1000, step=500, key="investment")
risk_tolerance = st.sidebar.selectbox("📉 Risk Tolerance", ["Low", "Medium", "High"], key="risk")
selected_sectors = st.sidebar.multiselect("📊 Preferred Sectors", ["Technology", "Healthcare", "Finance", "Energy", "Consumer Goods", "Industrials"], key="sectors")

# Ensure portfolio has valid tickers before forecasting
if not portfolio.empty:
    forecasted_returns = forecast_stock_prices(historical_data, forecast_periods=12, model_type="LSTM")

# Maintain portfolio persistence across tabs
if "portfolio" not in st.session_state:
    st.session_state["portfolio"] = pd.DataFrame()

if st.sidebar.button("🚀 Generate Portfolio"):
    st.session_state["portfolio"] = generate_portfolio(investment_amount, risk_tolerance, selected_sectors)
    
    if not st.session_state["portfolio"].empty:
        st.write("📊 Your AI-Optimized Portfolio")
        st.dataframe(st.session_state["portfolio"])

        if "user" in st.session_state and st.session_state["user"]:
            save_portfolio(st.session_state["user"], st.session_state["portfolio"])
        else:
            st.error("❌ You must be logged in to save your portfolio.")
    else:
        st.warning("⚠️ No valid portfolio generated. Please adjust your settings.")

if st.sidebar.button("📂 Load Saved Portfolio"):
    portfolio_df = load_portfolio(st.session_state["user"])
    
    if portfolio_df is not None:
        st.write("📊 Your Previously Saved Portfolio")
        st.dataframe(portfolio_df)


# Streamlit App Title
st.set_page_config(page_title="AI-Powered Portfolio Generator", layout="wide")
st.title("📈 AI-Powered Portfolio Generator")

# Fetch live stock data & explanations
stock_data = build_ticker_info()
st.write(stock_data)  # Display live stock data and explanations in the UI


# --- Multi-tab layout ---
tab1, tab2, tab3 = st.tabs(["📊 Portfolio Results", "🤖 AI Investment Logic", "📜 How the AI Works"])

with tab1:
    portfolio = st.session_state["portfolio"]

    if not portfolio.empty:
        st.subheader("📊 Recommended Portfolio Allocation")
        st.dataframe(portfolio[["Company", "Ticker", "Allocation (%)", "Investment ($)"]])

        # Portfolio Growth Chart
        st.subheader("📈 Portfolio Growth vs. S&P 500")
        filtered_tickers = get_stocks_from_selected_sectors(selected_sectors)

        if filtered_tickers:
            historical_data = fetch_stock_data(filtered_tickers)
            sp500_data = fetch_sp500_data()
        else:
            historical_data = pd.DataFrame()
            sp500_data = pd.DataFrame()

        if not historical_data.empty and not sp500_data.empty:
            portfolio_growth = calculate_portfolio_growth(portfolio, historical_data)
            sp500_growth = sp500_data / sp500_data.iloc[0]  # Normalize S&P 500 to start at 1

            # Plot Performance Comparison
            import matplotlib.pyplot as plt
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

        # 🔮 Forecasted Portfolio Growth
        st.subheader("🔮 Forecasted Portfolio Growth Over Time")
        
        # Ensure portfolio has valid tickers before forecasting
        from forecasting import forecast_stock_prices
        
        if not historical_data.empty:
            forecasted_returns = forecast_stock_prices(historical_data, forecast_periods=12, model_type="LSTM")

            # Generate projected portfolio value based on forecasted returns
            projected_growth = portfolio.copy()
            projected_growth["Projected Investment ($)"] = projected_growth["Investment ($)"] * (1 + forecasted_returns)

            # Plot future portfolio growth
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.barh(projected_growth["Ticker"], projected_growth["Projected Investment ($)"], color="green", edgecolor="black")
            ax.set_xlabel("Projected Investment ($)", fontsize=12)
            ax.set_title("🔮 Projected Portfolio Growth", fontsize=14, fontweight="bold")
            ax.grid(axis="x", linestyle="--", alpha=0.7)
            st.pyplot(fig)
        else:
            st.warning("⚠️ Portfolio data is missing. Generate a portfolio first to see projections.")

        # 📊 AI Portfolio Backtesting Performance
        st.subheader("📊 AI Portfolio Backtesting Performance")

        # Fetch past AI-selected portfolio and compare against historical market data
        from backtesting import evaluate_backtest_performance

        if not portfolio.empty:
            fig = evaluate_backtest_performance(portfolio)
            st.pyplot(fig)
        else:
            st.warning("⚠️ Portfolio data is missing. Generate a portfolio first to see backtesting results.")


with tab2:
    st.subheader("🤖 AI Investment Logic")
    selected_stock = st.selectbox("📌 Select a stock to understand its rationale:", options=list(TICKER_TO_COMPANY.keys()))
    explanation = explain_stock_choice(selected_stock)
    st.write(f"**{TICKER_TO_COMPANY[selected_stock]} ({selected_stock})**")
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