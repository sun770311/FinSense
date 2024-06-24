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
```json
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

## OpenAI Function Calling with External APIs
[See Tutorial](https://www.pragnakalp.com/openai-function-calling-with-external-api-examples/)

1. Utility Function Facilitating OpenAI Chat Completion Requests
```python
GPT_MODEL = config["GPT_MODEL"]
# Chat completion functions
def chat_completion_request(messages, functions=None, function_call=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['openai_api_key']}",
    }
    json_data = {"model": model, "messages": messages}
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": function_call})
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e
```

2. Define Functions Invoking the Finnhub and ChatOpenAI API
In app.py:
* get_current_stock_price: get current stock price
* get_company_news: get company-related news
* earn_surprises: get earnings surprises (quarter limit depends on Finnhub subscription tier)
* basic_fin: get company basic financials
* general_faq: general financial Q&A

3. Create function specifications for interacting with APIs
Example (earn_surprises):
```python
{
    "name": "earn_surprises",
    "description": "It will get the company historical quarterly earnings surprise.",
    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {
                "type": "string",
                "description": "This is the name of the company we want related news on.",
            },
            "limit": {
                "type": "string",
                "description": "Limit number of period returned. Leave blank to get the full history.",
            }
        },
        "required": ["company_name"],
    },
}
```
Here, company_name is the only required parameter. Not specifying limit retrieves the full history (up to 4 quarters for free Finnhub subscription).

4. Chat Endpoint Description
The /chat endpoint in the Flask application (see app.py) handles POST requests to facilitate interaction with OpenAI's ChatGPT model. It processes user input, generates responses using the ChatGPT model, and intelligently decides which of the 5 functions above to execute based on the model's output. 

## Web-based chat interface
![Interface Image](https://github.com/sun770311/FinSense/blob/main/finsense_ui.jpg)






