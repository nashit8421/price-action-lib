"""Session-based analysis for Indian market"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import time
from ..core.base import BaseAnalyzer


class SessionAnalysis(BaseAnalyzer):
    """Analyze price action during different market sessions"""
    
    def __init__(self):
        """Initialize SessionAnalysis"""
        super().__init__()
    
    def analyze_opening_session(self, df: pd.DataFrame, minutes: int = 30) -> pd.DataFrame:
        """
        Analyze opening session patterns
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        minutes : int
            Minutes after open to analyze
            
        Returns:
        --------
        pd.DataFrame
            Opening session analysis
        """
        df = self.normalize_dataframe(df)
        
        opening_analysis = []
        
        for date, day_data in df.groupby(df.index.date):
            market_open_time = pd.Timestamp.combine(date, self.MARKET_OPEN)
            session_end_time = market_open_time + pd.Timedelta(minutes=minutes)
            
            opening_bars = day_data.between_time(self.MARKET_OPEN, session_end_time.time())
            full_day_bars = day_data.between_time(self.MARKET_OPEN, self.MARKET_CLOSE)
            
            if not opening_bars.empty and not full_day_bars.empty:
                analysis = {
                    'date': date,
                    'opening_drive_direction': self._get_opening_drive(opening_bars),
                    'opening_range_high': opening_bars['high'].max(),
                    'opening_range_low': opening_bars['low'].min(),
                    'opening_volume': opening_bars['volume'].sum(),
                    'day_volume': full_day_bars['volume'].sum(),
                    'opening_volume_pct': (opening_bars['volume'].sum() / full_day_bars['volume'].sum()) * 100,
                    'gap_from_prev_close': self._calculate_opening_gap(df, date, opening_bars),
                    'first_bar_range': opening_bars.iloc[0]['high'] - opening_bars.iloc[0]['low'],
                    'or_breakout': self._check_or_breakout(opening_bars, full_day_bars),
                    'reversal_pattern': self._detect_opening_reversal(opening_bars)
                }
                opening_analysis.append(analysis)
        
        return pd.DataFrame(opening_analysis).set_index('date') if opening_analysis else pd.DataFrame()
    
    def analyze_closing_session(self, df: pd.DataFrame, minutes: int = 30) -> pd.DataFrame:
        """
        Analyze closing session patterns
        """
        df = self.normalize_dataframe(df)
        
        closing_analysis = []
        
        for date, day_data in df.groupby(df.index.date):
            market_close_time = pd.Timestamp.combine(date, self.MARKET_CLOSE)
            session_start_time = market_close_time - pd.Timedelta(minutes=minutes)
            
            closing_bars = day_data.between_time(session_start_time.time(), self.MARKET_CLOSE)
            full_day_bars = day_data.between_time(self.MARKET_OPEN, self.MARKET_CLOSE)
            
            if not closing_bars.empty and not full_day_bars.empty:
                analysis = {
                    'date': date,
                    'closing_drive_direction': self._get_closing_drive(closing_bars),
                    'closing_volume': closing_bars['volume'].sum(),
                    'closing_volume_pct': (closing_bars['volume'].sum() / full_day_bars['volume'].sum()) * 100,
                    'close_vs_high': (full_day_bars['close'].iloc[-1] - full_day_bars['high'].max()) / full_day_bars['high'].max() * 100,
                    'close_vs_low': (full_day_bars['close'].iloc[-1] - full_day_bars['low'].min()) / full_day_bars['low'].min() * 100,
                    'late_day_momentum': self._calculate_late_momentum(closing_bars)
                }
                closing_analysis.append(analysis)
        
        return pd.DataFrame(closing_analysis).set_index('date') if closing_analysis else pd.DataFrame()
    
    def analyze_session_characteristics(self, df: pd.DataFrame) -> Dict:
        """
        Analyze overall session characteristics
        """
        df = self.normalize_dataframe(df)
        
        session_stats = {
            'opening_30min': self._analyze_time_period(df, time(9, 15), time(9, 45)),
            'mid_morning': self._analyze_time_period(df, time(9, 45), time(11, 30)),
            'lunch_time': self._analyze_time_period(df, time(11, 30), time(13, 30)),
            'afternoon': self._analyze_time_period(df, time(13, 30), time(15, 00)),
            'closing_30min': self._analyze_time_period(df, time(15, 0), time(15, 30))
        }
        
        return session_stats
    
    def _get_opening_drive(self, opening_bars: pd.DataFrame) -> str:
        """
        Determine opening drive direction
        """
        if opening_bars.empty:
            return 'none'
        
        first_close = opening_bars['close'].iloc[0]
        last_close = opening_bars['close'].iloc[-1]
        
        change_pct = (last_close - first_close) / first_close * 100
        
        if change_pct > 0.5:
            return 'bullish'
        elif change_pct < -0.5:
            return 'bearish'
        else:
            return 'neutral'
    
    def _get_closing_drive(self, closing_bars: pd.DataFrame) -> str:
        """
        Determine closing drive direction
        """
        if closing_bars.empty:
            return 'none'
        
        first_close = closing_bars['close'].iloc[0]
        last_close = closing_bars['close'].iloc[-1]
        
        change_pct = (last_close - first_close) / first_close * 100
        
        if change_pct > 0.3:
            return 'bullish'
        elif change_pct < -0.3:
            return 'bearish'
        else:
            return 'neutral'
    
    def _calculate_opening_gap(self, df: pd.DataFrame, date, opening_bars: pd.DataFrame) -> float:
        """
        Calculate gap from previous day's close
        """
        if opening_bars.empty:
            return 0.0
        
        # Get previous trading day
        prev_date = pd.Timestamp(date) - pd.Timedelta(days=1)
        while prev_date.weekday() > 4 or prev_date not in df.index.date:
            prev_date -= pd.Timedelta(days=1)
            if (pd.Timestamp(date) - prev_date).days > 7:  # Safety check
                return 0.0
        
        try:
            prev_close = df[df.index.date == prev_date.date()]['close'].iloc[-1]
            current_open = opening_bars['open'].iloc[0]
            return (current_open - prev_close) / prev_close * 100
        except (IndexError, KeyError):
            return 0.0
    
    def _check_or_breakout(self, opening_bars: pd.DataFrame, full_day_bars: pd.DataFrame) -> str:
        """
        Check if opening range was broken during the day
        """
        if opening_bars.empty or full_day_bars.empty:
            return 'none'
        
        or_high = opening_bars['high'].max()
        or_low = opening_bars['low'].min()
        
        # Check post-OR price action
        post_or_bars = full_day_bars[full_day_bars.index > opening_bars.index[-1]]
        
        if post_or_bars.empty:
            return 'none'
        
        broke_high = (post_or_bars['high'] > or_high).any()
        broke_low = (post_or_bars['low'] < or_low).any()
        
        if broke_high and not broke_low:
            return 'upside_breakout'
        elif broke_low and not broke_high:
            return 'downside_breakout'
        elif broke_high and broke_low:
            return 'both_sides'
        else:
            return 'held'
    
    def _detect_opening_reversal(self, opening_bars: pd.DataFrame) -> bool:
        """
        Detect opening reversal patterns
        """
        if len(opening_bars) < 3:
            return False
        
        # Check if opened in one direction but closed opposite
        first_bar = opening_bars.iloc[0]
        last_bar = opening_bars.iloc[-1]
        
        # Strong opening that reversed
        initial_direction = 'up' if first_bar['close'] > first_bar['open'] else 'down'
        final_direction = 'up' if last_bar['close'] > first_bar['open'] else 'down'
        
        return initial_direction != final_direction
    
    def _calculate_late_momentum(self, closing_bars: pd.DataFrame) -> str:
        """
        Calculate momentum in closing session
        """
        if len(closing_bars) < 3:
            return 'insufficient_data'
        
        # Compare first half vs second half of closing session
        mid_point = len(closing_bars) // 2
        first_half = closing_bars.iloc[:mid_point]
        second_half = closing_bars.iloc[mid_point:]
        
        first_half_change = (first_half['close'].iloc[-1] - first_half['close'].iloc[0]) / first_half['close'].iloc[0]
        second_half_change = (second_half['close'].iloc[-1] - second_half['close'].iloc[0]) / second_half['close'].iloc[0]
        
        if second_half_change > first_half_change + 0.002:
            return 'accelerating'
        elif second_half_change < first_half_change - 0.002:
            return 'decelerating'
        else:
            return 'consistent'
    
    def _analyze_time_period(self, df: pd.DataFrame, start_time: time, end_time: time) -> Dict:
        """
        Analyze characteristics of a specific time period
        """
        period_data = df.between_time(start_time, end_time)
        
        if period_data.empty:
            return {'no_data': True}
        
        # Calculate metrics for this period
        total_volume = period_data['volume'].sum()
        avg_volume_per_bar = period_data['volume'].mean()
        price_range = period_data['high'].max() - period_data['low'].min()
        net_change = period_data['close'].iloc[-1] - period_data['open'].iloc[0]
        
        # Volatility
        returns = period_data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(len(returns)) if len(returns) > 1 else 0
        
        return {
            'total_bars': len(period_data),
            'avg_volume_per_bar': avg_volume_per_bar,
            'total_volume': total_volume,
            'price_range': price_range,
            'net_change': net_change,
            'net_change_pct': (net_change / period_data['open'].iloc[0]) * 100 if period_data['open'].iloc[0] != 0 else 0,
            'volatility': volatility,
            'avg_bar_range': (period_data['high'] - period_data['low']).mean()
        }