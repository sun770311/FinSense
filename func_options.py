# func_options.py
import csv
import json
import finnhub
from datetime import datetime, timezone
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Initialize the Finnhub client
with open('config.json') as config_file:
    config = json.load(config_file)

finnhub_client = finnhub.Client(api_key=config["finnhub_api_key"])

# Function to get current stock price
def get_current_stock_price(arguments):
    try:
        arguments = json.loads(arguments)['ticker_symbol']
        price_data = finnhub_client.quote(arguments)
        stock_price = price_data.get('c', None)
        if stock_price == 0:
            return "This company is not listed within USA, please provide another name."
        else:
            output_str = f"Current stock price of {arguments} is {stock_price}"
            return output_str
    except Exception as e:
        print(f"Error in get_current_stock_price: {e}")
        return "An error occurred while fetching the stock price."

# Function to load company conversions
def load_company_conversions(filename):
    conversions = {}
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            conversions[row['company_name']] = row['ticker']
    return conversions

# Function to get company news
def get_company_news(arguments):
    try:
        # Load company conversions
        conversions = load_company_conversions("conversions.csv")
        
        # Parse arguments
        args = json.loads(arguments)
        company_name = args['company_name']
        start_date = args['start_date']
        end_date = args['end_date']

        # Convert company name to ticker if necessary
        if company_name in conversions:
            company_name = conversions[company_name]
        
        # Retrieve company news
        news = finnhub_client.company_news(company_name, _from=start_date, to=end_date)
        
        for article in news:
            article['datetime'] = datetime.fromtimestamp(article['datetime'], timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        headers = set()
        for article in news:
            headers.update(article.keys())
        headers = list(headers)

        csv_file = 'company_news.csv'

        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(news)

        output_str = f"News articles on {company_name} from {start_date} to {end_date} written to {csv_file}"
        return output_str
    except Exception as e:
        print(f"Error in get_company_news: {e}")
        return "An error occurred while fetching the company news."

# Function to get earnings surprises
def earn_surprises(arguments):
    try:
        # Load company conversions
        conversions = load_company_conversions("conversions.csv")

        args = json.loads(arguments)
        company_name = args.get("company_name")

        # Convert company name to ticker if necessary
        if company_name in conversions:
            company_name = conversions[company_name]
        print(company_name)

        # Check if 'limit' attribute exists and is not None
        limit = args.get("limit")
        if limit is not None:
            limit = int(limit)
        print(f"limit is: {limit}")

        # Fetch earnings surprises
        earn_s = finnhub_client.company_earnings(company_name, limit=limit)
        
        headers = set()
        for record in earn_s:
            headers.update(record.keys())
        headers = list(headers)

        csv_file = f'{company_name}_earnings_surprises.csv'

        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(earn_s)

        output_str = f"Earnings surprises for {company_name} written to {csv_file}"
        return output_str
    except Exception as e:
        print(f"Error in earn_surprises: {e}")
        return "An error occurred while fetching and writing the earnings surprises data."

# Function to get basic financials
def basic_fin(arguments):
    try:
        # Load company conversions
        conversions = load_company_conversions("conversions.csv")

        args = json.loads(arguments)
        company_name = args.get("company_name")

        # Convert company name to ticker if necessary
        if company_name in conversions:
            company_name = conversions[company_name]
        print(company_name)

        # Fetch basic financial data
        basics = finnhub_client.company_basic_financials(company_name, "all")

        series_data = basics.get("series", {}).get("annual", {})
        metric_data = basics.get("metric", {})

        series_headers = set()
        for key in series_data:
            for record in series_data[key]:
                series_headers.update(record.keys())
        series_headers = list(series_headers)
        
        metric_headers = list(metric_data.keys())

        series_csv_file = f'{company_name}_financial_series.csv'
        metric_csv_file = f'{company_name}_financial_metrics.csv'

        with open(series_csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["type"] + series_headers)
            writer.writeheader()
            for key, records in series_data.items():
                for record in records:
                    record["type"] = key
                    writer.writerow(record)

        with open(metric_csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["metric", "value"])
            writer.writeheader()
            for key, value in metric_data.items():
                writer.writerow({"metric": key, "value": value})

        output_str = f"Financial series data written to {series_csv_file} and financial metrics written to {metric_csv_file}"
        return output_str

    except Exception as e:
        print(f"Error in basic_fin: {e}")
        return "An error occurred while fetching and writing the basic financial data."

# Function to answer general financial questions
def general_faq(arguments):
    try:
        query = json.loads(arguments)["query"]
        prompt = (
            f"Generate information related to {query}.\n"
            "Keep your response to less than 100 words."
        )
        client = ChatOpenAI(
            model=config["GPT_MODEL"], temperature=0.0,
            openai_api_key=config['openai_api_key']
        )
        messages = [HumanMessage(content=prompt)]
        response = client.invoke(messages)
        content = response.content
        return content

    except Exception as e:
        return "An error occurred while fetching answers on this topic."
