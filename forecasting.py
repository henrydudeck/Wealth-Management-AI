import numpy as np
import yfinance as yf
import pandas as pd
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt.risk_models import risk_matrix
from pypfopt.expected_returns import mean_historical_return
from statsmodels.tsa.arima.model import ARIMA
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

def fetch_stock_data(tickers, start, end):
    """Fetch historical closing prices for backtesting."""
    try:
        df = yf.download(tickers, start=start, end=end, interval="1wk")
        if df.empty:
            raise ValueError("Yahoo Finance returned an empty DataFrame.")
        return df["Close"] if "Close" in df else df
    except Exception as e:
        print(f"⚠️ Error fetching stock data: {e}")
        return pd.DataFrame()

def forecast_stock_prices(data, forecast_periods=12, model_type="ARIMA", fallback_to_historical=True):
    """Forecast future stock prices using ARIMA or LSTM, with fallbacks for failed predictions."""
    forecasted_returns = {}

    for ticker in data.columns:
        try:
            stock_prices = data[ticker].dropna()

            # Ensure there's enough data for forecasting
            if len(stock_prices) < 50:
                raise ValueError("Not enough data for forecasting")

            if model_type == "ARIMA":
                # Fit ARIMA Model
                model = ARIMA(stock_prices, order=(5,1,0))
                model_fit = model.fit()

                # Forecast next 'forecast_periods' weeks
                forecast = model_fit.forecast(steps=forecast_periods)

                # Calculate Expected Return based on forecast
                future_return = (forecast.iloc[-1] - stock_prices.iloc[-1]) / stock_prices.iloc[-1]
            
            elif model_type == "LSTM":
                # Prepare data for LSTM
                scaler = MinMaxScaler(feature_range=(0,1))
                scaled_data = scaler.fit_transform(stock_prices.values.reshape(-1,1))

                X_train, y_train = [], []
                for i in range(60, len(scaled_data)-forecast_periods):  # Use 60 days for training
                    X_train.append(scaled_data[i-60:i, 0])
                    y_train.append(scaled_data[i+forecast_periods, 0])  # Predict future point

                X_train, y_train = np.array(X_train), np.array(y_train)
                X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

                # Define LSTM model
                model = Sequential([
                    LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)),
                    LSTM(units=50, return_sequences=False),
                    Dense(units=25),
                    Dense(units=1)
                ])

                # Compile & Train
                model.compile(optimizer="adam", loss="mean_squared_error")
                model.fit(X_train, y_train, batch_size=1, epochs=10, verbose=0)

                # Predict future price
                X_test = scaled_data[-60:].reshape(1, 60, 1)  # Use last 60 days for prediction
                predicted_price = model.predict(X_test)[0][0]

                # Convert back to real prices
                predicted_price = scaler.inverse_transform([[predicted_price]])[0][0]

                # Calculate Expected Return based on forecast
                future_return = (predicted_price - stock_prices.iloc[-1]) / stock_prices.iloc[-1]

            else:
                raise ValueError("Invalid model_type. Choose 'ARIMA' or 'LSTM'.")

            forecasted_returns[ticker] = future_return

        except Exception as e:
            if fallback_to_historical:
                # Fallback: Use Historical Mean Return if ML Fails
                historical_return = (stock_prices.iloc[-1] - stock_prices.iloc[0]) / stock_prices.iloc[0]
                forecasted_returns[ticker] = historical_return
            else:
                forecasted_returns[ticker] = np.nan

    return forecasted_returns
