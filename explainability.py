import yfinance as yf

def get_stock_data(ticker):
    """Fetch live stock price, PE ratio, market cap, dividend yield, and 52-week high/low using Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info  # Retrieve stock info

        return {
            "price": info.get("currentPrice", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "high_52_week": info.get("fiftyTwoWeekHigh", "N/A"),
            "low_52_week": info.get("fiftyTwoWeekLow", "N/A")
        }
    except Exception as e:
        return {"price": "Error", "pe_ratio": "Error", "market_cap": "Error", "dividend_yield": "Error", "high_52_week": "Error", "low_52_week": "Error"}

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
        "NVDA": "🎮 NVIDIA dominates AI chip manufacturing and GPU markets, making it a leader in AI and gaming tech.",
        "META": "🌐 Meta Platforms, formerly Facebook, leads in social media and is investing heavily in virtual reality and the metaverse.",
        "AMD": "🔧 AMD is a key player in semiconductor manufacturing, providing processors and graphics cards for PCs and servers.",
        "CRM": "☁️ Salesforce is a leader in cloud-based customer relationship management (CRM) solutions.",
        "GS": "💼 Goldman Sachs is a leading global investment banking and financial services firm.",
        "PFE": "💊 Pfizer is a pharmaceutical giant known for its development of a wide range of medicines and vaccines.",
        "CVX": "🛢️ Chevron is a major energy corporation involved in every aspect of the oil and natural gas industries.",
        "WMT": "🛒 Walmart is a multinational retail corporation operating a chain of hypermarkets and grocery stores."
    }
    return explanations.get(ticker, "No specific rationale available.")

def build_ticker_info():
    """Dynamically build stock dictionary with live price, PE ratio, market cap, dividend yield, and 52-week high/low."""
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

    # Fetch live stock data
    stock_info = {
        ticker: {
            "name": name,
            "price": get_stock_data(ticker)["price"],
            "pe_ratio": get_stock_data(ticker)["pe_ratio"],
            "market_cap": get_stock_data(ticker)["market_cap"],
            "dividend_yield": get_stock_data(ticker)["dividend_yield"],
            "high_52_week": get_stock_data(ticker)["high_52_week"],
            "low_52_week": get_stock_data(ticker)["low_52_week"],
            "explanation": explain_stock_choice(ticker)
        }
        for ticker, name in ticker_to_company.items()
    }
    return stock_info