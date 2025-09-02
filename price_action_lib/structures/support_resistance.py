"""Support and Resistance detection module"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.signal import argrelextrema
from ..core.base import BaseAnalyzer


class SupportResistance(BaseAnalyzer):
    """Detect and analyze support and resistance levels"""
    
    def __init__(self, swing_strength: int = 2, 
                 cluster_threshold: float = 0.005,
                 min_touches: int = 2):
        """
        Initialize SupportResistance
        
        Parameters:
        -----------
        swing_strength : int
            Number of bars on each side for swing detection
        cluster_threshold : float
            Threshold for clustering nearby levels (as percentage)
        min_touches : int
            Minimum touches to consider a valid level
        """
        super().__init__()
        self.swing_strength = swing_strength
        self.cluster_threshold = cluster_threshold
        self.min_touches = min_touches
    
    def find_swing_points(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Find swing highs and lows
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        Dict[str, pd.Series]
            Dictionary with 'swing_highs' and 'swing_lows'
        """
        df = self.normalize_dataframe(df)
        
        # Find local maxima and minima
        high_indices = argrelextrema(
            df['high'].values, np.greater, order=self.swing_strength
        )[0]
        
        low_indices = argrelextrema(
            df['low'].values, np.less, order=self.swing_strength
        )[0]
        
        # Create series with swing points
        swing_highs = pd.Series(index=df.index, dtype=float)
        swing_lows = pd.Series(index=df.index, dtype=float)
        
        swing_highs.iloc[high_indices] = df['high'].iloc[high_indices]
        swing_lows.iloc[low_indices] = df['low'].iloc[low_indices]
        
        return {
            'swing_highs': swing_highs,
            'swing_lows': swing_lows
        }
    
    def find_major_swings(self, df: pd.DataFrame, 
                         lookback: int = 50) -> Dict[str, pd.Series]:
        """
        Find major swing points (higher timeframe swings)
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        lookback : int
            Lookback period for major swings
            
        Returns:
        --------
        Dict[str, pd.Series]
            Dictionary with major swing highs and lows
        """
        df = self.normalize_dataframe(df)
        
        # Rolling max/min for major swings
        rolling_high = df['high'].rolling(window=lookback, center=True).max()
        rolling_low = df['low'].rolling(window=lookback, center=True).min()
        
        # Identify major swing points
        major_highs = df['high'] == rolling_high
        major_lows = df['low'] == rolling_low
        
        # Create series
        major_swing_highs = pd.Series(index=df.index, dtype=float)
        major_swing_lows = pd.Series(index=df.index, dtype=float)
        
        major_swing_highs[major_highs] = df['high'][major_highs]
        major_swing_lows[major_lows] = df['low'][major_lows]
        
        return {
            'major_highs': major_swing_highs,
            'major_lows': major_swing_lows
        }
    
    def detect_support_resistance_zones(self, df: pd.DataFrame, 
                                       method: str = 'swings') -> pd.DataFrame:
        """
        Detect support and resistance zones
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        method : str
            Method for detection ('swings', 'volume', 'fractals')
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with support/resistance levels and metadata
        """
        df = self.normalize_dataframe(df)
        
        if method == 'swings':
            levels = self._detect_swing_based_levels(df)
        elif method == 'volume':
            levels = self._detect_volume_based_levels(df)
        elif method == 'fractals':
            levels = self._detect_fractal_levels(df)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Cluster nearby levels
        clustered_levels = self._cluster_levels(levels)
        
        # Score and validate levels
        validated_levels = self._validate_levels(df, clustered_levels)
        
        return validated_levels
    
    def _detect_swing_based_levels(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect levels based on swing points
        """
        swings = self.find_swing_points(df)
        levels = []
        
        # Process swing highs as resistance
        for idx, value in swings['swing_highs'].dropna().items():
            levels.append({
                'level': value,
                'type': 'resistance',
                'method': 'swing_high',
                'timestamp': idx,
                'touches': 1
            })
        
        # Process swing lows as support
        for idx, value in swings['swing_lows'].dropna().items():
            levels.append({
                'level': value,
                'type': 'support',
                'method': 'swing_low',
                'timestamp': idx,
                'touches': 1
            })
        
        return levels
    
    def _detect_volume_based_levels(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect levels based on volume profiles
        """
        levels = []
        
        # Calculate volume profile
        price_bins = np.linspace(df['low'].min(), df['high'].max(), 50)
        volume_profile = pd.cut(df['close'], bins=price_bins)
        volume_by_price = df.groupby(volume_profile)['volume'].sum()
        
        # Find high volume nodes (potential support/resistance)
        high_volume_threshold = volume_by_price.quantile(0.7)
        high_volume_prices = volume_by_price[volume_by_price > high_volume_threshold]
        
        for interval, volume in high_volume_prices.items():
            if pd.notna(interval):
                level_price = interval.mid
                levels.append({
                    'level': level_price,
                    'type': 'both',
                    'method': 'volume_node',
                    'volume': volume,
                    'touches': 0
                })
        
        # Find low volume nodes (potential breakout zones)
        low_volume_threshold = volume_by_price.quantile(0.3)
        low_volume_prices = volume_by_price[volume_by_price < low_volume_threshold]
        
        for interval, volume in low_volume_prices.items():
            if pd.notna(interval):
                level_price = interval.mid
                levels.append({
                    'level': level_price,
                    'type': 'breakout_zone',
                    'method': 'low_volume_node',
                    'volume': volume,
                    'touches': 0
                })
        
        return levels
    
    def _detect_fractal_levels(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect levels using fractal patterns
        """
        levels = []
        
        # Williams Fractal Pattern
        # Bearish fractal (resistance)
        for i in range(2, len(df) - 2):
            if (df['high'].iloc[i] > df['high'].iloc[i-1] and
                df['high'].iloc[i] > df['high'].iloc[i-2] and
                df['high'].iloc[i] > df['high'].iloc[i+1] and
                df['high'].iloc[i] > df['high'].iloc[i+2]):
                
                levels.append({
                    'level': df['high'].iloc[i],
                    'type': 'resistance',
                    'method': 'bearish_fractal',
                    'timestamp': df.index[i],
                    'touches': 1
                })
        
        # Bullish fractal (support)
        for i in range(2, len(df) - 2):
            if (df['low'].iloc[i] < df['low'].iloc[i-1] and
                df['low'].iloc[i] < df['low'].iloc[i-2] and
                df['low'].iloc[i] < df['low'].iloc[i+1] and
                df['low'].iloc[i] < df['low'].iloc[i+2]):
                
                levels.append({
                    'level': df['low'].iloc[i],
                    'type': 'support',
                    'method': 'bullish_fractal',
                    'timestamp': df.index[i],
                    'touches': 1
                })
        
        return levels
    
    def _cluster_levels(self, levels: List[Dict]) -> List[Dict]:
        """
        Cluster nearby levels together
        """
        if not levels:
            return []
        
        # Sort levels by price
        sorted_levels = sorted(levels, key=lambda x: x['level'])
        clustered = []
        current_cluster = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            # Check if level is within threshold of current cluster
            cluster_avg = np.mean([l['level'] for l in current_cluster])
            if abs(level['level'] - cluster_avg) / cluster_avg < self.cluster_threshold:
                current_cluster.append(level)
            else:
                # Process current cluster
                clustered.append(self._merge_cluster(current_cluster))
                current_cluster = [level]
        
        # Don't forget the last cluster
        if current_cluster:
            clustered.append(self._merge_cluster(current_cluster))
        
        return clustered
    
    def _merge_cluster(self, cluster: List[Dict]) -> Dict:
        """
        Merge a cluster of levels into a single level
        """
        # Calculate weighted average based on touches
        total_touches = sum(l.get('touches', 1) for l in cluster)
        weighted_sum = sum(l['level'] * l.get('touches', 1) for l in cluster)
        avg_level = weighted_sum / total_touches if total_touches > 0 else np.mean([l['level'] for l in cluster])
        
        # Determine type
        types = [l['type'] for l in cluster]
        if 'both' in types or ('support' in types and 'resistance' in types):
            level_type = 'both'
        elif 'resistance' in types:
            level_type = 'resistance'
        else:
            level_type = 'support'
        
        return {
            'level': avg_level,
            'type': level_type,
            'methods': list(set(l['method'] for l in cluster)),
            'touches': total_touches,
            'strength': len(cluster),
            'range': max(l['level'] for l in cluster) - min(l['level'] for l in cluster)
        }
    
    def _validate_levels(self, df: pd.DataFrame, levels: List[Dict]) -> pd.DataFrame:
        """
        Validate and score support/resistance levels
        """
        validated = []
        
        for level in levels:
            # Count actual touches
            touches = self._count_touches(df, level['level'], level['type'])
            
            if touches >= self.min_touches:
                level['actual_touches'] = touches
                level['score'] = self._calculate_level_score(level, touches)
                validated.append(level)
        
        # Sort by score
        validated.sort(key=lambda x: x['score'], reverse=True)
        
        return pd.DataFrame(validated)
    
    def _count_touches(self, df: pd.DataFrame, level: float, 
                      level_type: str) -> int:
        """
        Count how many times price touched a level
        """
        threshold = level * self.cluster_threshold
        touches = 0
        
        if level_type in ['support', 'both']:
            # Count times low came within threshold of level
            touches += ((df['low'] >= level - threshold) & 
                       (df['low'] <= level + threshold)).sum()
        
        if level_type in ['resistance', 'both']:
            # Count times high came within threshold of level
            touches += ((df['high'] >= level - threshold) & 
                       (df['high'] <= level + threshold)).sum()
        
        return touches
    
    def _calculate_level_score(self, level: Dict, touches: int) -> float:
        """
        Calculate strength score for a level
        """
        score = 0.0
        
        # Base score from touches
        score += min(touches * 10, 50)  # Cap at 50
        
        # Bonus for multiple detection methods
        score += len(level.get('methods', [])) * 5
        
        # Bonus for cluster strength
        score += level.get('strength', 1) * 3
        
        # Penalty for wide range (less precise)
        range_penalty = level.get('range', 0) * 100  # Convert to percentage
        score -= min(range_penalty, 10)
        
        return max(score, 0)
    
    def calculate_pivot_points(self, df: pd.DataFrame, 
                              method: str = 'traditional') -> pd.DataFrame:
        """
        Calculate pivot points
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        method : str
            Pivot calculation method ('traditional', 'fibonacci', 'camarilla', 'woodie')
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with pivot levels for each day
        """
        df = self.normalize_dataframe(df)
        
        # Group by date and calculate daily HLC
        daily_data = df.groupby(df.index.date).agg({
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'open': 'first'
        })
        
        pivots = []
        
        for date, row in daily_data.iterrows():
            if method == 'traditional':
                pivot_data = self._calculate_traditional_pivots(row)
            elif method == 'fibonacci':
                pivot_data = self._calculate_fibonacci_pivots(row)
            elif method == 'camarilla':
                pivot_data = self._calculate_camarilla_pivots(row)
            elif method == 'woodie':
                pivot_data = self._calculate_woodie_pivots(row)
            else:
                raise ValueError(f"Unknown pivot method: {method}")
            
            pivot_data['date'] = date
            pivots.append(pivot_data)
        
        return pd.DataFrame(pivots).set_index('date')
    
    def _calculate_traditional_pivots(self, row: pd.Series) -> Dict:
        """
        Calculate traditional pivot points
        """
        pp = (row['high'] + row['low'] + row['close']) / 3
        
        r1 = 2 * pp - row['low']
        r2 = pp + (row['high'] - row['low'])
        r3 = r1 + (row['high'] - row['low'])
        
        s1 = 2 * pp - row['high']
        s2 = pp - (row['high'] - row['low'])
        s3 = s1 - (row['high'] - row['low'])
        
        return {
            'pivot': pp,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        }
    
    def _calculate_fibonacci_pivots(self, row: pd.Series) -> Dict:
        """
        Calculate Fibonacci pivot points
        """
        pp = (row['high'] + row['low'] + row['close']) / 3
        range_hl = row['high'] - row['low']
        
        r1 = pp + 0.382 * range_hl
        r2 = pp + 0.618 * range_hl
        r3 = pp + 1.000 * range_hl
        
        s1 = pp - 0.382 * range_hl
        s2 = pp - 0.618 * range_hl
        s3 = pp - 1.000 * range_hl
        
        return {
            'pivot': pp,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        }
    
    def _calculate_camarilla_pivots(self, row: pd.Series) -> Dict:
        """
        Calculate Camarilla pivot points
        """
        pp = (row['high'] + row['low'] + row['close']) / 3
        range_hl = row['high'] - row['low']
        
        r4 = row['close'] + range_hl * 1.1 / 2
        r3 = row['close'] + range_hl * 1.1 / 4
        r2 = row['close'] + range_hl * 1.1 / 6
        r1 = row['close'] + range_hl * 1.1 / 12
        
        s1 = row['close'] - range_hl * 1.1 / 12
        s2 = row['close'] - range_hl * 1.1 / 6
        s3 = row['close'] - range_hl * 1.1 / 4
        s4 = row['close'] - range_hl * 1.1 / 2
        
        return {
            'pivot': pp,
            'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4,
            's1': s1, 's2': s2, 's3': s3, 's4': s4
        }
    
    def _calculate_woodie_pivots(self, row: pd.Series) -> Dict:
        """
        Calculate Woodie pivot points
        """
        pp = (row['high'] + row['low'] + 2 * row['close']) / 4
        
        r1 = 2 * pp - row['low']
        r2 = pp + row['high'] - row['low']
        
        s1 = 2 * pp - row['high']
        s2 = pp - row['high'] + row['low']
        
        return {
            'pivot': pp,
            'r1': r1, 'r2': r2,
            's1': s1, 's2': s2
        }
    
    def detect_psychological_levels(self, df: pd.DataFrame, 
                                   increment: float = 100) -> List[float]:
        """
        Detect psychological/round number levels
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        increment : float
            Round number increment (e.g., 100 for levels like 17000, 17100)
            
        Returns:
        --------
        List[float]
            List of psychological levels in the price range
        """
        df = self.normalize_dataframe(df)
        
        # Get price range
        min_price = df['low'].min()
        max_price = df['high'].max()
        
        # Find round levels within range
        start_level = np.floor(min_price / increment) * increment
        end_level = np.ceil(max_price / increment) * increment
        
        levels = []
        current = start_level
        while current <= end_level:
            if min_price <= current <= max_price:
                levels.append(current)
            current += increment
        
        return levels
    
    def detect_opening_range_levels(self, df: pd.DataFrame, 
                                   or_minutes: int = 15) -> pd.DataFrame:
        """
        Detect opening range levels for each day
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        or_minutes : int
            Minutes for opening range calculation
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with OR levels for each day
        """
        df = self.normalize_dataframe(df)
        
        or_levels = []
        
        for date, day_data in df.groupby(df.index.date):
            # Get opening range
            or_end = pd.Timestamp.combine(date, self.MARKET_OPEN) + pd.Timedelta(minutes=or_minutes)
            or_data = day_data.between_time(self.MARKET_OPEN, or_end.time())
            
            if not or_data.empty:
                or_high = or_data['high'].max()
                or_low = or_data['low'].min()
                or_mid = (or_high + or_low) / 2
                
                or_levels.append({
                    'date': date,
                    'or_high': or_high,
                    'or_low': or_low,
                    'or_mid': or_mid,
                    'or_range': or_high - or_low
                })
        
        return pd.DataFrame(or_levels).set_index('date') if or_levels else pd.DataFrame()
    
    def identify_confluence_zones(self, df: pd.DataFrame, 
                                 zone_threshold: float = 0.01) -> pd.DataFrame:
        """
        Identify zones where multiple S/R levels confluence
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        zone_threshold : float
            Threshold for considering levels in same zone
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with confluence zones
        """
        # Get all types of levels
        swing_levels = self.detect_support_resistance_zones(df, method='swings')
        pivot_levels = self.calculate_pivot_points(df)
        psych_levels = self.detect_psychological_levels(df)
        or_levels = self.detect_opening_range_levels(df)
        
        all_levels = []
        
        # Collect all levels
        if not swing_levels.empty:
            for _, row in swing_levels.iterrows():
                all_levels.append({
                    'level': row['level'],
                    'source': 'swing',
                    'type': row['type']
                })
        
        if not pivot_levels.empty:
            latest_pivots = pivot_levels.iloc[-1]
            for key in ['pivot', 'r1', 'r2', 'r3', 's1', 's2', 's3']:
                if key in latest_pivots:
                    all_levels.append({
                        'level': latest_pivots[key],
                        'source': 'pivot',
                        'type': key
                    })
        
        for level in psych_levels:
            all_levels.append({
                'level': level,
                'source': 'psychological',
                'type': 'round'
            })
        
        if not or_levels.empty:
            latest_or = or_levels.iloc[-1]
            for key in ['or_high', 'or_low', 'or_mid']:
                if key in latest_or:
                    all_levels.append({
                        'level': latest_or[key],
                        'source': 'opening_range',
                        'type': key
                    })
        
        # Find confluence zones
        if not all_levels:
            return pd.DataFrame()
        
        sorted_levels = sorted(all_levels, key=lambda x: x['level'])
        confluence_zones = []
        current_zone = [sorted_levels[0]]
        
        for level in sorted_levels[1:]:
            zone_center = np.mean([l['level'] for l in current_zone])
            if abs(level['level'] - zone_center) / zone_center < zone_threshold:
                current_zone.append(level)
            else:
                if len(current_zone) >= 2:  # At least 2 levels for confluence
                    confluence_zones.append(self._create_confluence_zone(current_zone))
                current_zone = [level]
        
        # Check last zone
        if len(current_zone) >= 2:
            confluence_zones.append(self._create_confluence_zone(current_zone))
        
        return pd.DataFrame(confluence_zones)
    
    def _create_confluence_zone(self, zone_levels: List[Dict]) -> Dict:
        """
        Create a confluence zone from multiple levels
        """
        levels = [l['level'] for l in zone_levels]
        sources = [l['source'] for l in zone_levels]
        
        return {
            'zone_center': np.mean(levels),
            'zone_high': max(levels),
            'zone_low': min(levels),
            'zone_width': max(levels) - min(levels),
            'num_levels': len(zone_levels),
            'sources': list(set(sources)),
            'strength': len(set(sources)) * len(zone_levels)
        }
    
    def detect_broken_levels(self, df: pd.DataFrame, 
                            lookback: int = 50) -> pd.DataFrame:
        """
        Detect recently broken support/resistance levels
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
        lookback : int
            Bars to look back for level breaks
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with broken levels and break details
        """
        df = self.normalize_dataframe(df)
        
        # Get S/R levels
        levels = self.detect_support_resistance_zones(df.iloc[:-lookback])
        
        if levels.empty:
            return pd.DataFrame()
        
        # Check recent price action for breaks
        recent_data = df.iloc[-lookback:]
        broken_levels = []
        
        for _, level in levels.iterrows():
            level_price = level['level']
            level_type = level['type']
            
            if level_type in ['resistance', 'both']:
                # Check for resistance break
                breaks = recent_data[recent_data['close'] > level_price * 1.002]  # 0.2% above
                if not breaks.empty:
                    first_break = breaks.index[0]
                    # Check for retest
                    post_break = recent_data[recent_data.index > first_break]
                    retest = post_break[
                        (post_break['low'] <= level_price * 1.002) & 
                        (post_break['close'] > level_price)
                    ]
                    
                    broken_levels.append({
                        'level': level_price,
                        'type': 'resistance',
                        'break_time': first_break,
                        'break_type': 'upside',
                        'retested': not retest.empty,
                        'retest_time': retest.index[0] if not retest.empty else None,
                        'held_after_retest': retest['close'].min() > level_price if not retest.empty else None
                    })
            
            if level_type in ['support', 'both']:
                # Check for support break
                breaks = recent_data[recent_data['close'] < level_price * 0.998]  # 0.2% below
                if not breaks.empty:
                    first_break = breaks.index[0]
                    # Check for retest
                    post_break = recent_data[recent_data.index > first_break]
                    retest = post_break[
                        (post_break['high'] >= level_price * 0.998) & 
                        (post_break['close'] < level_price)
                    ]
                    
                    broken_levels.append({
                        'level': level_price,
                        'type': 'support',
                        'break_time': first_break,
                        'break_type': 'downside',
                        'retested': not retest.empty,
                        'retest_time': retest.index[0] if not retest.empty else None,
                        'held_after_retest': retest['close'].max() < level_price if not retest.empty else None
                    })
        
        return pd.DataFrame(broken_levels) if broken_levels else pd.DataFrame()