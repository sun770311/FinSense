<!-- PROJECT: AUTO-GENERATED DOCS START (do not remove) -->

# FinSense
A financial analysis and recommendation system leveraging LLMs to answer user queries with real-time data. Intelligently selects which function to execute based on user input.

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

## Update (06/28/2024): Stock Forecasting


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

### Utility Function Facilitating OpenAI Chat Completion Requests
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

### Define Functions Invoking the Finnhub and ChatOpenAI API
In app.py:
* get_current_stock_price: get current stock price
* get_company_news: get company-related news
* earn_surprises: get earnings surprises (quarter limit depends on Finnhub subscription tier)
* basic_fin: get company basic financials
* general_faq: general financial Q&A

functions_map: a lookup table that maps function names to their corresponding implementations, allowing the system to dynamically call specific functions based on LLM responses.
```python
functions_map = {
    "get_current_stock_price": get_current_stock_price,
    "get_company_news": get_company_news,
    "earn_surprises": earn_surprises,
    "basic_fin": basic_fin,
    "general_faq": general_faq
}
```

### Create function specifications for interacting with APIs
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

### Chat Endpoint Description
The chat endpoint in the Flask application handles POST requests to facilitate interaction with OpenAI's ChatGPT model. It processes user input, generates responses using the ChatGPT model, and intelligently decides which of the 5 functions above to execute based on the model's output. 

Retrieve user input to guide assistant behavior
```python
user_input = request.json.get('user_input')

if not user_input:
    return jsonify({"error": "Invalid input"}), 400

# Initialize messages to guide assistant behavior
messages = [{"role": "system", "content": 
                "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."}]
messages.append({"role": "user", "content": user_input})
```

Call ChatGPT completion endpoint with error handling
```python
chat_response = chat_completion_request(messages, functions=functions)

if isinstance(chat_response, Exception):
    return jsonify({"response": "An error occurred while generating the response from ChatGPT."})

try: # parsing ChatGPT response
    assistant_message = chat_response.json()["choices"][0]["message"]
except Exception as e:
    print(f"Error parsing chat response: {e}")
    return jsonify({"response": "An error occurred while parsing the response from ChatGPT."})
```

Decide which function to execute based on LLM response
```python
fn_name = assistant_message["function_call"]["name"] # extracts name of function based on user input and context
arguments = assistant_message["function_call"]["arguments"] # extracts function arguments
function = functions_map.get(fn_name)
if function:
    try:
        result = function(arguments)
        response_content = result
    except Exception as e:
        response_content = "An error occurred while executing the function."
else:
    response_content = "Function not found.
```

### Running the App
Navigate to the FinSense directory, then execute from terminal:
```
python app.py
```

## Web-based chat interface


## Framework and Tools Used
[Finnhub](https://github.com/Finnhub-Stock-API/finnhub-python): FREE realtime API for stocks, forex and cryptocurrency.

[LangChain](https://js.langchain.com/v0.1/docs/integrations/chat/openai/): LangChain's interface for interacting with OpenAI's API.






