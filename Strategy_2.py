import pandas as pd
import numpy as np
import pandas_ta as ta
from backtester import BackTester

def process_data(
    data: pd.DataFrame,
    ema_length: int = 100,
    atr_length: int = 14,
    macd_fast: int = 6,
    macd_slow: int = 19,
    macd_signal: int = 4
) -> pd.DataFrame:
    """
    Process input data by adding EMA, ATR, and MACD indicators.

    Returns:
    --------
    pd.DataFrame
        DataFrame with EMA, ATR, MACD line, and MACD signal columns added.
    """
    data = data.copy()
    # Calculate EMA instead of SMA
    data['EMA'] = data['close'].ewm(span=ema_length, adjust=False).mean()
    data['ATR'] = ta.atr(data['high'], data['low'], data['close'], length=atr_length)

    # Calculate MACD using pandas_ta
    macd_df = ta.macd(data['close'], fast=macd_fast, slow=macd_slow, signal=macd_signal)

    data['MACD'] = macd_df[f'MACD_{macd_fast}_{macd_slow}_{macd_signal}']
    data['MACD_signal'] = macd_df[f'MACDs_{macd_fast}_{macd_slow}_{macd_signal}']

    return data


def strat(
    data: pd.DataFrame,
    ema_length: int = 100,
    atr_length: int = 14,
    trailing_stop_multiplier: float = 2.0,
    num_wrong_limit: int = 2
) -> pd.DataFrame:
    """
    Generate trading signals based on EMA trend filter, MACD momentum, and ATR trailing stops.
    """
    data = data.copy()
    data['signals'] = 0
    data['trade_type'] = "HOLD"

    position = 0  # 0 = no position, 1 = long, -1 = short
    trailing_stop = 0.0
    num_wrong = 0

    start_idx = max(ema_length, atr_length, 26)  # MACD slow period is 26

    for i in range(start_idx, len(data)):
        close = data.loc[i, 'close']
        open_ = data.loc[i, 'open']
        atr = data.loc[i, 'ATR']
        ema = data.loc[i, 'EMA']
        macd = data.loc[i, 'MACD']
        macd_signal = data.loc[i, 'MACD_signal']

        # Previous MACD values for crossover detection
        prev_macd = data.loc[i - 1, 'MACD']
        prev_macd_signal = data.loc[i - 1, 'MACD_signal']

        # Skip if any are NaN
        if pd.isna(atr) or pd.isna(macd) or pd.isna(macd_signal) or pd.isna(ema):
            continue

        # Detect MACD crossovers
        macd_cross_up = (prev_macd < prev_macd_signal) and (macd > macd_signal)
        macd_cross_down = (prev_macd > prev_macd_signal) and (macd < macd_signal)

        if position == 0:
            # Long entry
            if close > ema and macd_cross_up and close > open_:
                data.loc[i, 'signals'] = 1
                data.loc[i, 'trade_type'] = "LONG"
                position = 1
                trailing_stop = close - atr * trailing_stop_multiplier
                num_wrong = 0

            # Short entry
            elif close < ema and macd_cross_down and close < open_:
                data.loc[i, 'signals'] = -1
                data.loc[i, 'trade_type'] = "SHORT"
                position = -1
                trailing_stop = close + atr * trailing_stop_multiplier
                num_wrong = 0

        elif position == 1:
            # Long position management
            if close <= data.loc[i - 1, 'close']:
                num_wrong += 1
            else:
                num_wrong = 0

            exit_signal = macd_cross_down or (close < ema)

            if exit_signal or num_wrong >= num_wrong_limit or close < trailing_stop:
                data.loc[i, 'signals'] = -1  # Close long
                data.loc[i, 'trade_type'] = "CLOSE"
                position = 0
                num_wrong = 0
            else:
                trailing_stop = max(trailing_stop, close - atr * trailing_stop_multiplier)

        elif position == -1:
            # Short position management
            if close >= data.loc[i - 1, 'close']:
                num_wrong += 1
            else:
                num_wrong = 0

            exit_signal = macd_cross_up or (close > ema)

            if exit_signal or num_wrong >= num_wrong_limit or close > trailing_stop:
                data.loc[i, 'signals'] = 1   # Close short
                data.loc[i, 'trade_type'] = "CLOSE"
                position = 0
                num_wrong = 0
            else:
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