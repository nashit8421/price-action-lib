"""Gap analysis module"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from ..core.base import BaseAnalyzer


class GapAnalysis(BaseAnalyzer):
    """Analyze price gaps and their characteristics"""
    
    def __init__(self, min_gap_size: float = 0.002):
        """
        Initialize GapAnalysis
        
        Parameters:
        -----------
        min_gap_size : float
            Minimum gap size as percentage for detection
        """
        super().__init__()
        self.min_gap_size = min_gap_size
    
    def detect_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect all types of gaps
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with gap information
        """
        df = self.normalize_dataframe(df)
        gaps = []
        
        for i in range(1, len(df)):
            prev_high = df['high'].iloc[i-1]
            prev_low = df['low'].iloc[i-1]
            curr_high = df['high'].iloc[i]
            curr_low = df['low'].iloc[i]
            curr_close = df['close'].iloc[i]
            
            # Gap up - current low > previous high
            if curr_low > prev_high:
                gap_size = curr_low - prev_high
                gap_pct = gap_size / prev_high
                
                if gap_pct >= self.min_gap_size:
                    gaps.append({
                        'timestamp': df.index[i],
                        'gap_type': 'gap_up',
                        'gap_size': gap_size,
                        'gap_pct': gap_pct * 100,
                        'gap_high': curr_low,
                        'gap_low': prev_high,
                        'previous_close': df['close'].iloc[i-1],
                        'current_open': df['open'].iloc[i],
                        'filled': False,
                        'fill_date': None,
                        'classification': self._classify_gap_type(df, i, 'gap_up')
                    })
            
            # Gap down - current high < previous low
            elif curr_high < prev_low:
                gap_size = prev_low - curr_high
                gap_pct = gap_size / prev_low
                
                if gap_pct >= self.min_gap_size:
                    gaps.append({
                        'timestamp': df.index[i],
                        'gap_type': 'gap_down',
                        'gap_size': gap_size,
                        'gap_pct': gap_pct * 100,
                        'gap_high': prev_low,
                        'gap_low': curr_high,
                        'previous_close': df['close'].iloc[i-1],
                        'current_open': df['open'].iloc[i],
                        'filled': False,
                        'fill_date': None,
                        'classification': self._classify_gap_type(df, i, 'gap_down')
                    })
        
        gaps_df = pd.DataFrame(gaps)
        
        # Check which gaps were filled
        if not gaps_df.empty:
            gaps_df = self._check_gap_fills(df, gaps_df)
        
        return gaps_df
    
    def _classify_gap_type(self, df: pd.DataFrame, gap_index: int, gap_direction: str) -> str:
        """
        Classify gap type (Common, Breakaway, Runaway, Exhaustion)
        """
        # Get context around gap
        lookback = min(20, gap_index)
        context = df.iloc[gap_index-lookback:gap_index]
        
        if context.empty:
            return 'common'
        
        # Calculate trend strength before gap
        price_change = (context['close'].iloc[-1] - context['close'].iloc[0]) / context['close'].iloc[0]
        volatility = context['close'].std() / context['close'].mean()
        
        # Volume analysis if available
        has_volume = 'volume' in df.columns
        volume_spike = False
        if has_volume:
            avg_volume = context['volume'].mean()
            current_volume = df['volume'].iloc[gap_index]
            volume_spike = current_volume > avg_volume * 2
        
        # Classification logic
        if abs(price_change) < 0.02:  # Weak trend
            return 'common'
        elif volume_spike and abs(price_change) > 0.05:  # Strong trend with volume
            if gap_index > 50:
                recent_gaps = self._count_recent_gaps(df, gap_index, 20)
                if recent_gaps >= 2:
                    return 'exhaustion'
                else:
                    return 'breakaway'
            else:
                return 'breakaway'
        elif abs(price_change) > 0.05 and not volume_spike:
            return 'runaway'
        else:
            return 'common'
    
    def _count_recent_gaps(self, df: pd.DataFrame, current_index: int, lookback: int) -> int:
        """
        Count gaps in recent period
        """
        start_idx = max(0, current_index - lookback)
        recent_section = df.iloc[start_idx:current_index]
        
        gap_count = 0
        for i in range(1, len(recent_section)):
            prev_high = recent_section['high'].iloc[i-1]
            prev_low = recent_section['low'].iloc[i-1]
            curr_high = recent_section['high'].iloc[i]
            curr_low = recent_section['low'].iloc[i]
            
            if curr_low > prev_high or curr_high < prev_low:
                gap_count += 1
        
        return gap_count
    
    def _check_gap_fills(self, df: pd.DataFrame, gaps_df: pd.DataFrame) -> pd.DataFrame:
        """
        Check which gaps have been filled
        """
        for idx, gap in gaps_df.iterrows():
            gap_timestamp = gap['timestamp']
            gap_high = gap['gap_high']
            gap_low = gap['gap_low']
            
            # Look at future data
            future_data = df[df.index > gap_timestamp]
            
            if not future_data.empty:
                if gap['gap_type'] == 'gap_up':
                    # Gap up is filled when price trades back into gap zone
                    fill_bars = future_data[future_data['low'] <= gap_high]
                else:  # gap_down
                    # Gap down is filled when price trades back into gap zone
                    fill_bars = future_data[future_data['high'] >= gap_low]
                
                if not fill_bars.empty:
                    fill_date = fill_bars.index[0]
                    gaps_df.at[idx, 'filled'] = True
                    gaps_df.at[idx, 'fill_date'] = fill_date
                    gaps_df.at[idx, 'days_to_fill'] = (fill_date - gap_timestamp).days
        
        return gaps_df
    
    def analyze_gap_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Generate gap statistics
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with OHLCV data
            
        Returns:
        --------
        Dict
            Gap statistics
        """
        gaps = self.detect_gaps(df)
        
        if gaps.empty:
            return {'total_gaps': 0}
        
        stats = {
            'total_gaps': len(gaps),
            'gap_up_count': (gaps['gap_type'] == 'gap_up').sum(),
            'gap_down_count': (gaps['gap_type'] == 'gap_down').sum(),
            'filled_gaps': gaps['filled'].sum(),
            'fill_rate': gaps['filled'].mean() * 100,
            'avg_gap_size_pct': gaps['gap_pct'].mean(),
            'max_gap_size_pct': gaps['gap_pct'].max(),
            'gap_classifications': gaps['classification'].value_counts().to_dict()
        }
        
        if gaps['filled'].sum() > 0:
            filled_gaps = gaps[gaps['filled']]
            stats['avg_days_to_fill'] = filled_gaps['days_to_fill'].mean()
            stats['max_days_to_fill'] = filled_gaps['days_to_fill'].max()
        
        return stats