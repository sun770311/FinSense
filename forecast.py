import json
import requests
import numpy as np
import pandas as pd
import pmdarima as pm
import yfinance as yf
from datetime import timedelta
import matplotlib.pyplot as plt
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from sklearn.linear_model import LinearRegression

from func_options import *

"""Un-comment to run forecast.py by itself (serverless) to generate plot
    forecast_stock('<company name>')
    if calling using ticker, replace lines 191-200 with 'company_name = arguments'
"""

# Load configuration from config.json
with open('config.json') as config_file:
    config = json.load(config_file)

# Download existing stock data in CSV format
def load_stock_data(symbol_in):
    api_key = config["alpha_vantage_key"]
    symbol = symbol_in
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}&datatype=csv'

    response = requests.get(url)

    if response.status_code == 200:
        with open(f'{symbol}_stock_data.csv', 'wb') as file:
            file.write(response.content)
        print(f"CSV file has been downloaded and saved as '{symbol}_stock_data.csv'.")
    else:
        print("Failed to download the CSV file. Please check the URL and API key.")

    data = pd.read_csv(f'{symbol}_stock_data.csv', 
                       parse_dates=['timestamp'], 
                       dayfirst=False)
    data.sort_values('timestamp', inplace=True)
    data.set_index('timestamp', inplace=True)
    data = data.asfreq('D')
    data = data.ffill() # fill in missing values (weekends, holidays)
    return data['close']

# Load exogenous variables: 1) S&P 500 Index, 2) IRX
def exo_load(start_date, end_date):
    np.set_printoptions(precision=3, suppress=True)

    sp500 = yf.download(tickers="^GSPC", 
                        start=start_date, 
                        end=end_date,
                        interval="1d")
    sp500 = sp500['Close'].asfreq('D').ffill()

    irx = yf.download(tickers="^IRX",
                      start=start_date,
                      end=end_date,
                      interval="1d")
    irx = irx['Close'].asfreq('D').ffill()
    
    combined_exog = pd.DataFrame({'SP500': sp500, 'IRX': irx})
    combined_exog.ffill(inplace=True)
    
    exog_data = combined_exog.to_numpy()
    
    return exog_data

# Predict exogenous values for the next 30 days
def predict_exo(exog_data, start_date, forecast_periods=30):
    if not isinstance(exog_data, pd.DataFrame):
        exog_data = pd.DataFrame(exog_data, 
                                 columns=['SP500', 'IRX'], 
                                 index=pd.date_range(start=start_date, periods=len(exog_data), freq='D'))
    
    exog_data['date_int'] = np.arange(len(exog_data))
    
    X_sp500 = exog_data['date_int'].values.reshape(-1, 1)
    y_sp500 = exog_data['SP500'].values
    model_sp500 = LinearRegression()
    model_sp500.fit(X_sp500, y_sp500)
    
    y_irx = exog_data['IRX'].values
    model_irx = LinearRegression()
    model_irx.fit(X_sp500, y_irx)
    
    # Prepare dates for the forecast period
    last_date_int = exog_data['date_int'].iloc[-1]
    forecast_dates = np.arange(last_date_int + 1, last_date_int + 1 + forecast_periods).reshape(-1, 1)
    
    sp500_forecast = model_sp500.predict(forecast_dates)
    irx_forecast = model_irx.predict(forecast_dates)
    
    forecasted_exog = pd.DataFrame({
        'SP500': sp500_forecast,
        'IRX': irx_forecast
    }, index=pd.date_range(start=exog_data.index[-1] + timedelta(days=1), periods=forecast_periods))
    
    return forecasted_exog
    
# Forecast stock price
def arima_forecast(stock_data, 
                   exog_data=None,
                   forecasted_exog=None,
                   forecast_periods=30, 
                   seasonal=True, 
                   frequency=30):
    
    # Settings for exogenous variables
    sarimax_kwargs = {
        'time_varying_regression': True,
        'enforce_stationarity': True,
        'enforce_invertibility': True
    }
    # Automatically determine the best SARIMA parameters using pmdarima
    auto_model = pm.auto_arima(stock_data, 
                               seasonal=seasonal, 
                               m=frequency, 
                               D=1, 
                               stepwise=True, 
                               suppress_warnings=True, 
                               trace=True,
                               **sarimax_kwargs)
    print(auto_model.summary())
    
    # Match dimensions
    if exog_data is not None and stock_data.shape[0] != exog_data.shape[0]:
        if stock_data.shape[0] > exog_data.shape[0]:
            stock_data = stock_data.iloc[:exog_data.shape[0]]
        else:
            exog_data = exog_data[:stock_data.shape[0]]

    model_fit = auto_model.fit(y=stock_data, X=exog_data if exog_data is not None else None)
    
    forecast, conf_int = model_fit.predict(n_periods=forecast_periods,
                                           X=forecasted_exog if forecasted_exog is not None else None, 
                                           return_conf_int=True)
    
    return model_fit, forecast, conf_int

