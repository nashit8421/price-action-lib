"""Time frame management and resampling utilities"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from .base import BaseAnalyzer


class TimeFrameManager(BaseAnalyzer):
    """Manages time frame conversions and resampling for OHLCV data"""
    
    # Supported timeframes
    TIMEFRAMES = {
        '1min': '1T',
        '3min': '3T',
        '5min': '5T',
        '10min': '10T',
        '15min': '15T',
        '30min': '30T',
        '1H': '1H',
        '2H': '2H',
        '4H': '4H',
        '1D': '1D',
        '1W': '1W',
        '1M': '1M'
    }
    
    def __init__(self):
        """Initialize TimeFrameManager"""
        super().__init__()
        self.aggregation_rules = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
    
    def resample_ohlcv(self, df: pd.DataFrame, timeframe: str, 
                      session_aware: bool = True) -> pd.DataFrame:
        """
        Resample OHLCV data to specified timeframe
        
        Parameters:
        -----------
        df : pd.DataFrame
            Input DataFrame with OHLCV data (1-minute assumed)
        timeframe : str
            Target timeframe (e.g., '5min', '15min', '1H', '1D')
        session_aware : bool
            If True, respects market session boundaries
            
        Returns:
        --------
        pd.DataFrame
            Resampled OHLCV data
        """
        # Validate and normalize dataframe
        df = self.normalize_dataframe(df)
        
        # Validate timeframe
        if timeframe not in self.TIMEFRAMES:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(self.TIMEFRAMES.keys())}")
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")
        
        # Filter market hours if session aware
        if session_aware and timeframe not in ['1D', '1W', '1M']:
            df = self.filter_market_hours(df)
        
        # Get pandas resample rule
        rule = self.TIMEFRAMES[timeframe]
        
        # Perform resampling
        resampled = df.resample(rule).agg(self.aggregation_rules)
        
        # Remove any rows with NaN values (incomplete periods)
        resampled = resampled.dropna()
        
        # For daily and above, align to market session
        if timeframe == '1D' and session_aware:
            resampled = self._align_daily_to_session(df)
        
        return resampled
    
    def _align_daily_to_session(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Align daily bars to Indian market session (9:15 AM - 3:30 PM)
        
        Parameters:
        -----------
        df : pd.DataFrame
            Input DataFrame with intraday data
            
        Returns:
        --------
        pd.DataFrame
            Daily bars aligned to market sessions
        """
        # Group by date
        df = df.copy()
        df['date'] = df.index.date
        
        daily_data = []
        for date, group in df.groupby('date'):
            # Filter to market hours only
            market_data = group.between_time('09:15', '15:30')
            
            if not market_data.empty:
                daily_bar = {
                    'open': market_data['open'].iloc[0],
                    'high': market_data['high'].max(),
                    'low': market_data['low'].min(),
                    'close': market_data['close'].iloc[-1],
                    'volume': market_data['volume'].sum()
                }
                daily_data.append((pd.Timestamp(date), daily_bar))
        
        if not daily_data:
            return pd.DataFrame()
        
        # Create daily dataframe
        dates, bars = zip(*daily_data)
        daily_df = pd.DataFrame(bars, index=dates)
        
        return daily_df
    
    def create_multiple_timeframes(self, df: pd.DataFrame, 
                                  timeframes: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Create multiple timeframe dataframes from base data
        
        Parameters:
        -----------
        df : pd.DataFrame
            Input DataFrame with OHLCV data (1-minute)
        timeframes : List[str]
            List of timeframes to create (default: common timeframes)
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            Dictionary with timeframe as key and resampled data as value
        """
        if timeframes is None:
            timeframes = ['3min', '5min', '15min', '30min', '1H', '1D']
        
        result = {'1min': df.copy()}
        
        for tf in timeframes:
            if tf != '1min':
                try:
                    result[tf] = self.resample_ohlcv(df, tf)
                except Exception as e:
                    print(f"Error resampling to {tf}: {e}")
                    continue
        
        return result
    
    def get_session_bars(self, df: pd.DataFrame, session_type: str = 'regular') -> pd.DataFrame:
        """
        Extract specific session bars from the data
        
        Parameters:
        -----------
        df : pd.DataFrame
            Input DataFrame with OHLCV data
        session_type : str
            Type of session ('regular', 'opening', 'closing', 'premarket')
            
        Returns:
        --------
        pd.DataFrame
            Session-specific bars
        """
        df = self.normalize_dataframe(df)
        
        if session_type == 'regular':
            return self.filter_market_hours(df)
        elif session_type == 'opening':
            # First 30 minutes
            return df.between_time('09:15', '09:45')
        elif session_type == 'closing':
            # Last 30 minutes
            return df.between_time('15:00', '15:30')
        elif session_type == 'premarket':
            return df.between_time('09:00', '09:15')
        else:
            raise ValueError(f"Unknown session type: {session_type}")
    
    def calculate_vwap(self, df: pd.DataFrame, anchor: str = 'session') -> pd.Series:
        """
        Calculate Volume Weighted Average Price
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        anchor : str
            VWAP anchor point ('session', 'daily', 'weekly')
            
        Returns:
        --------
        pd.Series
            VWAP values
        """
        df = self.normalize_dataframe(df)
        
        # Calculate typical price
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        if anchor == 'session':
            # Reset at market open each day
            df['date'] = df.index.date
            df['session_start'] = df.index.time == self.MARKET_OPEN
            df['session_group'] = df.groupby('date')['session_start'].cumsum()
            
            # Calculate VWAP for each session
            df['pv'] = typical_price * df['volume']
            df['cumulative_pv'] = df.groupby('session_group')['pv'].cumsum()
            df['cumulative_volume'] = df.groupby('session_group')['volume'].cumsum()
            vwap = df['cumulative_pv'] / df['cumulative_volume']
            
        elif anchor == 'daily':
            # Reset daily
            df['date'] = df.index.date
            df['pv'] = typical_price * df['volume']
            df['cumulative_pv'] = df.groupby('date')['pv'].cumsum()
            df['cumulative_volume'] = df.groupby('date')['volume'].cumsum()
            vwap = df['cumulative_pv'] / df['cumulative_volume']
            
        elif anchor == 'weekly':
            # Reset weekly
            df['week'] = df.index.isocalendar().week
            df['year'] = df.index.year
            df['pv'] = typical_price * df['volume']
            df['cumulative_pv'] = df.groupby(['year', 'week'])['pv'].cumsum()
            df['cumulative_volume'] = df.groupby(['year', 'week'])['volume'].cumsum()
            vwap = df['cumulative_pv'] / df['cumulative_volume']
            
        else:
            raise ValueError(f"Unknown anchor type: {anchor}")
        
        return vwap
    
    def calculate_anchored_vwap(self, df: pd.DataFrame, 
                               anchor_datetime: pd.Timestamp) -> pd.Series:
        """
        Calculate VWAP anchored to a specific datetime
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        anchor_datetime : pd.Timestamp
            Datetime to anchor VWAP calculation
            
        Returns:
        --------
        pd.Series
            Anchored VWAP values
        """
        df = self.normalize_dataframe(df)
        
        # Filter data from anchor point onwards
        df_anchored = df[df.index >= anchor_datetime].copy()
        
        if df_anchored.empty:
            return pd.Series(dtype=float)
        
        # Calculate typical price
        typical_price = (df_anchored['high'] + df_anchored['low'] + df_anchored['close']) / 3
        
        # Calculate cumulative values
        df_anchored['pv'] = typical_price * df_anchored['volume']
        df_anchored['cumulative_pv'] = df_anchored['pv'].cumsum()
        df_anchored['cumulative_volume'] = df_anchored['volume'].cumsum()
        
        # Calculate VWAP
        vwap = df_anchored['cumulative_pv'] / df_anchored['cumulative_volume']
        
        # Create full series with NaN before anchor
        full_vwap = pd.Series(index=df.index, dtype=float)
        full_vwap[df.index >= anchor_datetime] = vwap.values
        
        return full_vwap
    
    def get_opening_range(self, df: pd.DataFrame, 
                         minutes: int = 15) -> Dict[str, pd.DataFrame]:
        """
        Calculate opening range for each day
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        minutes : int
            Minutes after open to calculate OR (default: 15)
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            Dictionary with date as key and OR data as value
        """
        df = self.normalize_dataframe(df)
        
        opening_ranges = {}
        
        # Group by date
        for date, day_data in df.groupby(df.index.date):
            # Get opening range period
            market_open = pd.Timestamp.combine(date, self.MARKET_OPEN)
            or_end = market_open + pd.Timedelta(minutes=minutes)
            
            # Filter for OR period
            or_data = day_data.between_time(
                self.MARKET_OPEN,
                or_end.time()
            )
            
            if not or_data.empty:
                opening_ranges[str(date)] = {
                    'high': or_data['high'].max(),
                    'low': or_data['low'].min(),
                    'open': or_data['open'].iloc[0] if len(or_data) > 0 else None,
                    'close': or_data['close'].iloc[-1] if len(or_data) > 0 else None,
                    'volume': or_data['volume'].sum(),
                    'or_broken_up': False,
                    'or_broken_down': False,
                    'or_break_time_up': None,
                    'or_break_time_down': None
                }
                
                # Check for OR breakouts in remaining session
                remaining_data = day_data[day_data.index > or_data.index[-1]]
                
                if not remaining_data.empty:
                    or_high = opening_ranges[str(date)]['high']
                    or_low = opening_ranges[str(date)]['low']
                    
                    # Check for upside break
                    upside_break = remaining_data[remaining_data['high'] > or_high]
                    if not upside_break.empty:
                        opening_ranges[str(date)]['or_broken_up'] = True
                        opening_ranges[str(date)]['or_break_time_up'] = upside_break.index[0]
                    
                    # Check for downside break
                    downside_break = remaining_data[remaining_data['low'] < or_low]
                    if not downside_break.empty:
                        opening_ranges[str(date)]['or_broken_down'] = True
                        opening_ranges[str(date)]['or_break_time_down'] = downside_break.index[0]
        
        return opening_ranges
    
    def calculate_session_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate session statistics for each day
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            Session statistics
        """
        df = self.normalize_dataframe(df)
        
        session_stats = []
        
        for date, day_data in df.groupby(df.index.date):
            market_data = day_data.between_time('09:15', '15:30')
            
            if not market_data.empty:
                stats = {
                    'date': date,
                    'open': market_data['open'].iloc[0],
                    'high': market_data['high'].max(),
                    'low': market_data['low'].min(),
                    'close': market_data['close'].iloc[-1],
                    'volume': market_data['volume'].sum(),
                    'range': market_data['high'].max() - market_data['low'].min(),
                    'body': abs(market_data['close'].iloc[-1] - market_data['open'].iloc[0]),
                    'upper_shadow': market_data['high'].max() - max(market_data['open'].iloc[0], 
                                                                   market_data['close'].iloc[-1]),
                    'lower_shadow': min(market_data['open'].iloc[0], 
                                      market_data['close'].iloc[-1]) - market_data['low'].min(),
                    'is_bullish': market_data['close'].iloc[-1] > market_data['open'].iloc[0],
                    'num_bars': len(market_data),
                    'avg_bar_range': (market_data['high'] - market_data['low']).mean(),
                    'max_bar_range': (market_data['high'] - market_data['low']).max(),
                    'min_bar_range': (market_data['high'] - market_data['low']).min()
                }
                session_stats.append(stats)
        
        return pd.DataFrame(session_stats).set_index('date') if session_stats else pd.DataFrame()