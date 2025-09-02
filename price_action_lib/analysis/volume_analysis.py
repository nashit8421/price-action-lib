"""Volume-Price analysis module"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from ..core.base import BaseAnalyzer


class VolumeAnalysis(BaseAnalyzer):
    """Analyze volume patterns and their relationship with price action"""
    
    def __init__(self, volume_ma_period: int = 20,
                 relative_volume_threshold: float = 1.5):
        """
        Initialize VolumeAnalysis
        
        Parameters:
        -----------
        volume_ma_period : int
            Period for volume moving average
        relative_volume_threshold : float
            Threshold for high relative volume
        """
        super().__init__()
        self.volume_ma_period = volume_ma_period
        self.relative_volume_threshold = relative_volume_threshold
    
    def analyze_volume_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Comprehensive volume pattern analysis
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with volume analysis results
        """
        df = self.normalize_dataframe(df)
        
        results = pd.DataFrame(index=df.index)
        
        # Basic volume metrics
        results['volume'] = df['volume']
        results['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period).mean()
        results['relative_volume'] = df['volume'] / results['volume_ma']
        
        # Volume classification
        results['volume_class'] = self._classify_volume(df)
        
        # Volume spikes and dry-ups
        results['volume_spike'] = self._detect_volume_spikes(df)
        results['volume_dryup'] = self._detect_volume_dryups(df)
        
        # Volume climax patterns
        results['volume_climax'] = self._detect_volume_climax(df)
        
        # Effort vs Result analysis
        results['effort_result'] = self._analyze_effort_vs_result(df)
        
        # Volume divergence
        results['volume_divergence'] = self._detect_volume_divergence(df)
        
        # Volume at key levels
        results['volume_at_support'] = self._volume_at_support_resistance(df, level_type='support')
        results['volume_at_resistance'] = self._volume_at_support_resistance(df, level_type='resistance')
        
        return results
    
    def _classify_volume(self, df: pd.DataFrame) -> pd.Series:
        """
        Classify volume as High/Average/Low
        """
        volume_ma = df['volume'].rolling(window=self.volume_ma_period).mean()
        volume_std = df['volume'].rolling(window=self.volume_ma_period).std()
        
        high_threshold = volume_ma + volume_std
        low_threshold = volume_ma - volume_std * 0.5
        
        classification = pd.Series(index=df.index, dtype='object')
        classification[:] = 'average'
        
        classification[df['volume'] > high_threshold] = 'high'
        classification[df['volume'] < low_threshold] = 'low'
        
        return classification
    
    def _detect_volume_spikes(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect volume spikes
        """
        volume_ma = df['volume'].rolling(window=self.volume_ma_period).mean()
        relative_volume = df['volume'] / volume_ma
        
        return relative_volume > self.relative_volume_threshold
    
    def _detect_volume_dryups(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect volume dry-ups (unusually low volume)
        """
        volume_ma = df['volume'].rolling(window=self.volume_ma_period).mean()
        volume_std = df['volume'].rolling(window=self.volume_ma_period).std()
        
        low_threshold = volume_ma - volume_std
        
        return df['volume'] < low_threshold
    
    def _detect_volume_climax(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect volume climax patterns (high volume with reversal)
        """
        climax = pd.Series(index=df.index, dtype='object')
        climax[:] = ''
        
        # Calculate volume and price metrics
        volume_ma = df['volume'].rolling(window=10).mean()
        is_high_volume = df['volume'] > volume_ma * 2
        
        price_change = df['close'].pct_change()
        body_size = abs(df['close'] - df['open'])
        avg_body = body_size.rolling(window=10).mean()
        
        for i in range(10, len(df)):
            if is_high_volume.iloc[i]:
                # Bullish climax - high volume, but price fails to advance
                if (price_change.iloc[i] > 0.01 and  # Initially moves up
                    body_size.iloc[i] > avg_body.iloc[i] * 1.5 and  # Large body
                    i < len(df) - 1 and  # Not last bar
                    df['close'].iloc[i+1] < df['close'].iloc[i]):  # Next bar closes lower
                    climax.iloc[i] = 'bullish_climax'
                
                # Bearish climax - high volume, but price fails to decline further
                elif (price_change.iloc[i] < -0.01 and  # Initially moves down
                      body_size.iloc[i] > avg_body.iloc[i] * 1.5 and  # Large body
                      i < len(df) - 1 and  # Not last bar
                      df['close'].iloc[i+1] > df['close'].iloc[i]):  # Next bar closes higher
                    climax.iloc[i] = 'bearish_climax'
        
        return climax
    
    def _analyze_effort_vs_result(self, df: pd.DataFrame) -> pd.Series:
        """
        Analyze effort (volume) vs result (price movement)
        """
        effort_result = pd.Series(index=df.index, dtype='object')
        effort_result[:] = 'normal'
        
        # Calculate metrics
        price_range = df['high'] - df['low']
        body_size = abs(df['close'] - df['open'])
        volume_ma = df['volume'].rolling(window=10).mean()
        range_ma = price_range.rolling(window=10).mean()
        
        for i in range(10, len(df)):
            vol_ratio = df['volume'].iloc[i] / volume_ma.iloc[i] if volume_ma.iloc[i] > 0 else 1
            range_ratio = price_range.iloc[i] / range_ma.iloc[i] if range_ma.iloc[i] > 0 else 1
            
            # High effort, low result (bearish)
            if vol_ratio > 1.5 and range_ratio < 0.7:
                effort_result.iloc[i] = 'high_effort_low_result'
            
            # Low effort, high result (continuation likely)
            elif vol_ratio < 0.7 and range_ratio > 1.3:
                effort_result.iloc[i] = 'low_effort_high_result'
            
            # High effort, high result (strong move)
            elif vol_ratio > 1.5 and range_ratio > 1.3:
                effort_result.iloc[i] = 'high_effort_high_result'
        
        return effort_result
    
    def _detect_volume_divergence(self, df: pd.DataFrame, 
                                lookback: int = 20) -> pd.Series:
        """
        Detect volume divergence with price
        """
        divergence = pd.Series(index=df.index, dtype='object')
        divergence[:] = ''
        
        # Calculate indicators for divergence
        price_rsi = self._calculate_rsi(df['close'])
        volume_rsi = self._calculate_rsi(df['volume'])
        
        for i in range(lookback, len(df)):
            # Look for divergence patterns
            recent_price_rsi = price_rsi.iloc[i-lookback:i+1]
            recent_volume_rsi = volume_rsi.iloc[i-lookback:i+1]
            
            # Bullish divergence - price makes lower lows, volume makes higher lows
            price_trend = np.polyfit(range(len(recent_price_rsi)), recent_price_rsi, 1)[0]
            volume_trend = np.polyfit(range(len(recent_volume_rsi)), recent_volume_rsi, 1)[0]
            
            if price_trend < -0.1 and volume_trend > 0.1:
                divergence.iloc[i] = 'bullish_divergence'
            elif price_trend > 0.1 and volume_trend < -0.1:
                divergence.iloc[i] = 'bearish_divergence'
        
        return divergence
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate RSI for divergence analysis
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _volume_at_support_resistance(self, df: pd.DataFrame, 
                                    level_type: str = 'support') -> pd.Series:
        """
        Analyze volume at support/resistance levels
        """
        from ..structures.support_resistance import SupportResistance
        
        sr_analyzer = SupportResistance()
        levels = sr_analyzer.detect_support_resistance_zones(df)
        
        volume_at_levels = pd.Series(index=df.index, dtype=float)
        volume_at_levels[:] = 0.0
        
        if not levels.empty:
            relevant_levels = levels[levels['type'].isin([level_type, 'both'])]
            
            for _, level in relevant_levels.iterrows():
                level_price = level['level']
                threshold = level_price * 0.002  # 0.2% threshold
                
                # Find bars near this level
                near_level = (
                    (df['low'] <= level_price + threshold) & 
                    (df['high'] >= level_price - threshold)
                )
                
                volume_at_levels[near_level] = df['volume'][near_level]
        
        return volume_at_levels
    
    def calculate_volume_profile(self, df: pd.DataFrame, 
                               bins: int = 50) -> pd.DataFrame:
        """
        Calculate Volume Profile (Volume by Price)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        bins : int
            Number of price bins
            
        Returns:
        --------
        pd.DataFrame
            Volume profile data
        """
        df = self.normalize_dataframe(df)
        
        # Create price bins
        price_min = df['low'].min()
        price_max = df['high'].max()
        price_bins = np.linspace(price_min, price_max, bins + 1)
        
        # Calculate typical price for each bar
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # Assign each bar to price bins and sum volume
        volume_profile = []
        
        for i in range(len(price_bins) - 1):
            bin_low = price_bins[i]
            bin_high = price_bins[i + 1]
            bin_mid = (bin_low + bin_high) / 2
            
            # Find bars whose typical price falls in this bin
            in_bin = (typical_price >= bin_low) & (typical_price < bin_high)
            bin_volume = df.loc[in_bin, 'volume'].sum()
            
            volume_profile.append({
                'price_low': bin_low,
                'price_high': bin_high,
                'price_mid': bin_mid,
                'volume': bin_volume
            })
        
        vp_df = pd.DataFrame(volume_profile)
        
        # Calculate additional metrics
        total_volume = vp_df['volume'].sum()
        vp_df['volume_pct'] = vp_df['volume'] / total_volume * 100 if total_volume > 0 else 0
        
        # Find Point of Control (highest volume)
        poc_idx = vp_df['volume'].idxmax()
        vp_df['is_poc'] = False
        if not pd.isna(poc_idx):
            vp_df.loc[poc_idx, 'is_poc'] = True
        
        return vp_df
    
    def calculate_value_area(self, volume_profile: pd.DataFrame, 
                           value_area_pct: float = 70.0) -> Dict:
        """
        Calculate Value Area (area containing specified % of volume)
        
        Parameters:
        -----------
        volume_profile : pd.DataFrame
            Volume profile from calculate_volume_profile
        value_area_pct : float
            Percentage of volume for value area
            
        Returns:
        --------
        Dict
            Value area information
        """
        if volume_profile.empty:
            return {}
        
        # Sort by volume descending
        sorted_profile = volume_profile.sort_values('volume', ascending=False)
        
        # Find Point of Control
        poc = sorted_profile.iloc[0]
        
        # Calculate value area starting from POC
        target_volume = volume_profile['volume'].sum() * (value_area_pct / 100)
        current_volume = poc['volume']
        value_area_prices = [poc['price_mid']]
        
        # Expand value area up and down from POC
        remaining_profile = sorted_profile.iloc[1:]
        
        while current_volume < target_volume and not remaining_profile.empty:
            # Add highest volume remaining bin
            next_bin = remaining_profile.iloc[0]
            value_area_prices.append(next_bin['price_mid'])
            current_volume += next_bin['volume']
            remaining_profile = remaining_profile.iloc[1:]
        
        if value_area_prices:
            va_high = max(value_area_prices)
            va_low = min(value_area_prices)
            
            return {
                'poc_price': poc['price_mid'],
                'poc_volume': poc['volume'],
                'value_area_high': va_high,
                'value_area_low': va_low,
                'value_area_volume': current_volume,
                'value_area_pct': (current_volume / volume_profile['volume'].sum()) * 100
            }
        
        return {}
    
    def detect_volume_supported_moves(self, df: pd.DataFrame, 
                                    min_volume_ratio: float = 1.5) -> pd.DataFrame:
        """
        Detect price moves supported by volume
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        min_volume_ratio : float
            Minimum volume ratio for supported move
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with supported moves
        """
        df = self.normalize_dataframe(df)
        
        supported_moves = []
        
        # Calculate volume moving average
        volume_ma = df['volume'].rolling(window=20).mean()
        
        # Look for moves with volume support
        for i in range(20, len(df) - 1):
            current_volume = df['volume'].iloc[i]
            avg_volume = volume_ma.iloc[i]
            
            if current_volume > avg_volume * min_volume_ratio:
                # Check price movement
                price_change = (df['close'].iloc[i] - df['close'].iloc[i-1]) / df['close'].iloc[i-1]
                body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
                avg_body = abs(df['close'] - df['open']).rolling(window=10).mean().iloc[i]
                
                if body_size > avg_body * 1.2:  # Significant price movement
                    move_type = 'bullish' if price_change > 0 else 'bearish'
                    
                    # Check if move continues
                    next_day_direction = 'same' if ((df['close'].iloc[i+1] > df['close'].iloc[i]) == 
                                                   (move_type == 'bullish')) else 'opposite'
                    
                    supported_moves.append({
                        'timestamp': df.index[i],
                        'move_type': move_type,
                        'price_change_pct': price_change * 100,
                        'volume_ratio': current_volume / avg_volume,
                        'body_size': body_size,
                        'continuation': next_day_direction == 'same'
                    })
        
        return pd.DataFrame(supported_moves) if supported_moves else pd.DataFrame()
    
    def analyze_breakout_volume(self, df: pd.DataFrame, 
                               lookback: int = 20) -> pd.DataFrame:
        """
        Analyze volume on breakouts from consolidation
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        lookback : int
            Lookback period for consolidation detection
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with breakout volume analysis
        """
        df = self.normalize_dataframe(df)
        
        breakouts = []
        
        for i in range(lookback, len(df)):
            # Define consolidation range
            consolidation_window = df.iloc[i-lookback:i]
            range_high = consolidation_window['high'].max()
            range_low = consolidation_window['low'].min()
            range_size = range_high - range_low
            
            # Check for consolidation (price within range)
            avg_range = (consolidation_window['high'] - consolidation_window['low']).mean()
            if range_size < avg_range * 1.5:  # Tight range
                
                # Check for breakout
                current_close = df['close'].iloc[i]
                current_volume = df['volume'].iloc[i]
                avg_volume = consolidation_window['volume'].mean()
                
                if current_close > range_high * 1.001:  # Upside breakout
                    breakouts.append({
                        'timestamp': df.index[i],
                        'breakout_type': 'upside',
                        'range_high': range_high,
                        'range_low': range_low,
                        'breakout_price': current_close,
                        'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0,
                        'range_size_pct': (range_size / range_low) * 100,
                        'volume_confirmed': current_volume > avg_volume * 1.5
                    })
                
                elif current_close < range_low * 0.999:  # Downside breakout
                    breakouts.append({
                        'timestamp': df.index[i],
                        'breakout_type': 'downside',
                        'range_high': range_high,
                        'range_low': range_low,
                        'breakout_price': current_close,
                        'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0,
                        'range_size_pct': (range_size / range_low) * 100,
                        'volume_confirmed': current_volume > avg_volume * 1.5
                    })
        
        return pd.DataFrame(breakouts) if breakouts else pd.DataFrame()
    
    def calculate_accumulation_distribution(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Accumulation/Distribution Line
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pd.Series
            A/D Line values
        """
        df = self.normalize_dataframe(df)
        
        # Money Flow Multiplier
        mf_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        mf_multiplier = mf_multiplier.fillna(0)  # Handle division by zero
        
        # Money Flow Volume
        mf_volume = mf_multiplier * df['volume']
        
        # Accumulation/Distribution Line
        ad_line = mf_volume.cumsum()
        
        return ad_line
    
    def calculate_on_balance_volume(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pd.Series
            OBV values
        """
        df = self.normalize_dataframe(df)
        
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df['volume'].iloc[0]
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    def detect_volume_patterns_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate summary of key volume patterns
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        Dict
            Summary of volume patterns
        """
        analysis = self.analyze_volume_patterns(df)
        
        summary = {
            'total_bars': len(df),
            'high_volume_bars': (analysis['volume_class'] == 'high').sum(),
            'low_volume_bars': (analysis['volume_class'] == 'low').sum(),
            'volume_spikes': analysis['volume_spike'].sum(),
            'volume_dryups': analysis['volume_dryup'].sum(),
            'volume_climax_events': (analysis['volume_climax'] != '').sum(),
            'avg_relative_volume': analysis['relative_volume'].mean(),
            'max_relative_volume': analysis['relative_volume'].max(),
            'volume_supported_moves': self.detect_volume_supported_moves(df),
            'breakout_analysis': self.analyze_breakout_volume(df)
        }
        
        return summary