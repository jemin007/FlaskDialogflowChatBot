from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)

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

# Function to get the latest stock price using yfinance
def get_latest_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        history = stock.history(period="1d")
        if history.empty:
            print("Stock history data not available.")
            return None
        latest_price = history['Close'][-1]
        return latest_price
    except Exception as error:
        print(f"Error fetching stock price: {error}")
        return None

# Function to get company fundamentals using yfinance
def get_company_fundamentals(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        if not info:
            print("Fundamentals data not available.")
            return None
        formatted_market_cap = format_market_cap(info.get('marketCap', 0))
        fundamentals = {
            'Name': info.get('shortName', 'N/A'),
            'Market Cap': formatted_market_cap,
            'P/E Ratio': info.get('trailingPE', 'N/A'),
            '52-Week High': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52-Week Low': info.get('fiftyTwoWeekLow', 'N/A'),  # Added this line to fetch 52-week low
            'Description': info.get('longBusinessSummary', 'N/A')
        }
        return fundamentals
    except Exception as error:
        print(f"Error fetching company fundamentals: {error}")
        return None

# Function to get dividend and P/E ratio using yfinance
def get_dividend_and_pe(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        if not info:
            print("Dividend and P/E ratio data not available.")
            return None
        dividend_and_pe = {
            'Dividend Yield': info.get('dividendYield', 'N/A'),
            'P/E Ratio': info.get('trailingPE', 'N/A')
        }
        return dividend_and_pe
    except Exception as error:
        print(f"Error fetching dividend and P/E ratio: {error}")
        return None

# Route for the root path
@app.route('/')
def index():
    # Structure the response as a dictionary
    response_data = {
        "Name": "Jemin Shrestha",
        "Student ID": "200567785",
        "Subject": "Conversational AI",
        "Assignment": "3"
    }
    
    # Return the response as JSON
    return jsonify(response_data)

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
            response_text = f"{company_name} is currently trading at ${stock_price:.2f}."
        else:
            response_text = f"Sorry, I couldn't fetch the latest stock price for {company_name}."

    # Handle the 'GetCompanyFundamentals' intent
    elif intent == 'GetCompanyFundamentals':
        fundamentals = get_company_fundamentals(company_name)
        if fundamentals:
            response_text = (f"(1): Company: {fundamentals['Name']}\n"
                             f"(2): Market Cap: {fundamentals['Market Cap']}\n"
                             f"(3): P/E Ratio: {fundamentals['P/E Ratio']}\n"
                             f"(4): 52-Week High: {fundamentals['52-Week High']}\n"
                             f"(5): Description: {fundamentals['Description']}")
        else:
            response_text = f"Sorry, I couldn't find the company fundamentals for {company_name}. Please check the symbol and try again."

    # Handle the 'GetDividendAndPE' intent
    elif intent == 'GetDividendAndPE':
        dividend_and_pe = get_dividend_and_pe(company_name)
        if dividend_and_pe:
            response_text = (f"Dividend Yield for {company_name}: {dividend_and_pe['Dividend Yield']}\n"
                             f"P/E Ratio: {dividend_and_pe['P/E Ratio']}")
        else:
            response_text = f"Sorry, I couldn't fetch the dividend yield and P/E ratio for {company_name}."
    
    # Handle the new 'GetMarketCapData' intent
    elif intent == 'GetMarketCapData':
        fundamentals = get_company_fundamentals(company_name)
        if fundamentals:
            market_cap = fundamentals['Market Cap']
            high = fundamentals['52-Week High']
            low = fundamentals['52-Week Low']
            
            # Respond with market cap, 52-week high and low in a single line
            response_text = (f"{company_name} - Market Cap: {market_cap}, "
                             f"52-Week High: {high}, 52-Week Low: {low}")
        else:
            response_text = f"Sorry, I couldn't fetch the data for {company_name}."
    
    return jsonify({
        'fulfillmentText': response_text
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)
