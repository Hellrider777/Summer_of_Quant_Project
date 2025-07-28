# Strategy Summary (with RSI)

This is a volume-spike + momentum + reversal strategy using:

ATR for dynamic trailing stop-loss,

RSI to validate momentum direction,

Volume spikes to trigger entries/reversals,

Adaptive exits based on adverse moves and trend reversals.

# Entry Logic

Conditions to open a new position (when no current position):

Volume Spike:

Current volume > average + 1.5 × std of last volume_lookback bars

Candle Confirmation:

Green candle → consider long

Red candle → consider short

RSI Filter:

Long: RSI ≥ rsi_entry_threshold_long

Short: RSI ≤ rsi_entry_threshold_short

If all 3 align, a trade is initiated:

Long: signal = 1

Short: signal = -1

Trailing stop initialized using ATR.

# Exit Logic

Active positions are monitored and exited if:

# Long Position

📉 Reversal Signal: Volume spike + red candle + RSI ≤ short threshold → reverse to short

❌ 3 consecutive closes ≤ previous → exit

🛑 Trailing stop hit → exit

🔁 Trailing stop updated upward only

# Short Position

📈 Reversal Signal: Volume spike + green candle + RSI ≥ long threshold → reverse to long

❌ 3 consecutive closes ≥ previous → exit

🛑 Trailing stop hit → exit

🔁 Trailing stop updated downward only

# Key Parameters

Parameter Role Default
atr_length ATR period for stop distance 14
trailing_stop_multiplier Multiplies ATR to get trailing stop distance 2.0
volume_lookback Rolling window for volume mean and std 11
num_wrong_limit Max adverse candles before forced exit 3
rsi_entry_threshold_long RSI minimum for long entry 50
rsi_entry_threshold_short RSI maximum for short entry 50

# Strategy Type

This strategy is a momentum-driven reversal system with:

Volume as the trigger

Candle direction as confirmation

RSI as a momentum gatekeeper

ATR for dynamic trailing stop-loss
