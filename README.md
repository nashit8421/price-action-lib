# Price Action Library

A comprehensive Python library for pure price action analysis, specifically optimized for the Indian stock market. Generate **95+ columns** of price action analysis with a single function call!

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Key Features

- **30+ Candlestick Patterns** - From basic doji to complex triple formations
- **15+ Chart Patterns** - Head & shoulders, triangles, wedges, flags, and more
- **Advanced Market Structure** - BOS, ChoCh, Fair Value Gaps, Order Blocks
- **Support & Resistance** - Multiple detection methods with confluence analysis
- **Volume Analysis** - Volume Spread Analysis (VSA) and volume patterns
- **Price Action Setups** - Pin bars, inside bars, fakey patterns, springs
- **Gap Analysis** - All gap types with classification and tracking
- **Session Analysis** - Indian market hours optimization (9:15 AM - 3:30 PM IST)
- **Multi-Timeframe** - Analyze across different time horizons
- **Machine Learning Ready** - Structured output perfect for ML models

## 🎯 Perfect For

- **Systematic Trading** - Algorithm development and backtesting
- **Market Research** - Comprehensive price action studies  
- **Machine Learning** - Feature engineering for ML models
- **Professional Trading** - Real-time pattern recognition
- **Education** - Learning price action concepts

## ⚡ Quick Start

### Installation

```bash
# Install dependencies
pip install pandas numpy scipy

# Install the library
pip install .
```

### Basic Usage

```python
from price_action_lib import PriceActionAnalyzer
import pandas as pd

# Initialize analyzer
analyzer = PriceActionAnalyzer()

# Load your OHLCV data (1-minute timeframe recommended)
# df should have columns: open, high, low, close, volume with DateTime index

# Get comprehensive analysis - 95+ columns!
result = analyzer.fetch_all(df)

print(f"Generated {result.shape[1]} columns of analysis!")
print(f"Analyzed {result.shape[0]} time periods")

# Individual analysis methods also available
patterns = analyzer.detect_candlestick_patterns(df)
structure = analyzer.analyze_market_structure(df)
levels = analyzer.find_support_resistance(df)
```

### Sample Output

The `fetch_all()` method returns a DataFrame with 95+ columns including:

- **Original OHLCV** (optional)
- **44+ Candlestick patterns** (`pattern_doji`, `pattern_hammer`, etc.)
- **14+ Chart patterns** (`chart_head_and_shoulders`, `chart_triangle`, etc.)
- **Market structure** (`structure_trend`, `structure_bos`, etc.)
- **Fair Value Gaps** (`fvg_bullish`, `fvg_bearish`)
- **Order Blocks** (`order_block_bullish`, `order_block_bearish`)
- **Price Action Setups** (`setup_pin_bar`, `setup_inside_bar`, etc.)
- **Support/Resistance** (`near_support`, `near_resistance`)
- **Volume Analysis** (`volume_spike`, `volume_climax`, etc.)
- **Gap Analysis** (`gap_breakaway`, `gap_exhaustion`, etc.)
- **Metadata** (ATR, volatility, trend classification, price zones)

## 📊 Example Analysis

```python
# Find high-probability trading setups
strong_signals = result[
    (result['near_support'] == True) &      # At key support level
    (result['setup_pin_bar'] == True) &     # Pin bar setup
    (result['volume_spike'] == True) &      # Volume confirmation
    (result['pattern_hammer'] != '')        # Hammer pattern
]

print(f"Found {len(strong_signals)} high-probability setups!")

# Analyze market structure
current_trend = result['structure_trend'].iloc[-1]
trend_strength = result['structure_trend_strength'].iloc[-1]
print(f"Current trend: {current_trend} (strength: {trend_strength:.2f})")
```

## 🇮🇳 Indian Market Optimization

- **Market Hours**: 9:15 AM - 3:30 PM IST
- **Session Analysis**: Pre-open, opening, regular, closing sessions
- **Holiday Handling**: Automatic weekend and holiday filtering
- **NSE/BSE Compatible**: Optimized for Indian stock exchanges

## 📈 Performance

- **Fast Processing**: 400+ bars/second on typical hardware
- **Memory Efficient**: Only 308KB package size
- **Vectorized Operations**: Optimized pandas/numpy operations
- **Scalable**: Handles datasets from 100 to 10,000+ bars

## 📚 Comprehensive Documentation

For detailed documentation, see **[DOCUMENTATION.md](DOCUMENTATION.md)** which includes:

- **Complete API Reference** - All methods with parameters and examples
- **Pattern Recognition Guide** - Details on all 30+ candlestick patterns
- **Market Structure Analysis** - BOS, ChoCh, FVGs, Order Blocks explained
- **Advanced Features** - Multi-timeframe, volume analysis, gap analysis
- **Best Practices** - Data preparation, performance optimization
- **Troubleshooting** - Common issues and solutions
- **Real-world Examples** - Complete trading workflows

## 🔧 Requirements

- **Python**: 3.7 or higher
- **pandas**: >= 1.3.0
- **numpy**: >= 1.21.0  
- **scipy**: >= 1.7.0

## 📋 Data Format

Your DataFrame should have:

```python
                     open    high     low   close  volume
2024-01-15 09:15:00  1000.0  1002.5   999.0  1001.5  25000
2024-01-15 09:16:00  1001.5  1003.0  1000.5  1002.0  18000
# ... with DateTime index and proper OHLC relationships
```

## 🚦 Quick Test

Verify your installation:

```python
from price_action_lib import PriceActionAnalyzer
analyzer = PriceActionAnalyzer()
print("✅ Price Action Library installed successfully!")
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎉 Ready to Get Started?

1. **Install** the library following the instructions above
2. **Read** the comprehensive [DOCUMENTATION.md](DOCUMENTATION.md)
3. **Load** your OHLCV data into a pandas DataFrame
4. **Run** `analyzer.fetch_all(df)` and get 95+ columns of analysis!

**Happy Trading!** 📈💰