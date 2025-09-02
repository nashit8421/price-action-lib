"""Chart pattern detection module"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.signal import argrelextrema
from ..core.base import BaseAnalyzer


class ChartPatterns(BaseAnalyzer):
    """Detect classic chart patterns"""
    
    def __init__(self, min_pattern_bars: int = 20,
                 symmetry_threshold: float = 0.1):
        """
        Initialize ChartPatterns
        
        Parameters:
        -----------
        min_pattern_bars : int
            Minimum bars for pattern formation
        symmetry_threshold : float
            Threshold for pattern symmetry validation
        """
        super().__init__()
        self.min_pattern_bars = min_pattern_bars
        self.symmetry_threshold = symmetry_threshold
    
    def detect_head_and_shoulders(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Head and Shoulders patterns
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        # Find swing points
        high_indices = argrelextrema(df['high'].values, np.greater, order=5)[0]
        
        if len(high_indices) < 5:
            return pd.DataFrame()
        
        for i in range(2, len(high_indices) - 2):
            left_shoulder = high_indices[i-2]
            left_valley = self._find_valley_between(df, high_indices[i-2], high_indices[i-1])
            head = high_indices[i]
            right_valley = self._find_valley_between(df, high_indices[i], high_indices[i+1])
            right_shoulder = high_indices[i+1]
            
            if left_valley is not None and right_valley is not None:
                # Validate H&S criteria
                left_shoulder_price = df['high'].iloc[left_shoulder]
                head_price = df['high'].iloc[head]
                right_shoulder_price = df['high'].iloc[right_shoulder]
                
                # Head should be highest
                if (head_price > left_shoulder_price and 
                    head_price > right_shoulder_price):
                    
                    # Shoulders should be roughly equal
                    shoulder_ratio = abs(left_shoulder_price - right_shoulder_price) / left_shoulder_price
                    
                    if shoulder_ratio < self.symmetry_threshold:
                        # Calculate neckline
                        left_valley_price = df['low'].iloc[left_valley]
                        right_valley_price = df['low'].iloc[right_valley]
                        neckline_slope = (right_valley_price - left_valley_price) / (right_valley - left_valley)
                        
                        patterns.append({
                            'pattern': 'head_and_shoulders',
                            'type': 'bearish',
                            'left_shoulder': df.index[left_shoulder],
                            'head': df.index[head],
                            'right_shoulder': df.index[right_shoulder],
                            'neckline_start': df.index[left_valley],
                            'neckline_end': df.index[right_valley],
                            'neckline_price': left_valley_price,
                            'target': left_valley_price - (head_price - left_valley_price),
                            'confirmed': False
                        })
        
        return pd.DataFrame(patterns)
    
    def detect_inverse_head_and_shoulders(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Inverse Head and Shoulders patterns
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        # Find swing lows
        low_indices = argrelextrema(df['low'].values, np.less, order=5)[0]
        
        if len(low_indices) < 5:
            return pd.DataFrame()
        
        for i in range(2, len(low_indices) - 2):
            left_shoulder = low_indices[i-2]
            left_peak = self._find_peak_between(df, low_indices[i-2], low_indices[i-1])
            head = low_indices[i]
            right_peak = self._find_peak_between(df, low_indices[i], low_indices[i+1])
            right_shoulder = low_indices[i+1]
            
            if left_peak is not None and right_peak is not None:
                # Validate inverse H&S criteria
                left_shoulder_price = df['low'].iloc[left_shoulder]
                head_price = df['low'].iloc[head]
                right_shoulder_price = df['low'].iloc[right_shoulder]
                
                # Head should be lowest
                if (head_price < left_shoulder_price and 
                    head_price < right_shoulder_price):
                    
                    # Shoulders should be roughly equal
                    shoulder_ratio = abs(left_shoulder_price - right_shoulder_price) / left_shoulder_price
                    
                    if shoulder_ratio < self.symmetry_threshold:
                        # Calculate neckline
                        left_peak_price = df['high'].iloc[left_peak]
                        right_peak_price = df['high'].iloc[right_peak]
                        
                        patterns.append({
                            'pattern': 'inverse_head_and_shoulders',
                            'type': 'bullish',
                            'left_shoulder': df.index[left_shoulder],
                            'head': df.index[head],
                            'right_shoulder': df.index[right_shoulder],
                            'neckline_start': df.index[left_peak],
                            'neckline_end': df.index[right_peak],
                            'neckline_price': left_peak_price,
                            'target': left_peak_price + (left_peak_price - head_price),
                            'confirmed': False
                        })
        
        return pd.DataFrame(patterns)
    
    def detect_double_tops_bottoms(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Double Top and Double Bottom patterns
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        # Find swing highs for double tops
        high_indices = argrelextrema(df['high'].values, np.greater, order=10)[0]
        
        for i in range(len(high_indices) - 1):
            for j in range(i + 1, len(high_indices)):
                if j - i > self.min_pattern_bars:  # Ensure minimum separation
                    first_peak = high_indices[i]
                    second_peak = high_indices[j]
                    
                    first_peak_price = df['high'].iloc[first_peak]
                    second_peak_price = df['high'].iloc[second_peak]
                    
                    # Check if peaks are roughly equal
                    peak_ratio = abs(first_peak_price - second_peak_price) / first_peak_price
                    
                    if peak_ratio < self.symmetry_threshold:
                        # Find valley between peaks
                        valley_idx = df.iloc[first_peak:second_peak+1]['low'].idxmin()
                        valley_price = df['low'].loc[valley_idx]
                        
                        patterns.append({
                            'pattern': 'double_top',
                            'type': 'bearish',
                            'first_peak': df.index[first_peak],
                            'second_peak': df.index[second_peak],
                            'valley': valley_idx,
                            'resistance_level': (first_peak_price + second_peak_price) / 2,
                            'support_level': valley_price,
                            'target': valley_price - (first_peak_price - valley_price),
                            'confirmed': False
                        })
        
        # Find swing lows for double bottoms
        low_indices = argrelextrema(df['low'].values, np.less, order=10)[0]
        
        for i in range(len(low_indices) - 1):
            for j in range(i + 1, len(low_indices)):
                if j - i > self.min_pattern_bars:
                    first_trough = low_indices[i]
                    second_trough = low_indices[j]
                    
                    first_trough_price = df['low'].iloc[first_trough]
                    second_trough_price = df['low'].iloc[second_trough]
                    
                    # Check if troughs are roughly equal
                    trough_ratio = abs(first_trough_price - second_trough_price) / first_trough_price
                    
                    if trough_ratio < self.symmetry_threshold:
                        # Find peak between troughs
                        peak_idx = df.iloc[first_trough:second_trough+1]['high'].idxmax()
                        peak_price = df['high'].loc[peak_idx]
                        
                        patterns.append({
                            'pattern': 'double_bottom',
                            'type': 'bullish',
                            'first_trough': df.index[first_trough],
                            'second_trough': df.index[second_trough],
                            'peak': peak_idx,
                            'support_level': (first_trough_price + second_trough_price) / 2,
                            'resistance_level': peak_price,
                            'target': peak_price + (peak_price - first_trough_price),
                            'confirmed': False
                        })
        
        return pd.DataFrame(patterns)
    
    def detect_triangles(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Triangle patterns (Ascending, Descending, Symmetrical)
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        # Find swing points
        high_indices = argrelextrema(df['high'].values, np.greater, order=3)[0]
        low_indices = argrelextrema(df['low'].values, np.less, order=3)[0]
        
        if len(high_indices) < 3 or len(low_indices) < 3:
            return pd.DataFrame()
        
        # Analyze trend lines
        for i in range(len(high_indices) - 2):
            for j in range(len(low_indices) - 2):
                if abs(high_indices[i] - low_indices[j]) < 50:  # Start around same time
                    # Get three consecutive highs and lows
                    high_points = high_indices[i:i+3]
                    low_points = low_indices[j:j+3]
                    
                    if len(high_points) == 3 and len(low_points) == 3:
                        # Calculate trend line slopes
                        high_prices = df['high'].iloc[high_points].values
                        low_prices = df['low'].iloc[low_points].values
                        
                        high_slope = (high_prices[2] - high_prices[0]) / (high_points[2] - high_points[0])
                        low_slope = (low_prices[2] - low_prices[0]) / (low_points[2] - low_points[0])
                        
                        # Classify triangle type
                        if abs(high_slope) < 0.01 and low_slope > 0.01:  # Horizontal resistance, rising support
                            triangle_type = 'ascending'
                            bias = 'bullish'
                        elif high_slope < -0.01 and abs(low_slope) < 0.01:  # Falling resistance, horizontal support
                            triangle_type = 'descending'
                            bias = 'bearish'
                        elif high_slope < -0.01 and low_slope > 0.01:  # Converging lines
                            triangle_type = 'symmetrical'
                            bias = 'neutral'
                        else:
                            continue
                        
                        patterns.append({
                            'pattern': f'{triangle_type}_triangle',
                            'type': bias,
                            'start': df.index[min(high_points[0], low_points[0])],
                            'end': df.index[max(high_points[2], low_points[2])],
                            'resistance_slope': high_slope,
                            'support_slope': low_slope,
                            'apex_price': (high_prices[0] + low_prices[0]) / 2,
                            'confirmed': False
                        })
        
        return pd.DataFrame(patterns)
    
    def detect_wedges(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Wedge patterns (Rising, Falling)
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        # Find swing points
        high_indices = argrelextrema(df['high'].values, np.greater, order=3)[0]
        low_indices = argrelextrema(df['low'].values, np.less, order=3)[0]
        
        if len(high_indices) < 3 or len(low_indices) < 3:
            return pd.DataFrame()
        
        # Look for converging trend lines with same direction
        for i in range(len(high_indices) - 2):
            for j in range(len(low_indices) - 2):
                high_points = high_indices[i:i+3]
                low_points = low_indices[j:j+3]
                
                if len(high_points) == 3 and len(low_points) == 3:
                    high_prices = df['high'].iloc[high_points].values
                    low_prices = df['low'].iloc[low_points].values
                    
                    high_slope = (high_prices[2] - high_prices[0]) / (high_points[2] - high_points[0])
                    low_slope = (low_prices[2] - low_prices[0]) / (low_points[2] - low_points[0])
                    
                    # Rising wedge - both lines rising, but resistance rises slower
                    if (high_slope > 0 and low_slope > 0 and low_slope > high_slope):
                        patterns.append({
                            'pattern': 'rising_wedge',
                            'type': 'bearish',
                            'start': df.index[min(high_points[0], low_points[0])],
                            'end': df.index[max(high_points[2], low_points[2])],
                            'resistance_slope': high_slope,
                            'support_slope': low_slope,
                            'confirmed': False
                        })
                    
                    # Falling wedge - both lines falling, but support falls slower
                    elif (high_slope < 0 and low_slope < 0 and low_slope > high_slope):
                        patterns.append({
                            'pattern': 'falling_wedge',
                            'type': 'bullish',
                            'start': df.index[min(high_points[0], low_points[0])],
                            'end': df.index[max(high_points[2], low_points[2])],
                            'resistance_slope': high_slope,
                            'support_slope': low_slope,
                            'confirmed': False
                        })
        
        return pd.DataFrame(patterns)
    
    def detect_flags_pennants(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Flag and Pennant patterns
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        # Look for strong moves followed by consolidation
        for i in range(20, len(df) - 20):
            # Identify flagpole (strong move)
            flagpole_start = i - 20
            flagpole_end = i
            
            flagpole_move = abs(df['close'].iloc[flagpole_end] - df['close'].iloc[flagpole_start])
            avg_move = abs(df['close'].diff()).rolling(window=20).mean().iloc[i]
            
            if flagpole_move > avg_move * 5:  # Strong move
                move_direction = 'up' if df['close'].iloc[flagpole_end] > df['close'].iloc[flagpole_start] else 'down'
                
                # Look for consolidation after strong move
                consolidation_end = min(i + 15, len(df) - 1)
                consolidation_data = df.iloc[i:consolidation_end]
                
                if len(consolidation_data) > 5:
                    cons_high = consolidation_data['high'].max()
                    cons_low = consolidation_data['low'].min()
                    cons_range = cons_high - cons_low
                    
                    # Flag criteria - parallel consolidation
                    if cons_range < flagpole_move * 0.3:  # Small consolidation relative to flagpole
                        # Check if consolidation slopes against the trend (typical for flags)
                        cons_slope = (consolidation_data['close'].iloc[-1] - consolidation_data['close'].iloc[0]) / len(consolidation_data)
                        
                        if ((move_direction == 'up' and cons_slope < 0) or
                            (move_direction == 'down' and cons_slope > 0)):
                            
                            patterns.append({
                                'pattern': 'flag',
                                'type': 'bullish' if move_direction == 'up' else 'bearish',
                                'flagpole_start': df.index[flagpole_start],
                                'flagpole_end': df.index[flagpole_end],
                                'flag_start': df.index[i],
                                'flag_end': df.index[consolidation_end],
                                'flagpole_size': flagpole_move,
                                'target': df['close'].iloc[consolidation_end] + (flagpole_move if move_direction == 'up' else -flagpole_move),
                                'confirmed': False
                            })
        
        return pd.DataFrame(patterns)
    
    def _find_valley_between(self, df: pd.DataFrame, start_idx: int, end_idx: int) -> Optional[int]:
        """Find the lowest point between two indices"""
        if start_idx >= end_idx or end_idx >= len(df):
            return None
        
        section = df.iloc[start_idx:end_idx+1]
        if section.empty:
            return None
        
        valley_idx = section['low'].idxmin()
        return df.index.get_loc(valley_idx)
    
    def _find_peak_between(self, df: pd.DataFrame, start_idx: int, end_idx: int) -> Optional[int]:
        """Find the highest point between two indices"""
        if start_idx >= end_idx or end_idx >= len(df):
            return None
        
        section = df.iloc[start_idx:end_idx+1]
        if section.empty:
            return None
        
        peak_idx = section['high'].idxmax()
        return df.index.get_loc(peak_idx)
    
    def detect_all_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect all chart patterns
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            Combined results of all pattern detection
        """
        all_patterns = []
        
        # Detect each pattern type
        hs_patterns = self.detect_head_and_shoulders(df)
        ihs_patterns = self.detect_inverse_head_and_shoulders(df)
        double_patterns = self.detect_double_tops_bottoms(df)
        triangle_patterns = self.detect_triangles(df)
        wedge_patterns = self.detect_wedges(df)
        flag_patterns = self.detect_flags_pennants(df)
        rounding_patterns = self.detect_rounding_patterns(df)
        v_patterns = self.detect_v_patterns(df)
        cup_handle_patterns = self.detect_cup_and_handle(df)
        rectangle_patterns = self.detect_rectangles(df)
        
        # Combine all patterns
        pattern_dfs = [hs_patterns, ihs_patterns, double_patterns, 
                      triangle_patterns, wedge_patterns, flag_patterns,
                      rounding_patterns, v_patterns, cup_handle_patterns, rectangle_patterns]
        
        for pdf in pattern_dfs:
            if not pdf.empty:
                all_patterns.extend(pdf.to_dict('records'))
        
        return pd.DataFrame(all_patterns) if all_patterns else pd.DataFrame()
    
    def detect_rounding_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Rounding Top and Bottom patterns
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        window_size = max(50, self.min_pattern_bars * 2)
        
        for i in range(window_size, len(df) - window_size):
            window = df.iloc[i-window_size:i+window_size]
            
            # Rounding Top
            if window['high'].idxmax() == df.index[i]:  # Peak in middle
                left_side = window.iloc[:window_size]
                right_side = window.iloc[window_size:]
                
                # Check for gradual rise and fall
                left_trend = (left_side['close'].iloc[-1] - left_side['close'].iloc[0]) / len(left_side)
                right_trend = (right_side['close'].iloc[-1] - right_side['close'].iloc[0]) / len(right_side)
                
                if left_trend > 0 and right_trend < 0 and abs(left_trend) > abs(right_trend) * 0.7:
                    patterns.append({
                        'pattern': 'rounding_top',
                        'type': 'bearish',
                        'start': window.index[0],
                        'peak': df.index[i],
                        'end': window.index[-1],
                        'peak_price': df['high'].iloc[i]
                    })
            
            # Rounding Bottom  
            elif window['low'].idxmin() == df.index[i]:  # Trough in middle
                left_side = window.iloc[:window_size]
                right_side = window.iloc[window_size:]
                
                # Check for gradual fall and rise
                left_trend = (left_side['close'].iloc[-1] - left_side['close'].iloc[0]) / len(left_side)
                right_trend = (right_side['close'].iloc[-1] - right_side['close'].iloc[0]) / len(right_side)
                
                if left_trend < 0 and right_trend > 0 and abs(left_trend) > abs(right_trend) * 0.7:
                    patterns.append({
                        'pattern': 'rounding_bottom',
                        'type': 'bullish',
                        'start': window.index[0],
                        'trough': df.index[i],
                        'end': window.index[-1],
                        'trough_price': df['low'].iloc[i]
                    })
        
        return pd.DataFrame(patterns)
    
    def detect_v_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect V-Top and V-Bottom patterns (sharp reversals)
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        # Calculate price velocity
        price_velocity = df['close'].diff().abs()
        high_velocity_threshold = price_velocity.quantile(0.9)
        
        for i in range(10, len(df) - 10):
            # V-Top pattern
            if df['high'].iloc[i] == df['high'].iloc[i-10:i+11].max():
                # Check for sharp rise and fall
                left_velocity = price_velocity.iloc[i-5:i].mean()
                right_velocity = price_velocity.iloc[i:i+5].mean()
                
                if (left_velocity > high_velocity_threshold * 0.7 and
                    right_velocity > high_velocity_threshold * 0.7):
                    
                    # Ensure it's actually a peak
                    if (df['close'].iloc[i-5] < df['close'].iloc[i] and
                        df['close'].iloc[i+5] < df['close'].iloc[i]):
                        
                        patterns.append({
                            'pattern': 'v_top',
                            'type': 'bearish',
                            'start': df.index[i-5],
                            'peak': df.index[i],
                            'end': df.index[i+5],
                            'peak_price': df['high'].iloc[i],
                            'sharpness': (left_velocity + right_velocity) / 2
                        })
            
            # V-Bottom pattern
            elif df['low'].iloc[i] == df['low'].iloc[i-10:i+11].min():
                # Check for sharp fall and rise
                left_velocity = price_velocity.iloc[i-5:i].mean()
                right_velocity = price_velocity.iloc[i:i+5].mean()
                
                if (left_velocity > high_velocity_threshold * 0.7 and
                    right_velocity > high_velocity_threshold * 0.7):
                    
                    # Ensure it's actually a trough
                    if (df['close'].iloc[i-5] > df['close'].iloc[i] and
                        df['close'].iloc[i+5] > df['close'].iloc[i]):
                        
                        patterns.append({
                            'pattern': 'v_bottom',
                            'type': 'bullish',
                            'start': df.index[i-5],
                            'trough': df.index[i],
                            'end': df.index[i+5],
                            'trough_price': df['low'].iloc[i],
                            'sharpness': (left_velocity + right_velocity) / 2
                        })
        
        return pd.DataFrame(patterns)
    
    def detect_cup_and_handle(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Cup and Handle patterns
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        min_cup_size = max(30, self.min_pattern_bars)
        
        for i in range(min_cup_size, len(df) - 20):
            # Look for cup formation (U-shaped)
            cup_window = df.iloc[i-min_cup_size:i]
            
            if len(cup_window) < min_cup_size:
                continue
                
            # Find potential cup boundaries
            left_high_idx = cup_window['high'].iloc[:10].idxmax()
            right_high_idx = cup_window['high'].iloc[-10:].idxmax()
            cup_low_idx = cup_window['low'].idxmin()
            
            left_high = cup_window.loc[left_high_idx, 'high']
            right_high = cup_window.loc[right_high_idx, 'high']
            cup_low = cup_window.loc[cup_low_idx, 'low']
            
            # Check cup criteria
            if (abs(left_high - right_high) / left_high < 0.03 and  # Similar heights
                cup_low < left_high * 0.85):  # Deep enough cup
                
                # Look for handle formation after cup
                handle_window = df.iloc[i:i+15]
                if len(handle_window) >= 5:
                    handle_high = handle_window['high'].max()
                    handle_low = handle_window['low'].min()
                    
                    # Handle should be smaller pullback
                    if (handle_high < right_high and
                        handle_low > cup_low and
                        (right_high - handle_low) / right_high < 0.15):
                        
                        patterns.append({
                            'pattern': 'cup_and_handle',
                            'type': 'bullish',
                            'cup_start': left_high_idx,
                            'cup_low': cup_low_idx,
                            'cup_end': right_high_idx,
                            'handle_start': df.index[i],
                            'handle_end': handle_window.index[-1],
                            'resistance_level': right_high,
                            'target': right_high + (right_high - cup_low),
                            'confirmed': False
                        })
        
        return pd.DataFrame(patterns)
    
    def detect_rectangles(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Rectangle patterns (horizontal channels)
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        min_rectangle_size = max(20, self.min_pattern_bars)
        
        for i in range(min_rectangle_size, len(df)):
            window = df.iloc[i-min_rectangle_size:i]
            
            # Identify potential support and resistance levels
            resistance_level = window['high'].quantile(0.95)
            support_level = window['low'].quantile(0.05)
            
            # Check if price has been contained within these levels
            touches_resistance = (window['high'] >= resistance_level * 0.998).sum()
            touches_support = (window['low'] <= support_level * 1.002).sum()
            
            # Rectangle criteria
            if (touches_resistance >= 2 and touches_support >= 2 and
                (resistance_level - support_level) / support_level > 0.02):
                
                # Ensure most prices are within the rectangle
                within_rectangle = ((window['low'] >= support_level * 0.995) & 
                                  (window['high'] <= resistance_level * 1.005)).sum()
                
                if within_rectangle / len(window) > 0.8:
                    patterns.append({
                        'pattern': 'rectangle',
                        'type': 'neutral',
                        'start': window.index[0],
                        'end': window.index[-1],
                        'resistance_level': resistance_level,
                        'support_level': support_level,
                        'height': resistance_level - support_level,
                        'resistance_touches': touches_resistance,
                        'support_touches': touches_support,
                        'confirmed': False
                    })
        
        return pd.DataFrame(patterns)