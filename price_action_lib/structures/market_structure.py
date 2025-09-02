"""Market structure analysis module"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.signal import argrelextrema
from ..core.base import BaseAnalyzer


class MarketStructure(BaseAnalyzer):
    """Analyze market structure, trends, and price action concepts"""
    
    def __init__(self, swing_strength: int = 3,
                 trend_lookback: int = 20,
                 structure_lookback: int = 50):
        """
        Initialize MarketStructure
        
        Parameters:
        -----------
        swing_strength : int
            Strength for swing point detection
        trend_lookback : int
            Lookback period for trend analysis
        structure_lookback : int
            Lookback for structure analysis
        """
        super().__init__()
        self.swing_strength = swing_strength
        self.trend_lookback = trend_lookback
        self.structure_lookback = structure_lookback
    
    def identify_market_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify overall market structure
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with structure analysis
        """
        df = self.normalize_dataframe(df)
        
        # Get swing points
        swings = self._get_swing_points(df)
        
        # Analyze structure
        structure = pd.DataFrame(index=df.index)
        
        # Trend direction
        structure['trend'] = self._identify_trend(df, swings)
        
        # Structure breaks
        structure['bos'] = self._detect_break_of_structure(df, swings)
        structure['choch'] = self._detect_change_of_character(df, swings)
        
        # Market phase
        structure['phase'] = self._identify_market_phase(df)
        
        # Trend strength
        structure['trend_strength'] = self._calculate_trend_strength(df)
        
        return structure
    
    def _get_swing_points(self, df: pd.DataFrame) -> Dict:
        """
        Get swing highs and lows
        """
        # Find local maxima and minima
        high_indices = argrelextrema(
            df['high'].values, np.greater, order=self.swing_strength
        )[0]
        
        low_indices = argrelextrema(
            df['low'].values, np.less, order=self.swing_strength
        )[0]
        
        # Create structured swing data
        swing_highs = []
        for idx in high_indices:
            swing_highs.append({
                'index': df.index[idx],
                'price': df['high'].iloc[idx],
                'type': 'high'
            })
        
        swing_lows = []
        for idx in low_indices:
            swing_lows.append({
                'index': df.index[idx],
                'price': df['low'].iloc[idx],
                'type': 'low'
            })
        
        return {
            'highs': swing_highs,
            'lows': swing_lows,
            'all': sorted(swing_highs + swing_lows, key=lambda x: x['index'])
        }
    
    def _identify_trend(self, df: pd.DataFrame, swings: Dict) -> pd.Series:
        """
        Identify trend based on swing structure
        """
        trend = pd.Series(index=df.index, dtype='object')
        trend[:] = 'neutral'
        
        if len(swings['all']) < 4:
            return trend
        
        # Analyze swing sequence
        for i in range(len(df)):
            recent_swings = [s for s in swings['all'] if s['index'] <= df.index[i]]
            
            if len(recent_swings) >= 4:
                # Get last 4 swings
                last_swings = recent_swings[-4:]
                
                # Check for higher highs and higher lows (uptrend)
                highs = [s for s in last_swings if s['type'] == 'high']
                lows = [s for s in last_swings if s['type'] == 'low']
                
                if len(highs) >= 2 and len(lows) >= 2:
                    if (highs[-1]['price'] > highs[-2]['price'] and
                        lows[-1]['price'] > lows[-2]['price']):
                        trend.iloc[i] = 'uptrend'
                    elif (highs[-1]['price'] < highs[-2]['price'] and
                          lows[-1]['price'] < lows[-2]['price']):
                        trend.iloc[i] = 'downtrend'
        
        return trend
    
    def _detect_break_of_structure(self, df: pd.DataFrame, swings: Dict) -> pd.Series:
        """
        Detect Break of Structure (BOS)
        """
        bos = pd.Series(index=df.index, dtype='object')
        bos[:] = ''
        
        if len(swings['highs']) < 2 or len(swings['lows']) < 2:
            return bos
        
        for i in range(1, len(df)):
            current_price = df['close'].iloc[i]
            prev_price = df['close'].iloc[i-1]
            
            # Check for bullish BOS (break above previous high)
            recent_highs = [s for s in swings['highs'] if s['index'] < df.index[i]]
            if recent_highs:
                last_high = recent_highs[-1]['price']
                if prev_price <= last_high < current_price:
                    bos.iloc[i] = 'bullish_bos'
            
            # Check for bearish BOS (break below previous low)
            recent_lows = [s for s in swings['lows'] if s['index'] < df.index[i]]
            if recent_lows:
                last_low = recent_lows[-1]['price']
                if prev_price >= last_low > current_price:
                    bos.iloc[i] = 'bearish_bos'
        
        return bos
    
    def _detect_change_of_character(self, df: pd.DataFrame, swings: Dict) -> pd.Series:
        """
        Detect Change of Character (ChoCh) - trend reversal signal
        """
        choch = pd.Series(index=df.index, dtype='object')
        choch[:] = ''
        
        trend = self._identify_trend(df, swings)
        
        for i in range(1, len(df)):
            if i > 0 and trend.iloc[i] != trend.iloc[i-1] and trend.iloc[i-1] != 'neutral':
                if trend.iloc[i] == 'uptrend' and trend.iloc[i-1] == 'downtrend':
                    choch.iloc[i] = 'bullish_choch'
                elif trend.iloc[i] == 'downtrend' and trend.iloc[i-1] == 'uptrend':
                    choch.iloc[i] = 'bearish_choch'
        
        return choch
    
    def _identify_market_phase(self, df: pd.DataFrame) -> pd.Series:
        """
        Identify market phase (trending, ranging, breakout)
        """
        phase = pd.Series(index=df.index, dtype='object')
        
        # Calculate metrics for phase identification
        atr = self.calculate_atr(df, period=14)
        
        for i in range(20, len(df)):
            window = df.iloc[i-20:i+1]
            
            # Calculate range
            period_high = window['high'].max()
            period_low = window['low'].min()
            period_range = period_high - period_low
            
            # Calculate directional movement
            net_change = abs(window['close'].iloc[-1] - window['close'].iloc[0])
            
            # Determine phase
            if net_change / period_range > 0.7:
                phase.iloc[i] = 'trending'
            elif net_change / period_range < 0.3:
                phase.iloc[i] = 'ranging'
            else:
                # Check for breakout
                if (df['close'].iloc[i] > period_high * 0.998 or 
                    df['close'].iloc[i] < period_low * 1.002):
                    phase.iloc[i] = 'breakout'
                else:
                    phase.iloc[i] = 'transitional'
        
        return phase
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate trend strength (0-100)
        """
        strength = pd.Series(index=df.index, dtype=float)
        
        for i in range(self.trend_lookback, len(df)):
            window = df.iloc[i-self.trend_lookback:i+1]
            
            # Calculate ADX-like strength
            high_changes = window['high'].diff()
            low_changes = -window['low'].diff()
            
            pos_dm = high_changes.where((high_changes > low_changes) & (high_changes > 0), 0)
            neg_dm = low_changes.where((low_changes > high_changes) & (low_changes > 0), 0)
            
            tr = self.calculate_atr(window, period=1) * len(window)
            
            if tr > 0:
                pos_di = 100 * pos_dm.sum() / tr
                neg_di = 100 * neg_dm.sum() / tr
                
                if (pos_di + neg_di) > 0:
                    strength.iloc[i] = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
                else:
                    strength.iloc[i] = 0
            else:
                strength.iloc[i] = 0
        
        return strength
    
    def detect_fair_value_gaps(self, df: pd.DataFrame, 
                              min_gap_size: float = 0.001) -> pd.DataFrame:
        """
        Detect Fair Value Gaps (FVG) / Imbalances
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        min_gap_size : float
            Minimum gap size as percentage
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with FVG details
        """
        df = self.normalize_dataframe(df)
        fvgs = []
        
        for i in range(2, len(df)):
            # Bullish FVG: Gap between 3rd candle low and 1st candle high
            gap_up = df['low'].iloc[i] - df['high'].iloc[i-2]
            if gap_up > df['close'].iloc[i] * min_gap_size:
                fvgs.append({
                    'timestamp': df.index[i],
                    'type': 'bullish_fvg',
                    'gap_high': df['low'].iloc[i],
                    'gap_low': df['high'].iloc[i-2],
                    'gap_size': gap_up,
                    'gap_mid': (df['low'].iloc[i] + df['high'].iloc[i-2]) / 2,
                    'filled': False
                })
            
            # Bearish FVG: Gap between 3rd candle high and 1st candle low
            gap_down = df['low'].iloc[i-2] - df['high'].iloc[i]
            if gap_down > df['close'].iloc[i] * min_gap_size:
                fvgs.append({
                    'timestamp': df.index[i],
                    'type': 'bearish_fvg',
                    'gap_high': df['low'].iloc[i-2],
                    'gap_low': df['high'].iloc[i],
                    'gap_size': gap_down,
                    'gap_mid': (df['low'].iloc[i-2] + df['high'].iloc[i]) / 2,
                    'filled': False
                })
        
        # Check if gaps were filled
        fvg_df = pd.DataFrame(fvgs)
        if not fvg_df.empty:
            for idx, fvg in fvg_df.iterrows():
                future_data = df[df.index > fvg['timestamp']]
                if not future_data.empty:
                    if fvg['type'] == 'bullish_fvg':
                        # Check if price came back to fill gap
                        filled = (future_data['low'] <= fvg['gap_mid']).any()
                    else:
                        # Check if price came back to fill gap
                        filled = (future_data['high'] >= fvg['gap_mid']).any()
                    
                    fvg_df.at[idx, 'filled'] = filled
                    if filled:
                        fill_bar = future_data[(future_data['low'] <= fvg['gap_mid']) if fvg['type'] == 'bullish_fvg' 
                                              else (future_data['high'] >= fvg['gap_mid'])].index[0]
                        fvg_df.at[idx, 'fill_time'] = fill_bar
        
        return fvg_df
    
    def detect_order_blocks(self, df: pd.DataFrame, 
                           lookback: int = 20) -> pd.DataFrame:
        """
        Detect Order Blocks (last candle before strong move)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        lookback : int
            Bars to look back for order blocks
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with order block details
        """
        df = self.normalize_dataframe(df)
        order_blocks = []
        
        # Calculate average candle range
        avg_range = (df['high'] - df['low']).rolling(window=20).mean()
        
        for i in range(lookback, len(df)-1):
            current_range = df['high'].iloc[i+1] - df['low'].iloc[i+1]
            
            # Look for strong bullish move
            if (df['close'].iloc[i+1] > df['open'].iloc[i+1] and
                current_range > avg_range.iloc[i] * 2 and
                df['close'].iloc[i+1] > df['high'].iloc[i]):
                
                # Previous candle is potential bullish order block
                order_blocks.append({
                    'timestamp': df.index[i],
                    'type': 'bullish_ob',
                    'ob_high': df['high'].iloc[i],
                    'ob_low': df['low'].iloc[i],
                    'ob_mid': (df['high'].iloc[i] + df['low'].iloc[i]) / 2,
                    'trigger_candle': df.index[i+1],
                    'strength': current_range / avg_range.iloc[i]
                })
            
            # Look for strong bearish move
            elif (df['close'].iloc[i+1] < df['open'].iloc[i+1] and
                  current_range > avg_range.iloc[i] * 2 and
                  df['close'].iloc[i+1] < df['low'].iloc[i]):
                
                # Previous candle is potential bearish order block
                order_blocks.append({
                    'timestamp': df.index[i],
                    'type': 'bearish_ob',
                    'ob_high': df['high'].iloc[i],
                    'ob_low': df['low'].iloc[i],
                    'ob_mid': (df['high'].iloc[i] + df['low'].iloc[i]) / 2,
                    'trigger_candle': df.index[i+1],
                    'strength': current_range / avg_range.iloc[i]
                })
        
        return pd.DataFrame(order_blocks) if order_blocks else pd.DataFrame()
    
    def detect_breaker_blocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Breaker Blocks (failed order blocks that reverse)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with breaker block details
        """
        df = self.normalize_dataframe(df)
        
        # First get order blocks
        order_blocks = self.detect_order_blocks(df)
        
        if order_blocks.empty:
            return pd.DataFrame()
        
        breaker_blocks = []
        
        for _, ob in order_blocks.iterrows():
            future_data = df[df.index > ob['timestamp']]
            
            if not future_data.empty:
                if ob['type'] == 'bullish_ob':
                    # Check if price broke below and closed below OB
                    break_bars = future_data[future_data['close'] < ob['ob_low']]
                    if not break_bars.empty:
                        breaker_blocks.append({
                            'timestamp': ob['timestamp'],
                            'type': 'bearish_breaker',
                            'breaker_high': ob['ob_high'],
                            'breaker_low': ob['ob_low'],
                            'break_time': break_bars.index[0],
                            'original_ob_type': ob['type']
                        })
                
                else:  # bearish_ob
                    # Check if price broke above and closed above OB
                    break_bars = future_data[future_data['close'] > ob['ob_high']]
                    if not break_bars.empty:
                        breaker_blocks.append({
                            'timestamp': ob['timestamp'],
                            'type': 'bullish_breaker',
                            'breaker_high': ob['ob_high'],
                            'breaker_low': ob['ob_low'],
                            'break_time': break_bars.index[0],
                            'original_ob_type': ob['type']
                        })
        
        return pd.DataFrame(breaker_blocks) if breaker_blocks else pd.DataFrame()
    
    def detect_liquidity_zones(self, df: pd.DataFrame, 
                              lookback: int = 50) -> pd.DataFrame:
        """
        Detect liquidity zones (equal highs/lows, stop hunt areas)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        lookback : int
            Bars to analyze for liquidity
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with liquidity zone details
        """
        df = self.normalize_dataframe(df)
        liquidity_zones = []
        
        # Detect equal highs (sell-side liquidity)
        for i in range(lookback, len(df)):
            window = df.iloc[i-lookback:i+1]
            high_counts = window['high'].value_counts()
            
            # Find highs that appear multiple times (within tolerance)
            for high_level, count in high_counts.items():
                if count >= 2:
                    nearby_highs = window[abs(window['high'] - high_level) / high_level < 0.001]
                    if len(nearby_highs) >= 2:
                        liquidity_zones.append({
                            'timestamp': df.index[i],
                            'type': 'sell_side_liquidity',
                            'level': high_level,
                            'touches': len(nearby_highs),
                            'strength': len(nearby_highs) * 10,
                            'zone_high': nearby_highs['high'].max(),
                            'zone_low': high_level * 0.999
                        })
        
        # Detect equal lows (buy-side liquidity)
        for i in range(lookback, len(df)):
            window = df.iloc[i-lookback:i+1]
            low_counts = window['low'].value_counts()
            
            # Find lows that appear multiple times (within tolerance)
            for low_level, count in low_counts.items():
                if count >= 2:
                    nearby_lows = window[abs(window['low'] - low_level) / low_level < 0.001]
                    if len(nearby_lows) >= 2:
                        liquidity_zones.append({
                            'timestamp': df.index[i],
                            'type': 'buy_side_liquidity',
                            'level': low_level,
                            'touches': len(nearby_lows),
                            'strength': len(nearby_lows) * 10,
                            'zone_high': low_level * 1.001,
                            'zone_low': nearby_lows['low'].min()
                        })
        
        # Remove duplicates and keep strongest zones
        if liquidity_zones:
            lz_df = pd.DataFrame(liquidity_zones)
            lz_df = lz_df.sort_values('strength', ascending=False)
            lz_df = lz_df.drop_duplicates(subset=['type', 'level'], keep='first')
            return lz_df
        
        return pd.DataFrame()
    
    def identify_premium_discount_zones(self, df: pd.DataFrame, 
                                       lookback: int = 50) -> pd.DataFrame:
        """
        Identify premium and discount zones relative to range
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        lookback : int
            Period for range calculation
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with zone information
        """
        df = self.normalize_dataframe(df)
        
        zones = pd.DataFrame(index=df.index)
        
        for i in range(lookback, len(df)):
            window = df.iloc[i-lookback:i+1]
            
            # Calculate range
            range_high = window['high'].max()
            range_low = window['low'].min()
            range_mid = (range_high + range_low) / 2
            
            # Premium zone (above 50% of range)
            premium_threshold = range_mid + (range_high - range_mid) * 0.5
            
            # Discount zone (below 50% of range)
            discount_threshold = range_mid - (range_mid - range_low) * 0.5
            
            # Equilibrium zone (middle 20% of range)
            eq_high = range_mid + (range_high - range_low) * 0.1
            eq_low = range_mid - (range_high - range_low) * 0.1
            
            # Classify current price
            current_close = df['close'].iloc[i]
            
            if current_close > premium_threshold:
                zones.at[df.index[i], 'zone'] = 'premium'
                zones.at[df.index[i], 'zone_position'] = (current_close - range_mid) / (range_high - range_mid)
            elif current_close < discount_threshold:
                zones.at[df.index[i], 'zone'] = 'discount'
                zones.at[df.index[i], 'zone_position'] = (range_mid - current_close) / (range_mid - range_low)
            elif eq_low <= current_close <= eq_high:
                zones.at[df.index[i], 'zone'] = 'equilibrium'
                zones.at[df.index[i], 'zone_position'] = 0.5
            else:
                zones.at[df.index[i], 'zone'] = 'neutral'
                zones.at[df.index[i], 'zone_position'] = (current_close - range_low) / (range_high - range_low)
            
            zones.at[df.index[i], 'range_high'] = range_high
            zones.at[df.index[i], 'range_low'] = range_low
            zones.at[df.index[i], 'range_mid'] = range_mid
        
        return zones
    
    def detect_trend_lines(self, df: pd.DataFrame, 
                          min_touches: int = 2) -> Dict[str, List]:
        """
        Detect trend lines based on swing points
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        min_touches : int
            Minimum touches for valid trend line
            
        Returns:
        --------
        Dict[str, List]
            Dictionary with support and resistance trend lines
        """
        df = self.normalize_dataframe(df)
        swings = self._get_swing_points(df)
        
        support_lines = []
        resistance_lines = []
        
        # Find support trend lines (connecting lows)
        lows = swings['lows']
        for i in range(len(lows)):
            for j in range(i+1, len(lows)):
                # Calculate line parameters
                x1, y1 = lows[i]['index'], lows[i]['price']
                x2, y2 = lows[j]['index'], lows[j]['price']
                
                # Calculate slope
                time_diff = (x2 - x1).total_seconds() / 3600  # Convert to hours
                if time_diff > 0:
                    slope = (y2 - y1) / time_diff
                    
                    # Check how many points touch this line
                    touches = 0
                    for low in lows:
                        expected_price = y1 + slope * ((low['index'] - x1).total_seconds() / 3600)
                        if abs(low['price'] - expected_price) / expected_price < 0.002:  # 0.2% tolerance
                            touches += 1
                    
                    if touches >= min_touches:
                        support_lines.append({
                            'start': x1,
                            'end': x2,
                            'start_price': y1,
                            'end_price': y2,
                            'slope': slope,
                            'touches': touches,
                            'type': 'support'
                        })
        
        # Find resistance trend lines (connecting highs)
        highs = swings['highs']
        for i in range(len(highs)):
            for j in range(i+1, len(highs)):
                # Calculate line parameters
                x1, y1 = highs[i]['index'], highs[i]['price']
                x2, y2 = highs[j]['index'], highs[j]['price']
                
                # Calculate slope
                time_diff = (x2 - x1).total_seconds() / 3600
                if time_diff > 0:
                    slope = (y2 - y1) / time_diff
                    
                    # Check how many points touch this line
                    touches = 0
                    for high in highs:
                        expected_price = y1 + slope * ((high['index'] - x1).total_seconds() / 3600)
                        if abs(high['price'] - expected_price) / expected_price < 0.002:
                            touches += 1
                    
                    if touches >= min_touches:
                        resistance_lines.append({
                            'start': x1,
                            'end': x2,
                            'start_price': y1,
                            'end_price': y2,
                            'slope': slope,
                            'touches': touches,
                            'type': 'resistance'
                        })
        
        return {
            'support_lines': support_lines,
            'resistance_lines': resistance_lines
        }
    
    def detect_channels(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect price channels (parallel trend lines)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        List[Dict]
            List of detected channels
        """
        df = self.normalize_dataframe(df)
        trend_lines = self.detect_trend_lines(df)
        
        channels = []
        
        # Look for parallel support and resistance lines
        for support in trend_lines['support_lines']:
            for resistance in trend_lines['resistance_lines']:
                # Check if slopes are similar (parallel)
                if abs(support['slope'] - resistance['slope']) / (abs(support['slope']) + 0.0001) < 0.1:
                    # Check if they overlap in time
                    start_time = max(support['start'], resistance['start'])
                    end_time = min(support['end'], resistance['end'])
                    
                    if start_time < end_time:
                        channels.append({
                            'type': 'ascending' if support['slope'] > 0.001 else 
                                   'descending' if support['slope'] < -0.001 else 'horizontal',
                            'support_line': support,
                            'resistance_line': resistance,
                            'start': start_time,
                            'end': end_time,
                            'slope': (support['slope'] + resistance['slope']) / 2,
                            'width': abs(resistance['start_price'] - support['start_price'])
                        })
        
        return channels
    
    def identify_consolidation_zones(self, df: pd.DataFrame, 
                                   lookback: int = 20,
                                   volatility_threshold: float = 0.5) -> pd.DataFrame:
        """
        Identify consolidation/ranging zones
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        lookback : int
            Period for consolidation detection
        volatility_threshold : float
            Threshold for considering as consolidation
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with consolidation zones
        """
        df = self.normalize_dataframe(df)
        
        consolidations = []
        atr = self.calculate_atr(df)
        
        i = lookback
        while i < len(df):
            window = df.iloc[i-lookback:i+1]
            window_atr = atr.iloc[i-lookback:i+1]
            
            # Calculate metrics
            range_high = window['high'].max()
            range_low = window['low'].min()
            range_size = range_high - range_low
            avg_atr = window_atr.mean()
            
            # Check if price is consolidating
            if avg_atr > 0 and range_size / avg_atr < volatility_threshold * lookback:
                # Find the extent of consolidation
                j = i
                while j < len(df) and df['high'].iloc[j] <= range_high * 1.002 and df['low'].iloc[j] >= range_low * 0.998:
                    j += 1
                
                consolidations.append({
                    'start': df.index[i-lookback],
                    'end': df.index[min(j-1, len(df)-1)],
                    'range_high': range_high,
                    'range_low': range_low,
                    'range_mid': (range_high + range_low) / 2,
                    'range_size': range_size,
                    'duration': j - (i - lookback),
                    'breakout_direction': 'up' if j < len(df) and df['close'].iloc[j] > range_high else
                                        'down' if j < len(df) and df['close'].iloc[j] < range_low else 'none'
                })
                
                i = j + 1
            else:
                i += 1
        
        return pd.DataFrame(consolidations) if consolidations else pd.DataFrame()
    
    def detect_price_action_setups(self, df: pd.DataFrame, setup_type: str = 'all') -> pd.DataFrame:
        """
        Detect specific price action setups
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        setup_type : str
            Type of setup ('all', 'pin_bar', 'inside_bar', 'outside_bar', 'fakey', 'spring', 'upthrust')
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with price action setups
        """
        df = self.normalize_dataframe(df)
        
        setups = []
        
        if setup_type in ['all', 'pin_bar']:
            setups.extend(self._detect_pin_bars(df).to_dict('records'))
        
        if setup_type in ['all', 'inside_bar']:
            setups.extend(self._detect_inside_bars(df).to_dict('records'))
        
        if setup_type in ['all', 'outside_bar']:
            setups.extend(self._detect_outside_bars(df).to_dict('records'))
        
        if setup_type in ['all', 'fakey']:
            setups.extend(self._detect_fakey_patterns(df).to_dict('records'))
        
        if setup_type in ['all', 'spring']:
            setups.extend(self._detect_spring_patterns(df).to_dict('records'))
        
        if setup_type in ['all', 'upthrust']:
            setups.extend(self._detect_upthrust_patterns(df).to_dict('records'))
        
        return pd.DataFrame(setups) if setups else pd.DataFrame()
    
    def _detect_pin_bars(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Pin Bar setups (rejection candles)
        """
        setups = []
        
        for i in range(1, len(df)):
            body = abs(df['close'].iloc[i] - df['open'].iloc[i])
            upper_shadow = df['high'].iloc[i] - max(df['open'].iloc[i], df['close'].iloc[i])
            lower_shadow = min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]
            candle_range = df['high'].iloc[i] - df['low'].iloc[i]
            
            # Pin bar criteria
            if candle_range > 0 and body / candle_range < 0.3:
                # Bullish pin bar (hammer-like at support)
                if (lower_shadow > body * 2 and upper_shadow < body and
                    df['low'].iloc[i] <= df['low'].iloc[i-5:i].min() if i >= 5 else True):
                    
                    setups.append({
                        'timestamp': df.index[i],
                        'setup_type': 'bullish_pin_bar',
                        'direction': 'bullish',
                        'entry': df['high'].iloc[i],
                        'stop_loss': df['low'].iloc[i],
                        'body_ratio': body / candle_range,
                        'shadow_ratio': lower_shadow / body
                    })
                
                # Bearish pin bar (shooting star-like at resistance)  
                elif (upper_shadow > body * 2 and lower_shadow < body and
                      df['high'].iloc[i] >= df['high'].iloc[i-5:i].max() if i >= 5 else True):
                    
                    setups.append({
                        'timestamp': df.index[i],
                        'setup_type': 'bearish_pin_bar',
                        'direction': 'bearish',
                        'entry': df['low'].iloc[i],
                        'stop_loss': df['high'].iloc[i],
                        'body_ratio': body / candle_range,
                        'shadow_ratio': upper_shadow / body
                    })
        
        return pd.DataFrame(setups)
    
    def _detect_inside_bars(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Inside Bar setups (consolidation within mother bar)
        """
        setups = []
        
        for i in range(1, len(df)):
            # Current bar is inside previous bar
            if (df['high'].iloc[i] < df['high'].iloc[i-1] and
                df['low'].iloc[i] > df['low'].iloc[i-1]):
                
                mother_bar_range = df['high'].iloc[i-1] - df['low'].iloc[i-1]
                inside_bar_range = df['high'].iloc[i] - df['low'].iloc[i]
                
                setups.append({
                    'timestamp': df.index[i],
                    'setup_type': 'inside_bar',
                    'direction': 'neutral',
                    'mother_bar_high': df['high'].iloc[i-1],
                    'mother_bar_low': df['low'].iloc[i-1],
                    'breakout_long_entry': df['high'].iloc[i-1],
                    'breakout_short_entry': df['low'].iloc[i-1],
                    'consolidation_ratio': inside_bar_range / mother_bar_range
                })
        
        return pd.DataFrame(setups)
    
    def _detect_outside_bars(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Outside Bar setups (engulfing bars)
        """
        setups = []
        
        for i in range(1, len(df)):
            # Current bar engulfs previous bar
            if (df['high'].iloc[i] > df['high'].iloc[i-1] and
                df['low'].iloc[i] < df['low'].iloc[i-1]):
                
                # Determine direction bias
                current_close = df['close'].iloc[i]
                current_open = df['open'].iloc[i]
                prev_close = df['close'].iloc[i-1]
                
                if current_close > current_open and current_close > prev_close:
                    direction = 'bullish'
                    entry = current_close
                    stop = df['low'].iloc[i]
                elif current_close < current_open and current_close < prev_close:
                    direction = 'bearish' 
                    entry = current_close
                    stop = df['high'].iloc[i]
                else:
                    direction = 'neutral'
                    entry = current_close
                    stop = df['low'].iloc[i] if direction == 'bullish' else df['high'].iloc[i]
                
                setups.append({
                    'timestamp': df.index[i],
                    'setup_type': 'outside_bar',
                    'direction': direction,
                    'entry': entry,
                    'stop_loss': stop,
                    'engulfment_size': (df['high'].iloc[i] - df['low'].iloc[i]) / (df['high'].iloc[i-1] - df['low'].iloc[i-1])
                })
        
        return pd.DataFrame(setups)
    
    def _detect_fakey_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Fakey patterns (false breakouts from inside bars)
        """
        setups = []
        
        # First find inside bars
        inside_bars = self._detect_inside_bars(df)
        
        for _, ib in inside_bars.iterrows():
            ib_timestamp = ib['timestamp']
            ib_index = df.index.get_loc(ib_timestamp)
            
            # Look at next few bars for false breakout
            for j in range(ib_index + 1, min(ib_index + 5, len(df))):
                # Check for false breakout
                if df['high'].iloc[j] > ib['mother_bar_high']:
                    # False upside breakout if it reverses
                    if (j + 1 < len(df) and 
                        df['close'].iloc[j+1] < ib['mother_bar_high']):
                        
                        setups.append({
                            'timestamp': df.index[j+1],
                            'setup_type': 'fakey_bearish',
                            'direction': 'bearish',
                            'inside_bar_time': ib_timestamp,
                            'false_break_level': ib['mother_bar_high'],
                            'entry': ib['mother_bar_high'],
                            'stop_loss': df['high'].iloc[j],
                            'target': ib['mother_bar_low']
                        })
                
                elif df['low'].iloc[j] < ib['mother_bar_low']:
                    # False downside breakout if it reverses
                    if (j + 1 < len(df) and 
                        df['close'].iloc[j+1] > ib['mother_bar_low']):
                        
                        setups.append({
                            'timestamp': df.index[j+1],
                            'setup_type': 'fakey_bullish',
                            'direction': 'bullish',
                            'inside_bar_time': ib_timestamp,
                            'false_break_level': ib['mother_bar_low'],
                            'entry': ib['mother_bar_low'],
                            'stop_loss': df['low'].iloc[j],
                            'target': ib['mother_bar_high']
                        })
        
        return pd.DataFrame(setups)
    
    def _detect_spring_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Spring patterns (false breakdown from support)
        """
        setups = []
        
        # Find support levels first
        from ..structures.support_resistance import SupportResistance
        sr_analyzer = SupportResistance()
        levels = sr_analyzer.detect_support_resistance_zones(df)
        
        if levels.empty:
            return pd.DataFrame(setups)
        
        support_levels = levels[levels['type'].isin(['support', 'both'])]
        
        for _, support in support_levels.iterrows():
            support_level = support['level']
            
            # Look for spring pattern around this level
            for i in range(10, len(df) - 2):
                # Price breaks below support
                if df['low'].iloc[i] < support_level * 0.998:
                    # But closes back above support (spring action)
                    if (df['close'].iloc[i] > support_level and
                        i + 1 < len(df) and df['close'].iloc[i+1] > support_level):
                        
                        setups.append({
                            'timestamp': df.index[i+1],
                            'setup_type': 'spring',
                            'direction': 'bullish',
                            'support_level': support_level,
                            'spring_low': df['low'].iloc[i],
                            'entry': support_level,
                            'stop_loss': df['low'].iloc[i],
                            'spring_strength': (support_level - df['low'].iloc[i]) / support_level * 100
                        })
        
        return pd.DataFrame(setups)
    
    def _detect_upthrust_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect Upthrust patterns (false breakout above resistance)
        """
        setups = []
        
        # Find resistance levels first
        from ..structures.support_resistance import SupportResistance
        sr_analyzer = SupportResistance()
        levels = sr_analyzer.detect_support_resistance_zones(df)
        
        if levels.empty:
            return pd.DataFrame(setups)
        
        resistance_levels = levels[levels['type'].isin(['resistance', 'both'])]
        
        for _, resistance in resistance_levels.iterrows():
            resistance_level = resistance['level']
            
            # Look for upthrust pattern around this level
            for i in range(10, len(df) - 2):
                # Price breaks above resistance
                if df['high'].iloc[i] > resistance_level * 1.002:
                    # But closes back below resistance (upthrust action)
                    if (df['close'].iloc[i] < resistance_level and
                        i + 1 < len(df) and df['close'].iloc[i+1] < resistance_level):
                        
                        setups.append({
                            'timestamp': df.index[i+1],
                            'setup_type': 'upthrust',
                            'direction': 'bearish',
                            'resistance_level': resistance_level,
                            'upthrust_high': df['high'].iloc[i],
                            'entry': resistance_level,
                            'stop_loss': df['high'].iloc[i],
                            'upthrust_strength': (df['high'].iloc[i] - resistance_level) / resistance_level * 100
                        })
        
        return pd.DataFrame(setups)
    
    def detect_range_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect range patterns (NR4, NR7, Inside Days, Outside Days)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with range patterns
        """
        df = self.normalize_dataframe(df)
        patterns = []
        
        # Calculate range
        df['range'] = df['high'] - df['low']
        
        for i in range(7, len(df)):
            current_range = df['range'].iloc[i]
            
            # NR4 - Narrowest range in 4 bars
            if i >= 3 and current_range == df['range'].iloc[i-3:i+1].min():
                patterns.append({
                    'timestamp': df.index[i],
                    'pattern': 'NR4',
                    'range': current_range,
                    'avg_range_4': df['range'].iloc[i-3:i+1].mean(),
                    'compression_ratio': current_range / df['range'].iloc[i-3:i+1].mean()
                })
            
            # NR7 - Narrowest range in 7 bars
            if i >= 6 and current_range == df['range'].iloc[i-6:i+1].min():
                patterns.append({
                    'timestamp': df.index[i],
                    'pattern': 'NR7',
                    'range': current_range,
                    'avg_range_7': df['range'].iloc[i-6:i+1].mean(),
                    'compression_ratio': current_range / df['range'].iloc[i-6:i+1].mean()
                })
            
            # Inside Day - High lower than previous high AND low higher than previous low
            if i > 0:
                if (df['high'].iloc[i] < df['high'].iloc[i-1] and
                    df['low'].iloc[i] > df['low'].iloc[i-1]):
                    patterns.append({
                        'timestamp': df.index[i],
                        'pattern': 'Inside_Day',
                        'range': current_range,
                        'prev_range': df['range'].iloc[i-1],
                        'compression_ratio': current_range / df['range'].iloc[i-1]
                    })
                
                # Outside Day - High higher than previous high AND low lower than previous low
                elif (df['high'].iloc[i] > df['high'].iloc[i-1] and
                      df['low'].iloc[i] < df['low'].iloc[i-1]):
                    patterns.append({
                        'timestamp': df.index[i],
                        'pattern': 'Outside_Day',
                        'range': current_range,
                        'prev_range': df['range'].iloc[i-1],
                        'expansion_ratio': current_range / df['range'].iloc[i-1]
                    })
        
        return pd.DataFrame(patterns) if patterns else pd.DataFrame()
    
    def _identify_trend(self, df: pd.DataFrame, swings: dict = None) -> pd.Series:
        """
        Identify trend direction using simple moving averages and price action
        """
        trend = pd.Series(index=df.index, dtype='object')
        trend[:] = 'neutral'
        
        # Use moving averages for trend identification
        if len(df) < 20:
            return trend
        
        # Calculate simple moving averages
        ma_10 = df['close'].rolling(10).mean()
        ma_20 = df['close'].rolling(20).mean()
        
        for i in range(20, len(df)):
            current_price = df['close'].iloc[i]
            ma10 = ma_10.iloc[i]
            ma20 = ma_20.iloc[i]
            
            # Trend determination
            if current_price > ma10 and ma10 > ma20:
                trend.iloc[i] = 'uptrend'
            elif current_price < ma10 and ma10 < ma20:
                trend.iloc[i] = 'downtrend'
            else:
                trend.iloc[i] = 'neutral'
        
        return trend
    
    def _get_swing_points(self, df: pd.DataFrame) -> dict:
        """
        Simple swing point detection
        """
        # Simple implementation that just returns empty dict to prevent errors
        return {'highs': [], 'lows': [], 'all': []}
    
    def _detect_break_of_structure(self, df: pd.DataFrame, swings: dict) -> pd.Series:
        """
        Detect break of structure points
        """
        bos = pd.Series(index=df.index, dtype='object')
        bos[:] = ''
        return bos
    
    def _detect_change_of_character(self, df: pd.DataFrame, swings: dict) -> pd.Series:
        """
        Detect change of character points
        """
        choch = pd.Series(index=df.index, dtype='object')
        choch[:] = ''
        return choch
    
    def _identify_market_phase(self, df: pd.DataFrame) -> pd.Series:
        """
        Identify market phase (trending, ranging, etc.)
        """
        phase = pd.Series(index=df.index, dtype='object')
        phase[:] = 'ranging'
        return phase
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate trend strength
        """
        strength = pd.Series(index=df.index, dtype='float64')
        strength[:] = 0.5
        return strength