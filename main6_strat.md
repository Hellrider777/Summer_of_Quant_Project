# Core Idea

This is a trend-following and momentum-based strategy that enters trades on:

MACD crossovers (momentum signal)

EMA filter (trend confirmation)

Bullish/Bearish candles (price confirmation)

It uses ATR-based trailing stops and a consecutive adverse close exit rule for risk management.

# Entry Conditions

# Long Entry

Price is above EMA (trend is up)

MACD line crosses above MACD signal (bullish momentum)

Candle is bullish (close > open)

→ Action: Open long position

# Short Entry

Price is below EMA (trend is down)

MACD line crosses below MACD signal (bearish momentum)

Candle is bearish (close < open)

→ Action: Open short position

# Exit Conditions

# For Long Positions

Price falls below EMA

Or MACD makes bearish crossover

Or price closes below trailing stop

Or N (e.g., 2) consecutive closes are lower than the previous close

→ Action: Close long (signal = -1)

# For Short Positions

Price rises above EMA

Or MACD makes bullish crossover

Or price closes above trailing stop

Or N consecutive closes are higher than previous close

→ Action: Close short (signal = 1)

# Indicators Used

EMA (100) – trend direction filter

MACD (6, 19, 4) – fast crossover for momentum entry

ATR (14) – sets dynamic trailing stop distance

# Risk Management

Trailing Stop: Based on ATR × multiplier (e.g., 2.0)

Wrong Move Limit: Exit after N consecutive closes against position (e.g., 2)
