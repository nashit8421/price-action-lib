"""Multi-timeframe analysis module"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from ..core.timeframe import TimeFrameManager
from ..patterns.candlestick import CandlestickPatterns
from ..structures.market_structure import MarketStructure
from ..core.base import BaseAnalyzer


class MultiTimeframeAnalysis(BaseAnalyzer):
    """Analyze price action across multiple timeframes"""
    
    def __init__(self, timeframes: List[str] = None):
        """
        Initialize MultiTimeframeAnalysis
        
        Parameters:
        -----------
        timeframes : List[str]
            List of timeframes to analyze
        """
        super().__init__()
        self.timeframes = timeframes or ['5min', '15min', '1H', '1D']
        self.tf_manager = TimeFrameManager()
        self.candlestick_analyzer = CandlestickPatterns()
        self.structure_analyzer = MarketStructure()
    
    def analyze_multiple_timeframes(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Perform comprehensive multi-timeframe analysis
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with 1-minute OHLCV data
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            Analysis results for each timeframe
        """
        df = self.normalize_dataframe(df)
        
        results = {}
        
        # Create multiple timeframe data
        mtf_data = self.tf_manager.create_multiple_timeframes(df, self.timeframes)
        
        for timeframe, tf_data in mtf_data.items():
            if not tf_data.empty:
                results[timeframe] = self._analyze_single_timeframe(tf_data, timeframe)
        
        return results
    
    def _analyze_single_timeframe(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """
        Analyze a single timeframe
        """
        analysis = {
            'timeframe': timeframe,
            'data_points': len(df),
            'date_range': {
                'start': df.index[0],
                'end': df.index[-1]
            }
        }
        
        # Market structure
        try:
            structure = self.structure_analyzer.identify_market_structure(df)
            analysis['structure'] = {
                'current_trend': structure['trend'].iloc[-1] if not structure.empty else 'unknown',
                'trend_changes': (structure['trend'].diff() != 0).sum(),
                'bos_signals': (structure['bos'] != '').sum(),
                'choch_signals': (structure['choch'] != '').sum()
            }
        except Exception:
            analysis['structure'] = {'error': 'Could not analyze structure'}
        
        # Key levels
        try:
            from ..structures.support_resistance import SupportResistance
            sr_analyzer = SupportResistance()
            levels = sr_analyzer.detect_support_resistance_zones(df)
            analysis['key_levels'] = {
                'total_levels': len(levels),
                'support_levels': len(levels[levels['type'].isin(['support', 'both'])]) if not levels.empty else 0,
                'resistance_levels': len(levels[levels['type'].isin(['resistance', 'both'])]) if not levels.empty else 0
            }
        except Exception:
            analysis['key_levels'] = {'error': 'Could not detect levels'}
        
        # Candlestick patterns
        try:
            patterns = self.candlestick_analyzer.detect_all_patterns(df)
            pattern_count = {}
            for col in patterns.columns:
                if col not in ['open', 'high', 'low', 'close', 'volume']:
                    if patterns[col].dtype == 'bool':
                        pattern_count[col] = patterns[col].sum()
                    else:
                        pattern_count[col] = (patterns[col] != '').sum()
            
            analysis['candlestick_patterns'] = pattern_count
        except Exception:
            analysis['candlestick_patterns'] = {'error': 'Could not detect patterns'}
        
        # Volatility metrics
        analysis['volatility'] = self._calculate_volatility_metrics(df)
        
        return analysis
    
    def _calculate_volatility_metrics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate volatility metrics for timeframe
        """
        try:
            returns = df['close'].pct_change().dropna()
            atr = self.calculate_atr(df)
            
            return {
                'price_volatility': returns.std() * np.sqrt(len(returns)) if len(returns) > 1 else 0,
                'avg_atr': atr.mean() if not atr.empty else 0,
                'current_atr': atr.iloc[-1] if not atr.empty else 0,
                'atr_pct': (atr.iloc[-1] / df['close'].iloc[-1] * 100) if not atr.empty and df['close'].iloc[-1] != 0 else 0
            }
        except Exception:
            return {'error': 'Could not calculate volatility'}
    
    def find_timeframe_confluences(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Find confluences across timeframes
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with 1-minute OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            Confluence points across timeframes
        """
        df = self.normalize_dataframe(df)
        
        confluences = []
        
        # Get multi-timeframe data
        mtf_data = self.tf_manager.create_multiple_timeframes(df, self.timeframes)
        
        # Analyze each timeframe for key levels
        tf_levels = {}
        for timeframe, tf_data in mtf_data.items():
            if not tf_data.empty:
                try:
                    from ..structures.support_resistance import SupportResistance
                    sr_analyzer = SupportResistance()
                    levels = sr_analyzer.detect_support_resistance_zones(tf_data)
                    tf_levels[timeframe] = levels
                except Exception:
                    continue
        
        # Find price levels that appear in multiple timeframes
        all_levels = []
        for timeframe, levels_df in tf_levels.items():
            if not levels_df.empty:
                for _, level in levels_df.iterrows():
                    all_levels.append({
                        'timeframe': timeframe,
                        'level': level['level'],
                        'type': level['type'],
                        'strength': level.get('score', 0)
                    })
        
        if not all_levels:
            return pd.DataFrame()
        
        # Group nearby levels (within 0.5%)
        all_levels.sort(key=lambda x: x['level'])
        
        i = 0
        while i < len(all_levels):
            level_group = [all_levels[i]]
            j = i + 1
            
            while j < len(all_levels):
                if abs(all_levels[j]['level'] - level_group[0]['level']) / level_group[0]['level'] < 0.005:
                    level_group.append(all_levels[j])
                    j += 1
                else:
                    break
            
            if len(level_group) >= 2:  # Confluence requires at least 2 timeframes
                confluences.append({
                    'price_level': np.mean([lg['level'] for lg in level_group]),
                    'timeframes': [lg['timeframe'] for lg in level_group],
                    'num_timeframes': len(level_group),
                    'avg_strength': np.mean([lg['strength'] for lg in level_group]),
                    'level_types': list(set([lg['type'] for lg in level_group]))
                })
            
            i = j
        
        return pd.DataFrame(confluences) if confluences else pd.DataFrame()
    
    def get_higher_timeframe_context(self, df: pd.DataFrame, 
                                   reference_timeframe: str = '15min') -> Dict:
        """
        Get higher timeframe context for lower timeframe analysis
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with 1-minute OHLCV data
        reference_timeframe : str
            Reference timeframe for analysis
            
        Returns:
        --------
        Dict
            Higher timeframe context
        """
        df = self.normalize_dataframe(df)
        
        # Define timeframe hierarchy
        tf_hierarchy = {
            '1min': ['5min', '15min', '1H', '1D'],
            '3min': ['15min', '1H', '1D'],
            '5min': ['15min', '1H', '1D'],
            '15min': ['1H', '1D'],
            '1H': ['1D'],
            '1D': []
        }
        
        higher_timeframes = tf_hierarchy.get(reference_timeframe, ['1H', '1D'])
        
        if not higher_timeframes:
            return {'message': 'No higher timeframes available'}
        
        context = {}
        
        for htf in higher_timeframes:
            try:
                htf_data = self.tf_manager.resample_ohlcv(df, htf)
                
                if not htf_data.empty:
                    # Get trend direction
                    structure = self.structure_analyzer.identify_market_structure(htf_data)
                    current_trend = structure['trend'].iloc[-1] if not structure.empty else 'unknown'
                    
                    # Get key levels
                    from ..structures.support_resistance import SupportResistance
                    sr_analyzer = SupportResistance()
                    levels = sr_analyzer.detect_support_resistance_zones(htf_data)
                    
                    # Current price position
                    current_price = htf_data['close'].iloc[-1]
                    
                    context[htf] = {
                        'trend': current_trend,
                        'current_price': current_price,
                        'key_levels_count': len(levels) if not levels.empty else 0,
                        'price_vs_range': self._calculate_price_position(htf_data),
                        'recent_high': htf_data['high'].tail(10).max(),
                        'recent_low': htf_data['low'].tail(10).min()
                    }
                    
                    # Find nearest support/resistance
                    if not levels.empty:
                        resistance_levels = levels[levels['type'].isin(['resistance', 'both'])]
                        support_levels = levels[levels['type'].isin(['support', 'both'])]
                        
                        nearest_resistance = None
                        nearest_support = None
                        
                        if not resistance_levels.empty:
                            above_price = resistance_levels[resistance_levels['level'] > current_price]
                            if not above_price.empty:
                                nearest_resistance = above_price['level'].min()
                        
                        if not support_levels.empty:
                            below_price = support_levels[support_levels['level'] < current_price]
                            if not below_price.empty:
                                nearest_support = below_price['level'].max()
                        
                        context[htf]['nearest_resistance'] = nearest_resistance
                        context[htf]['nearest_support'] = nearest_support
            
            except Exception as e:
                context[htf] = {'error': str(e)}
        
        return context
    
    def _calculate_price_position(self, df: pd.DataFrame, lookback: int = 50) -> Dict:
        """
        Calculate current price position relative to recent range
        """
        if len(df) < lookback:
            lookback = len(df)
        
        recent_data = df.tail(lookback)
        range_high = recent_data['high'].max()
        range_low = recent_data['low'].min()
        current_price = df['close'].iloc[-1]
        
        if range_high == range_low:
            position_pct = 50.0
        else:
            position_pct = ((current_price - range_low) / (range_high - range_low)) * 100
        
        return {
            'range_high': range_high,
            'range_low': range_low,
            'position_pct': position_pct,
            'position_description': (
                'premium' if position_pct > 70 else
                'discount' if position_pct < 30 else
                'neutral'
            )
        }
    
    def generate_mtf_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate comprehensive multi-timeframe summary
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with 1-minute OHLCV data
            
        Returns:
        --------
        Dict
            Multi-timeframe summary
        """
        mtf_analysis = self.analyze_multiple_timeframes(df)
        confluences = self.find_timeframe_confluences(df)
        
        summary = {
            'analysis_timestamp': pd.Timestamp.now(),
            'timeframes_analyzed': list(mtf_analysis.keys()),
            'total_confluences': len(confluences),
            'trend_alignment': self._check_trend_alignment(mtf_analysis),
            'key_insights': self._extract_key_insights(mtf_analysis, confluences)
        }
        
        return summary
    
    def _check_trend_alignment(self, mtf_analysis: Dict) -> Dict:
        """
        Check if trends are aligned across timeframes
        """
        trends = {}
        
        for timeframe, analysis in mtf_analysis.items():
            if 'structure' in analysis and 'current_trend' in analysis['structure']:
                trends[timeframe] = analysis['structure']['current_trend']
        
        if not trends:
            return {'aligned': False, 'message': 'No trend data available'}
        
        trend_values = list(trends.values())
        most_common_trend = max(set(trend_values), key=trend_values.count)
        alignment_pct = (trend_values.count(most_common_trend) / len(trend_values)) * 100
        
        return {
            'aligned': alignment_pct >= 70,
            'dominant_trend': most_common_trend,
            'alignment_percentage': alignment_pct,
            'trend_by_timeframe': trends
        }
    
    def _extract_key_insights(self, mtf_analysis: Dict, confluences: pd.DataFrame) -> List[str]:
        """
        Extract key insights from multi-timeframe analysis
        """
        insights = []
        
        # Trend insights
        trend_alignment = self._check_trend_alignment(mtf_analysis)
        if trend_alignment['aligned']:
            insights.append(f"Strong trend alignment: {trend_alignment['dominant_trend']} across {trend_alignment['alignment_percentage']:.0f}% of timeframes")
        
        # Confluence insights
        if not confluences.empty:
            strong_confluences = confluences[confluences['num_timeframes'] >= 3]
            if not strong_confluences.empty:
                insights.append(f"Found {len(strong_confluences)} strong confluence zones with 3+ timeframe agreement")
        
        # Pattern insights
        total_patterns = 0
        for tf, analysis in mtf_analysis.items():
            if 'candlestick_patterns' in analysis and isinstance(analysis['candlestick_patterns'], dict):
                tf_patterns = sum(v for v in analysis['candlestick_patterns'].values() if isinstance(v, (int, float)))
                total_patterns += tf_patterns
        
        if total_patterns > 10:
            insights.append(f"High pattern activity detected: {total_patterns} patterns across all timeframes")
        
        return insights