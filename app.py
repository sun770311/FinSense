# app.py
import json
import secrets
import requests
from flask import Flask, request, jsonify, render_template
from func_options import get_current_stock_price, get_company_news, earn_surprises, basic_fin, general_faq

# Load configuration from config.json
with open('config.json') as config_file:
    config = json.load(config_file)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Use a securely generated random string

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

functions_map = {
    "get_current_stock_price": get_current_stock_price,
    "get_company_news": get_company_news,
    "earn_surprises": earn_surprises,
    "basic_fin": basic_fin,
    "general_faq": general_faq
}

functions = [
    {
        "name": "get_current_stock_price",
        "description": "It will get the current stock price of the US company.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker_symbol": {
                    "type": "string",
                    "description": "This is the symbol of the company.",
                }
            },
            "required": ["ticker_symbol"],
        },
    },
    {
        "name": "get_company_news",
        "description": "It will get the news related to a company within a specified date range.",
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "This is the name of the company we want related news on.",
                },
                "start_date": {
                    "type": "string",
                    "description": "Format: YYYY-MM-DD",
                },
                "end_date": {
                    "type": "string",
                    "description": "Format: YYYY-MM-DD",
                }
            },
            "required": ["company_name","start_date","end_date"],
        },
    },
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
    },
    {
        "name": "basic_fin",
        "description": "Get company basic financials such as margin, P/E ratio, 52-week high/low etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "This is the name of the company we want basic financials on.",
                }
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "general_faq",
        "description": "Answers general questions related to personal finance, investing, banking, planning.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "This is what the user wants to know information about.",
                }
            },
            "required": ["query"],
        },
    },
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('user_input')

    if not user_input:
        return jsonify({"error": "Invalid input"}), 400

    # Initialize messages to guide assistant behavior
    messages = [{"role": "system", "content": 
                 "Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."}]
    messages.append({"role": "user", "content": user_input})

    # calling chat_completion_request to call ChatGPT completion endpoint
    chat_response = chat_completion_request(messages, functions=functions)

    if isinstance(chat_response, Exception):
        return jsonify({"response": "An error occurred while generating the response from ChatGPT."})

    try: # parsing ChatGPT response
        assistant_message = chat_response.json()["choices"][0]["message"]
    except Exception as e:
        print(f"Error parsing chat response: {e}")
        return jsonify({"response": "An error occurred while parsing the response from ChatGPT."})

    # Decide which function to execute based on ChatGPT response
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
        response_content = "Function not found."

    # Append the assistant's second message
    more_questions_message = "Do you have any more questions I can help with?"

    func = config[fn_name] + " speaking:"

    return jsonify({
        "func": func,
        "response": response_content,
        "more_questions": more_questions_message
    })

if __name__ == '__main__':
    app.run(debug=True)