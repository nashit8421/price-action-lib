# Price Action Library - Comprehensive Documentation

A comprehensive Python library for price action analysis optimized for the Indian stock market. This library provides pure price action analysis without traditional technical indicators, focusing on candlestick patterns, chart formations, market structure, and volume-price relationships.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Pattern Recognition](#pattern-recognition)
- [Market Structure Analysis](#market-structure-analysis)
- [Advanced Features](#advanced-features)
- [Data Requirements](#data-requirements)
- [Performance Guidelines](#performance-guidelines)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The Price Action Library is designed specifically for traders and analysts working with Indian stock markets. It provides:

- **30+ Candlestick Patterns** - From basic doji to complex triple candlestick formations
- **15+ Chart Patterns** - Head & shoulders, triangles, wedges, and more
- **Market Structure Analysis** - BOS, ChoCh, Fair Value Gaps, Order Blocks
- **Support & Resistance Detection** - Multiple methods including swing points, fractals, and volume
- **Volume Analysis** - Volume Spread Analysis (VSA) and volume patterns
- **Session Analysis** - Indian market hours optimization (9:15 AM - 3:30 PM IST)
- **Multi-timeframe Analysis** - Analyze across different time horizons
- **Comprehensive Output** - Single function returns 95+ columns of analysis

### Key Features

- **Pure Price Action Focus** - No lagging indicators, only price and volume
- **Indian Market Optimized** - Built for NSE/BSE trading hours and patterns
- **High Performance** - Vectorized operations for fast analysis
- **Machine Learning Ready** - Structured output perfect for ML models
- **Comprehensive Coverage** - Every major price action concept included

## Installation

### Prerequisites

- Python 3.7 or higher
- pandas >= 1.3.0
- numpy >= 1.21.0
- scipy >= 1.7.0

### Install from Source

```bash
# Clone or download the library
cd price_action_lib

# Install dependencies
pip install -r requirements.txt

# Install the library
pip install .

# Or install in development mode
pip install -e .
```

### Verify Installation

```python
from price_action_lib import PriceActionAnalyzer
print("Price Action Library installed successfully!")
```

## Quick Start

### Basic Usage

```python
import pandas as pd
from price_action_lib import PriceActionAnalyzer

# Initialize the analyzer
analyzer = PriceActionAnalyzer()

# Load your OHLCV data (1-minute timeframe recommended)
# df should have columns: open, high, low, close, volume
# with DateTime index

# Get comprehensive analysis (95+ columns!)
result = analyzer.fetch_all(df)

print(f"Analysis complete! Generated {result.shape[1]} columns")
print(f"Analyzing {result.shape[0]} time periods")
```

### Sample Data Format

Your DataFrame should look like this:

```python
                     open    high     low   close  volume
2024-01-15 09:15:00  1000.0  1002.5   999.0  1001.5  25000
2024-01-15 09:16:00  1001.5  1003.0  1000.5  1002.0  18000
2024-01-15 09:17:00  1002.0  1002.8  1001.2  1001.8  22000
...
```

**Important:** 
- Index must be DateTime
- Columns must be named: `open`, `high`, `low`, `close`, `volume`
- Data should be in 1-minute intervals for best results
- Ensure proper OHLC relationships (High >= max(Open,Close), etc.)

## API Reference

### PriceActionAnalyzer Class

The main class that provides access to all price action analysis functionality.

```python
analyzer = PriceActionAnalyzer(**kwargs)
```

**Parameters:**
- `**kwargs`: Optional configuration parameters for individual analyzers

### Core Methods

#### fetch_all()

The primary method that returns comprehensive price action analysis.

```python
result = analyzer.fetch_all(
    df, 
    include_ohlcv=True, 
    include_metadata=True
)
```

**Parameters:**
- `df` (pd.DataFrame): OHLCV data with DateTime index
- `include_ohlcv` (bool): Include original OHLCV columns (default: True)
- `include_metadata` (bool): Include metadata columns like ATR, volatility (default: True)

**Returns:**
- `pd.DataFrame`: Comprehensive analysis with 95+ columns

**Output Columns Include:**
- Original OHLCV data (if enabled)
- 44+ Candlestick pattern columns (`pattern_doji`, `pattern_hammer`, etc.)
- 14+ Chart pattern columns (`chart_head_and_shoulders`, `chart_triangle`, etc.)
- Market structure columns (`structure_trend`, `structure_bos`, etc.)
- Fair Value Gap indicators (`fvg_bullish`, `fvg_bearish`)
- Order Block indicators (`order_block_bullish`, `order_block_bearish`)
- Price Action Setup indicators (`setup_pin_bar`, `setup_inside_bar`, etc.)
- Support/Resistance proximity (`near_support`, `near_resistance`)
- Volume analysis (`volume_spike`, `volume_climax`, etc.)
- Gap analysis (`gap_breakaway`, `gap_exhaustion`, etc.)
- Session indicators (`session`)
- Metadata (ATR, volatility regime, trend classification, price zones)

#### Individual Analysis Methods

For focused analysis, use these individual methods:

```python
# Candlestick patterns
patterns = analyzer.detect_candlestick_patterns(df, pattern_type='all')

# Chart patterns  
chart_patterns = analyzer.detect_chart_patterns(df)

# Market structure
structure = analyzer.analyze_market_structure(df)

# Support and resistance
levels = analyzer.find_support_resistance(df, method='swings')

# Volume analysis
volume = analyzer.analyze_volume(df)

# Gap analysis
gaps = analyzer.detect_gaps(df)

# Price action setups
setups = analyzer.find_price_action_setups(df, setup_type='all')

# Breakout analysis
breakouts = analyzer.identify_breakouts(df, lookback=20)

# Timeframe resampling
df_5min = analyzer.resample_timeframe(df, '5min')

# Multi-timeframe analysis
mtf_analysis = analyzer.get_multi_timeframe_analysis(
    df, 
    timeframes=['5min', '15min', '1H']
)
```

## Pattern Recognition

### Candlestick Patterns

The library detects 30+ candlestick patterns across four categories:

#### Single Candlestick Patterns

**Basic Patterns:**
- **Doji** - `pattern_doji`
  - Standard Doji: Small body with equal shadows
  - Dragonfly Doji: Long lower shadow, minimal upper shadow
  - Gravestone Doji: Long upper shadow, minimal lower shadow
  - Long-legged Doji: Long shadows on both sides

- **Hammer & Hanging Man** - `pattern_hammer`, `pattern_hanging_man`
  - Small body at top/bottom of candle with long lower shadow
  - Context determines bullish (hammer) vs bearish (hanging man) bias

- **Inverted Hammer & Shooting Star** - `pattern_inverted_hammer`, `pattern_shooting_star`
  - Small body with long upper shadow
  - Context determines interpretation

- **Marubozu** - `pattern_marubozu_bullish`, `pattern_marubozu_bearish`
  - Long body with minimal shadows
  - Strong directional movement indication

#### Double Candlestick Patterns

- **Engulfing Patterns** - `pattern_engulfing_bullish`, `pattern_engulfing_bearish`
  - Second candle completely engulfs the first
  - Strong reversal signal

- **Piercing Pattern** - `pattern_piercing`
  - Bullish reversal: Gap down followed by strong bounce
  
- **Dark Cloud Cover** - `pattern_dark_cloud`
  - Bearish reversal: Gap up followed by strong decline

- **Harami Patterns** - `pattern_harami_bullish`, `pattern_harami_bearish`, `pattern_harami_cross`
  - Small candle inside previous large candle
  - Indicates potential trend change

#### Triple Candlestick Patterns

- **Morning/Evening Stars** - `pattern_morning_star`, `pattern_evening_star`
  - Three-candle reversal patterns
  - Gap between first and second candle

- **Three White Soldiers/Black Crows** - `pattern_three_white_soldiers`, `pattern_three_black_crows`
  - Three consecutive candles in same direction
  - Strong trend continuation/reversal

#### Advanced Multi-Candle Patterns

- **Rising/Falling Three Methods** - `pattern_rising_three_methods`, `pattern_falling_three_methods`
  - Continuation patterns with brief consolidation

### Chart Patterns

The library identifies major chart formations:

#### Reversal Patterns

- **Head and Shoulders** - `chart_head_and_shoulders`
  - Classic reversal pattern with three peaks
  - Middle peak (head) higher than shoulders

- **Inverse Head and Shoulders** - `chart_inverse_head_and_shoulders`
  - Bullish reversal pattern
  - Three valleys with middle valley lowest

- **Double Top/Bottom** - `chart_double_top`, `chart_double_bottom`
  - Two peaks/valleys at similar levels
  - Strong reversal implications

- **Rounding Top/Bottom** - `chart_rounding_top`, `chart_rounding_bottom`
  - Gradual reversal patterns
  - Bowl or dome shaped price action

#### Continuation Patterns

- **Triangles** - `chart_triangle`
  - Ascending, Descending, Symmetrical triangles
  - Converging trendlines indicating consolidation

- **Wedges** - `chart_wedge`
  - Rising wedge (bearish) or falling wedge (bullish)
  - Converging trendlines with directional bias

- **Flags and Pennants** - `chart_flag`, `chart_pennant`
  - Brief consolidation after strong moves
  - Continuation patterns

## Market Structure Analysis

### Trend Analysis

The library provides comprehensive trend analysis:

```python
structure = analyzer.analyze_market_structure(df)
```

**Key Columns:**
- `structure_trend`: Current trend direction (uptrend/downtrend/neutral)
- `structure_trend_strength`: Trend strength (0-1 scale)
- `structure_bos`: Break of Structure points
- `structure_choch`: Change of Character points

### Advanced Concepts

#### Fair Value Gaps (FVGs)

Detected gaps in price action indicating imbalances:

- `fvg_bullish`: Bullish fair value gaps
- `fvg_bearish`: Bearish fair value gaps

```python
# FVGs are automatically included in fetch_all()
result = analyzer.fetch_all(df)
bullish_fvgs = result[result['fvg_bullish'] == True]
```

#### Order Blocks

Key decision points where large orders were likely placed:

- `order_block_bullish`: Bullish order blocks
- `order_block_bearish`: Bearish order blocks

#### Price Action Setups

Professional trading setups:

- `setup_pin_bar`: Pin bar/rejection candle setups
- `setup_inside_bar`: Inside bar setups
- `setup_outside_bar`: Outside bar/engulfing setups
- `setup_fakey`: False breakout patterns
- `setup_spring`: Spring patterns (false breakdown)
- `setup_upthrust`: Upthrust patterns (false breakout)

## Advanced Features

### Support and Resistance Detection

Multiple methods for identifying key levels:

```python
# Swing-based levels
levels = analyzer.find_support_resistance(df, method='swings')

# Volume-based levels  
levels = analyzer.find_support_resistance(df, method='volume')

# Fractal-based levels
levels = analyzer.find_support_resistance(df, method='fractals')
```

**Proximity Indicators in fetch_all():**
- `near_support`: Price near support level
- `near_resistance`: Price near resistance level
- `at_major_level`: Price at major S/R level

### Volume Analysis

Comprehensive volume-price analysis:

```python
volume_analysis = analyzer.analyze_volume(df)
```

**Volume Indicators:**
- `volume_spike`: Unusual volume spikes
- `volume_climax`: Volume climax patterns
- `volume_class`: Volume classification (high/medium/low)
- Accumulation/Distribution patterns

### Gap Analysis

All major gap types are detected:

```python
gaps = analyzer.detect_gaps(df)
```

**Gap Types:**
- `gap_common`: Common gaps (usually filled)
- `gap_breakaway`: Breakaway gaps (trend starts)
- `gap_runaway`: Runaway/measuring gaps (trend continuation)
- `gap_exhaustion`: Exhaustion gaps (trend ending)

### Session Analysis

Optimized for Indian market trading sessions:

**Sessions:**
- Pre-market: Before 9:15 AM
- Opening: 9:15 AM - 10:00 AM
- Regular: 10:00 AM - 3:00 PM
- Closing: 3:00 PM - 3:30 PM

The `session` column in fetch_all() indicates the current session.

### Multi-Timeframe Analysis

Analyze confluence across multiple timeframes:

```python
mtf_result = analyzer.get_multi_timeframe_analysis(
    df, 
    timeframes=['5min', '15min', '30min', '1H']
)
```

**Supported Timeframes:**
- Minutes: 3min, 5min, 10min, 15min, 30min
- Hours: 1H, 2H, 4H
- Days: Daily, Weekly, Monthly

## Data Requirements

### Input Data Format

```python
# Required columns
df = pd.DataFrame({
    'open': [...],      # Opening prices
    'high': [...],      # High prices  
    'low': [...],       # Low prices
    'close': [...],     # Closing prices
    'volume': [...]     # Volume data
}, index=pd.DatetimeIndex([...]))  # DateTime index required
```

### Data Quality Requirements

1. **OHLC Relationships:** Ensure High >= max(Open, Close) and Low <= min(Open, Close)
2. **No Missing Data:** Fill gaps or handle missing periods appropriately
3. **Consistent Timeframe:** Regular intervals (1-minute recommended)
4. **Valid Volume:** Non-negative volume values
5. **Indian Market Hours:** Data should focus on 9:15 AM - 3:30 PM IST

### Minimum Data Requirements

- **Candlestick Patterns:** Minimum 3 bars for most patterns
- **Chart Patterns:** Minimum 20-50 bars depending on pattern
- **Market Structure:** Minimum 50 bars for meaningful analysis
- **Support/Resistance:** Minimum 100 bars recommended
- **Volume Analysis:** Minimum 20 bars for relative calculations

## Performance Guidelines

### Optimal Dataset Sizes

- **Small (< 500 bars):** Near-instantaneous processing
- **Medium (500-2000 bars):** 1-5 seconds processing time
- **Large (2000-10000 bars):** 5-30 seconds processing time
- **Very Large (> 10000 bars):** Consider batch processing

### Performance Tips

1. **Use 1-minute base data** and resample to higher timeframes as needed
2. **Limit analysis scope** to recent periods for real-time applications
3. **Cache results** when analyzing the same data repeatedly
4. **Use individual methods** instead of fetch_all() for focused analysis

### Memory Optimization

```python
# For large datasets, consider excluding OHLCV data
result = analyzer.fetch_all(df, include_ohlcv=False)

# Or exclude metadata for smaller output
result = analyzer.fetch_all(df, include_metadata=False)
```

## Examples

### Complete Analysis Workflow

```python
import pandas as pd
from price_action_lib import PriceActionAnalyzer
import numpy as np

# Initialize analyzer
analyzer = PriceActionAnalyzer()

# Load your data (example with sample data)
df = pd.read_csv('your_stock_data.csv', index_col=0, parse_dates=True)

# Ensure proper column names
df.columns = ['open', 'high', 'low', 'close', 'volume']

# Get comprehensive analysis
result = analyzer.fetch_all(df)

print(f"Analysis Results:")
print(f"- Total columns: {result.shape[1]}")
print(f"- Time periods: {result.shape[0]}")
print(f"- Date range: {result.index[0]} to {result.index[-1]}")

# Analyze specific patterns
bullish_patterns = result[
    (result['pattern_hammer'] != '') |
    (result['pattern_morning_star'] != '') |
    (result['setup_pin_bar'] == True)
]

print(f"Found {len(bullish_patterns)} bullish signals")
```

### Finding Trading Opportunities

```python
# Find confluence setups
confluence_signals = result[
    (result['near_support'] == True) &
    (result['setup_pin_bar'] == True) &
    (result['volume_spike'] == True)
]

print("High-probability trading setups:")
for timestamp, signal in confluence_signals.iterrows():
    print(f"- {timestamp}: Pin bar at support with volume spike")
```

### Market Structure Analysis

```python
# Analyze current market structure
structure = analyzer.analyze_market_structure(df)

current_trend = structure['trend'].iloc[-1]
trend_strength = structure['trend_strength'].iloc[-1]

print(f"Current Market Structure:")
print(f"- Trend: {current_trend}")
print(f"- Strength: {trend_strength:.2f}")

# Find structure breaks
bos_points = structure[structure['bos'] != '']
print(f"- Structure breaks found: {len(bos_points)}")
```

### Volume Analysis

```python
# Analyze volume patterns
volume_analysis = analyzer.analyze_volume(df)

# Find volume climaxes
climax_points = volume_analysis[volume_analysis['volume_climax'] != '']
print(f"Volume climax points: {len(climax_points)}")

# Identify accumulation/distribution
acc_dist = volume_analysis['accumulation'].sum()
print(f"Net accumulation/distribution: {acc_dist:.0f}")
```

### Multi-Timeframe Confluence

```python
# Analyze multiple timeframes
timeframes = ['5min', '15min', '30min', '1H']
mtf_analysis = analyzer.get_multi_timeframe_analysis(df, timeframes)

# Check for confluence across timeframes
for tf, analysis in mtf_analysis.items():
    if 'trend' in analysis:
        print(f"{tf} trend: {analysis['trend'].iloc[-1]}")
```

## Best Practices

### Data Preparation

1. **Clean Your Data**
   ```python
   # Remove invalid OHLC relationships
   valid_mask = (df['high'] >= df['low']) & \
                (df['high'] >= df['open']) & \
                (df['high'] >= df['close']) & \
                (df['low'] <= df['open']) & \
                (df['low'] <= df['close'])
   df = df[valid_mask]
   ```

2. **Handle Missing Data**
   ```python
   # Forward fill small gaps
   df = df.fillna(method='ffill', limit=5)
   
   # Or drop rows with missing data
   df = df.dropna()
   ```

3. **Ensure Proper Timeframe**
   ```python
   # Resample to consistent 1-minute intervals if needed
   df = df.resample('1min').agg({
       'open': 'first',
       'high': 'max', 
       'low': 'min',
       'close': 'last',
       'volume': 'sum'
   }).dropna()
   ```

### Analysis Workflow

1. **Start with Comprehensive Analysis**
   ```python
   # Get complete picture first
   result = analyzer.fetch_all(df)
   
   # Then focus on specific areas
   patterns = analyzer.detect_candlestick_patterns(df)
   ```

2. **Use Multiple Confirmations**
   ```python
   # Look for confluence
   strong_signals = result[
       (result['near_support']) &           # At key level
       (result['setup_pin_bar']) &          # Clear setup
       (result['volume_spike']) &           # Volume confirmation
       (result['pattern_hammer'] != '')     # Pattern confirmation
   ]
   ```

3. **Consider Market Context**
   ```python
   # Factor in overall market structure
   if structure['trend'].iloc[-1] == 'uptrend':
       # Look for bullish setups
       bullish_setups = result[result['setup_pin_bar'] & result['near_support']]
   ```

### Performance Optimization

1. **Process Recent Data First**
   ```python
   # Analyze last 1000 bars for real-time analysis
   recent_data = df.tail(1000)
   result = analyzer.fetch_all(recent_data)
   ```

2. **Use Targeted Analysis**
   ```python
   # For specific pattern hunting
   patterns = analyzer.detect_candlestick_patterns(df, pattern_type='double')
   ```

3. **Cache Results**
   ```python
   # Store results for reuse
   import pickle
   
   result = analyzer.fetch_all(df)
   with open('analysis_cache.pkl', 'wb') as f:
       pickle.dump(result, f)
   ```

## Troubleshooting

### Common Issues

#### 1. "Invalid OHLC relationships detected"

**Cause:** High < Low or improper OHLC data
**Solution:**
```python
# Check data integrity
print("Data validation:")
print(f"High < Low: {(df['high'] < df['low']).sum()} rows")
print(f"High < Open: {(df['high'] < df['open']).sum()} rows")
print(f"High < Close: {(df['high'] < df['close']).sum()} rows")

# Clean the data
valid_mask = (df['high'] >= df['low']) & \
             (df['high'] >= df['open']) & \
             (df['high'] >= df['close']) & \
             (df['low'] <= df['open']) & \
             (df['low'] <= df['close'])
df_clean = df[valid_mask]
```

#### 2. "Missing required columns"

**Cause:** DataFrame doesn't have required OHLCV columns
**Solution:**
```python
# Ensure proper column names
required_columns = ['open', 'high', 'low', 'close', 'volume']
print(f"Available columns: {list(df.columns)}")
print(f"Required columns: {required_columns}")

# Rename columns if needed
df.columns = ['open', 'high', 'low', 'close', 'volume']
```

#### 3. "Input DataFrame is empty"

**Cause:** Empty or filtered DataFrame
**Solution:**
```python
# Check DataFrame size
print(f"DataFrame shape: {df.shape}")
print(f"Date range: {df.index.min()} to {df.index.max()}")

# Ensure sufficient data
if len(df) < 20:
    print("Warning: Insufficient data for meaningful analysis")
```

#### 4. Memory or Performance Issues

**Cause:** Processing very large datasets
**Solution:**
```python
# Process in chunks for large datasets
chunk_size = 5000
results = []

for i in range(0, len(df), chunk_size):
    chunk = df.iloc[i:i+chunk_size]
    result = analyzer.fetch_all(chunk, include_ohlcv=False)
    results.append(result)

final_result = pd.concat(results)
```

### Getting Help

For additional support:

1. Check that your data meets the requirements in [Data Requirements](#data-requirements)
2. Review the examples in the [Examples](#examples) section
3. Ensure you're using supported Python and package versions
4. Test with smaller datasets first to isolate issues

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run analysis with debug information
result = analyzer.fetch_all(df)
```

---

## Conclusion

The Price Action Library provides a comprehensive toolkit for analyzing price action in Indian stock markets. With 95+ output columns covering every major price action concept, it's designed to be both powerful for advanced users and accessible for beginners.

Key strengths:
- **Comprehensive Coverage:** Every major price action pattern and concept
- **Indian Market Focus:** Optimized for NSE/BSE trading sessions
- **High Performance:** Fast, vectorized operations
- **Machine Learning Ready:** Structured output perfect for ML models
- **Production Ready:** Robust error handling and validation

Whether you're developing trading algorithms, conducting market research, or building analytical tools, this library provides the foundation for sophisticated price action analysis.

**Happy Trading!** 📈