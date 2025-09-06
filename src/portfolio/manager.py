"""
Portfolio Manager
Manages investment portfolios with database persistence and analysis integration
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

from analysis.analyzer import FinancialAnalyzer


logger = logging.getLogger(__name__)


@dataclass
class Holding:
    """Portfolio holding data class"""
    id: Optional[int]
    portfolio_id: int
    symbol: str
    quantity: float
    avg_cost: float
    purchase_date: datetime
    notes: Optional[str] = None


@dataclass
class Portfolio:
    """Portfolio data class"""
    id: Optional[int]
    name: str
    description: str
    created_date: datetime
    cash_balance: float = 0.0


class PortfolioManager:
    """Portfolio management with database persistence"""
    
    def __init__(self, database_url: str, analyzer: FinancialAnalyzer):
        self.database_url = database_url
        self.analyzer = analyzer
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            # Extract database path from URL
            db_path = self.database_url.replace('sqlite:///', '')
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create portfolios table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_date TEXT NOT NULL,
                    cash_balance REAL DEFAULT 0.0
                )
            ''')
            
            # Create holdings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    avg_cost REAL NOT NULL,
                    purchase_date TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            ''')
            
            # Create transactions table for tracking trades
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    transaction_date TEXT NOT NULL,
                    fees REAL DEFAULT 0.0,
                    notes TEXT,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def create_portfolio(self, name: str, description: str = "", cash_balance: float = 0.0) -> Portfolio:
        """Create a new portfolio"""
        try:
            db_path = self.database_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            created_date = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO portfolios (name, description, created_date, cash_balance)
                VALUES (?, ?, ?, ?)
            ''', (name, description, created_date, cash_balance))
            
            portfolio_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            portfolio = Portfolio(
                id=portfolio_id,
                name=name,
                description=description,
                created_date=datetime.fromisoformat(created_date),
                cash_balance=cash_balance
            )
            
            logger.info(f"Created portfolio: {name}")
            return portfolio
            
        except Exception as e:
            logger.error(f"Error creating portfolio: {e}")
            raise
    
    def get_portfolios(self) -> List[Portfolio]:
        """Get all portfolios"""
        try:
            db_path = self.database_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM portfolios ORDER BY created_date DESC')
            rows = cursor.fetchall()
            conn.close()
            
            portfolios = []
            for row in rows:
                portfolio = Portfolio(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    created_date=datetime.fromisoformat(row[3]),
                    cash_balance=row[4]
                )
                portfolios.append(portfolio)
            
            return portfolios
            
        except Exception as e:
            logger.error(f"Error getting portfolios: {e}")
            return []
    
    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get a specific portfolio by ID"""
        try:
            db_path = self.database_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM portfolios WHERE id = ?', (portfolio_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return Portfolio(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    created_date=datetime.fromisoformat(row[3]),
                    cash_balance=row[4]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting portfolio {portfolio_id}: {e}")
            return None
    
    def add_holding(self, portfolio_id: int, symbol: str, quantity: float, avg_cost: float, notes: str = "") -> Holding:
        """Add a new holding to a portfolio"""
        try:
            db_path = self.database_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            purchase_date = datetime.now().isoformat()
            
            # Check if holding already exists
            cursor.execute('''
                SELECT id, quantity, avg_cost FROM holdings 
                WHERE portfolio_id = ? AND symbol = ?
            ''', (portfolio_id, symbol))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing holding (average cost calculation)
                existing_quantity = existing[1]
                existing_avg_cost = existing[2]
                
                total_cost = (existing_quantity * existing_avg_cost) + (quantity * avg_cost)
                new_quantity = existing_quantity + quantity
                new_avg_cost = total_cost / new_quantity if new_quantity > 0 else 0
                
                cursor.execute('''
                    UPDATE holdings 
                    SET quantity = ?, avg_cost = ?, purchase_date = ?, notes = ?
                    WHERE id = ?
                ''', (new_quantity, new_avg_cost, purchase_date, notes, existing[0]))
                
                holding_id = existing[0]
            else:
                # Create new holding
                cursor.execute('''
                    INSERT INTO holdings (portfolio_id, symbol, quantity, avg_cost, purchase_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (portfolio_id, symbol, quantity, avg_cost, purchase_date, notes))
                
                holding_id = cursor.lastrowid
            
            # Record transaction
            cursor.execute('''
                INSERT INTO transactions (portfolio_id, symbol, transaction_type, quantity, price, transaction_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (portfolio_id, symbol, 'BUY', quantity, avg_cost, purchase_date, notes))
            
            conn.commit()
            conn.close()
            
            holding = Holding(
                id=holding_id,
                portfolio_id=portfolio_id,
                symbol=symbol,
                quantity=quantity,
                avg_cost=avg_cost,
                purchase_date=datetime.fromisoformat(purchase_date),
                notes=notes
            )
            
            logger.info(f"Added holding: {symbol} to portfolio {portfolio_id}")
            return holding
            
        except Exception as e:
            logger.error(f"Error adding holding: {e}")
            raise
    
    def get_holdings(self, portfolio_id: int) -> List[Holding]:
        """Get all holdings for a portfolio"""
        try:
            db_path = self.database_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM holdings 
                WHERE portfolio_id = ? 
                ORDER BY symbol
            ''', (portfolio_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            holdings = []
            for row in rows:
                holding = Holding(
                    id=row[0],
                    portfolio_id=row[1],
                    symbol=row[2],
                    quantity=row[3],
                    avg_cost=row[4],
                    purchase_date=datetime.fromisoformat(row[5]),
                    notes=row[6]
                )
                holdings.append(holding)
            
            return holdings
            
        except Exception as e:
            logger.error(f"Error getting holdings for portfolio {portfolio_id}: {e}")
            return []
    
    def remove_holding(self, portfolio_id: int, symbol: str, quantity: float = None) -> bool:
        """Remove or reduce a holding"""
        try:
            db_path = self.database_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, quantity, avg_cost FROM holdings 
                WHERE portfolio_id = ? AND symbol = ?
            ''', (portfolio_id, symbol))
            
            holding = cursor.fetchone()
            if not holding:
                return False
            
            current_quantity = holding[1]
            avg_cost = holding[2]
            
            if quantity is None or quantity >= current_quantity:
                # Remove entire holding
                cursor.execute('DELETE FROM holdings WHERE id = ?', (holding[0],))
                sell_quantity = current_quantity
            else:
                # Reduce holding
                new_quantity = current_quantity - quantity
                cursor.execute('''
                    UPDATE holdings SET quantity = ? WHERE id = ?
                ''', (new_quantity, holding[0]))
                sell_quantity = quantity
            
            # Record sell transaction
            transaction_date = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO transactions (portfolio_id, symbol, transaction_type, quantity, price, transaction_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (portfolio_id, symbol, 'SELL', sell_quantity, avg_cost, transaction_date))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Removed/reduced holding: {symbol} from portfolio {portfolio_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing holding: {e}")
            return False
    
    async def analyze_portfolio(self, portfolio_id: int) -> Dict[str, Any]:
        """Analyze portfolio performance and generate insights"""
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                return {'error': 'Portfolio not found'}
            
            holdings = self.get_holdings(portfolio_id)
            if not holdings:
                return {'error': 'No holdings in portfolio'}
            
            # Convert holdings to format expected by analyzer
            holdings_data = []
            for holding in holdings:
                holdings_data.append({
                    'symbol': holding.symbol,
                    'quantity': holding.quantity,
                    'avg_cost': holding.avg_cost
                })
            
            # Perform analysis
            analysis = await self.analyzer.analyze_portfolio(holdings_data)
            
            # Add portfolio metadata
            analysis['portfolio_info'] = {
                'id': portfolio.id,
                'name': portfolio.name,
                'description': portfolio.description,
                'cash_balance': portfolio.cash_balance,
                'created_date': portfolio.created_date.isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio {portfolio_id}: {e}")
            return {'error': str(e)}
    
    def get_transaction_history(self, portfolio_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get transaction history for a portfolio"""
        try:
            db_path = self.database_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE portfolio_id = ? 
                ORDER BY transaction_date DESC 
                LIMIT ?
            ''', (portfolio_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            transactions = []
            for row in rows:
                transaction = {
                    'id': row[0],
                    'portfolio_id': row[1],
                    'symbol': row[2],
                    'transaction_type': row[3],
                    'quantity': row[4],
                    'price': row[5],
                    'transaction_date': row[6],
                    'fees': row[7],
                    'notes': row[8]
                }
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
