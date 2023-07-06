import requests
import datetime
import statistics

STOCK = (input("stock ticker symbol: ")).upper()
SHEETY_ENDPOINT = "https://api.sheety.co/e116470edd1aa26f1b53d119a702f00f/stocks/sheet1"

# Data Retreival
API_KEY = "KY72V2Q9ARPH22LV"
book_value_url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={STOCK}&apikey={API_KEY}'
eps_url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={STOCK}&apikey={API_KEY}'
inflation_url = f'https://www.alphavantage.co/query?function=INFLATION&apikey={API_KEY}'
price_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={STOCK}&apikey={API_KEY}'

# requests
book_value_r = requests.get(book_value_url)
eps_r = requests.get(eps_url)
inflation_r = requests.get(inflation_url)
price_r = requests.get(price_url)

# json formatting
book_value_data = book_value_r.json()
eps_data = eps_r.json()
inflation_data = inflation_r.json()
price_data = price_r.json()


# eps values and dates
yearly_eps_values = [float(eps_data["annualEarnings"][i]["reportedEPS"]) for i in range(0, len(eps_data["annualEarnings"]))]
yearly_eps_dates = [eps_data["annualEarnings"][i]["fiscalDateEnding"].split("-")[0] for i in range(0, len(eps_data["annualEarnings"]))]

#inflation values and dates
yearly_inflation_values = [float(inflation_data["data"][i]["value"])/100 for i in range(0, len(inflation_data["data"]))] #values in decimal format
yearly_inflation_dates = [inflation_data["data"][i]["date"].split("-")[0] for i in range(0, len(inflation_data["data"]))]

# Book value
book_value = book_value_data["BookValue"] #gets book value

# gets stock price at close
now = datetime.datetime.now()
today = datetime.date.today()
current_time = str(now.time())
closing_time = "13:00:00"
one_day_ago = today - datetime.timedelta(days=1)
two_days_ago = today - datetime.timedelta(days=2)
three_days_ago = today - datetime.timedelta(days=3)
weekday = datetime.datetime.today().weekday()

if weekday == 0:
    try:
        daily_price = float(price_data["Time Series (Daily)"][today.strftime("%Y-%m-%d")]['4. close'])
    except KeyError:
        daily_price = float(price_data["Time Series (Daily)"][three_days_ago.strftime("%Y-%m-%d")]['4. close'])

elif 4 >= weekday > 0:
    try:
        daily_price = float(price_data["Time Series (Daily)"][today.strftime("%Y-%m-%d")]['4. close'])
    except KeyError:
        daily_price = float(price_data["Time Series (Daily)"][one_day_ago.strftime("%Y-%m-%d")]['4. close'])

elif weekday == 5:
    daily_price = float(price_data["Time Series (Daily)"][one_day_ago.strftime("%Y-%m-%d")]['4. close'])
else:
    daily_price = float(price_data["Time Series (Daily)"][two_days_ago.strftime("%Y-%m-%d")]['4. close'])

# Shiller calculations
for i in range(0, len(yearly_eps_dates)):
    if yearly_inflation_dates[i] == yearly_eps_dates[i]:
        adjusted_eps = [item * (1-inf) for inf, item in zip(yearly_inflation_values, yearly_eps_values)]
        average = statistics.mean(adjusted_eps)
        shiller = daily_price / average
    else:
        adjusted_eps = [item * (1-inf) for inf, item in zip(yearly_inflation_values, yearly_eps_values[1:])]
        average = statistics.mean(adjusted_eps)
        shiller = daily_price / average

# percentage gain between price and book value
under_book_value_percent = float((float(book_value)-float(daily_price))/float(daily_price))*100

# read/post/delete/update to google sheets
read_response = requests.get(url=SHEETY_ENDPOINT)
data = read_response.json()
print("response.text =", read_response.text)

ticker = [data["sheet1"][i]["ticker"] for i in range(0, len(data["sheet1"]))]
print("Google Sheet =", read_response.status_code)

info = {
    "sheet1": {
        "ticker": STOCK,
        "price": daily_price,
        "book": book_value,
        "shiller": shiller,
        "%": under_book_value_percent,
    }
}

if float(book_value) > float(daily_price):
    if 15 >= shiller > 0:
        if STOCK in ticker:
            id_endpoint = f"{SHEETY_ENDPOINT}/{ticker.index(STOCK) + 2}"
            response = requests.put(url=id_endpoint, json=info)
            print("Updated to google sheet! =", response.status_code)
        else:
            response = requests.post(url=SHEETY_ENDPOINT, json=info, headers={"Content-Type": "application/json"})
            print("Posted to google sheet! =", response.status_code)
    else:
        if STOCK in ticker:
            id_endpoint = f"{SHEETY_ENDPOINT}/{ticker.index(STOCK)+2}"
            response = requests.delete(url=id_endpoint)
            print("Deleted! =", response.status_code)
        print(f"PE ratio not in range! PE={shiller}")
else:
    if STOCK in ticker:
        id_endpoint = f"{SHEETY_ENDPOINT}/{ticker.index(STOCK)+2}"
        response = requests.delete(url=id_endpoint)
        print("Deleted! =", response.status_code)
    print(f"overvalued! Current Price:${daily_price}, Book Value:${book_value}")




