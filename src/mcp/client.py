"""
MCP (Model Context Protocol) Client
Handles communication with MCP servers for AI-powered financial analysis
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
import httpx
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """MCP request model"""
    method: str
    params: Dict[str, Any]
    id: Optional[str] = None


class MCPResponse(BaseModel):
    """MCP response model"""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class MCPClient:
    """MCP Client for financial analysis integration"""
    
    def __init__(self, server_url: str, api_key: str = None):
        self.server_url = server_url
        self.api_key = api_key
        self.session = None
        self._connected = False
        
    async def connect(self):
        """Establish connection to MCP server"""
        try:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}" if self.api_key else None
                }
            )
            
            # Test connection
            response = await self._send_request("ping", {})
            if response and not response.error:
                self._connected = True
                logger.info("Successfully connected to MCP server")
            else:
                logger.warning("MCP server connection test failed, continuing without MCP")
                
        except Exception as e:
            logger.warning(f"Failed to connect to MCP server: {e}, continuing without MCP")
            self._connected = False
    
    async def disconnect(self):
        """Close connection to MCP server"""
        if self.session:
            await self.session.aclose()
        self._connected = False
        logger.info("Disconnected from MCP server")
    
    def is_connected(self) -> bool:
        """Check if connected to MCP server"""
        return self._connected
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Optional[MCPResponse]:
        """Send request to MCP server"""
        if not self.session:
            return None
            
        request = MCPRequest(method=method, params=params)
        
        try:
            response = await self.session.post(
                f"{self.server_url}/mcp/request",
                json=request.dict()
            )
            response.raise_for_status()
            
            data = response.json()
            return MCPResponse(**data)
            
        except Exception as e:
            logger.error(f"MCP request failed: {e}")
            return MCPResponse(error={"message": str(e)})
    
    async def analyze_financial_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Use MCP to analyze financial data"""
        if not self._connected:
            return None
            
        response = await self._send_request("analyze_financial_data", {
            "data": data,
            "analysis_type": "comprehensive"
        })
        
        return response.result if response and not response.error else None
    
    async def generate_investment_insights(self, portfolio_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate AI-powered investment insights"""
        if not self._connected:
            return None
            
        response = await self._send_request("generate_insights", {
            "portfolio": portfolio_data,
            "insight_type": "investment_recommendations"
        })
        
        return response.result if response and not response.error else None
    
    async def assess_market_sentiment(self, news_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze market sentiment from news data"""
        if not self._connected:
            return None
            
        response = await self._send_request("analyze_sentiment", {
            "news_articles": news_data,
            "analysis_depth": "detailed"
        })
        
        return response.result if response and not response.error else None
    
    async def predict_price_movements(self, historical_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Predict price movements using AI models"""
        if not self._connected:
            return None
            
        response = await self._send_request("predict_prices", {
            "historical_data": historical_data,
            "prediction_horizon": "30_days"
        })
        
        return response.result if response and not response.error else None
    
    async def generate_risk_assessment(self, portfolio_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate comprehensive risk assessment"""
        if not self._connected:
            return None
            
        response = await self._send_request("assess_risk", {
            "portfolio": portfolio_data,
            "risk_metrics": ["var", "sharpe", "beta", "correlation"]
        })
        
        return response.result if response and not response.error else None