# Plot visualization with both lines
def plot_forecast(stock_data, 
                  forecast_with_exog, 
                  conf_int_with_exog, 
                  forecast_without_exog, 
                  conf_int_without_exog, 
                  forecast_periods=30, 
                  title='Stock Price Forecast', 
                  f_name='forecast.png'):
    plt.figure(figsize=(12, 6))
    plt.plot(stock_data, label='Past Stock Prices')
    
    forecast_index = pd.date_range(start=stock_data.index[-1], 
                                   periods=forecast_periods + 1, 
                                   freq='D')[1:]
    
    plt.plot(forecast_index, 
             forecast_with_exog, 
             color='red', 
             linestyle='--', 
             label='ARIMA Forecasted Prices with Exogenous Variables')
    plt.fill_between(forecast_index, 
                     conf_int_with_exog[:, 0], 
                     conf_int_with_exog[:, 1], 
                     color='red', 
                     alpha=0.3, 
                     label='Confidence Interval with Exogenous Variables')
    
    plt.plot(forecast_index, 
             forecast_without_exog, 
             color='blue', 
             linestyle='--', 
             label='ARIMA Forecasted Prices without Exogenous Variables')
    plt.fill_between(forecast_index, 
                     conf_int_without_exog[:, 0], 
                     conf_int_without_exog[:, 1], 
                     color='blue', 
                     alpha=0.3, 
                     label='Confidence Interval without Exogenous Variables')
    
    plt.xlabel('Time')
    plt.ylabel('Stock Price')
    plt.title(title)
    plt.legend()
    plt.xticks(rotation=20)  # Rotate the x-axis labels by 20 degrees
    plt.tight_layout()  

    plt.savefig(f_name)
    plt.show()

# LLM explanation of prediction
def explain_forecast(model_fit, forecast):
    summary = model_fit.summary()
    forecast_values = forecast.tolist()

    # User can add summary into the prompt for a more comprehensive and technical explanation
    prompt = f"""
    The model forecasted the following stock prices for the next {len(forecast_values)} periods:
    {forecast_values}

    Respond with the forecasted prices and whether they show an increasing or decreasing trend.
    """

    client = ChatOpenAI(
        model=config["GPT_MODEL"], 
        temperature=0.0,
        openai_api_key=config["openai_api_key"]
    )

    messages = [HumanMessage(content=prompt)]
    response = client.invoke(messages)
    content = response.content
    return content

def forecast_stock(arguments):
    # Load company conversions
    conversions = load_company_conversions("conversions.csv")
    
    # Parse arguments
    args = json.loads(arguments)
    company_name = args['company_name']

    # Convert company name to ticker if necessary
    if company_name in conversions:
        company_name = conversions[company_name]

    stock_data = load_stock_data(company_name)
    # Load exogenous variables
    start_date = stock_data.index.min()
    end_date = stock_data.index.max()
    exogenous = exo_load(start_date, end_date)

    # Predict exogenous variables
    exog_forecast = predict_exo(exogenous, start_date, forecast_periods=30)

    # Forecast the next 30 days using ARIMA with exogenous variables
    model_fit_with_exog, forecast_with_exog, conf_int_with_exog = arima_forecast(stock_data, 
                                                                                exog_data=exogenous,
                                                                                forecasted_exog=exog_forecast.values,
                                                                                forecast_periods=30, 
                                                                                seasonal=True, 
                                                                                frequency=30)

    # Forecast the next 30 days using ARIMA without exogenous variables
    model_fit_without_exog, forecast_without_exog, conf_int_without_exog = arima_forecast(stock_data, 
                                                                                        forecast_periods=30, 
                                                                                        seasonal=True, 
                                                                                        frequency=30)

    """ Un-comment to generate plot
    # Plot the results
    plot_forecast(stock_data, 
                forecast_with_exog, 
                conf_int_with_exog, 
                forecast_without_exog, 
                conf_int_without_exog, 
                forecast_periods=30, 
                title='Stock Price Forecast with and without Exogenous Variables', 
                f_name='forecast.png')
    
    return "Forecast graph saved to forecast.png"
    """
    # Get the explanation from the LLM for the model with exogenous variables
    explanation_with_exog = explain_forecast(model_fit_with_exog, forecast_with_exog)
    return explanation_with_exog




