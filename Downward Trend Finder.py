import ccxt.async_support as ccxt_async
import pandas as pd
import asyncio
import mplfinance as mpf

# Initialize the Binance exchange with rate limiting enabled
exchange = ccxt_async.binance({'enableRateLimit': True})

# Define the trading symbol, timeframe, data limit, and the number of windows
symbol = 'ETH/USDT'
timeframe = "4h"
limit = 1000
windows = 3

# Function to fetch OHLCV (Open, High, Low, Close, Volume) data asynchronously
async def fetch_ohlcv(symbol, timeframe, limit):
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except Exception as e:
        print(f"Error fetching OHLCV data: {str(e)}")
        return None

# Function to find significant lows and highs in the price data
async def find_significant_lows_highs(symbol, timeframe, limit):
    try:
        df = await fetch_ohlcv(symbol, timeframe, limit)
        if df is None:
            return None

        lows = []  # Create an empty "lows" list.
        highs = []
        consecutive_lows = 0
        consecutive_highs = 0
        all_highs = []

        for i in range(len(df)):
            if len(highs) == 0:
                lows.append((df['low'][i], i))  # Append (value, index) pairs.
                highs.append((df["high"][i], i))
            else:
                # Get the previous highest value and index
                previous_high, previous_high_index = highs[-1]
                current_high, current_high_index = df['high'][i], i
                previous_low, previous_low_index = lows[-1]
                current_low, current_low_index = df["low"][i], i

                if previous_high > current_high:
                    consecutive_highs = 0
                    if previous_low > current_low:
                        highs.append((current_high, current_high_index))
                        lows.append((current_low, current_low_index))
                        consecutive_highs = 0
                    else:
                        consecutive_lows += 1
                        if consecutive_lows >= 1:
                            lows = []
                            highs = []
                            consecutive_highs = 0
                            consecutive_lows = 0
                        else:
                            highs.append((current_high, current_high_index))
                            lows.append((current_low, current_low_index))
                else:
                    consecutive_highs += 1
                    if consecutive_highs >= 2:
                        consecutive_highs = 0
                        consecutive_lows = 0
                        lows = []
                        highs = []

            if len(highs) == 5:
                all_highs.append(highs)
                highs = []

        print("Shape of all_highs:", len(all_highs), "x", len(all_highs[0]) if all_highs else 0)
        print("Contents of all_highs:")
        for i, sublist in enumerate(all_highs):
            print(f"Sublist {i + 1}: {sublist}")

        return all_highs
    except Exception as e:
        print(f"Error finding significant lows and highs: {str(e)}")
        return None

# Function to plot significant lows and highs as candlestick charts
async def plot_significant_lows_highs(symbol, timeframe, limit, min_low_count, min_high_count):
    try:
        all_highs = await find_significant_lows_highs(symbol, timeframe, limit)
        if all_highs is None:
            return

        df = await fetch_ohlcv(symbol, timeframe, limit)
        if df is None:
            return

        # Convert timestamp to a more readable date format
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        for sublist in all_highs:
            high_indices = [high_index for _, high_index in sublist]
            # Find the first and last index of significant highs in the sublist
            first_high_index = min(high_indices)
            last_high_index = max(high_indices)

            # Extract the portion of the DataFrame between the first and last significant highs
            df_subset = df.iloc[first_high_index:last_high_index + 1]

            # Create a DataFrame in the OHLC format for mplfinance
            ohlc_data = df_subset[['timestamp', 'open', 'high', 'low', 'close']]
            ohlc_data.set_index('timestamp', inplace=True)

            # Define the date format as 'YYYY-MM-DD HH:mm:ss' (year-month-day hour:minute:second)
            date_format = '%Y-%m-%d %H:%M:%S'

            # Plot candlestick chart for the current sublist with the custom date format
            mpf.plot(ohlc_data, type='candle', style='yahoo', title=f'Upward Trends for {symbol} ({timeframe})',
                     datetime_format=date_format)
    except Exception as e:
        print(f"Error plotting significant lows and highs: {str(e)}")

# Main asynchronous function
async def main():
    try:
        # Call the function to plot significant lows and highs
        await plot_significant_lows_highs(symbol, timeframe, limit, min_low_count=6 , min_high_count=6)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the exchange instance and related resources
        try:
            await exchange.close()
        except Exception as e:
            print(f"Error closing exchange connection: {str(e)}")

# Run the main asynchronous function
if __name__ == "__main__":
    asyncio.run(main())
