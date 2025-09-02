"""Main API interface for Price Action Library"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from .core.timeframe import TimeFrameManager
from .patterns.candlestick import CandlestickPatterns
from .patterns.chart_patterns import ChartPatterns
from .structures.support_resistance import SupportResistance
from .structures.market_structure import MarketStructure
from .analysis.volume_analysis import VolumeAnalysis
from .analysis.gap_analysis import GapAnalysis
from .analysis.session_analysis import SessionAnalysis
from .analysis.multi_timeframe import MultiTimeframeAnalysis


class PriceActionAnalyzer:
    """
    Main interface for Price Action Library
    
    This class provides a unified interface to all price action analysis capabilities.
    Takes OHLCV data as input and provides comprehensive price action analysis.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize Price Action Analyzer
        
        Parameters:
        -----------
        **kwargs : dict
            Configuration parameters for individual analyzers
        """
        # Initialize all analyzers
        self.timeframe_manager = TimeFrameManager()
        self.candlestick_analyzer = CandlestickPatterns(**kwargs.get('candlestick_params', {}))
        self.chart_pattern_analyzer = ChartPatterns(**kwargs.get('chart_pattern_params', {}))
        self.support_resistance_analyzer = SupportResistance(**kwargs.get('sr_params', {}))
        self.market_structure_analyzer = MarketStructure(**kwargs.get('structure_params', {}))
        self.volume_analyzer = VolumeAnalysis(**kwargs.get('volume_params', {}))
        self.gap_analyzer = GapAnalysis(**kwargs.get('gap_params', {}))
        self.session_analyzer = SessionAnalysis()
        self.mtf_analyzer = MultiTimeframeAnalysis(**kwargs.get('mtf_params', {}))
    
    def analyze(self, df: pd.DataFrame, 
                analysis_type: str = 'comprehensive',
                timeframes: List[str] = None) -> Dict:
        """
        Main analysis method
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data with DateTime index (1-minute timeframe assumed)
        analysis_type : str
            Type of analysis ('comprehensive', 'patterns', 'structure', 'volume', 'quick')
        timeframes : List[str]
            Timeframes for multi-timeframe analysis
            
        Returns:
        --------
        Dict
            Comprehensive analysis results
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty")
        
        results = {
            'analysis_timestamp': pd.Timestamp.now(),
            'data_info': {
                'total_bars': len(df),
                'date_range': {
                    'start': df.index[0],
                    'end': df.index[-1]
                },
                'timeframe': self._detect_timeframe(df)
            }
        }
        
        if analysis_type in ['comprehensive', 'patterns']:
            results['candlestick_patterns'] = self._analyze_candlestick_patterns(df)
            results['chart_patterns'] = self._analyze_chart_patterns(df)
        
        if analysis_type in ['comprehensive', 'structure']:
            results['support_resistance'] = self._analyze_support_resistance(df)
            results['market_structure'] = self._analyze_market_structure(df)
        
        if analysis_type in ['comprehensive', 'volume']:
            results['volume_analysis'] = self._analyze_volume(df)
        
        if analysis_type == 'comprehensive':
            results['gap_analysis'] = self._analyze_gaps(df)
            results['session_analysis'] = self._analyze_sessions(df)
            
            # Multi-timeframe analysis
            if timeframes:
                results['multi_timeframe'] = self._analyze_multiple_timeframes(df, timeframes)
        
        elif analysis_type == 'quick':
            results['quick_summary'] = self._quick_analysis(df)
        
        return results
    
    def _detect_timeframe(self, df: pd.DataFrame) -> str:
        """
        Detect the timeframe of input data
        """
        if len(df) < 2:
            return 'unknown'
        
        time_diff = df.index[1] - df.index[0]
        
        if time_diff.total_seconds() <= 60:
            return '1min'
        elif time_diff.total_seconds() <= 180:
            return '3min'
        elif time_diff.total_seconds() <= 300:
            return '5min'
        elif time_diff.total_seconds() <= 900:
            return '15min'
        elif time_diff.total_seconds() <= 1800:
            return '30min'
        elif time_diff.total_seconds() <= 3600:
            return '1H'
        else:
            return 'daily_or_higher'
    
    def _analyze_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze candlestick patterns"""
        try:
            patterns = self.candlestick_analyzer.detect_all_patterns(df)
            signals = self.candlestick_analyzer.get_pattern_signals(df)
            
            return {
                'patterns_detected': self._count_pattern_occurrences(patterns),
                'recent_signals': signals.tail(10).to_dict('records') if len(signals) > 0 else [],
                'total_patterns': len(signals),
                'bullish_signals': len(signals[signals['bias'] == 'bullish']) if len(signals) > 0 else 0,
                'bearish_signals': len(signals[signals['bias'] == 'bearish']) if len(signals) > 0 else 0
            }
        except Exception as e:
            return {'error': f'Candlestick analysis failed: {str(e)}'}
    
    def _analyze_chart_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze chart patterns"""
        try:
            patterns = self.chart_pattern_analyzer.detect_all_patterns(df)
            
            return {
                'patterns_found': len(patterns),
                'pattern_details': patterns.to_dict('records') if len(patterns) > 0 else [],
                'pattern_types': patterns['pattern'].value_counts().to_dict() if len(patterns) > 0 else {}
            }
        except Exception as e:
            return {'error': f'Chart pattern analysis failed: {str(e)}'}
    
    def _analyze_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Analyze support and resistance levels"""
        try:
            levels = self.support_resistance_analyzer.detect_support_resistance_zones(df)
            confluences = self.support_resistance_analyzer.identify_confluence_zones(df)
            
            return {
                'total_levels': len(levels),
                'support_levels': len(levels[levels['type'].isin(['support', 'both'])]) if len(levels) > 0 else 0,
                'resistance_levels': len(levels[levels['type'].isin(['resistance', 'both'])]) if len(levels) > 0 else 0,
                'key_levels': levels.head(10).to_dict('records') if len(levels) > 0 else [],
                'confluence_zones': len(confluences),
                'strongest_confluences': confluences.head(5).to_dict('records') if len(confluences) > 0 else []
            }
        except Exception as e:
            return {'error': f'Support/Resistance analysis failed: {str(e)}'}
    
    def _analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        """Analyze market structure"""
        try:
            structure = self.market_structure_analyzer.identify_market_structure(df)
            fvgs = self.market_structure_analyzer.detect_fair_value_gaps(df)
            order_blocks = self.market_structure_analyzer.detect_order_blocks(df)
            
            current_trend = structure['trend'].iloc[-1] if len(structure) > 0 else 'unknown'
            trend_strength = structure['trend_strength'].iloc[-1] if len(structure) > 0 else 0
            
            return {
                'current_trend': current_trend,
                'trend_strength': trend_strength,
                'structure_breaks': (structure['bos'] != '').sum() if len(structure) > 0 else 0,
                'character_changes': (structure['choch'] != '').sum() if len(structure) > 0 else 0,
                'fair_value_gaps': len(fvgs),
                'unfilled_fvgs': len(fvgs[~fvgs['filled']]) if len(fvgs) > 0 else 0,
                'order_blocks': len(order_blocks),
                'recent_fvgs': fvgs.tail(5).to_dict('records') if len(fvgs) > 0 else []
            }
        except Exception as e:
            return {'error': f'Market structure analysis failed: {str(e)}'}
    
    def _analyze_volume(self, df: pd.DataFrame) -> Dict:
        """Analyze volume patterns"""
        try:
            volume_analysis = self.volume_analyzer.analyze_volume_patterns(df)
            volume_summary = self.volume_analyzer.detect_volume_patterns_summary(df)
            
            return {
                'volume_summary': volume_summary,
                'high_volume_bars': (volume_analysis['volume_class'] == 'high').sum(),
                'volume_spikes': volume_analysis['volume_spike'].sum(),
                'volume_climax': (volume_analysis['volume_climax'] != '').sum(),
                'current_relative_volume': volume_analysis['relative_volume'].iloc[-1] if len(volume_analysis) > 0 else 0
            }
        except Exception as e:
            return {'error': f'Volume analysis failed: {str(e)}'}
    
    def _analyze_gaps(self, df: pd.DataFrame) -> Dict:
        """Analyze gaps"""
        try:
            gaps = self.gap_analyzer.detect_gaps(df)
            gap_stats = self.gap_analyzer.analyze_gap_statistics(df)
            
            return {
                'total_gaps': len(gaps),
                'recent_gaps': gaps.tail(5).to_dict('records') if len(gaps) > 0 else [],
                'gap_statistics': gap_stats
            }
        except Exception as e:
            return {'error': f'Gap analysis failed: {str(e)}'}
    
    def _analyze_sessions(self, df: pd.DataFrame) -> Dict:
        """Analyze session patterns"""
        try:
            opening_analysis = self.session_analyzer.analyze_opening_session(df)
            closing_analysis = self.session_analyzer.analyze_closing_session(df)
            session_chars = self.session_analyzer.analyze_session_characteristics(df)
            
            return {
                'opening_patterns': opening_analysis.tail(5).to_dict('records') if len(opening_analysis) > 0 else [],
                'closing_patterns': closing_analysis.tail(5).to_dict('records') if len(closing_analysis) > 0 else [],
                'session_characteristics': session_chars
            }
        except Exception as e:
            return {'error': f'Session analysis failed: {str(e)}'}
    
    def _analyze_multiple_timeframes(self, df: pd.DataFrame, timeframes: List[str]) -> Dict:
        """Analyze multiple timeframes"""
        try:
            mtf_analyzer = MultiTimeframeAnalysis(timeframes)
            mtf_analysis = mtf_analyzer.analyze_multiple_timeframes(df)
            confluences = mtf_analyzer.find_timeframe_confluences(df)
            
            return {
                'timeframe_analysis': mtf_analysis,
                'confluences': confluences.to_dict('records') if len(confluences) > 0 else [],
                'summary': mtf_analyzer.generate_mtf_summary(df)
            }
        except Exception as e:
            return {'error': f'Multi-timeframe analysis failed: {str(e)}'}
    
    def _quick_analysis(self, df: pd.DataFrame) -> Dict:
        """Quick analysis for fast insights"""
        try:
            current_price = df['close'].iloc[-1]
            
            # Quick trend assessment
            ma_20 = df['close'].rolling(20).mean().iloc[-1] if len(df) >= 20 else current_price
            ma_50 = df['close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else current_price
            
            trend = 'bullish' if current_price > ma_20 > ma_50 else 'bearish' if current_price < ma_20 < ma_50 else 'neutral'
            
            # Quick volatility check
            atr = self.support_resistance_analyzer.calculate_atr(df).iloc[-1] if len(df) >= 14 else 0
            atr_pct = (atr / current_price * 100) if current_price > 0 else 0
            
            # Recent range
            recent_high = df['high'].tail(20).max()
            recent_low = df['low'].tail(20).min()
            range_position = ((current_price - recent_low) / (recent_high - recent_low) * 100) if recent_high != recent_low else 50
            
            return {
                'current_price': current_price,
                'trend_assessment': trend,
                'volatility_pct': atr_pct,
                'range_position_pct': range_position,
                'recent_high': recent_high,
                'recent_low': recent_low,
                'price_zone': 'premium' if range_position > 70 else 'discount' if range_position < 30 else 'neutral'
            }
        except Exception as e:
            return {'error': f'Quick analysis failed: {str(e)}'}
    
    def _count_pattern_occurrences(self, patterns_df: pd.DataFrame) -> Dict:
        """Count pattern occurrences"""
        pattern_counts = {}
        
        for col in patterns_df.columns:
            if col not in ['open', 'high', 'low', 'close', 'volume']:
                if patterns_df[col].dtype == 'bool':
                    pattern_counts[col] = patterns_df[col].sum()
                elif patterns_df[col].dtype == 'object':
                    pattern_counts[col] = (patterns_df[col] != '').sum()
        
        return pattern_counts
    
    # Convenience methods for specific analyses
    
    def detect_candlestick_patterns(self, df: pd.DataFrame, 
                                  pattern_type: str = 'all') -> pd.DataFrame:
        """
        Detect candlestick patterns
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data
        pattern_type : str
            Pattern type to detect ('all', 'single', 'double', 'triple')
            
        Returns:
        --------
        pd.DataFrame
            Pattern detection results
        """
        return self.candlestick_analyzer.get_pattern_signals(df, pattern_type)
    
    def find_support_resistance(self, df: pd.DataFrame, 
                               method: str = 'swings') -> pd.DataFrame:
        """
        Find support and resistance levels
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data
        method : str
            Detection method ('swings', 'volume', 'fractals')
            
        Returns:
        --------
        pd.DataFrame
            Support/resistance levels
        """
        return self.support_resistance_analyzer.detect_support_resistance_zones(df, method)
    
    def analyze_market_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze market structure
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            Market structure analysis
        """
        return self.market_structure_analyzer.identify_market_structure(df)
    
    def resample_timeframe(self, df: pd.DataFrame, 
                          timeframe: str) -> pd.DataFrame:
        """
        Resample to different timeframe
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data
        timeframe : str
            Target timeframe
            
        Returns:
        --------
        pd.DataFrame
            Resampled data
        """
        return self.timeframe_manager.resample_ohlcv(df, timeframe)
    
    def detect_chart_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect chart patterns
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            Chart patterns
        """
        return self.chart_pattern_analyzer.detect_all_patterns(df)
    
    def analyze_volume(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze volume patterns
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            Volume analysis
        """
        return self.volume_analyzer.analyze_volume_patterns(df)
    
    def detect_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect price gaps
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            Gap analysis
        """
        return self.gap_analyzer.detect_gaps(df)
    
    def get_multi_timeframe_analysis(self, df: pd.DataFrame, 
                                   timeframes: List[str] = None) -> Dict:
        """
        Get multi-timeframe analysis
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data (1-minute assumed)
        timeframes : List[str]
            Timeframes to analyze
            
        Returns:
        --------
        Dict
            Multi-timeframe analysis
        """
        mtf_analyzer = MultiTimeframeAnalysis(timeframes)
        return mtf_analyzer.analyze_multiple_timeframes(df)
    
    def find_price_action_setups(self, df: pd.DataFrame, 
                               setup_type: str = 'all') -> pd.DataFrame:
        """
        Find price action setups
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data
        setup_type : str
            Type of setup ('all', 'pin_bar', 'inside_bar', 'outside_bar', 'fakey', 'spring', 'upthrust')
            
        Returns:
        --------
        pd.DataFrame
            Price action setups
        """
        return self.market_structure_analyzer.detect_price_action_setups(df, setup_type)
    
    def identify_breakouts(self, df: pd.DataFrame, 
                         lookback: int = 20) -> pd.DataFrame:
        """
        Identify breakout patterns
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data
        lookback : int
            Lookback period for breakout detection
            
        Returns:
        --------
        pd.DataFrame
            Breakout patterns
        """
        return self.volume_analyzer.analyze_breakout_volume(df, lookback)
    
    def fetch_all(self, df: pd.DataFrame, 
                 include_ohlcv: bool = True,
                 include_metadata: bool = True) -> pd.DataFrame:
        """
        Fetch all price action analysis results in a single comprehensive DataFrame
        
        This function consolidates all price action analysis into one DataFrame with
        all pattern detections, structure analysis, support/resistance levels, 
        volume analysis, and more as additional columns.
        
        Parameters:
        -----------
        df : pd.DataFrame
            OHLCV data with DateTime index
        include_ohlcv : bool, default True
            Whether to include original OHLCV columns in output
        include_metadata : bool, default True
            Whether to include metadata columns (ATR, volatility, etc.)
            
        Returns:
        --------
        pd.DataFrame
            Comprehensive DataFrame with all price action analysis results
            Index: DateTime (same as input)
            Columns: OHLCV + all pattern detections + structure analysis + levels
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty")
        
        # Start with base DataFrame
        if include_ohlcv:
            result_df = df.copy()
        else:
            result_df = pd.DataFrame(index=df.index)
        
        try:
            # 1. CANDLESTICK PATTERNS
            print("Processing candlestick patterns...")
            candlestick_patterns = self.candlestick_analyzer.detect_all_patterns(df)
            
            # Add candlestick pattern columns
            for col in candlestick_patterns.columns:
                if col not in ['open', 'high', 'low', 'close', 'volume']:
                    result_df[f'pattern_{col}'] = candlestick_patterns[col]
            
            # 2. CHART PATTERNS
            print("Processing chart patterns...")
            chart_patterns = self.chart_pattern_analyzer.detect_all_patterns(df)
            
            # Create chart pattern indicator columns
            chart_pattern_cols = {}
            pattern_types = ['head_and_shoulders', 'inverse_head_and_shoulders', 
                           'double_top', 'double_bottom', 'triangle', 'wedge', 
                           'flag', 'pennant', 'rectangle', 'cup_and_handle',
                           'rounding_top', 'rounding_bottom', 'v_top', 'v_bottom']
            
            for pattern_type in pattern_types:
                chart_pattern_cols[f'chart_{pattern_type}'] = pd.Series(index=df.index, dtype=bool)
                chart_pattern_cols[f'chart_{pattern_type}'][:] = False
            
            # Mark pattern occurrences
            if not chart_patterns.empty:
                for _, pattern in chart_patterns.iterrows():
                    pattern_name = f"chart_{pattern['pattern']}"
                    if pattern_name in chart_pattern_cols:
                        start_idx = pattern.get('start_idx', 0) 
                        end_idx = pattern.get('end_idx', len(df)-1)
                        if start_idx < len(df) and end_idx < len(df):
                            chart_pattern_cols[pattern_name].iloc[start_idx:end_idx+1] = True
            
            # Add to result
            for col, series in chart_pattern_cols.items():
                result_df[col] = series
            
            # 3. MARKET STRUCTURE
            print("Processing market structure...")
            market_structure = self.market_structure_analyzer.identify_market_structure(df)
            
            # Add market structure columns
            structure_cols = ['trend', 'trend_strength', 'swing_high', 'swing_low', 
                            'bos', 'choch', 'higher_high', 'higher_low', 
                            'lower_high', 'lower_low']
            
            for col in structure_cols:
                if col in market_structure.columns:
                    result_df[f'structure_{col}'] = market_structure[col]
            
            # 4. FAIR VALUE GAPS
            print("Processing Fair Value Gaps...")
            fvgs = self.market_structure_analyzer.detect_fair_value_gaps(df)
            
            # Create FVG indicator columns
            result_df['fvg_bullish'] = pd.Series(index=df.index, dtype=bool)
            result_df['fvg_bearish'] = pd.Series(index=df.index, dtype=bool)
            result_df['fvg_bullish'][:] = False
            result_df['fvg_bearish'][:] = False
            
            # Mark FVG occurrences
            if not fvgs.empty:
                for _, fvg in fvgs.iterrows():
                    timestamp = fvg['timestamp']
                    if timestamp in result_df.index:
                        if fvg['type'] == 'bullish_fvg':
                            result_df.loc[timestamp, 'fvg_bullish'] = True
                        elif fvg['type'] == 'bearish_fvg':
                            result_df.loc[timestamp, 'fvg_bearish'] = True
            
            # 5. ORDER BLOCKS
            print("Processing Order Blocks...")
            order_blocks = self.market_structure_analyzer.detect_order_blocks(df)
            
            # Create Order Block indicator columns
            result_df['order_block_bullish'] = pd.Series(index=df.index, dtype=bool)
            result_df['order_block_bearish'] = pd.Series(index=df.index, dtype=bool)
            result_df['order_block_bullish'][:] = False
            result_df['order_block_bearish'][:] = False
            
            # Mark Order Block occurrences
            if not order_blocks.empty:
                for _, ob in order_blocks.iterrows():
                    timestamp = ob['timestamp']
                    if timestamp in result_df.index:
                        if ob['type'] == 'bullish':
                            result_df.loc[timestamp, 'order_block_bullish'] = True
                        elif ob['type'] == 'bearish':
                            result_df.loc[timestamp, 'order_block_bearish'] = True
            
            # 6. PRICE ACTION SETUPS
            print("Processing Price Action Setups...")
            pa_setups = self.market_structure_analyzer.detect_price_action_setups(df)
            
            # Create PA setup indicator columns
            setup_types = ['pin_bar', 'inside_bar', 'outside_bar', 'fakey', 'spring', 'upthrust']
            for setup_type in setup_types:
                result_df[f'setup_{setup_type}'] = pd.Series(index=df.index, dtype=bool)
                result_df[f'setup_{setup_type}'][:] = False
            
            # Mark PA setup occurrences
            if not pa_setups.empty:
                for _, setup in pa_setups.iterrows():
                    timestamp = setup['timestamp']
                    setup_type = setup['setup_type']
                    if timestamp in result_df.index and f'setup_{setup_type}' in result_df.columns:
                        result_df.loc[timestamp, f'setup_{setup_type}'] = True
            
            # 7. SUPPORT & RESISTANCE
            print("Processing Support & Resistance...")
            sr_levels = self.support_resistance_analyzer.detect_support_resistance_zones(df)
            
            # Create S/R proximity indicators
            result_df['near_support'] = pd.Series(index=df.index, dtype=bool)
            result_df['near_resistance'] = pd.Series(index=df.index, dtype=bool)
            result_df['at_major_level'] = pd.Series(index=df.index, dtype=bool)
            result_df['near_support'][:] = False
            result_df['near_resistance'][:] = False
            result_df['at_major_level'][:] = False
            
            # Check proximity to S/R levels
            if not sr_levels.empty:
                tolerance = 0.005  # 0.5% tolerance
                for i, row in result_df.iterrows():
                    current_price = row['close']
                    
                    # Check each S/R level
                    for _, level in sr_levels.iterrows():
                        level_price = level['level']
                        level_type = level['type']
                        level_strength = level.get('strength', 0)
                        
                        price_diff = abs(current_price - level_price) / current_price
                        
                        if price_diff <= tolerance:
                            if level_type in ['support', 'both']:
                                result_df.loc[i, 'near_support'] = True
                            if level_type in ['resistance', 'both']:
                                result_df.loc[i, 'near_resistance'] = True
                            if level_strength > 3:  # Major level
                                result_df.loc[i, 'at_major_level'] = True
            
            # 8. VOLUME ANALYSIS
            print("Processing Volume Analysis...")
            volume_analysis = self.volume_analyzer.analyze_volume_patterns(df)
            
            # Add volume analysis columns
            volume_cols = ['volume_class', 'relative_volume', 'volume_spike', 
                          'volume_climax', 'accumulation', 'distribution']
            
            for col in volume_cols:
                if col in volume_analysis.columns:
                    result_df[f'volume_{col}'] = volume_analysis[col]
            
            # 9. GAP ANALYSIS
            print("Processing Gap Analysis...")
            gaps = self.gap_analyzer.detect_gaps(df)
            
            # Create gap indicator columns
            gap_types = ['common', 'breakaway', 'runaway', 'exhaustion']
            for gap_type in gap_types:
                result_df[f'gap_{gap_type}'] = pd.Series(index=df.index, dtype=bool)
                result_df[f'gap_{gap_type}'][:] = False
            
            # Mark gap occurrences
            if not gaps.empty:
                for _, gap in gaps.iterrows():
                    timestamp = gap['timestamp']
                    gap_type = gap['gap_type']
                    if timestamp in result_df.index and f'gap_{gap_type}' in result_df.columns:
                        result_df.loc[timestamp, f'gap_{gap_type}'] = True
            
            # 10. SESSION ANALYSIS
            print("Processing Session Analysis...")
            session_analysis = self.session_analyzer.analyze_session_characteristics(df)
            
            # Add session-based columns
            result_df['session'] = pd.Series(index=df.index, dtype='object')
            result_df['session'][:] = 'regular'
            
            # Mark different sessions
            for i, timestamp in enumerate(df.index):
                time_obj = timestamp.time()
                if time_obj < pd.Timestamp('09:15').time():
                    result_df.iloc[i, result_df.columns.get_loc('session')] = 'pre_market'
                elif time_obj >= pd.Timestamp('15:30').time():
                    result_df.iloc[i, result_df.columns.get_loc('session')] = 'post_market'
                elif time_obj <= pd.Timestamp('10:00').time():
                    result_df.iloc[i, result_df.columns.get_loc('session')] = 'opening'
                elif time_obj >= pd.Timestamp('15:00').time():
                    result_df.iloc[i, result_df.columns.get_loc('session')] = 'closing'
            
            # 11. METADATA (if requested)
            if include_metadata:
                print("Adding metadata columns...")
                
                # ATR
                atr = self.support_resistance_analyzer.calculate_atr(df)
                result_df['atr'] = atr
                result_df['atr_percent'] = (atr / df['close']) * 100
                
                # Price position in range
                high_20 = df['high'].rolling(20).max()
                low_20 = df['low'].rolling(20).min()
                result_df['range_position'] = ((df['close'] - low_20) / (high_20 - low_20)) * 100
                
                # Volatility classification
                result_df['volatility_regime'] = pd.cut(result_df['atr_percent'], 
                                                      bins=[0, 1, 2, 5, float('inf')],
                                                      labels=['low', 'medium', 'high', 'extreme'])
                
                # Trend classification based on recent price action
                ma_5 = df['close'].rolling(5).mean()
                ma_20 = df['close'].rolling(20).mean()
                ma_50 = df['close'].rolling(50).mean()
                
                conditions = [
                    (df['close'] > ma_5) & (ma_5 > ma_20) & (ma_20 > ma_50),
                    (df['close'] < ma_5) & (ma_5 < ma_20) & (ma_20 < ma_50),
                ]
                choices = ['strong_bullish', 'strong_bearish']
                result_df['trend_classification'] = pd.Series(np.select(conditions, choices, default='neutral'), 
                                                            index=df.index)
                
                # Price zones
                result_df['price_zone'] = pd.Series(index=df.index, dtype='object')
                result_df['price_zone'][:] = 'neutral'
                
                # Premium/Discount zones
                result_df.loc[result_df['range_position'] > 70, 'price_zone'] = 'premium'
                result_df.loc[result_df['range_position'] < 30, 'price_zone'] = 'discount'
            
            print(f"✅ fetch_all completed successfully!")
            print(f"📊 Output DataFrame shape: {result_df.shape}")
            print(f"📅 Date range: {result_df.index[0]} to {result_df.index[-1]}")
            print(f"📈 Total columns: {len(result_df.columns)}")
            
            return result_df
            
        except Exception as e:
            print(f"❌ Error in fetch_all: {str(e)}")
            # Return basic DataFrame with error info
            error_df = df.copy() if include_ohlcv else pd.DataFrame(index=df.index)
            error_df['fetch_all_error'] = str(e)
            return error_df