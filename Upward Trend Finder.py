import ccxt.async_support as ccxt_async
import pandas as pd
import asyncio
import mplfinance as mpf

# Create an asynchronous Binance exchange instance with rate limiting enabled
exchange = ccxt_async.binance({'enableRateLimit': True})

# Example usage:
symbol = 'ETH/USDT'  # The trading pair symbol
timeframe = "4h"  # The timeframe for OHLCV data
limit = 1000  # The maximum number of data points to retrieve
windows = 3  # Number of consecutive windows for pattern detection

# Asynchronous function to fetch OHLCV (Open, High, Low, Close, Volume) data
async def fetch_ohlcv(symbol, timeframe, limit):
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except Exception as e:
        print(f"Error fetching OHLCV data: {str(e)}")
        return None

# Asynchronous function to find significant lows and highs in the OHLCV data
async def find_significant_lows_highs(symbol, timeframe, limit):
    try:
        df = await fetch_ohlcv(symbol, timeframe, limit)
        if df is None:
            return None

        lows = []  # Create an empty list to store significant lows
        highs = []  # Create an empty list to store significant highs
        consecutive_lows = 0
        consecutive_highs = 0
        all_lows = []  # Store lists of consecutive lows

        for i in range(len(df)):
            if len(lows) == 0:
                lows.append((df['low'][i], i))  # Append (value, index) pair to lows list
                highs.append((df["high"][i], i))  # Append (value, index) pair to highs list
            else:
                previous_low, previous_low_index = lows[-1]
                current_low, current_low_index = df['low'][i], i
                previous_high, previous_high_index = highs[-1]
                current_high, current_high_index = df["high"][i], i

                if previous_low < current_low:
                    consecutive_lows = 0
                    if previous_high < current_high:
                        lows.append((current_low, current_low_index))
                        highs.append((current_high, current_high_index))
                        consecutive_highs = 0
                    else:
                        consecutive_highs += 1
                        if consecutive_highs >= 1:
                            lows = []
                            highs = []
                            consecutive_highs = 0
                            consecutive_lows = 0
                        else:
                            lows.append((current_low, current_low_index))
                            highs.append((current_high, current_high_index))
                else:
                    consecutive_lows += 1
                    if consecutive_lows >= 2:
                        consecutive_highs = 0
                        consecutive_lows = 0
                        lows = []
                        highs = []

            if len(lows) == 5:
                all_lows.append(lows)
                lows = []

        print("Shape of all_lows:", len(all_lows), "x", len(all_lows[0]) if all_lows else 0)
        print("Contents of all_lows:")
        for i, sublist in enumerate(all_lows):
            print(f"Sublist {i + 1}: {sublist}")

        return all_lows
    except Exception as e:
        print(f"Error finding significant lows and highs: {str(e)}")
        return None

# Asynchronous function to plot significant lows and highs using mplfinance
async def plot_significant_lows_highs(symbol, timeframe, limit, min_low_count, min_high_count):
    try:
        all_lows = await find_significant_lows_highs(symbol, timeframe, limit)

        if all_lows is None:
            return

        df = await fetch_ohlcv(symbol, timeframe, limit)

        if df is None:
            return

        # Convert timestamp to a more readable date format
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        for sublist in all_lows:
            low_indices = [low_index for _, low_index in sublist]
            first_low_index = min(low_indices)
            last_low_index = max(low_indices)

            df_subset = df.iloc[first_low_index:last_low_index + 1]

            ohlc_data = df_subset[['timestamp', 'open', 'high', 'low', 'close']]
            ohlc_data.set_index('timestamp', inplace=True)

            date_format = '%Y-%m-%d %H:%M:%S'

            mpf.plot(ohlc_data, type='candle', style='yahoo', title=f'Upward Trends for {symbol} ({timeframe})',
                     datetime_format=date_format)
    except Exception as e:
        print(f"Error plotting significant lows and highs: {str(e)}")

# Asynchronous main function
async def main():
    try:
        await plot_significant_lows_highs(symbol, timeframe, limit, min_low_count=6, min_high_count=6)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the exchange instance and related resources
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(main())

