# Import required libraries
import ccxt.async_support as ccxt_async
import pandas as pd
import asyncio
import mplfinance as mpf

# Create a Binance exchange object with rate limiting enabled
exchange = ccxt_async.binance({'enableRateLimit': True})

# Define the trading symbol, timeframe, data limit, and window size for lows and highs
symbol = 'ETH/USDT'
timeframe = "1d"
limit = 400
windows = 3

# Function to fetch OHLCV data and convert it to a DataFrame
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
            previous_low = lows[-1]  # Get the previous low
            current_low = df['low'][i]  # Get the current low

            if previous_low <= current_low:
                lows.append(current_low)  # Add the current low to the list
                consecutive_lows = 0  # Reset consecutive lows counter
            else:
                consecutive_lows += 1  # Increment consecutive lows counter
                if consecutive_lows >= 4:  # Check if there are at least 5 consecutive lows
                    consecutive_lows = 0  # Reset consecutive lows counter
                    lows = []  # Reset the lows list

        if len(lows) == 6:  # Check if we have collected 6 lows
            all_lows.append(lows)  # Add the set of lows to the list
            lows = []  # Reset the lows list

    print("Shape of all_lows:", len(all_lows), "x", len(all_lows[0]) if all_lows else 0)
    print("Contents of all_lows:")
    for i, sublist in enumerate(all_lows):
        print(f"Sublist {i + 1}: {sublist}")
    return all_lows

# Function to find significant highs in the OHLCV data
async def find_significant_highs(symbol, timeframe, limit):
    df = await fetch_ohlcv(symbol, timeframe, limit)
    highs = []  # Initialize an empty list to store highs
    consecutive_highs = 0  # Initialize a counter for consecutive highs
    all_highs = []  # Initialize a list to store all sets of significant highs

    for i in range(len(df)):
        if len(highs) == 0:
            highs.append(df['high'][i])  # Add the high of the first candle to the list
        else:
            previous_high = highs[-1]  # Get the previous high
            current_high = df['high'][i]  # Get the current high

            if previous_high <= current_high:
                highs.append(current_high)  # Add the current high to the list
                consecutive_highs = 0  # Reset consecutive highs counter
            else:
                consecutive_highs += 1  # Increment consecutive highs counter
                if consecutive_highs >= 4:  # Check if there are at least 5 consecutive highs
                    consecutive_highs = 0  # Reset consecutive highs counter
                    highs = []  # Reset the highs list

        if len(highs) == 6:  # Check if we have collected 6 highs
            all_highs.append(highs)  # Add the set of highs to the list
            highs = []  # Reset the highs list

    print("Shape of all_highs:", len(all_highs), "x", len(all_highs[0]) if all_highs else 0)
    print("Contents of all_highs:")
    for i, sublist in enumerate(all_highs):
        print(f"Sublist {i + 1}: {sublist}")
    return all_highs

# Function to plot significant lows and highs on a candlestick chart
async def plot_significant_lows_highs(symbol, timeframe, limit, min_low_count, min_high_count):
    all_lows = await find_significant_lows(symbol, timeframe, limit)
    all_highs = await find_significant_highs(symbol, timeframe, limit)

    if all(len(sublist) >= min_low_count for sublist in all_lows) and all(len(sublist) >= min_high_count for sublist in all_highs):
        df = await fetch_ohlcv(symbol, timeframe, limit)

        # Convert timestamp to a more readable date format
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        for sublist in all_lows:
            # Find the index of the first and last significant lows in the sublist
            first_low_index = df[df['low'] == sublist[0]].index[0]
            last_low_index = df[df['low'] == sublist[-1]].index[0]

            # Extract the portion of the DataFrame between the first and last significant lows
            df_subset = df[first_low_index:last_low_index + 1]

            # Create a DataFrame in the OHLC format for mplfinance
            ohlc_data = df_subset[['timestamp', 'open', 'high', 'low', 'close']]
            ohlc_data.set_index('timestamp', inplace=True)

            # Plot candlestick chart for the current sublist
            mpf.plot(ohlc_data, type='candle', style='yahoo', title=f'Upward Trends for {symbol} ({timeframe})')

    else:
        print(f"Not enough significant lows or highs found. Expected at least {min_low_count} or more elements in each sublist.")

# Main asynchronous function to run the program
async def main():
    try:
        await plot_significant_lows_highs(symbol, timeframe, limit, min_low_count=6, min_high_count=6)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the exchange instance and related resources
        await exchange.close()

# Entry point for the script
if __name__ == "__main__":
    asyncio.run(main())
