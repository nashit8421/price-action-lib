"""Candlestick pattern recognition module"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from ..core.base import BaseAnalyzer


class CandlestickPatterns(BaseAnalyzer):
    """Detect and analyze candlestick patterns"""
    
    def __init__(self, min_body_ratio: float = 0.1, 
                 doji_threshold: float = 0.1,
                 equal_threshold: float = 0.002):
        """
        Initialize CandlestickPatterns
        
        Parameters:
        -----------
        min_body_ratio : float
            Minimum body to range ratio for pattern detection
        doji_threshold : float
            Maximum body to range ratio to consider as doji
        equal_threshold : float
            Threshold for considering prices as equal (as percentage)
        """
        super().__init__()
        self.min_body_ratio = min_body_ratio
        self.doji_threshold = doji_threshold
        self.equal_threshold = equal_threshold
    
    def detect_all_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect all candlestick patterns
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with pattern detection results
        """
        df = self.normalize_dataframe(df)
        results = df.copy()
        
        # Single candlestick patterns
        results['doji'] = self.detect_doji(df)
        results['hammer'] = self.detect_hammer(df)
        results['hanging_man'] = self.detect_hanging_man(df)
        results['inverted_hammer'] = self.detect_inverted_hammer(df)
        results['shooting_star'] = self.detect_shooting_star(df)
        results['marubozu'] = self.detect_marubozu(df)
        results['spinning_top'] = self.detect_spinning_top(df)
        results['high_wave'] = self.detect_high_wave(df)
        
        # Double candlestick patterns
        results['engulfing_bullish'] = self.detect_engulfing_bullish(df)
        results['engulfing_bearish'] = self.detect_engulfing_bearish(df)
        results['piercing'] = self.detect_piercing_pattern(df)
        results['dark_cloud'] = self.detect_dark_cloud_cover(df)
        results['tweezer_top'] = self.detect_tweezer_top(df)
        results['tweezer_bottom'] = self.detect_tweezer_bottom(df)
        results['harami_bullish'] = self.detect_harami_bullish(df)
        results['harami_bearish'] = self.detect_harami_bearish(df)
        results['harami_cross'] = self.detect_harami_cross(df)
        results['homing_pigeon'] = self.detect_homing_pigeon(df)
        results['matching_low'] = self.detect_matching_low(df)
        results['matching_high'] = self.detect_matching_high(df)
        results['on_neck'] = self.detect_on_neck(df)
        results['in_neck'] = self.detect_in_neck(df)
        
        # Triple candlestick patterns
        results['morning_star'] = self.detect_morning_star(df)
        results['evening_star'] = self.detect_evening_star(df)
        results['morning_doji_star'] = self.detect_morning_doji_star(df)
        results['evening_doji_star'] = self.detect_evening_doji_star(df)
        results['three_white_soldiers'] = self.detect_three_white_soldiers(df)
        results['three_black_crows'] = self.detect_three_black_crows(df)
        results['three_inside_up'] = self.detect_three_inside_up(df)
        results['three_inside_down'] = self.detect_three_inside_down(df)
        results['three_outside_up'] = self.detect_three_outside_up(df)
        results['three_outside_down'] = self.detect_three_outside_down(df)
        results['abandoned_baby_bullish'] = self.detect_abandoned_baby_bullish(df)
        results['abandoned_baby_bearish'] = self.detect_abandoned_baby_bearish(df)
        results['three_line_strike'] = self.detect_three_line_strike(df)
        results['advance_block'] = self.detect_advance_block(df)
        results['deliberation'] = self.detect_deliberation_pattern(df)
        
        # Multi-candlestick patterns
        results['rising_three_methods'] = self.detect_rising_three_methods(df)
        results['falling_three_methods'] = self.detect_falling_three_methods(df)
        results['mat_hold'] = self.detect_mat_hold(df)
        results['rising_window'] = self.detect_rising_window(df)
        results['falling_window'] = self.detect_falling_window(df)
        results['ladder_bottom'] = self.detect_ladder_bottom(df)
        results['ladder_top'] = self.detect_ladder_top(df)
        
        return results
    
    # Single Candlestick Patterns
    
    def detect_doji(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Doji patterns (including types)
        
        Returns dictionary with doji types:
        - standard: Regular doji
        - dragonfly: Dragonfly doji (long lower shadow)
        - gravestone: Gravestone doji (long upper shadow)
        - long_legged: Long-legged doji (long both shadows)
        """
        df = self.normalize_dataframe(df)
        
        body = self.calculate_body_height(df)
        candle_range = self.calculate_candle_range(df)
        upper_shadow = self.calculate_upper_shadow(df)
        lower_shadow = self.calculate_lower_shadow(df)
        
        # Basic doji condition
        body_ratio = body / candle_range
        is_doji = body_ratio < self.doji_threshold
        
        # Doji subtypes
        doji_types = pd.Series(index=df.index, dtype='object')
        doji_types[:] = ''
        
        # Standard doji
        standard_doji = is_doji & (upper_shadow > 0) & (lower_shadow > 0)
        
        # Dragonfly doji - long lower shadow, minimal upper shadow
        dragonfly = is_doji & (lower_shadow > body * 3) & (upper_shadow < body)
        
        # Gravestone doji - long upper shadow, minimal lower shadow
        gravestone = is_doji & (upper_shadow > body * 3) & (lower_shadow < body)
        
        # Long-legged doji - long shadows on both sides
        long_legged = is_doji & (upper_shadow > body * 2) & (lower_shadow > body * 2)
        
        # Assign types
        doji_types[long_legged] = 'long_legged'
        doji_types[dragonfly] = 'dragonfly'
        doji_types[gravestone] = 'gravestone'
        doji_types[standard_doji & (doji_types == '')] = 'standard'
        
        return doji_types
    
    def detect_hammer(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Hammer pattern (bullish reversal at bottom)
        """
        df = self.normalize_dataframe(df)
        
        body = self.calculate_body_height(df)
        candle_range = self.calculate_candle_range(df)
        upper_shadow = self.calculate_upper_shadow(df)
        lower_shadow = self.calculate_lower_shadow(df)
        
        # Hammer conditions
        # 1. Lower shadow at least 2x body
        # 2. Upper shadow minimal or none
        # 3. Body in upper third of range
        # 4. Appears in downtrend (check with 10-period low)
        
        is_hammer = (
            (lower_shadow >= body * 2) &
            (upper_shadow <= body * 0.3) &
            (body > 0) &
            (df['close'] > df['open']) &  # Bullish hammer
            (df['low'] == df['low'].rolling(10).min())  # At local low
        )
        
        return is_hammer
    
    def detect_hanging_man(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Hanging Man pattern (bearish reversal at top)
        """
        df = self.normalize_dataframe(df)
        
        body = self.calculate_body_height(df)
        upper_shadow = self.calculate_upper_shadow(df)
        lower_shadow = self.calculate_lower_shadow(df)
        
        # Hanging man conditions (similar to hammer but at top)
        is_hanging_man = (
            (lower_shadow >= body * 2) &
            (upper_shadow <= body * 0.3) &
            (body > 0) &
            (df['high'] == df['high'].rolling(10).max())  # At local high
        )
        
        return is_hanging_man
    
    def detect_inverted_hammer(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Inverted Hammer pattern
        """
        df = self.normalize_dataframe(df)
        
        body = self.calculate_body_height(df)
        upper_shadow = self.calculate_upper_shadow(df)
        lower_shadow = self.calculate_lower_shadow(df)
        
        # Inverted hammer conditions
        is_inverted_hammer = (
            (upper_shadow >= body * 2) &
            (lower_shadow <= body * 0.3) &
            (body > 0) &
            (df['low'] == df['low'].rolling(10).min())  # At local low
        )
        
        return is_inverted_hammer
    
    def detect_shooting_star(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Shooting Star pattern
        """
        df = self.normalize_dataframe(df)
        
        body = self.calculate_body_height(df)
        upper_shadow = self.calculate_upper_shadow(df)
        lower_shadow = self.calculate_lower_shadow(df)
        
        # Shooting star conditions
        is_shooting_star = (
            (upper_shadow >= body * 2) &
            (lower_shadow <= body * 0.3) &
            (body > 0) &
            (df['high'] == df['high'].rolling(10).max())  # At local high
        )
        
        return is_shooting_star
    
    def detect_marubozu(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Marubozu pattern (strong directional candle)
        Returns: 'bullish', 'bearish', or empty string
        """
        df = self.normalize_dataframe(df)
        
        body = self.calculate_body_height(df)
        candle_range = self.calculate_candle_range(df)
        upper_shadow = self.calculate_upper_shadow(df)
        lower_shadow = self.calculate_lower_shadow(df)
        
        marubozu_type = pd.Series(index=df.index, dtype='object')
        marubozu_type[:] = ''
        
        # Marubozu conditions - minimal or no shadows
        shadow_threshold = candle_range * 0.03
        
        # Bullish Marubozu
        bullish_marubozu = (
            (df['close'] > df['open']) &
            (upper_shadow <= shadow_threshold) &
            (lower_shadow <= shadow_threshold) &
            (body / candle_range > 0.95)
        )
        
        # Bearish Marubozu
        bearish_marubozu = (
            (df['close'] < df['open']) &
            (upper_shadow <= shadow_threshold) &
            (lower_shadow <= shadow_threshold) &
            (body / candle_range > 0.95)
        )
        
        marubozu_type[bullish_marubozu] = 'bullish'
        marubozu_type[bearish_marubozu] = 'bearish'
        
        return marubozu_type
    
    def detect_spinning_top(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Spinning Top pattern
        """
        df = self.normalize_dataframe(df)
        
        body = self.calculate_body_height(df)
        candle_range = self.calculate_candle_range(df)
        upper_shadow = self.calculate_upper_shadow(df)
        lower_shadow = self.calculate_lower_shadow(df)
        
        # Spinning top - small body with shadows on both sides
        is_spinning_top = (
            (body / candle_range < 0.3) &
            (body / candle_range > self.doji_threshold) &
            (upper_shadow > body) &
            (lower_shadow > body)
        )
        
        return is_spinning_top
    
    def detect_high_wave(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect High Wave Candle pattern
        """
        df = self.normalize_dataframe(df)
        
        body = self.calculate_body_height(df)
        candle_range = self.calculate_candle_range(df)
        upper_shadow = self.calculate_upper_shadow(df)
        lower_shadow = self.calculate_lower_shadow(df)
        
        # High wave - very long shadows relative to body
        is_high_wave = (
            (upper_shadow > body * 3) &
            (lower_shadow > body * 3) &
            (candle_range > candle_range.rolling(20).mean() * 1.5)
        )
        
        return is_high_wave
    
    # Double Candlestick Patterns
    
    def detect_engulfing_bullish(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Bullish Engulfing pattern
        """
        df = self.normalize_dataframe(df)
        
        # Current and previous candles
        curr_open = df['open']
        curr_close = df['close']
        prev_open = df['open'].shift(1)
        prev_close = df['close'].shift(1)
        
        # Bullish engulfing conditions
        is_engulfing_bullish = (
            # Previous candle is bearish
            (prev_close < prev_open) &
            # Current candle is bullish
            (curr_close > curr_open) &
            # Current body engulfs previous body
            (curr_open < prev_close) &
            (curr_close > prev_open) &
            # In downtrend
            (df['low'].shift(1) == df['low'].shift(1).rolling(10).min())
        )
        
        return is_engulfing_bullish
    
    def detect_engulfing_bearish(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Bearish Engulfing pattern
        """
        df = self.normalize_dataframe(df)
        
        # Current and previous candles
        curr_open = df['open']
        curr_close = df['close']
        prev_open = df['open'].shift(1)
        prev_close = df['close'].shift(1)
        
        # Bearish engulfing conditions
        is_engulfing_bearish = (
            # Previous candle is bullish
            (prev_close > prev_open) &
            # Current candle is bearish
            (curr_close < curr_open) &
            # Current body engulfs previous body
            (curr_open > prev_close) &
            (curr_close < prev_open) &
            # In uptrend
            (df['high'].shift(1) == df['high'].shift(1).rolling(10).max())
        )
        
        return is_engulfing_bearish
    
    def detect_piercing_pattern(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Piercing Pattern (bullish reversal)
        """
        df = self.normalize_dataframe(df)
        
        curr_open = df['open']
        curr_close = df['close']
        prev_open = df['open'].shift(1)
        prev_close = df['close'].shift(1)
        prev_body = abs(prev_close - prev_open)
        
        # Piercing pattern conditions
        is_piercing = (
            # Previous candle is bearish
            (prev_close < prev_open) &
            # Current candle is bullish
            (curr_close > curr_open) &
            # Opens below previous low
            (curr_open < df['low'].shift(1)) &
            # Closes above midpoint of previous body
            (curr_close > prev_close + prev_body * 0.5) &
            # But not above previous open (that would be engulfing)
            (curr_close < prev_open) &
            # In downtrend
            (df['low'].shift(1) == df['low'].shift(1).rolling(10).min())
        )
        
        return is_piercing
    
    def detect_dark_cloud_cover(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Dark Cloud Cover pattern (bearish reversal)
        """
        df = self.normalize_dataframe(df)
        
        curr_open = df['open']
        curr_close = df['close']
        prev_open = df['open'].shift(1)
        prev_close = df['close'].shift(1)
        prev_body = abs(prev_close - prev_open)
        
        # Dark cloud cover conditions
        is_dark_cloud = (
            # Previous candle is bullish
            (prev_close > prev_open) &
            # Current candle is bearish
            (curr_close < curr_open) &
            # Opens above previous high
            (curr_open > df['high'].shift(1)) &
            # Closes below midpoint of previous body
            (curr_close < prev_open + prev_body * 0.5) &
            # But not below previous open
            (curr_close > prev_open) &
            # In uptrend
            (df['high'].shift(1) == df['high'].shift(1).rolling(10).max())
        )
        
        return is_dark_cloud
    
    def detect_tweezer_top(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Tweezer Top pattern
        """
        df = self.normalize_dataframe(df)
        
        # Check for equal highs
        high_equal = abs(df['high'] - df['high'].shift(1)) / df['high'] < self.equal_threshold
        
        # Tweezer top conditions
        is_tweezer_top = (
            high_equal &
            # First candle bullish, second bearish (typical)
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'] < df['open']) &
            # At resistance/top
            (df['high'] == df['high'].rolling(20).max())
        )
        
        return is_tweezer_top
    
    def detect_tweezer_bottom(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Tweezer Bottom pattern
        """
        df = self.normalize_dataframe(df)
        
        # Check for equal lows
        low_equal = abs(df['low'] - df['low'].shift(1)) / df['low'] < self.equal_threshold
        
        # Tweezer bottom conditions
        is_tweezer_bottom = (
            low_equal &
            # First candle bearish, second bullish (typical)
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'] > df['open']) &
            # At support/bottom
            (df['low'] == df['low'].rolling(20).min())
        )
        
        return is_tweezer_bottom
    
    def detect_harami_bullish(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Bullish Harami pattern
        """
        df = self.normalize_dataframe(df)
        
        curr_open = df['open']
        curr_close = df['close']
        prev_open = df['open'].shift(1)
        prev_close = df['close'].shift(1)
        
        # Bullish harami conditions
        is_harami_bullish = (
            # Previous candle is bearish and large
            (prev_close < prev_open) &
            (abs(prev_close - prev_open) > abs(prev_close - prev_open).rolling(10).mean()) &
            # Current candle is small and inside previous
            (curr_open > prev_close) &
            (curr_open < prev_open) &
            (curr_close > prev_close) &
            (curr_close < prev_open) &
            # Current candle is bullish
            (curr_close > curr_open)
        )
        
        return is_harami_bullish
    
    def detect_harami_bearish(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Bearish Harami pattern
        """
        df = self.normalize_dataframe(df)
        
        curr_open = df['open']
        curr_close = df['close']
        prev_open = df['open'].shift(1)
        prev_close = df['close'].shift(1)
        
        # Bearish harami conditions
        is_harami_bearish = (
            # Previous candle is bullish and large
            (prev_close > prev_open) &
            (abs(prev_close - prev_open) > abs(prev_close - prev_open).rolling(10).mean()) &
            # Current candle is small and inside previous
            (curr_open < prev_close) &
            (curr_open > prev_open) &
            (curr_close < prev_close) &
            (curr_close > prev_open) &
            # Current candle is bearish
            (curr_close < curr_open)
        )
        
        return is_harami_bearish
    
    # Triple Candlestick Patterns
    
    def detect_morning_star(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Morning Star pattern (bullish reversal)
        """
        df = self.normalize_dataframe(df)
        
        # Candle positions
        first_close = df['close'].shift(2)
        first_open = df['open'].shift(2)
        second_close = df['close'].shift(1)
        second_open = df['open'].shift(1)
        second_body = abs(second_close - second_open)
        third_close = df['close']
        third_open = df['open']
        
        # Morning star conditions
        is_morning_star = (
            # First candle is bearish and long
            (first_close < first_open) &
            (abs(first_close - first_open) > abs(first_close - first_open).rolling(10).mean()) &
            # Second candle has small body (star)
            (second_body < abs(first_close - first_open) * 0.3) &
            # Gap down from first to second
            (second_open < first_close) &
            # Third candle is bullish
            (third_close > third_open) &
            # Third closes above midpoint of first
            (third_close > (first_open + first_close) / 2) &
            # In downtrend
            (df['low'].shift(2) == df['low'].shift(2).rolling(15).min())
        )
        
        return is_morning_star
    
    def detect_evening_star(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Evening Star pattern (bearish reversal)
        """
        df = self.normalize_dataframe(df)
        
        # Candle positions
        first_close = df['close'].shift(2)
        first_open = df['open'].shift(2)
        second_close = df['close'].shift(1)
        second_open = df['open'].shift(1)
        second_body = abs(second_close - second_open)
        third_close = df['close']
        third_open = df['open']
        
        # Evening star conditions
        is_evening_star = (
            # First candle is bullish and long
            (first_close > first_open) &
            (abs(first_close - first_open) > abs(first_close - first_open).rolling(10).mean()) &
            # Second candle has small body (star)
            (second_body < abs(first_close - first_open) * 0.3) &
            # Gap up from first to second
            (second_open > first_close) &
            # Third candle is bearish
            (third_close < third_open) &
            # Third closes below midpoint of first
            (third_close < (first_open + first_close) / 2) &
            # In uptrend
            (df['high'].shift(2) == df['high'].shift(2).rolling(15).max())
        )
        
        return is_evening_star
    
    def detect_three_white_soldiers(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Three White Soldiers pattern
        """
        df = self.normalize_dataframe(df)
        
        # Three consecutive bullish candles
        first_bullish = df['close'].shift(2) > df['open'].shift(2)
        second_bullish = df['close'].shift(1) > df['open'].shift(1)
        third_bullish = df['close'] > df['open']
        
        # Each closes higher than previous
        higher_closes = (
            (df['close'] > df['close'].shift(1)) &
            (df['close'].shift(1) > df['close'].shift(2))
        )
        
        # Each opens within previous body
        opens_in_body = (
            (df['open'] > df['open'].shift(1)) &
            (df['open'] < df['close'].shift(1)) &
            (df['open'].shift(1) > df['open'].shift(2)) &
            (df['open'].shift(1) < df['close'].shift(2))
        )
        
        # Pattern conditions
        is_three_white_soldiers = (
            first_bullish & second_bullish & third_bullish &
            higher_closes & opens_in_body &
            # In downtrend or bottom
            (df['low'].shift(3) == df['low'].shift(3).rolling(20).min())
        )
        
        return is_three_white_soldiers
    
    def detect_three_black_crows(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Three Black Crows pattern
        """
        df = self.normalize_dataframe(df)
        
        # Three consecutive bearish candles
        first_bearish = df['close'].shift(2) < df['open'].shift(2)
        second_bearish = df['close'].shift(1) < df['open'].shift(1)
        third_bearish = df['close'] < df['open']
        
        # Each closes lower than previous
        lower_closes = (
            (df['close'] < df['close'].shift(1)) &
            (df['close'].shift(1) < df['close'].shift(2))
        )
        
        # Each opens within previous body
        opens_in_body = (
            (df['open'] < df['open'].shift(1)) &
            (df['open'] > df['close'].shift(1)) &
            (df['open'].shift(1) < df['open'].shift(2)) &
            (df['open'].shift(1) > df['close'].shift(2))
        )
        
        # Pattern conditions
        is_three_black_crows = (
            first_bearish & second_bearish & third_bearish &
            lower_closes & opens_in_body &
            # In uptrend or top
            (df['high'].shift(3) == df['high'].shift(3).rolling(20).max())
        )
        
        return is_three_black_crows
    
    def detect_three_inside_up(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Three Inside Up pattern
        """
        df = self.normalize_dataframe(df)
        
        # First two form bullish harami
        harami_bullish = self.detect_harami_bullish(df).shift(1)
        
        # Third candle confirms with higher close
        third_confirms = (
            (df['close'] > df['open']) &
            (df['close'] > df['close'].shift(1)) &
            (df['close'] > df['open'].shift(2))
        )
        
        return harami_bullish & third_confirms
    
    def detect_three_inside_down(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Three Inside Down pattern
        """
        df = self.normalize_dataframe(df)
        
        # First two form bearish harami
        harami_bearish = self.detect_harami_bearish(df).shift(1)
        
        # Third candle confirms with lower close
        third_confirms = (
            (df['close'] < df['open']) &
            (df['close'] < df['close'].shift(1)) &
            (df['close'] < df['open'].shift(2))
        )
        
        return harami_bearish & third_confirms
    
    def detect_three_outside_up(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Three Outside Up pattern
        """
        df = self.normalize_dataframe(df)
        
        # First two form bullish engulfing
        engulfing_bullish = self.detect_engulfing_bullish(df).shift(1)
        
        # Third candle confirms with higher close
        third_confirms = (
            (df['close'] > df['open']) &
            (df['close'] > df['close'].shift(1))
        )
        
        return engulfing_bullish & third_confirms
    
    def detect_three_outside_down(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Three Outside Down pattern
        """
        df = self.normalize_dataframe(df)
        
        # First two form bearish engulfing
        engulfing_bearish = self.detect_engulfing_bearish(df).shift(1)
        
        # Third candle confirms with lower close
        third_confirms = (
            (df['close'] < df['open']) &
            (df['close'] < df['close'].shift(1))
        )
        
        return engulfing_bearish & third_confirms
    
    def detect_abandoned_baby_bullish(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Bullish Abandoned Baby pattern
        """
        df = self.normalize_dataframe(df)
        
        # First candle is bearish
        first_bearish = df['close'].shift(2) < df['open'].shift(2)
        
        # Second is doji with gap down
        second_doji = self.detect_doji(df).shift(1) != ''
        gap_down = df['high'].shift(1) < df['low'].shift(2)
        
        # Third is bullish with gap up
        third_bullish = df['close'] > df['open']
        gap_up = df['low'] > df['high'].shift(1)
        
        return first_bearish & second_doji & gap_down & third_bullish & gap_up
    
    def detect_abandoned_baby_bearish(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Bearish Abandoned Baby pattern
        """
        df = self.normalize_dataframe(df)
        
        # First candle is bullish
        first_bullish = df['close'].shift(2) > df['open'].shift(2)
        
        # Second is doji with gap up
        second_doji = self.detect_doji(df).shift(1) != ''
        gap_up = df['low'].shift(1) > df['high'].shift(2)
        
        # Third is bearish with gap down
        third_bearish = df['close'] < df['open']
        gap_down = df['high'] < df['low'].shift(1)
        
        return first_bullish & second_doji & gap_up & third_bearish & gap_down
    
    # Multi-candlestick patterns
    
    def detect_rising_three_methods(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Rising Three Methods pattern (bullish continuation)
        """
        df = self.normalize_dataframe(df)
        
        # First candle is long bullish
        first_bullish = (
            (df['close'].shift(4) > df['open'].shift(4)) &
            (abs(df['close'].shift(4) - df['open'].shift(4)) > 
             abs(df['close'].shift(4) - df['open'].shift(4)).rolling(10).mean() * 1.5)
        )
        
        # Next three are small bearish/neutral within first's range
        small_middle = True
        for i in range(3, 0, -1):
            small_middle = small_middle & (
                (abs(df['close'].shift(i) - df['open'].shift(i)) < 
                 abs(df['close'].shift(4) - df['open'].shift(4)) * 0.5) &
                (df['high'].shift(i) < df['high'].shift(4)) &
                (df['low'].shift(i) > df['low'].shift(4))
            )
        
        # Fifth candle is bullish and closes above first
        fifth_bullish = (
            (df['close'] > df['open']) &
            (df['close'] > df['close'].shift(4))
        )
        
        return first_bullish & small_middle & fifth_bullish
    
    def detect_falling_three_methods(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Falling Three Methods pattern (bearish continuation)
        """
        df = self.normalize_dataframe(df)
        
        # First candle is long bearish
        first_bearish = (
            (df['close'].shift(4) < df['open'].shift(4)) &
            (abs(df['close'].shift(4) - df['open'].shift(4)) > 
             abs(df['close'].shift(4) - df['open'].shift(4)).rolling(10).mean() * 1.5)
        )
        
        # Next three are small bullish/neutral within first's range
        small_middle = True
        for i in range(3, 0, -1):
            small_middle = small_middle & (
                (abs(df['close'].shift(i) - df['open'].shift(i)) < 
                 abs(df['close'].shift(4) - df['open'].shift(4)) * 0.5) &
                (df['high'].shift(i) < df['high'].shift(4)) &
                (df['low'].shift(i) > df['low'].shift(4))
            )
        
        # Fifth candle is bearish and closes below first
        fifth_bearish = (
            (df['close'] < df['open']) &
            (df['close'] < df['close'].shift(4))
        )
        
        return first_bearish & small_middle & fifth_bearish
    
    def get_pattern_signals(self, df: pd.DataFrame, 
                           pattern_type: str = 'all') -> pd.DataFrame:
        """
        Get pattern signals with metadata
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        pattern_type : str
            Type of patterns to detect ('single', 'double', 'triple', 'all')
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with pattern signals and metadata
        """
        patterns = self.detect_all_patterns(df)
        
        # Create signals dataframe
        signals = []
        
        # Map patterns to their types and bias
        pattern_info = {
            'hammer': ('single', 'bullish'),
            'hanging_man': ('single', 'bearish'),
            'inverted_hammer': ('single', 'bullish'),
            'shooting_star': ('single', 'bearish'),
            'engulfing_bullish': ('double', 'bullish'),
            'engulfing_bearish': ('double', 'bearish'),
            'piercing': ('double', 'bullish'),
            'dark_cloud': ('double', 'bearish'),
            'morning_star': ('triple', 'bullish'),
            'evening_star': ('triple', 'bearish'),
            'three_white_soldiers': ('triple', 'bullish'),
            'three_black_crows': ('triple', 'bearish'),
        }
        
        for pattern_name, (p_type, bias) in pattern_info.items():
            if pattern_type != 'all' and p_type != pattern_type:
                continue
            
            if pattern_name in patterns.columns:
                pattern_signals = patterns[patterns[pattern_name]]
                for idx in pattern_signals.index:
                    signals.append({
                        'timestamp': idx,
                        'pattern': pattern_name,
                        'type': p_type,
                        'bias': bias,
                        'open': df.loc[idx, 'open'],
                        'high': df.loc[idx, 'high'],
                        'low': df.loc[idx, 'low'],
                        'close': df.loc[idx, 'close'],
                        'volume': df.loc[idx, 'volume']
                    })
        
        return pd.DataFrame(signals) if signals else pd.DataFrame()
    
    # Additional Missing Pattern Implementations
    
    def detect_harami_cross(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Harami Cross pattern (doji inside large body)
        """
        df = self.normalize_dataframe(df)
        
        harami_cross = pd.Series(index=df.index, dtype=bool)
        harami_cross[:] = False
        
        doji = self.detect_doji(df)
        
        for i in range(1, len(df)):
            # Current candle is doji
            if doji.iloc[i] != '':
                # Previous candle is large body
                prev_body = abs(df['close'].iloc[i-1] - df['open'].iloc[i-1])
                avg_body = abs(df['close'] - df['open']).rolling(window=10).mean().iloc[i]
                
                if prev_body > avg_body * 1.5:
                    # Doji is inside previous candle's body
                    prev_high = max(df['open'].iloc[i-1], df['close'].iloc[i-1])
                    prev_low = min(df['open'].iloc[i-1], df['close'].iloc[i-1])
                    
                    if (df['open'].iloc[i] < prev_high and df['open'].iloc[i] > prev_low and
                        df['close'].iloc[i] < prev_high and df['close'].iloc[i] > prev_low):
                        harami_cross.iloc[i] = True
        
        return harami_cross
    
    def detect_homing_pigeon(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Homing Pigeon pattern (small black inside large black)
        """
        df = self.normalize_dataframe(df)
        
        homing_pigeon = pd.Series(index=df.index, dtype=bool)
        homing_pigeon[:] = False
        
        for i in range(1, len(df)):
            # Both candles are bearish
            if (df['close'].iloc[i-1] < df['open'].iloc[i-1] and
                df['close'].iloc[i] < df['open'].iloc[i]):
                
                # Previous candle is large bearish
                prev_body = df['open'].iloc[i-1] - df['close'].iloc[i-1]
                curr_body = df['open'].iloc[i] - df['close'].iloc[i]
                
                if curr_body < prev_body * 0.5:  # Current is smaller
                    # Current is inside previous
                    if (df['open'].iloc[i] < df['open'].iloc[i-1] and
                        df['close'].iloc[i] > df['close'].iloc[i-1]):
                        homing_pigeon.iloc[i] = True
        
        return homing_pigeon
    
    def detect_matching_low(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Matching Low pattern
        """
        df = self.normalize_dataframe(df)
        
        matching_low = pd.Series(index=df.index, dtype=bool)
        matching_low[:] = False
        
        for i in range(1, len(df)):
            # Check if lows are approximately equal
            if abs(df['low'].iloc[i] - df['low'].iloc[i-1]) / df['low'].iloc[i-1] < self.equal_threshold:
                # Both should be bearish candles
                if (df['close'].iloc[i-1] < df['open'].iloc[i-1] and
                    df['close'].iloc[i] < df['open'].iloc[i]):
                    matching_low.iloc[i] = True
        
        return matching_low
    
    def detect_matching_high(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Matching High pattern
        """
        df = self.normalize_dataframe(df)
        
        matching_high = pd.Series(index=df.index, dtype=bool)
        matching_high[:] = False
        
        for i in range(1, len(df)):
            # Check if highs are approximately equal
            if abs(df['high'].iloc[i] - df['high'].iloc[i-1]) / df['high'].iloc[i-1] < self.equal_threshold:
                # Both should be bullish candles
                if (df['close'].iloc[i-1] > df['open'].iloc[i-1] and
                    df['close'].iloc[i] > df['open'].iloc[i]):
                    matching_high.iloc[i] = True
        
        return matching_high
    
    def detect_on_neck(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect On Neck pattern
        """
        df = self.normalize_dataframe(df)
        
        on_neck = pd.Series(index=df.index, dtype=bool)
        on_neck[:] = False
        
        for i in range(1, len(df)):
            # First candle bearish, second bullish
            if (df['close'].iloc[i-1] < df['open'].iloc[i-1] and
                df['close'].iloc[i] > df['open'].iloc[i]):
                
                # Second opens below first's low
                if df['open'].iloc[i] < df['low'].iloc[i-1]:
                    # Second closes at or near first's low
                    if abs(df['close'].iloc[i] - df['low'].iloc[i-1]) / df['low'].iloc[i-1] < self.equal_threshold:
                        on_neck.iloc[i] = True
        
        return on_neck
    
    def detect_in_neck(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect In Neck pattern
        """
        df = self.normalize_dataframe(df)
        
        in_neck = pd.Series(index=df.index, dtype=bool)
        in_neck[:] = False
        
        for i in range(1, len(df)):
            # First candle bearish, second bullish
            if (df['close'].iloc[i-1] < df['open'].iloc[i-1] and
                df['close'].iloc[i] > df['open'].iloc[i]):
                
                # Second opens below first's low
                if df['open'].iloc[i] < df['low'].iloc[i-1]:
                    # Second closes slightly into first's body
                    first_body_bottom = df['close'].iloc[i-1]
                    if (df['close'].iloc[i] > first_body_bottom and
                        df['close'].iloc[i] < first_body_bottom + (df['open'].iloc[i-1] - first_body_bottom) * 0.1):
                        in_neck.iloc[i] = True
        
        return in_neck
    
    def detect_morning_doji_star(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Morning Doji Star pattern
        """
        df = self.normalize_dataframe(df)
        
        morning_doji_star = pd.Series(index=df.index, dtype=bool)
        morning_doji_star[:] = False
        
        doji = self.detect_doji(df)
        
        for i in range(2, len(df)):
            # First candle bearish
            if df['close'].iloc[i-2] < df['open'].iloc[i-2]:
                # Second candle is doji with gap down
                if (doji.iloc[i-1] != '' and 
                    df['high'].iloc[i-1] < df['low'].iloc[i-2]):
                    # Third candle bullish with gap up
                    if (df['close'].iloc[i] > df['open'].iloc[i] and
                        df['low'].iloc[i] > df['high'].iloc[i-1]):
                        morning_doji_star.iloc[i] = True
        
        return morning_doji_star
    
    def detect_evening_doji_star(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Evening Doji Star pattern
        """
        df = self.normalize_dataframe(df)
        
        evening_doji_star = pd.Series(index=df.index, dtype=bool)
        evening_doji_star[:] = False
        
        doji = self.detect_doji(df)
        
        for i in range(2, len(df)):
            # First candle bullish
            if df['close'].iloc[i-2] > df['open'].iloc[i-2]:
                # Second candle is doji with gap up
                if (doji.iloc[i-1] != '' and 
                    df['low'].iloc[i-1] > df['high'].iloc[i-2]):
                    # Third candle bearish with gap down
                    if (df['close'].iloc[i] < df['open'].iloc[i] and
                        df['high'].iloc[i] < df['low'].iloc[i-1]):
                        evening_doji_star.iloc[i] = True
        
        return evening_doji_star
    
    def detect_three_line_strike(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Three Line Strike pattern
        """
        df = self.normalize_dataframe(df)
        
        three_line_strike = pd.Series(index=df.index, dtype='object')
        three_line_strike[:] = ''
        
        for i in range(3, len(df)):
            # Bullish three line strike
            if (df['close'].iloc[i-3] > df['open'].iloc[i-3] and  # First bullish
                df['close'].iloc[i-2] > df['open'].iloc[i-2] and  # Second bullish  
                df['close'].iloc[i-1] > df['open'].iloc[i-1] and  # Third bullish
                df['close'].iloc[i] < df['open'].iloc[i]):        # Fourth bearish
                
                # Each closes higher than previous
                if (df['close'].iloc[i-2] > df['close'].iloc[i-3] and
                    df['close'].iloc[i-1] > df['close'].iloc[i-2]):
                    
                    # Fourth engulfs all three
                    if (df['open'].iloc[i] > df['close'].iloc[i-1] and
                        df['close'].iloc[i] < df['open'].iloc[i-3]):
                        three_line_strike.iloc[i] = 'bearish_strike'
            
            # Bearish three line strike  
            elif (df['close'].iloc[i-3] < df['open'].iloc[i-3] and  # First bearish
                  df['close'].iloc[i-2] < df['open'].iloc[i-2] and  # Second bearish
                  df['close'].iloc[i-1] < df['open'].iloc[i-1] and  # Third bearish
                  df['close'].iloc[i] > df['open'].iloc[i]):        # Fourth bullish
                
                # Each closes lower than previous
                if (df['close'].iloc[i-2] < df['close'].iloc[i-3] and
                    df['close'].iloc[i-1] < df['close'].iloc[i-2]):
                    
                    # Fourth engulfs all three
                    if (df['open'].iloc[i] < df['close'].iloc[i-1] and
                        df['close'].iloc[i] > df['open'].iloc[i-3]):
                        three_line_strike.iloc[i] = 'bullish_strike'
        
        return three_line_strike
    
    def detect_advance_block(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Advance Block pattern (weakening bullish momentum)
        """
        df = self.normalize_dataframe(df)
        
        advance_block = pd.Series(index=df.index, dtype=bool)
        advance_block[:] = False
        
        for i in range(2, len(df)):
            # Three consecutive bullish candles
            if (df['close'].iloc[i-2] > df['open'].iloc[i-2] and
                df['close'].iloc[i-1] > df['open'].iloc[i-1] and
                df['close'].iloc[i] > df['open'].iloc[i]):
                
                # Each closes higher
                if (df['close'].iloc[i-1] > df['close'].iloc[i-2] and
                    df['close'].iloc[i] > df['close'].iloc[i-1]):
                    
                    # Bodies get progressively smaller (weakening)
                    body1 = df['close'].iloc[i-2] - df['open'].iloc[i-2]
                    body2 = df['close'].iloc[i-1] - df['open'].iloc[i-1] 
                    body3 = df['close'].iloc[i] - df['open'].iloc[i]
                    
                    if body2 < body1 and body3 < body2:
                        # Upper shadows increase
                        shadow1 = df['high'].iloc[i-2] - df['close'].iloc[i-2]
                        shadow2 = df['high'].iloc[i-1] - df['close'].iloc[i-1]
                        shadow3 = df['high'].iloc[i] - df['close'].iloc[i]
                        
                        if shadow2 > shadow1 and shadow3 > shadow2:
                            advance_block.iloc[i] = True
        
        return advance_block
    
    def detect_deliberation_pattern(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Deliberation pattern (similar to advance block)
        """
        df = self.normalize_dataframe(df)
        
        deliberation = pd.Series(index=df.index, dtype=bool)
        deliberation[:] = False
        
        for i in range(2, len(df)):
            # Three consecutive bullish candles
            if (df['close'].iloc[i-2] > df['open'].iloc[i-2] and
                df['close'].iloc[i-1] > df['open'].iloc[i-1] and
                df['close'].iloc[i] > df['open'].iloc[i]):
                
                # Third candle shows hesitation (small body, long upper shadow)
                body3 = df['close'].iloc[i] - df['open'].iloc[i]
                shadow3 = df['high'].iloc[i] - df['close'].iloc[i]
                avg_body = abs(df['close'] - df['open']).rolling(window=5).mean().iloc[i]
                
                if body3 < avg_body * 0.5 and shadow3 > body3 * 2:
                    deliberation.iloc[i] = True
        
        return deliberation
    
    def detect_mat_hold(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Mat Hold pattern (bullish continuation)
        """
        df = self.normalize_dataframe(df)
        
        mat_hold = pd.Series(index=df.index, dtype=bool)
        mat_hold[:] = False
        
        for i in range(4, len(df)):
            # First candle long bullish
            if df['close'].iloc[i-4] > df['open'].iloc[i-4]:
                body1 = df['close'].iloc[i-4] - df['open'].iloc[i-4]
                avg_body = abs(df['close'] - df['open']).rolling(window=10).mean().iloc[i]
                
                if body1 > avg_body * 1.5:
                    # Next three candles small and contained within first
                    small_candles = True
                    for j in range(1, 4):
                        candle_body = abs(df['close'].iloc[i-4+j] - df['open'].iloc[i-4+j])
                        if (candle_body > body1 * 0.3 or
                            df['high'].iloc[i-4+j] > df['high'].iloc[i-4] or
                            df['low'].iloc[i-4+j] < df['low'].iloc[i-4]):
                            small_candles = False
                            break
                    
                    if small_candles:
                        # Fifth candle bullish and closes above first
                        if (df['close'].iloc[i] > df['open'].iloc[i] and
                            df['close'].iloc[i] > df['close'].iloc[i-4]):
                            mat_hold.iloc[i] = True
        
        return mat_hold
    
    def detect_rising_window(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Rising Window (gap up)
        """
        df = self.normalize_dataframe(df)
        
        rising_window = pd.Series(index=df.index, dtype=bool)
        rising_window[:] = False
        
        for i in range(1, len(df)):
            # Gap up - current low > previous high
            if df['low'].iloc[i] > df['high'].iloc[i-1]:
                gap_size = df['low'].iloc[i] - df['high'].iloc[i-1]
                if gap_size / df['close'].iloc[i-1] > 0.001:  # Minimum gap size
                    rising_window.iloc[i] = True
        
        return rising_window
    
    def detect_falling_window(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Falling Window (gap down)
        """
        df = self.normalize_dataframe(df)
        
        falling_window = pd.Series(index=df.index, dtype=bool)
        falling_window[:] = False
        
        for i in range(1, len(df)):
            # Gap down - current high < previous low
            if df['high'].iloc[i] < df['low'].iloc[i-1]:
                gap_size = df['low'].iloc[i-1] - df['high'].iloc[i]
                if gap_size / df['close'].iloc[i-1] > 0.001:  # Minimum gap size
                    falling_window.iloc[i] = True
        
        return falling_window
    
    def detect_ladder_bottom(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Ladder Bottom pattern (bullish reversal)
        """
        df = self.normalize_dataframe(df)
        
        ladder_bottom = pd.Series(index=df.index, dtype=bool)
        ladder_bottom[:] = False
        
        for i in range(4, len(df)):
            # First three candles bearish with lower closes
            bearish_sequence = all(
                df['close'].iloc[i-4+j] < df['open'].iloc[i-4+j] 
                for j in range(3)
            )
            
            if bearish_sequence:
                # Each closes lower than previous
                lower_closes = (df['close'].iloc[i-3] < df['close'].iloc[i-4] and
                               df['close'].iloc[i-2] < df['close'].iloc[i-3])
                
                if lower_closes:
                    # Fourth candle bearish but with long lower shadow
                    if df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                        body4 = df['open'].iloc[i-1] - df['close'].iloc[i-1]
                        shadow4 = df['close'].iloc[i-1] - df['low'].iloc[i-1]
                        
                        if shadow4 > body4 * 2:
                            # Fifth candle bullish
                            if df['close'].iloc[i] > df['open'].iloc[i]:
                                ladder_bottom.iloc[i] = True
        
        return ladder_bottom
    
    def detect_ladder_top(self, df: pd.DataFrame) -> pd.Series:
        """
        Detect Ladder Top pattern (bearish reversal)
        """
        df = self.normalize_dataframe(df)
        
        ladder_top = pd.Series(index=df.index, dtype=bool)
        ladder_top[:] = False
        
        for i in range(4, len(df)):
            # First three candles bullish with higher closes
            bullish_sequence = all(
                df['close'].iloc[i-4+j] > df['open'].iloc[i-4+j] 
                for j in range(3)
            )
            
            if bullish_sequence:
                # Each closes higher than previous
                higher_closes = (df['close'].iloc[i-3] > df['close'].iloc[i-4] and
                               df['close'].iloc[i-2] > df['close'].iloc[i-3])
                
                if higher_closes:
                    # Fourth candle bullish but with long upper shadow
                    if df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                        body4 = df['close'].iloc[i-1] - df['open'].iloc[i-1]
                        shadow4 = df['high'].iloc[i-1] - df['close'].iloc[i-1]
                        
                        if shadow4 > body4 * 2:
                            # Fifth candle bearish
                            if df['close'].iloc[i] < df['open'].iloc[i]:
                                ladder_top.iloc[i] = True
        
        return ladder_top