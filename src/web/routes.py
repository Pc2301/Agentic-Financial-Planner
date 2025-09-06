"""
Web Routes
FastAPI routes for the financial analyst web interface
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import services (these will be injected from main.py)
from data.market_data import MarketDataService
from analysis.analyzer import FinancialAnalyzer
from portfolio.manager import PortfolioManager


logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Global service references (will be set from main.py)
market_data_service: Optional[MarketDataService] = None
financial_analyzer: Optional[FinancialAnalyzer] = None
portfolio_manager: Optional[PortfolioManager] = None
financial_agent = None


# Pydantic models for API requests
class StockAnalysisRequest(BaseModel):
    symbol: str


class AddHoldingRequest(BaseModel):
    portfolio_id: int
    symbol: str
    quantity: float
    avg_cost: float
    notes: Optional[str] = ""


class CreatePortfolioRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    cash_balance: Optional[float] = 0.0


class AgentChatRequest(BaseModel):
    message: str
    portfolio_id: int


class AgentControlRequest(BaseModel):
    action: str  # "start", "stop", "status"
    portfolio_id: int
    goal: Optional[str] = "balanced_growth"


# Web Interface Routes
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    try:
        # Get market indices
        market_data = await market_data_service.get_market_indices() if market_data_service else {}
        
        # Get sector performance
        sector_data = await market_data_service.get_sector_performance() if market_data_service else {}
        
        # Get portfolios
        portfolios = portfolio_manager.get_portfolios() if portfolio_manager else []
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "market_data": market_data,
            "sector_data": sector_data,
            "portfolios": portfolios,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error loading dashboard")


@router.get("/portfolio/{portfolio_id}", response_class=HTMLResponse)
async def portfolio_detail(request: Request, portfolio_id: int):
    """Portfolio detail page"""
    try:
        if not portfolio_manager:
            raise HTTPException(status_code=500, detail="Portfolio manager not available")
        
        portfolio = portfolio_manager.get_portfolio(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        holdings = portfolio_manager.get_holdings(portfolio_id)
        analysis = await portfolio_manager.analyze_portfolio(portfolio_id)
        transactions = portfolio_manager.get_transaction_history(portfolio_id, limit=20)
        
        return templates.TemplateResponse("portfolio.html", {
            "request": request,
            "portfolio": portfolio,
            "holdings": holdings,
            "analysis": analysis,
            "transactions": transactions
        })
    except Exception as e:
        logger.error(f"Error loading portfolio {portfolio_id}: {e}")
        raise HTTPException(status_code=500, detail="Error loading portfolio")


@router.get("/stock/{symbol}", response_class=HTMLResponse)
async def stock_detail(request: Request, symbol: str):
    """Stock analysis page"""
    try:
        if not financial_analyzer:
            raise HTTPException(status_code=500, detail="Financial analyzer not available")
        
        analysis = await financial_analyzer.analyze_stock(symbol.upper())
        
        return templates.TemplateResponse("stock.html", {
            "request": request,
            "symbol": symbol.upper(),
            "analysis": analysis
        })
    except Exception as e:
        logger.error(f"Error analyzing stock {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing stock")


# API Routes
@router.post("/api/analyze-stock")
async def analyze_stock_api(request: StockAnalysisRequest):
    """API endpoint for stock analysis"""
    try:
        if not financial_analyzer:
            raise HTTPException(status_code=500, detail="Financial analyzer not available")
        
        analysis = await financial_analyzer.analyze_stock(request.symbol.upper())
        return JSONResponse(content=analysis)
    except Exception as e:
        logger.error(f"Error in stock analysis API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/market-data")
async def get_market_data():
    """API endpoint for market data"""
    try:
        if not market_data_service:
            raise HTTPException(status_code=500, detail="Market data service not available")
        
        indices = await market_data_service.get_market_indices()
        sectors = await market_data_service.get_sector_performance()
        economic = await market_data_service.get_economic_indicators()
        
        return JSONResponse(content={
            "indices": indices,
            "sectors": sectors,
            "economic_indicators": economic,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/portfolios")
async def create_portfolio_api(request: CreatePortfolioRequest):
    """API endpoint to create a new portfolio"""
    try:
        if not portfolio_manager:
            raise HTTPException(status_code=500, detail="Portfolio manager not available")
        
        portfolio = portfolio_manager.create_portfolio(
            name=request.name,
            description=request.description,
            cash_balance=request.cash_balance
        )
        
        return JSONResponse(content={
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "cash_balance": portfolio.cash_balance,
            "created_date": portfolio.created_date.isoformat()
        })
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/portfolios")
async def get_portfolios_api():
    """API endpoint to get all portfolios"""
    try:
        if not portfolio_manager:
            raise HTTPException(status_code=500, detail="Portfolio manager not available")
        
        portfolios = portfolio_manager.get_portfolios()
        
        portfolio_data = []
        for portfolio in portfolios:
            portfolio_data.append({
                "id": portfolio.id,
                "name": portfolio.name,
                "description": portfolio.description,
                "cash_balance": portfolio.cash_balance,
                "created_date": portfolio.created_date.isoformat()
            })
        
        return JSONResponse(content=portfolio_data)
    except Exception as e:
        logger.error(f"Error getting portfolios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/holdings")
async def add_holding_api(request: AddHoldingRequest):
    """API endpoint to add a holding to a portfolio"""
    try:
        if not portfolio_manager:
            raise HTTPException(status_code=500, detail="Portfolio manager not available")
        
        holding = portfolio_manager.add_holding(
            portfolio_id=request.portfolio_id,
            symbol=request.symbol.upper(),
            quantity=request.quantity,
            avg_cost=request.avg_cost,
            notes=request.notes
        )
        
        return JSONResponse(content={
            "id": holding.id,
            "portfolio_id": holding.portfolio_id,
            "symbol": holding.symbol,
            "quantity": holding.quantity,
            "avg_cost": holding.avg_cost,
            "purchase_date": holding.purchase_date.isoformat(),
            "notes": holding.notes
        })
    except Exception as e:
        logger.error(f"Error adding holding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/portfolio/{portfolio_id}/analysis")
async def get_portfolio_analysis_api(portfolio_id: int):
    """API endpoint for portfolio analysis"""
    try:
        if not portfolio_manager:
            raise HTTPException(status_code=500, detail="Portfolio manager not available")
        
        analysis = await portfolio_manager.analyze_portfolio(portfolio_id)
        return JSONResponse(content=analysis)
    except Exception as e:
        logger.error(f"Error getting portfolio analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/search-stocks")
async def search_stocks_api(q: str, limit: int = 10):
    """API endpoint to search for stocks"""
    try:
        if not market_data_service:
            raise HTTPException(status_code=500, detail="Market data service not available")
        
        results = await market_data_service.search_stocks(q, limit)
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent API Endpoints
@router.post("/api/agent/chat")
async def agent_chat_api(request: AgentChatRequest):
    """Chat with the financial agent"""
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Financial agent not available")
        
        response = await financial_agent.chat_with_agent(request.message, request.portfolio_id)
        return JSONResponse(content={"response": response})
    except Exception as e:
        logger.error(f"Error in agent chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/agent/control")
async def agent_control_api(request: AgentControlRequest):
    """Control agent operations (start/stop autonomous mode)"""
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Financial agent not available")
        
        if request.action == "start":
            from agent.financial_agent import Goal
            goal = Goal(request.goal) if request.goal else Goal.BALANCED_GROWTH
            # Start agent in background task
            import asyncio
            asyncio.create_task(financial_agent.start_autonomous_mode(request.portfolio_id, goal))
            return JSONResponse(content={"status": "Agent started", "goal": goal.value})
            
        elif request.action == "stop":
            financial_agent.stop_autonomous_mode()
            return JSONResponse(content={"status": "Agent stopped"})
            
        elif request.action == "status":
            status = financial_agent.get_agent_status()
            return JSONResponse(content=status)
            
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
            
    except Exception as e:
        logger.error(f"Error in agent control: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/agent/status/{portfolio_id}")
async def get_agent_status_api(portfolio_id: int):
    """Get agent status for a portfolio"""
    try:
        if not financial_agent:
            raise HTTPException(status_code=500, detail="Financial agent not available")
        
        status = financial_agent.get_agent_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility function to inject services
def set_services(market_service: MarketDataService, analyzer: FinancialAnalyzer, portfolio_mgr: PortfolioManager, agent=None):
    """Set service references for the routes"""
    global market_data_service, financial_analyzer, portfolio_manager, financial_agent
    market_data_service = market_service
    financial_analyzer = analyzer
    portfolio_manager = portfolio_mgr
    financial_agent = agent
