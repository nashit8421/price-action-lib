"""Base classes and utilities for price action analysis"""

import pandas as pd
import numpy as np
from typing import Union, Tuple, Optional, Dict, Any
from datetime import datetime, time


class BaseAnalyzer:
    """Base class for all analyzers with common functionality"""
    
    # Indian market timings
    MARKET_OPEN = time(9, 15)
    MARKET_CLOSE = time(15, 30)
    PRE_OPEN_START = time(9, 0)
    PRE_OPEN_END = time(9, 8)
    AUCTION_START = time(9, 8)
    AUCTION_END = time(9, 15)
    
    def __init__(self):
        """Initialize base analyzer"""
        self.required_columns = ['open', 'high', 'low', 'close', 'volume']
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """
        Validate that dataframe has required OHLCV columns
        
        Parameters:
        -----------
        df : pd.DataFrame
            Input dataframe to validate
            
        Returns:
        --------
        bool
            True if valid, raises exception otherwise
        """
        # Check if dataframe is empty
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        # Check for required columns (case insensitive)
        df_columns = [col.lower() for col in df.columns]
        missing_columns = []
        
        for col in self.required_columns:
            if col.lower() not in df_columns:
                missing_columns.append(col)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Standardize column names to lowercase
        df.columns = [col.lower() for col in df.columns]
        
        # Validate OHLC relationships
        if not self.validate_ohlc_relationships(df):
            raise ValueError("Invalid OHLC relationships detected")
        
        # Check for non-negative volume
        if (df['volume'] < 0).any():
            raise ValueError("Negative volume values detected")
        
        return True
    
    def validate_ohlc_relationships(self, df: pd.DataFrame) -> bool:
        """
        Validate OHLC relationships (High >= Low, High >= Open/Close, Low <= Open/Close)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLC data
            
        Returns:
        --------
        bool
            True if relationships are valid
        """
        # High should be >= Low
        if (df['high'] < df['low']).any():
            return False
        
        # High should be >= Open and Close
        if (df['high'] < df['open']).any() or (df['high'] < df['close']).any():
            return False
        
        # Low should be <= Open and Close
        if (df['low'] > df['open']).any() or (df['low'] > df['close']).any():
            return False
        
        return True
    
    def is_market_hours(self, timestamp: pd.Timestamp) -> bool:
        """
        Check if timestamp is within Indian market hours
        
        Parameters:
        -----------
        timestamp : pd.Timestamp
            Timestamp to check
            
        Returns:
        --------
        bool
            True if within market hours
        """
        market_time = timestamp.time()
        return self.MARKET_OPEN <= market_time <= self.MARKET_CLOSE
    
    def filter_market_hours(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter dataframe to only include market hours
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with datetime index
            
        Returns:
        --------
        pd.DataFrame
            Filtered dataframe
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        
        mask = df.index.map(self.is_market_hours)
        return df[mask]
    
    def calculate_body_height(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate candle body height (abs(close - open))
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLC data
            
        Returns:
        --------
        pd.Series
            Body heights
        """
        return abs(df['close'] - df['open'])
    
    def calculate_upper_shadow(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate upper shadow/wick length
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLC data
            
        Returns:
        --------
        pd.Series
            Upper shadow lengths
        """
        return df['high'] - df[['open', 'close']].max(axis=1)
    
    def calculate_lower_shadow(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate lower shadow/wick length
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLC data
            
        Returns:
        --------
        pd.Series
            Lower shadow lengths
        """
        return df[['open', 'close']].min(axis=1) - df['low']
    
    def calculate_candle_range(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate full candle range (high - low)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLC data
            
        Returns:
        --------
        pd.Series
            Candle ranges
        """
        return df['high'] - df['low']
    
    def is_bullish_candle(self, df: pd.DataFrame) -> pd.Series:
        """
        Check if candles are bullish (close > open)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLC data
            
        Returns:
        --------
        pd.Series
            Boolean series indicating bullish candles
        """
        return df['close'] > df['open']
    
    def is_bearish_candle(self, df: pd.DataFrame) -> pd.Series:
        """
        Check if candles are bearish (close < open)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLC data
            
        Returns:
        --------
        pd.Series
            Boolean series indicating bearish candles
        """
        return df['close'] < df['open']
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLC data
        period : int
            ATR period (default: 14)
            
        Returns:
        --------
        pd.Series
            ATR values
        """
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize dataframe columns to lowercase and validate
        
        Parameters:
        -----------
        df : pd.DataFrame
            Input dataframe
            
        Returns:
        --------
        pd.DataFrame
            Normalized dataframe
        """
        df = df.copy()
        df.columns = [col.lower() for col in df.columns]
        self.validate_dataframe(df)
        return df