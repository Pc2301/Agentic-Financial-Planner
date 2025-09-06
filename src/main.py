#!/usr/bin/env python3
"""
MCP-Powered Financial Analyst
Main application entry point
"""

import asyncio
import logging
import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from mcp.client import MCPClient
from web.routes import router as web_router, set_services
from data.market_data import MarketDataService
from analysis.analyzer import FinancialAnalyzer
from portfolio.manager import PortfolioManager
from agent.financial_agent import FinancialAgent

# Load environment variables
load_dotenv()

# Configure logging
log_file = os.getenv('LOG_FILE', 'logs/financial_analyst.log')
log_dir = os.path.dirname(log_file)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP-Powered Financial Analyst",
    description="AI-powered financial analysis tool using Model Context Protocol",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(web_router)

# Global services
mcp_client = None
market_data_service = None
financial_analyzer = None
portfolio_manager = None
financial_agent = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global mcp_client, market_data_service, financial_analyzer, portfolio_manager
    
    logger.info("Starting MCP-Powered Financial Analyst...")
    
    try:
        # Initialize MCP client
        mcp_client = MCPClient(
            server_url=os.getenv('MCP_SERVER_URL'),
            api_key=os.getenv('MCP_API_KEY')
        )
        await mcp_client.connect()
        logger.info("MCP client connected successfully")
        
        # Initialize market data service
        market_data_service = MarketDataService(
            alpha_vantage_key=os.getenv('ALPHA_VANTAGE_API_KEY'),
            fmp_key=os.getenv('FINANCIAL_MODELING_PREP_API_KEY')
        )
        
        # Initialize financial analyzer with MCP integration
        financial_analyzer = FinancialAnalyzer(
            mcp_client=mcp_client,
            market_data_service=market_data_service
        )
        
        # Initialize portfolio manager
        portfolio_manager = PortfolioManager(
            database_url=os.getenv('DATABASE_URL'),
            analyzer=financial_analyzer
        )
        
        # Initialize financial agent
        financial_agent = FinancialAgent(
            mcp_client=mcp_client,
            market_data=market_data_service,
            analyzer=financial_analyzer,
            portfolio_manager=portfolio_manager
        )
        
        # Inject services into web routes
        set_services(market_data_service, financial_analyzer, portfolio_manager, financial_agent)
        
        logger.info("All services including Financial Agent initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down MCP-Powered Financial Analyst...")
    
    if mcp_client:
        await mcp_client.disconnect()
    
    logger.info("Shutdown complete")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MCP-Powered Financial Analyst API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "mcp_client": mcp_client is not None and mcp_client.is_connected(),
            "market_data": market_data_service is not None,
            "analyzer": financial_analyzer is not None,
            "portfolio_manager": portfolio_manager is not None
        }
    }


def main():
    """Main function to run the application"""
    host = os.getenv('HOST', 'localhost')
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )


if __name__ == "__main__":
    main()
