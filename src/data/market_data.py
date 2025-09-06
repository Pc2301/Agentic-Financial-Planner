"""
Market Data Service
Handles fetching and processing financial market data from various sources
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import yfinance as yf
import httpx
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData


logger = logging.getLogger(__name__)


class MarketDataService:
    """Service for fetching financial market data"""
    
    def __init__(self, alpha_vantage_key: str = None, fmp_key: str = None):
        self.alpha_vantage_key = alpha_vantage_key
        self.fmp_key = fmp_key
        
        # Initialize Alpha Vantage clients
        if alpha_vantage_key:
            self.ts = TimeSeries(key=alpha_vantage_key, output_format='pandas')
            self.fd = FundamentalData(key=alpha_vantage_key, output_format='pandas')
        
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock price and basic info"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'current_price': info.get('currentPrice', 0),
                'previous_close': info.get('previousClose', 0),
                'open': info.get('open', 0),
                'day_high': info.get('dayHigh', 0),
                'day_low': info.get('dayLow', 0),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'company_name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical stock data"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                return None
                
            # Reset index to make Date a column
            data = data.reset_index()
            
            return data
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def get_financial_statements(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get financial statements for a company"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get financial statements
            income_stmt = ticker.financials
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cashflow
            
            return {
                'symbol': symbol,
                'income_statement': income_stmt.to_dict() if not income_stmt.empty else {},
                'balance_sheet': balance_sheet.to_dict() if not balance_sheet.empty else {},
                'cash_flow': cash_flow.to_dict() if not cash_flow.empty else {},
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching financial statements for {symbol}: {e}")
            return None
    
    async def get_market_indices(self) -> Dict[str, Any]:
        """Get major market indices data"""
        indices = {
            'S&P 500': '^GSPC',
            'Dow Jones': '^DJI',
            'NASDAQ': '^IXIC',
            'Russell 2000': '^RUT',
            'VIX': '^VIX'
        }
        
        results = {}
        
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="2d")
                
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = current - previous
                    change_pct = (change / previous) * 100 if previous != 0 else 0
                    
                    results[name] = {
                        'symbol': symbol,
                        'current': float(current),
                        'change': float(change),
                        'change_percent': float(change_pct),
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Error fetching data for {name}: {e}")
                continue
        
        return results
    
    async def get_sector_performance(self) -> Dict[str, Any]:
        """Get sector performance data"""
        sector_etfs = {
            'Technology': 'XLK',
            'Healthcare': 'XLV',
            'Financials': 'XLF',
            'Consumer Discretionary': 'XLY',
            'Communication Services': 'XLC',
            'Industrials': 'XLI',
            'Consumer Staples': 'XLP',
            'Energy': 'XLE',
            'Utilities': 'XLU',
            'Real Estate': 'XLRE',
            'Materials': 'XLB'
        }
        
        results = {}
        
        for sector, etf in sector_etfs.items():
            try:
                ticker = yf.Ticker(etf)
                hist = ticker.history(period="5d")
                
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    week_ago = hist['Close'].iloc[0]
                    change = current - week_ago
                    change_pct = (change / week_ago) * 100 if week_ago != 0 else 0
                    
                    results[sector] = {
                        'etf_symbol': etf,
                        'current': float(current),
                        'change_5d': float(change),
                        'change_5d_percent': float(change_pct),
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Error fetching sector data for {sector}: {e}")
                continue
        
        return results
    
    async def get_economic_indicators(self) -> Dict[str, Any]:
        """Get key economic indicators"""
        # This would typically use FRED API or similar
        # For now, we'll return placeholder data
        return {
            'treasury_10y': {'value': 4.5, 'change': 0.1},
            'treasury_2y': {'value': 4.8, 'change': 0.05},
            'dxy': {'value': 103.5, 'change': -0.2},
            'gold': {'value': 2050, 'change': 15.5},
            'oil': {'value': 85.2, 'change': -1.2},
            'timestamp': datetime.now().isoformat()
        }
    
    async def search_stocks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for stocks by name or symbol"""
        try:
            # Use yfinance to search (limited functionality)
            # In a real implementation, you'd use a proper search API
            results = []
            
            # Try to get info for the query as a symbol
            try:
                ticker = yf.Ticker(query.upper())
                info = ticker.info
                
                if info and 'longName' in info:
                    results.append({
                        'symbol': query.upper(),
                        'name': info.get('longName', ''),
                        'sector': info.get('sector', ''),
                        'market_cap': info.get('marketCap', 0),
                        'current_price': info.get('currentPrice', 0)
                    })
            except:
                pass
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []
    
    async def close(self):
        """Close the HTTP session"""
        await self.session.aclose()
