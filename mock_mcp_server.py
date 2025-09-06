#!/usr/bin/env python3
"""
Mock MCP Server for Financial Agent Demo
Provides AI-like responses for financial analysis without requiring external AI services
"""

import asyncio
import json
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

app = FastAPI(title="Mock MCP Server", version="1.0.0")


class MCPRequest(BaseModel):
    method: str
    params: Dict[str, Any]
    id: Optional[str] = None


class MCPResponse(BaseModel):
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    id: Optional[str] = None


# Mock financial knowledge base
FINANCIAL_RESPONSES = {
    "portfolio_analysis": [
        "Your portfolio shows strong diversification across sectors. Tech allocation at 35% is appropriate for growth-oriented strategy.",
        "Current portfolio beta of 1.2 indicates higher volatility than market. Consider adding defensive positions.",
        "Portfolio performance is tracking 2.3% above S&P 500 YTD. Strong stock selection in growth names.",
        "Risk-adjusted returns look solid. Sharpe ratio of 1.4 suggests good risk management.",
    ],

    "stock_recommendations": [
        "AAPL shows strong technical momentum with RSI at 55. Good entry point for long-term positions.",
        "TSLA trading near resistance. Wait for pullback to $200 support before adding exposure.",
        "MSFT fundamentals remain strong. Cloud growth driving revenue. Consider on any weakness.",
        "NVDA benefiting from AI boom but valuation stretched. Take profits on strength.",
    ],

    "market_outlook": [
        "Market showing resilience despite macro headwinds. Fed policy remains key catalyst.",
        "Earnings season approaching. Focus on companies with strong guidance and margin expansion.",
        "Sector rotation favoring value over growth. Consider rebalancing accordingly.",
        "VIX elevated suggests continued volatility. Maintain defensive cash allocation.",
    ],

    "risk_assessment": [
        "Current market environment suggests elevated risk. Recommend 15-20% cash allocation.",
        "Portfolio concentration risk acceptable but monitor position sizes in individual names.",
        "Interest rate sensitivity moderate. Duration risk manageable at current levels.",
        "Geopolitical risks remain elevated. Consider defensive sectors like utilities and healthcare.",
    ]
}

CHAT_RESPONSES = {
    "greeting": [
        "Hello! I'm your AI financial advisor. How can I help you optimize your portfolio today?",
        "Hi there! Ready to discuss your investment strategy and market opportunities?",
        "Welcome! I'm here to provide personalized financial insights and recommendations.",
    ],

    "portfolio_performance": [
        "Your portfolio is performing well with a 8.2% return YTD, beating the S&P 500 by 1.5%. Your tech holdings are the main drivers.",
        "Strong performance this quarter! Your diversified approach is paying off with consistent gains across sectors.",
        "Portfolio up 12.3% this year. Your value picks in financials and healthcare are outperforming expectations.",
    ],

    "investment_advice": [
        "Based on current market conditions, I recommend a balanced approach with 60% equities, 30% bonds, 10% cash.",
        "Consider dollar-cost averaging into quality growth names during market volatility.",
        "Current environment favors dividend-paying stocks and defensive sectors. Maintain diversification.",
    ]
}


def get_smart_response(context: Dict[str, Any], task: str) -> str:
    """Generate contextual financial advice based on request"""

    # Analyze the context to provide relevant response
    if "portfolio" in task.lower():
        if "performance" in str(context).lower():
            return random.choice(CHAT_RESPONSES["portfolio_performance"])
        else:
            return random.choice(FINANCIAL_RESPONSES["portfolio_analysis"])

    elif "stock" in task.lower() or "buy" in task.lower() or "sell" in task.lower():
        return random.choice(FINANCIAL_RESPONSES["stock_recommendations"])

    elif "market" in task.lower() or "outlook" in task.lower():
        return random.choice(FINANCIAL_RESPONSES["market_outlook"])

    elif "risk" in task.lower():
        return random.choice(FINANCIAL_RESPONSES["risk_assessment"])

    elif any(word in str(context).lower() for word in ["hello", "hi", "help"]):
        return random.choice(CHAT_RESPONSES["greeting"])

    else:
        return random.choice(CHAT_RESPONSES["investment_advice"])


@app.post("/mcp/request")
async def handle_mcp_request(request: MCPRequest):
    """Handle MCP protocol requests"""
    try:
        method = request.method
        params = request.params

        if method == "agent_reasoning":
            # Financial agent reasoning request
            context = params.get("context", {})
            task = params.get("task", "general_advice")

            # Generate intelligent response based on context
            advice = get_smart_response(context, task)

            result = {
                "reasoning": advice,
                "confidence": random.uniform(0.7, 0.95),
                "recommended_actions": [
                    {
                        "action": "monitor_positions",
                        "priority": "medium",
                        "reasoning": "Continue tracking current holdings performance"
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }

        elif method == "analyze_financial_data":
            # Financial data analysis request
            data = params.get("data", {})

            result = {
                "analysis": "Technical indicators suggest neutral to bullish sentiment. RSI at 58 indicates room for upward movement.",
                "signals": ["bullish_momentum", "volume_confirmation"],
                "confidence": random.uniform(0.6, 0.9),
                "timestamp": datetime.now().isoformat()
            }

        elif method == "chat_with_agent":
            # Chat interface request
            message = params.get("message", "")
            portfolio_id = params.get("portfolio_id", 1)

            # Generate contextual chat response
            response = get_smart_response({"message": message, "portfolio_id": portfolio_id}, message)

            result = {
                "response": response,
                "context_used": True,
                "timestamp": datetime.now().isoformat()
            }

        elif method == "get_market_insights":
            # Market insights request
            result = {
                "insights": random.choice(FINANCIAL_RESPONSES["market_outlook"]),
                "sentiment": random.choice(["bullish", "neutral", "bearish"]),
                "key_factors": ["fed_policy", "earnings_growth", "geopolitical_risks"],
                "timestamp": datetime.now().isoformat()
            }

        elif method == "ping":
            # Connection test request
            result = {
                "status": "ok",
                "message": "MCP server is running",
                "timestamp": datetime.now().isoformat()
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")

        return MCPResponse(result=result, id=request.id)

    except Exception as e:
        return MCPResponse(error=str(e), id=request.id)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Mock MCP Server",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Mock MCP Server for Financial Agent",
        "version": "1.0.0",
        "endpoints": {
            "mcp_request": "/mcp/request",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    print("🚀 Starting Mock MCP Server...")
    print("📍 Server will be available at: http://localhost:8081")
    print("🔗 Use this URL in your .env file: MCP_SERVER_URL=http://localhost:8081")

    uvicorn.run(
        "mock_mcp_server:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    )
