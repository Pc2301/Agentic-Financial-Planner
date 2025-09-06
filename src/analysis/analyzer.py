"""
Financial Analyzer
Core financial analysis engine with MCP integration for AI-powered insights
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from mcp.client import MCPClient
from data.market_data import MarketDataService


logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """Advanced financial analysis with MCP AI integration"""
    
    def __init__(self, mcp_client: MCPClient, market_data_service: MarketDataService):
        self.mcp_client = mcp_client
        self.market_data = market_data_service
    
    async def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """Comprehensive stock analysis with AI insights"""
        try:
            # Get basic stock data
            stock_data = await self.market_data.get_stock_price(symbol)
            if not stock_data:
                return {'error': f'Could not fetch data for {symbol}'}
            
            # Get historical data for technical analysis
            historical_data = await self.market_data.get_historical_data(symbol, "1y")
            if historical_data is None or historical_data.empty:
                return {'error': f'No historical data available for {symbol}'}
            
            # Perform technical analysis
            technical_analysis = self._calculate_technical_indicators(historical_data)
            
            # Calculate financial ratios and metrics
            financial_metrics = await self._calculate_financial_metrics(symbol)
            
            # Get AI-powered insights from MCP
            ai_insights = await self._get_ai_insights(symbol, stock_data, technical_analysis)
            
            # Combine all analysis
            analysis = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'basic_data': stock_data,
                'technical_analysis': technical_analysis,
                'financial_metrics': financial_metrics,
                'ai_insights': ai_insights,
                'recommendation': self._generate_recommendation(stock_data, technical_analysis, financial_metrics)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing stock {symbol}: {e}")
            return {'error': str(e)}
    
    def _calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical analysis indicators"""
        try:
            close_prices = data['Close'].values
            high_prices = data['High'].values
            low_prices = data['Low'].values
            volume = data['Volume'].values
            
            # Moving averages
            sma_20 = self._calculate_sma(close_prices, 20)
            sma_50 = self._calculate_sma(close_prices, 50)
            ema_12 = self._calculate_ema(close_prices, 12)
            ema_26 = self._calculate_ema(close_prices, 26)
            
            # MACD
            macd, macd_signal = self._calculate_macd(close_prices)
            
            # RSI
            rsi = self._calculate_rsi(close_prices, 14)
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(close_prices)
            
            # Stochastic
            stoch_k, stoch_d = self._calculate_stochastic(high_prices, low_prices, close_prices)
            
            # Volume indicators
            obv = self._calculate_obv(close_prices, volume)
            
            # Support and resistance levels
            support_resistance = self._calculate_support_resistance(data)
            
            current_price = close_prices[-1]
            
            return {
                'moving_averages': {
                    'sma_20': float(sma_20[-1]) if not np.isnan(sma_20[-1]) else None,
                    'sma_50': float(sma_50[-1]) if not np.isnan(sma_50[-1]) else None,
                    'ema_12': float(ema_12[-1]) if not np.isnan(ema_12[-1]) else None,
                    'ema_26': float(ema_26[-1]) if not np.isnan(ema_26[-1]) else None,
                },
                'momentum': {
                    'rsi': float(rsi[-1]) if not np.isnan(rsi[-1]) else None,
                    'macd': float(macd[-1]) if not np.isnan(macd[-1]) else None,
                    'macd_signal': float(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else None,
                    'stoch_k': float(stoch_k[-1]) if not np.isnan(stoch_k[-1]) else None,
                    'stoch_d': float(stoch_d[-1]) if not np.isnan(stoch_d[-1]) else None,
                },
                'volatility': {
                    'bb_upper': float(bb_upper[-1]) if not np.isnan(bb_upper[-1]) else None,
                    'bb_middle': float(bb_middle[-1]) if not np.isnan(bb_middle[-1]) else None,
                    'bb_lower': float(bb_lower[-1]) if not np.isnan(bb_lower[-1]) else None,
                    'bb_position': self._calculate_bb_position(current_price, bb_upper[-1], bb_lower[-1]),
                },
                'volume': {
                    'obv': float(obv[-1]) if not np.isnan(obv[-1]) else None,
                    'avg_volume_20d': float(np.mean(volume[-20:])),
                    'volume_trend': 'increasing' if volume[-1] > np.mean(volume[-20:]) else 'decreasing'
                },
                'support_resistance': support_resistance,
                'trend_analysis': self._analyze_trend(close_prices, sma_20, sma_50)
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}
    
    def _calculate_support_resistance(self, data: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
        """Calculate support and resistance levels"""
        try:
            highs = data['High'].rolling(window=window).max()
            lows = data['Low'].rolling(window=window).min()
            
            # Find local maxima and minima
            resistance_levels = []
            support_levels = []
            
            for i in range(window, len(data) - window):
                if data['High'].iloc[i] == highs.iloc[i]:
                    resistance_levels.append(float(data['High'].iloc[i]))
                if data['Low'].iloc[i] == lows.iloc[i]:
                    support_levels.append(float(data['Low'].iloc[i]))
            
            # Remove duplicates and sort
            resistance_levels = sorted(list(set(resistance_levels)))[-5:]  # Top 5
            support_levels = sorted(list(set(support_levels)), reverse=True)[-5:]  # Top 5
            
            return {
                'resistance': resistance_levels,
                'support': support_levels
            }
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {'resistance': [], 'support': []}
    
    def _calculate_bb_position(self, price: float, bb_upper: float, bb_lower: float) -> str:
        """Calculate Bollinger Band position"""
        if np.isnan(bb_upper) or np.isnan(bb_lower):
            return 'unknown'
        
        if price > bb_upper:
            return 'above_upper'
        elif price < bb_lower:
            return 'below_lower'
        else:
            position = (price - bb_lower) / (bb_upper - bb_lower)
            if position > 0.8:
                return 'near_upper'
            elif position < 0.2:
                return 'near_lower'
            else:
                return 'middle'
    
    def _analyze_trend(self, prices: np.ndarray, sma_20: np.ndarray, sma_50: np.ndarray) -> Dict[str, str]:
        """Analyze price trend"""
        current_price = prices[-1]
        
        # Short-term trend (20-day SMA)
        short_trend = 'bullish' if current_price > sma_20[-1] else 'bearish'
        
        # Long-term trend (50-day SMA)
        long_trend = 'bullish' if current_price > sma_50[-1] else 'bearish'
        
        # Overall trend
        if sma_20[-1] > sma_50[-1]:
            overall_trend = 'bullish'
        elif sma_20[-1] < sma_50[-1]:
            overall_trend = 'bearish'
        else:
            overall_trend = 'neutral'
        
        return {
            'short_term': short_trend,
            'long_term': long_trend,
            'overall': overall_trend
        }
    
    async def _calculate_financial_metrics(self, symbol: str) -> Dict[str, Any]:
        """Calculate financial metrics and ratios"""
        try:
            stock_data = await self.market_data.get_stock_price(symbol)
            financial_statements = await self.market_data.get_financial_statements(symbol)
            
            if not stock_data or not financial_statements:
                return {}
            
            metrics = {
                'valuation': {
                    'pe_ratio': stock_data.get('pe_ratio', 0),
                    'market_cap': stock_data.get('market_cap', 0),
                    'price_to_book': None,  # Would calculate from balance sheet
                    'price_to_sales': None,  # Would calculate from income statement
                },
                'profitability': {
                    'dividend_yield': stock_data.get('dividend_yield', 0),
                    'roe': None,  # Return on Equity
                    'roa': None,  # Return on Assets
                    'profit_margin': None,
                },
                'financial_health': {
                    'debt_to_equity': None,
                    'current_ratio': None,
                    'quick_ratio': None,
                },
                'growth': {
                    'revenue_growth': None,
                    'earnings_growth': None,
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating financial metrics: {e}")
            return {}
    
    async def _get_ai_insights(self, symbol: str, stock_data: Dict, technical_analysis: Dict) -> Dict[str, Any]:
        """Get AI-powered insights from MCP"""
        try:
            if not self.mcp_client.is_connected():
                return {'message': 'MCP not available - using traditional analysis only'}
            
            # Prepare data for MCP analysis
            analysis_data = {
                'symbol': symbol,
                'current_data': stock_data,
                'technical_indicators': technical_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            # Get AI insights
            insights = await self.mcp_client.analyze_financial_data(analysis_data)
            
            if insights:
                return {
                    'ai_summary': insights.get('summary', ''),
                    'key_insights': insights.get('insights', []),
                    'risk_factors': insights.get('risks', []),
                    'opportunities': insights.get('opportunities', []),
                    'confidence_score': insights.get('confidence', 0.5)
                }
            else:
                return {'message': 'AI analysis not available'}
                
        except Exception as e:
            logger.error(f"Error getting AI insights: {e}")
            return {'error': str(e)}
    
    def _generate_recommendation(self, stock_data: Dict, technical_analysis: Dict, financial_metrics: Dict) -> Dict[str, Any]:
        """Generate investment recommendation based on analysis"""
        try:
            score = 0
            factors = []
            
            # Technical analysis factors
            if technical_analysis:
                trend = technical_analysis.get('trend_analysis', {})
                momentum = technical_analysis.get('momentum', {})
                
                # Trend scoring
                if trend.get('overall') == 'bullish':
                    score += 2
                    factors.append('Bullish trend')
                elif trend.get('overall') == 'bearish':
                    score -= 2
                    factors.append('Bearish trend')
                
                # RSI scoring
                rsi = momentum.get('rsi')
                if rsi:
                    if rsi < 30:
                        score += 1
                        factors.append('Oversold (RSI < 30)')
                    elif rsi > 70:
                        score -= 1
                        factors.append('Overbought (RSI > 70)')
            
            # Valuation factors
            if financial_metrics:
                valuation = financial_metrics.get('valuation', {})
                pe_ratio = valuation.get('pe_ratio', 0)
                
                if pe_ratio and 10 <= pe_ratio <= 20:
                    score += 1
                    factors.append('Reasonable P/E ratio')
                elif pe_ratio > 30:
                    score -= 1
                    factors.append('High P/E ratio')
            
            # Generate recommendation
            if score >= 3:
                recommendation = 'Strong Buy'
            elif score >= 1:
                recommendation = 'Buy'
            elif score >= -1:
                recommendation = 'Hold'
            elif score >= -3:
                recommendation = 'Sell'
            else:
                recommendation = 'Strong Sell'
            
            return {
                'recommendation': recommendation,
                'score': score,
                'factors': factors,
                'confidence': min(abs(score) * 0.2, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return {'error': str(e)}
    
    def _calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average"""
        sma = np.full(len(prices), np.nan)
        for i in range(period - 1, len(prices)):
            sma[i] = np.mean(prices[i - period + 1:i + 1])
        return sma
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average"""
        ema = np.full(len(prices), np.nan)
        multiplier = 2 / (period + 1)
        
        # Start with SMA for the first value
        ema[period - 1] = np.mean(prices[:period])
        
        for i in range(period, len(prices)):
            ema[i] = (prices[i] * multiplier) + (ema[i - 1] * (1 - multiplier))
        
        return ema
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index"""
        rsi = np.full(len(prices), np.nan)
        
        if len(prices) < period + 1:
            return rsi
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        if avg_loss == 0:
            rsi[period] = 100
        else:
            rs = avg_gain / avg_loss
            rsi[period] = 100 - (100 / (1 + rs))
        
        for i in range(period + 1, len(prices)):
            gain = gains[i - 1]
            loss = losses[i - 1]
            
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            
            if avg_loss == 0:
                rsi[i] = 100
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD"""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line[~np.isnan(macd_line)], signal)
        
        # Pad signal line to match macd_line length
        padded_signal = np.full(len(macd_line), np.nan)
        valid_start = len(macd_line) - len(signal_line)
        padded_signal[valid_start:] = signal_line
        
        return macd_line, padded_signal
    
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: int = 2) -> tuple:
        """Calculate Bollinger Bands"""
        sma = self._calculate_sma(prices, period)
        
        bb_upper = np.full(len(prices), np.nan)
        bb_lower = np.full(len(prices), np.nan)
        
        for i in range(period - 1, len(prices)):
            std = np.std(prices[i - period + 1:i + 1])
            bb_upper[i] = sma[i] + (std * std_dev)
            bb_lower[i] = sma[i] - (std * std_dev)
        
        return bb_upper, sma, bb_lower
    
    def _calculate_stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3) -> tuple:
        """Calculate Stochastic Oscillator"""
        stoch_k = np.full(len(close), np.nan)
        
        for i in range(k_period - 1, len(close)):
            highest_high = np.max(high[i - k_period + 1:i + 1])
            lowest_low = np.min(low[i - k_period + 1:i + 1])
            
            if highest_high != lowest_low:
                stoch_k[i] = ((close[i] - lowest_low) / (highest_high - lowest_low)) * 100
            else:
                stoch_k[i] = 50
        
        stoch_d = self._calculate_sma(stoch_k[~np.isnan(stoch_k)], d_period)
        
        # Pad stoch_d to match stoch_k length
        padded_d = np.full(len(stoch_k), np.nan)
        valid_start = len(stoch_k) - len(stoch_d)
        padded_d[valid_start:] = stoch_d
        
        return stoch_k, padded_d
    
    def _calculate_obv(self, prices: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """Calculate On-Balance Volume"""
        obv = np.zeros(len(prices))
        
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:
                obv[i] = obv[i - 1] + volume[i]
            elif prices[i] < prices[i - 1]:
                obv[i] = obv[i - 1] - volume[i]
            else:
                obv[i] = obv[i - 1]
        
        return obv
    
    async def analyze_portfolio(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze entire portfolio performance and risk"""
        try:
            portfolio_analysis = {
                'total_value': 0,
                'total_gain_loss': 0,
                'holdings_analysis': [],
                'sector_allocation': {},
                'risk_metrics': {},
                'ai_insights': {}
            }
            
            # Analyze each holding
            for holding in holdings:
                symbol = holding['symbol']
                quantity = holding['quantity']
                avg_cost = holding['avg_cost']
                
                stock_analysis = await self.analyze_stock(symbol)
                if 'error' not in stock_analysis:
                    current_price = stock_analysis['basic_data']['current_price']
                    current_value = current_price * quantity
                    cost_basis = avg_cost * quantity
                    gain_loss = current_value - cost_basis
                    
                    portfolio_analysis['total_value'] += current_value
                    portfolio_analysis['total_gain_loss'] += gain_loss
                    
                    portfolio_analysis['holdings_analysis'].append({
                        'symbol': symbol,
                        'quantity': quantity,
                        'current_price': current_price,
                        'current_value': current_value,
                        'cost_basis': cost_basis,
                        'gain_loss': gain_loss,
                        'gain_loss_percent': (gain_loss / cost_basis) * 100 if cost_basis > 0 else 0,
                        'recommendation': stock_analysis.get('recommendation', {})
                    })
                    
                    # Sector allocation
                    sector = stock_analysis['basic_data'].get('sector', 'Unknown')
                    if sector in portfolio_analysis['sector_allocation']:
                        portfolio_analysis['sector_allocation'][sector] += current_value
                    else:
                        portfolio_analysis['sector_allocation'][sector] = current_value
            
            # Calculate portfolio-level metrics
            if portfolio_analysis['total_value'] > 0:
                portfolio_analysis['total_return_percent'] = (
                    portfolio_analysis['total_gain_loss'] / 
                    (portfolio_analysis['total_value'] - portfolio_analysis['total_gain_loss'])
                ) * 100
                
                # Convert sector allocation to percentages
                for sector in portfolio_analysis['sector_allocation']:
                    portfolio_analysis['sector_allocation'][sector] = (
                        portfolio_analysis['sector_allocation'][sector] / 
                        portfolio_analysis['total_value']
                    ) * 100
            
            # Get AI insights for portfolio
            if self.mcp_client.is_connected():
                ai_insights = await self.mcp_client.generate_investment_insights(portfolio_analysis)
                portfolio_analysis['ai_insights'] = ai_insights or {}
            
            return portfolio_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {e}")
            return {'error': str(e)}
