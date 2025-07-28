# Strategy Summary

This is a volume-spike momentum reversal strategy with ATR-based trailing stops and adaptive exit logic. It aims to:

Enter trades on volume spikes aligned with momentum (candle color),

Exit trades based on trend weakness (losing streaks or trailing stops),

Reverse positions when a volume spike suggests a trend flip.

# Entry Logic

The strategy waits for:

Volume spike:

Current volume > mean + 1.5 × std of past volume_lookback bars.

Candle direction:

Green candle (close > open) → open a long.

Red candle (close < open) → open a short.

Once both conditions are met:

A position is entered, and

A trailing stop is set using:
close - atr × multiplier (for long)
close + atr × multiplier (for short)

# Exit Logic

An open position will close in any of the following conditions:

# For Long:

3 consecutive bad closes (each close ≤ previous close)

Trailing stop hit (i.e., close < trailing_stop)

Reversal trigger: A red candle + volume spike → reverse to short

# For Short:

3 consecutive bad closes (each close ≥ previous close)

Trailing stop hit (i.e., close > trailing_stop)

Reversal trigger: A green candle + volume spike → reverse to long

Trailing stop is updated dynamically:

Long: max(trailing_stop, close - atr × multiplier)

Short: min(trailing_stop, close + atr × multiplier)

# Tunable Parameters

You can adjust the following to refine behavior:

Parameter Description
atr_length ATR period (default: 14)
trailing_stop_multiplier Multiplier for stop distance (default: 2.0)
volume_lookback Rolling volume window (default: 11)
num_wrong_limit Max losing streak before exit (default: 3)

# Strategy Type

This is a trend-reversal momentum-following strategy with:

Volume as a trigger filter

Candle direction as momentum confirmation

ATR-based stop to protect downside and lock in profit

Reversal logic to capture trend flips
