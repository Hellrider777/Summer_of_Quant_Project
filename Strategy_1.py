import pandas as pd
import numpy as np
import pandas_ta as ta
from backtester import BackTester

def process_data(data: pd.DataFrame, atr_length: int = 14) -> pd.DataFrame:
    """
    Process the input data and return a dataframe with the necessary indicators.

    Parameters:
    -----------
    data : pd.DataFrame
        The input OHLCV data.

    atr_length : int
        The period used to calculate the ATR.

    Returns:
    --------
    pd.DataFrame
        DataFrame with ATR column added.
    """
    data = data.copy()
    data['ATR'] = ta.atr(data['high'], data['low'], data['close'], length=atr_length)
    return data


def strat(
    data: pd.DataFrame,
    atr_length: int = 14,
    trailing_stop_multiplier: float = 2.0,
    volume_lookback: int = 11, #5
    num_wrong_limit: int = 3
) -> pd.DataFrame:
    """
    Generate trade signals using a volume spike filter, ATR trailing stop, and reversal logic.

    Parameters:
    -----------
    data : pd.DataFrame
        The input data including ATR column.

    atr_length : int
        ATR period used to align with the process_data ATR length.

    trailing_stop_multiplier : float
        Multiplier for ATR when calculating trailing stops.

    volume_lookback : int
        Lookback window size to compute rolling mean and std of volume.

    num_wrong_limit : int
        Number of consecutive adverse closes to trigger an exit.

    Returns:
    --------
    pd.DataFrame
        Modified DataFrame with columns: 'signals' and 'trade_type'.
    """
    data = data.copy()

    # Initialize columns
    data['signals'] = 0
    data['trade_type'] = "HOLD"

    position = 0  # 0 = no position, 1 = long, -1 = short
    trailing_stop = 0.0
    num_wrong = 0

    # To ensure enough data for ATR and volume calculations
    start_idx = max(atr_length, volume_lookback)

    for i in range(start_idx, len(data)):

        # Cache required row values
        vol = data.loc[i, 'volume']
        vol_window = data.loc[i - volume_lookback: i, 'volume']
        close = data.loc[i, 'close']
        open_ = data.loc[i, 'open']
        atr = data.loc[i, 'ATR']

        # Skip iteration if ATR is NaN
        if pd.isna(atr):
            continue

        # Calculate volume spike threshold
        vol_spike_threshold = vol_window.mean() + 1.5 * vol_window.std()
        volume_spike = vol > vol_spike_threshold

        if position == 0:
            # Look for new entries
            if volume_spike:
                if close > open_:
                    # Long entry
                    data.loc[i, 'signals'] = 1
                    data.loc[i, 'trade_type'] = "LONG"
                    position = 1
                    trailing_stop = close - (atr * trailing_stop_multiplier)
                    num_wrong = 0
                elif close < open_:
                    # Short entry
                    data.loc[i, 'signals'] = -1
                    data.loc[i, 'trade_type'] = "SHORT"
                    position = -1
                    trailing_stop = close + (atr * trailing_stop_multiplier)
                    num_wrong = 0

        elif position == 1:
            # Long position management
            trend_reversal = volume_spike and (close < open_)
            if close <= data.loc[i - 1, 'close']:
                num_wrong += 1
            else:
                num_wrong = 0

            if trend_reversal:
                # Reverse long to short
                data.loc[i, 'signals'] = -2
                data.loc[i, 'trade_type'] = "REVERSE_LONG_TO_SHORT"
                position = -1
                trailing_stop = close + (atr * trailing_stop_multiplier)
                num_wrong = 0
            elif num_wrong >= num_wrong_limit:
                # Close long position after consecutive bad closes
                data.loc[i, 'signals'] = -1
                data.loc[i, 'trade_type'] = "CLOSE"
                position = 0
                num_wrong = 0
            elif close < trailing_stop:
                # Trailing stop hit, close position
                data.loc[i, 'signals'] = -1
                data.loc[i, 'trade_type'] = "CLOSE"
                position = 0
                num_wrong = 0
            else:
                # Update trailing stop (only move up)
                trailing_stop = max(trailing_stop, close - atr * trailing_stop_multiplier)

        elif position == -1:
            # Short position management
            trend_reversal = volume_spike and (close > open_)
            if close >= data.loc[i - 1, 'close']:
                num_wrong += 1
            else:
                num_wrong = 0

            if trend_reversal:
                # Reverse short to long
                data.loc[i, 'signals'] = 2
                data.loc[i, 'trade_type'] = "REVERSE_SHORT_TO_LONG"
                position = 1
                trailing_stop = close - (atr * trailing_stop_multiplier)
                num_wrong = 0
            elif num_wrong >= num_wrong_limit:
                # Close short position after consecutive bad closes
                data.loc[i, 'signals'] = 1
                data.loc[i, 'trade_type'] = "CLOSE"
                position = 0
                num_wrong = 0
            elif close > trailing_stop:
                # Trailing stop hit, close position
                data.loc[i, 'signals'] = 1
                data.loc[i, 'trade_type'] = "CLOSE"
                position = 0
                num_wrong = 0
            else:
                # Update trailing stop (only move down)
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