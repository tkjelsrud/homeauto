import requests

def get_stock_data(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1mo&interval=1d"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": f"Failed to fetch data for {symbol}"}

    data = response.json()

    try:
        timestamps = data["chart"]["result"][0]["timestamp"]
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]

        last_close = closes[-1]
        last_week_close = closes[-5]
        start_of_year_close = closes[0]

        daily_change = ((last_close - closes[-2]) / closes[-2]) * 100
        weekly_change = ((last_close - last_week_close) / last_week_close) * 100
        ytd_change = ((last_close - start_of_year_close) / start_of_year_close) * 100

        return {
            "index": symbol,
            "last_close": round(last_close, 2),
            "daily_change": f"{round(daily_change, 2)}%",
            "weekly_change": f"{round(weekly_change, 2)}%",
            "ytd_change": f"{round(ytd_change, 2)}%"
        }

    except (KeyError, IndexError):
        return {"error": f"Invalid data format for {symbol}"}

# Get data for Oslo Børs and Nasdaq
oslo_bors = get_stock_data("^OSEBX")
nasdaq = get_stock_data("^IXIC")

# Print results
print(oslo_bors)
print(nasdaq)