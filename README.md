<!-- PROJECT: AUTO-GENERATED DOCS START (do not remove) -->

# FinSense
A financial analysis and recommendation system leveraging LLMs to answer user input questions with real-time data. 

## Installation
Required packages:
* finnhub-python==2.4.20
* Flask==3.0.3
* requests==2.31.0
* langchain-openai==0.1.8
* langchain-core==0.2.7
```
pip install -r requirements.txt
```

## Getting Started: Configure API Keys and Model Name
Modify config.json with your API keys and selected LLM.
```
{
    "finnhub_api_key": "<your finnhub API key here>",
    "openai_api_key": "<your OpenAI API key here>",
    "GPT_MODEL": "<your LLM here>",
    "get_current_stock_price": "Stock Price Retriever",
    "get_company_news": "Company News Reporter",
    "earn_surprises": "Earning Surprises Retriever",
    "basic_fin": "Basic Financials Retriever",
    "general_faq": "General Financial Advisor"
}
```





