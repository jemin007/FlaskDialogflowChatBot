from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# AlphaVantage API key 
ALPHAVANTAGE_API_KEY = '9GZJKCNBTDQJL9BR'

# Function to format market cap
def format_market_cap(value):
    if value >= 1e12:
        return f"{value / 1e12:.2f} Trillion"
    elif value >= 1e9:
        return f"{value / 1e9:.2f} Billion"
    elif value >= 1e6:
        return f"{value / 1e6:.2f} Million"
    else:
        return str(value)

# Function to get the latest stock price (1-minute interval)
def get_latest_stock_price(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey={ALPHAVANTAGE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if the API request fails
        data = response.json()
        time_series = data.get('Time Series (1min)', {})
        if time_series:
            latest_timestamp = list(time_series.keys())[0]  # Get the most recent timestamp
            latest_data = time_series[latest_timestamp]
            latest_price = latest_data['1. open']  # Get the latest opening price
            return latest_price
        return None
    except requests.exceptions.RequestException as error:
        print(f"Error fetching stock price: {error}")
        return None

# Route for the root path
@app.route('/')
def index():
    return "Jemin Shrestha : 200567785"

# POST endpoint for Dialogflow webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    # Extract the intent and parameters from Dialogflow's request
    data = request.get_json()
    intent = data['queryResult']['intent']['displayName']  # Name of the intent
    company_name = data['queryResult']['parameters']['company_name']  # The parameter sent by Dialogflow
    
    response_text = ''  # This will hold the response to send back to Dialogflow

    # Check which intent is being triggered
    if intent == 'GetStockPrice':
        # Fetch the latest stock price
        stock_price = get_latest_stock_price(company_name)
        if stock_price:
            response_text = f"{company_name} is currently trading at ${stock_price}."
        else:
            response_text = f"Sorry, I couldn't fetch the latest stock price for {company_name}."

    # Handle the 'GetCompanyFundamentals' intent
    elif intent == 'GetCompanyFundamentals':
        api_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={company_name}&apikey={ALPHAVANTAGE_API_KEY}"
        try:
            api_response = requests.get(api_url)
            api_response.raise_for_status()
            data = api_response.json()

            if data and data.get('Name'):
                formatted_market_cap = format_market_cap(float(data['MarketCapitalization']))
                response_text = (f"(1): Company: {data['Name']}\n"
                                 f"(2): Market Cap: {formatted_market_cap}\n"
                                 f"(3): P/E Ratio: {data['PERatio']}\n"
                                 f"(4): 52-Week High: {data['52WeekHigh']}\n"
                                 f"(5): Description: {data['Description']}")
            else:
                response_text = f"Sorry, I couldn't find the company fundamentals for {company_name}. Please check the symbol and try again."
        except requests.exceptions.RequestException as error:
            print(f"Error fetching company fundamentals: {error}")
            response_text = f"Sorry, I couldn't fetch the company fundamentals for {company_name}."

    # Handle the 'GetEarningsReport' intent
    elif intent == 'GetEarningsReport':
        api_url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={company_name}&apikey={ALPHAVANTAGE_API_KEY}'
        try:
            api_response = requests.get(api_url).json()
            quarterly_earnings = api_response.get('quarterlyEarnings', [])
            
            if quarterly_earnings:
                latest_earnings = quarterly_earnings[0]  # Get the most recent earnings report
                # Safely access the keys and handle missing data
                report_date = latest_earnings.get('reportedDate', 'N/A')
                estimated_eps = latest_earnings.get('estimatedEPS', 'N/A')
                reported_eps = latest_earnings.get('reportedEPS', 'N/A')
                surprise = latest_earnings.get('surprise', 'N/A')
                
                response_text = (f"Latest earnings report for {company_name}:\n"
                                 f"Reported Date: {report_date}\n"
                                 f"Estimated EPS: {estimated_eps}\n"
                                 f"Actual EPS: {reported_eps}\n"
                                 f"Surprise: {surprise}")
            else:
                response_text = f"Sorry, I couldn't find the earnings report for {company_name}."
        except Exception as e:
            print(f"Error fetching earnings report: {e}")
            response_text = f"Sorry, I couldn't fetch the earnings report for {company_name}."
    
    return jsonify({
        'fulfillmentText': response_text
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)
