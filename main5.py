import pandas as pd
import numpy as np
import pandas_ta as ta
from backtester import BackTester

def process_data(
    data: pd.DataFrame,
    sma_length: int = 150,
    atr_length: int = 14,
    rsi_length: int = 14
) -> pd.DataFrame:
    """
    Process input data by adding SMA, ATR, and RSI indicators.

    Parameters:
    -----------
    data : pd.DataFrame
        The input OHLCV data.

    sma_length : int
        Period for Simple Moving Average (SMA).

    atr_length : int
        Period for Average True Range (ATR).

    rsi_length : int
        Period for Relative Strength Index (RSI).

    Returns:
    --------
    pd.DataFrame
        DataFrame with SMA, ATR, and RSI columns added.
    """
    data = data.copy()
    data['SMA'] = data['close'].rolling(window=sma_length).mean()
    data['ATR'] = ta.atr(data['high'], data['low'], data['close'], length=atr_length)
    data['RSI'] = ta.rsi(data['close'], length=rsi_length)
    return data


def strat(
    data: pd.DataFrame,
    sma_length: int = 150,
    atr_length: int = 14,
    trailing_stop_multiplier: float = 2.0,
    rsi_entry_threshold_long: float = 60,
    rsi_entry_threshold_short: float = 40,
    num_wrong_limit: int = 3
) -> pd.DataFrame:
    """
    Generate trading signals based on SMA trend filter, RSI momentum, and ATR trailing stops.

    Parameters:
    -----------
    data : pd.DataFrame
        Input data with SMA, ATR, and RSI columns.

    sma_length : int
        Period for SMA used as trend filter.

    atr_length : int
        ATR period (matching process_data).

    trailing_stop_multiplier : float
        Multiplier for ATR to set trailing stop distance.

    rsi_entry_threshold_long : float
        Minimum RSI value to allow long entries.

    rsi_entry_threshold_short : float
        Maximum RSI value to allow short entries.

    num_wrong_limit : int
        Number of consecutive adverse closes allowed before exit.

    Returns:
    --------
    pd.DataFrame
        DataFrame with added 'signals' and 'trade_type' columns.
    """
    data = data.copy()
    data['signals'] = 0
    data['trade_type'] = "HOLD"

    position = 0  # 0 = no position, 1 = long, -1 = short
    trailing_stop = 0.0
    num_wrong = 0

    start_idx = max(sma_length, atr_length)

    for i in range(start_idx, len(data)):
        close = data.loc[i, 'close']
        open_ = data.loc[i, 'open']
        atr = data.loc[i, 'ATR']
        rsi = data.loc[i, 'RSI']
        sma = data.loc[i, 'SMA']

        if pd.isna(atr) or pd.isna(rsi) or pd.isna(sma):
            continue

        if position == 0:
            # Long Entry: price > SMA and RSI above threshold and bullish candle
            if close > sma and rsi >= rsi_entry_threshold_long and close > open_:
                data.loc[i, 'signals'] = 1
                data.loc[i, 'trade_type'] = "LONG"
                position = 1
                trailing_stop = close - atr * trailing_stop_multiplier
                num_wrong = 0

            # Short Entry: price < SMA and RSI below threshold and bearish candle
            elif close < sma and rsi <= rsi_entry_threshold_short and close < open_:
                data.loc[i, 'signals'] = -1
                data.loc[i, 'trade_type'] = "SHORT"
                position = -1
                trailing_stop = close + atr * trailing_stop_multiplier
                num_wrong = 0

        elif position == 1:
            # Long position management
            # Count consecutive closes below previous close as adverse
            if close <= data.loc[i - 1, 'close']:
                num_wrong += 1
            else:
                num_wrong = 0

            # Exit long if RSI falls below short threshold or SMA trend is lost
            exit_signal = (rsi < rsi_entry_threshold_short) or (close < sma)

            if exit_signal or num_wrong >= num_wrong_limit or close < trailing_stop:
                data.loc[i, 'signals'] = -1   # Close long
                data.loc[i, 'trade_type'] = "CLOSE"
                position = 0
                num_wrong = 0
            else:
                # Move trailing stop up only
                trailing_stop = max(trailing_stop, close - atr * trailing_stop_multiplier)

        elif position == -1:
            # Short position management
            # Count consecutive closes above previous close as adverse
            if close >= data.loc[i - 1, 'close']:
                num_wrong += 1
            else:
                num_wrong = 0

            # Exit short if RSI rises above long threshold or SMA trend is lost
            exit_signal = (rsi > rsi_entry_threshold_long) or (close > sma)

            if exit_signal or num_wrong >= num_wrong_limit or close > trailing_stop:
                data.loc[i, 'signals'] = 1    # Close short
                data.loc[i, 'trade_type'] = "CLOSE"
                position = 0
                num_wrong = 0
            else:
                # Move trailing stop down only
                trailing_stop = min(trailing_stop, close + atr * trailing_stop_multiplier)

    return data

def main():
    data = pd.read_csv("BTC_2019_2023_1d.csv")
    processed_data = process_data(data) # process the data
    result_data = strat(processed_data) # Apply the strategy
    csv_file_path = "final_data.csv" 
    result_data.to_csv(csv_file_path, index=False)

    bt = BackTester("BTC", signal_data_path="final_data.csv", master_file_path="final_data.csv", compound_flag=1)
    bt.get_trades(1000)

    # print trades and their PnL
    for trade in bt.trades: 
        print(trade)
        print(trade.pnl())

    # Print results
    stats = bt.get_statistics()
    for key, val in stats.items():
        print(key, ":", val)


    #Check for lookahead bias
    print("Checking for lookahead bias...")
    lookahead_bias = False
    for i in range(len(result_data)):
        if result_data.loc[i, 'signals'] != 0:  # If there's a signal
            temp_data = data.iloc[:i+1].copy()  # Take data only up to that point
            temp_data = process_data(temp_data) # process the data
            temp_data = strat(temp_data) # Re-run strategy
            if temp_data.loc[i, 'signals'] != result_data.loc[i, 'signals']:
                print(f"Lookahead bias detected at index {i}")
                lookahead_bias = True

    if not lookahead_bias:
        print("No lookahead bias detected.")

    # Generate the PnL graph
    bt.make_trade_graph()
    bt.make_pnl_graph()
    
if __name__ == "__main__":
    main()