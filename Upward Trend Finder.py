# Import necessary libraries
import ccxt.async_support as ccxt_async
import pandas as pd
import numpy as np
import asyncio
import matplotlib.pyplot as plt
import datetime
import mplfinance as mpf

# Initialize the Binance exchange object
exchange = ccxt_async.binance({'enableRateLimit': True})

# Define the trading pair symbol, timeframe, data limit, and consecutive count for lows and highs
symbol = 'ETH/USDT'
timeframe = "1d"
limit = 400
windows = 3

# Function to fetch OHLCV data from the exchange
async def fetch_ohlcv(symbol, timeframe, limit):
    ohlcv = await exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

# Function to find significant lows in the OHLCV data
async def find_significant_lows(symbol, timeframe, limit):
    df = await fetch_ohlcv(symbol, timeframe, limit)
    lows = []  # Initialize an empty list to store lows
    consecutive_lows = 0  # Initialize a counter for consecutive lows
    all_lows = []  # Initialize a list to store all sets of significant lows

    for i in range(len(df)):
        if len(lows) == 0:
            lows.append(df['low'][i])  # Add the low of the first candle to the list
        else:
            previous_low = lows[-1]  
            current_low = df['low'][i] 

            if previous_low <= current_low:
                lows.append(current_low)
                consecutive_lows = 0  
            else:
                consecutive_lows += 1
                if consecutive_lows >= 4:  # Check for a sequence of 5 consecutive lows
                    consecutive_lows = 0
                    lows = []

        if len(lows) == 6:  
            all_lows.append(lows)
            lows = []

    # Print the shape and content of significant lows
    print("all_lows shape:", len(all_lows), "x", len(all_lows[0]) if all_lows else 0)
    print("all_lows content:")
    for i, sublist in enumerate(all_lows):
        print(f"Sublist {i + 1}: {sublist}")
    return all_lows

# Function to find significant highs in the OHLCV data
async def find_significant_highs(symbol, timeframe, limit):
    df = await fetch_ohlcv(symbol, timeframe, limit)
    highs = [] # Initialize an empty list to store highs
    consecutive_highs = 0  # Initialize a counter for consecutive highs
    all_highs = []  # Initialize a list to store all sets of significant highs

    for i in range(len(df)):
        if len(highs) == 0:
            highs.append(df['high'][i])  
        else:
            previous_high = highs[-1]  # Get the previous high
            current_high = df['high'][i]  # Get the current high

            if previous_high <= current_high:
                highs.append(current_high)
                consecutive_highs = 0  
            else:
                consecutive_highs += 1
                if consecutive_highs >= 4:  # Check for a sequence of 5 consecutive highs
                    consecutive_highs = 0
                    highs = []

        if len(highs) == 6: 
            all_highs.append(highs)
            highs = []

    # Print the shape and content of significant highs
    print("all_highs shape:", len(all_highs), "x", len(all_highs[0]) if all_highs else 0)
    print("all_highs content:")
    for i, sublist in enumerate(all_highs):
        print(f"Sublist {i + 1}: {sublist}")
    return all_highs

# Function to plot candlestick charts for significant lows and highs
async def plot_significant_lows_highs(symbol, timeframe, limit, min_low_count, min_high_count):
    all_lows = await find_significant_lows(symbol, timeframe, limit)
    all_highs = await find_significant_highs(symbol, timeframe, limit)

    # Check if there are enough significant lows and highs to plot
    if all(len(sublist) >= min_low_count for sublist in all_lows) and all(len(sublist) >= min_high_count for sublist in all_highs):
        df = await fetch_ohlcv(symbol, timeframe, limit)

        # Convert timestamp to a more readable date format
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        for sublist in all_lows:
            first_low_index = df[df['low'] == sublist[0]].index[0]
            last_low_index = df[df['low'] == sublist[-1]].index[0]
            df_subset = df[first_low_index:last_low_index + 1]
            ohlc_data = df_subset[['timestamp', 'open', 'high', 'low', 'close']]
            ohlc_data.set_index('timestamp', inplace=True)
            mpf.plot(ohlc_data, type='candle', style='yahoo', title=f'Upward Trends for {symbol} ({timeframe})')
    else:
        print(f"Not enough significant lows found. Expected at least {min_low_count} or more elements in each sublist.")

# Main asynchronous function
async def main():
    try:
        await plot_significant_lows_highs(symbol, timeframe, limit, min_low_count=6, min_high_count=6)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the exchange instance and related resources
        await exchange.close()

# Execute the main function
if __name__ == "__main__":
    asyncio.run(main())
