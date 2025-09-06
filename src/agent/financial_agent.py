"""
MCP-Powered Financial Agent
Autonomous financial advisor with reasoning, planning, and execution capabilities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import json

from mcp.client import MCPClient
from data.market_data import MarketDataService
from analysis.analyzer import FinancialAnalyzer
from portfolio.manager import PortfolioManager

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent operational states"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    LEARNING = "learning"


class Goal(Enum):
    """Financial goals the agent can work towards"""
    MAXIMIZE_RETURNS = "maximize_returns"
    MINIMIZE_RISK = "minimize_risk"
    BALANCED_GROWTH = "balanced_growth"
    INCOME_GENERATION = "income_generation"
    CAPITAL_PRESERVATION = "capital_preservation"


class Action:
    """Represents an action the agent can take"""

    def __init__(self, action_type: str, parameters: Dict[str, Any], confidence: float, reasoning: str):
        self.action_type = action_type
        self.parameters = parameters
        self.confidence = confidence
        self.reasoning = reasoning
        self.timestamp = datetime.now()
        self.executed = False
        self.result = None


class FinancialAgent:
    """Autonomous Financial Agent with MCP integration"""

    def __init__(self, mcp_client: MCPClient, market_data: MarketDataService,
                 analyzer: FinancialAnalyzer, portfolio_manager: PortfolioManager):
        self.mcp_client = mcp_client
        self.market_data = market_data
        self.analyzer = analyzer
        self.portfolio_manager = portfolio_manager

        self.state = AgentState.IDLE
        self.current_goal = Goal.BALANCED_GROWTH
        self.risk_tolerance = 0.5  # 0 = conservative, 1 = aggressive
        self.target_portfolio_value = 100000

        # Agent memory and learning
        self.memory = {
            'successful_strategies': [],
            'failed_strategies': [],
            'market_patterns': {},
            'user_preferences': {},
            'performance_history': []
        }

        # Action queue and history
        self.pending_actions = []
        self.action_history = []

        # Monitoring settings
        self.monitoring_interval = 300  # 5 minutes
        self.last_analysis = None

    async def start_autonomous_mode(self, portfolio_id: int, goal: Goal = Goal.BALANCED_GROWTH):
        """Start autonomous financial management"""
        logger.info(f"Starting autonomous mode for portfolio {portfolio_id} with goal: {goal}")

        self.current_goal = goal
        self.state = AgentState.MONITORING

        # Start the main agent loop
        await self._agent_loop(portfolio_id)

    async def _agent_loop(self, portfolio_id: int):
        """Main agent reasoning and execution loop"""
        while self.state != AgentState.IDLE:
            try:
                # 1. Analyze current situation
                await self._analyze_situation(portfolio_id)

                # 2. Reason about next actions
                await self._reason_and_plan(portfolio_id)

                # 3. Execute high-confidence actions
                await self._execute_actions(portfolio_id)

                # 4. Learn from results
                await self._learn_and_adapt()

                # 5. Wait before next cycle
                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in agent loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _analyze_situation(self, portfolio_id: int):
        """Analyze current market and portfolio situation"""
        self.state = AgentState.ANALYZING

        try:
            # Get current portfolio analysis
            portfolio_analysis = await self.portfolio_manager.analyze_portfolio(portfolio_id)

            # Get market conditions
            market_data = await self.market_data.get_market_indices()
            sector_data = await self.market_data.get_sector_performance()

            # Analyze each holding
            holdings = self.portfolio_manager.get_holdings(portfolio_id)
            holding_analyses = []

            for holding in holdings:
                analysis = await self.analyzer.analyze_stock(holding.symbol)
                holding_analyses.append({
                    'holding': holding,
                    'analysis': analysis
                })

            # Store current situation
            self.current_situation = {
                'timestamp': datetime.now(),
                'portfolio': portfolio_analysis,
                'market': market_data,
                'sectors': sector_data,
                'holdings': holding_analyses
            }

            logger.info("Situation analysis complete")

        except Exception as e:
            logger.error(f"Error analyzing situation: {e}")

    async def _reason_and_plan(self, portfolio_id: int):
        """Use MCP to reason about the situation and plan actions"""
        self.state = AgentState.PLANNING

        try:
            if not self.mcp_client.is_connected():
                # Fallback to rule-based reasoning
                await self._rule_based_reasoning()
                return

            # Prepare context for MCP reasoning
            reasoning_context = {
                'goal': self.current_goal.value,
                'risk_tolerance': self.risk_tolerance,
                'current_situation': self.current_situation,
                'memory': self.memory,
                'target_value': self.target_portfolio_value
            }

            # Get AI reasoning from MCP
            reasoning_result = await self.mcp_client._send_request("agent_reasoning", {
                'context': reasoning_context,
                'task': 'financial_portfolio_management'
            })

            if reasoning_result and not reasoning_result.error:
                await self._process_mcp_reasoning(reasoning_result.result)
            else:
                # Fallback to rule-based reasoning
                await self._rule_based_reasoning()

        except Exception as e:
            logger.error(f"Error in reasoning: {e}")
            await self._rule_based_reasoning()

    async def _process_mcp_reasoning(self, reasoning_result: Dict[str, Any]):
        """Process MCP reasoning results into actionable plans"""
        try:
            # Extract recommended actions from MCP
            recommended_actions = reasoning_result.get('recommended_actions', [])
            reasoning = reasoning_result.get('reasoning', '')
            confidence = reasoning_result.get('confidence', 0.5)

            logger.info(f"MCP Reasoning: {reasoning}")

            # Convert MCP recommendations to Action objects
            for action_data in recommended_actions:
                action = Action(
                    action_type=action_data['type'],
                    parameters=action_data['parameters'],
                    confidence=action_data.get('confidence', confidence),
                    reasoning=action_data.get('reasoning', reasoning)
                )

                # Only queue high-confidence actions
                if action.confidence > 0.7:
                    self.pending_actions.append(action)
                    logger.info(f"Queued action: {action.action_type} (confidence: {action.confidence})")

        except Exception as e:
            logger.error(f"Error processing MCP reasoning: {e}")

    async def _rule_based_reasoning(self):
        """Fallback rule-based reasoning when MCP is unavailable"""
        try:
            portfolio = self.current_situation['portfolio']

            # Rule 1: Rebalance if allocation is off
            if 'sector_allocation' in portfolio:
                await self._check_rebalancing_needs()

            # Rule 2: Take profits on big winners
            await self._check_profit_taking()

            # Rule 3: Cut losses on big losers
            await self._check_stop_losses()

            # Rule 4: Add to positions on dips
            await self._check_buying_opportunities()

            logger.info("Rule-based reasoning complete")

        except Exception as e:
            logger.error(f"Error in rule-based reasoning: {e}")

    async def _check_rebalancing_needs(self):
        """Check if portfolio needs rebalancing"""
        portfolio = self.current_situation['portfolio']
        sector_allocation = portfolio.get('sector_allocation', {})

        # Target allocation based on goal
        target_allocations = self._get_target_allocation()

        for sector, current_pct in sector_allocation.items():
            target_pct = target_allocations.get(sector, 0)
            deviation = abs(current_pct - target_pct)

            if deviation > 10:  # More than 10% deviation
                action = Action(
                    action_type="rebalance_sector",
                    parameters={
                        'sector': sector,
                        'current_allocation': current_pct,
                        'target_allocation': target_pct
                    },
                    confidence=0.8,
                    reasoning=f"Sector {sector} is {deviation:.1f}% off target allocation"
                )
                self.pending_actions.append(action)

    async def _check_profit_taking(self):
        """Check for profit-taking opportunities"""
        holdings = self.current_situation['holdings']

        for holding_data in holdings:
            holding = holding_data['holding']
            analysis = holding_data['analysis']

            if 'error' in analysis:
                continue

            # Get current performance
            basic_data = analysis.get('basic_data', {})
            current_price = basic_data.get('current_price', 0)

            if current_price > 0:
                gain_pct = ((current_price - holding.avg_cost) / holding.avg_cost) * 100

                # Take profits if gain > 20% and technical indicators suggest overbought
                technical = analysis.get('technical_analysis', {})
                momentum = technical.get('momentum', {})
                rsi = momentum.get('rsi', 50)

                if gain_pct > 20 and rsi > 70:
                    action = Action(
                        action_type="sell_partial",
                        parameters={
                            'symbol': holding.symbol,
                            'quantity': holding.quantity * 0.25,  # Sell 25%
                            'reason': 'profit_taking'
                        },
                        confidence=0.75,
                        reasoning=f"{holding.symbol} up {gain_pct:.1f}% and RSI overbought at {rsi}"
                    )
                    self.pending_actions.append(action)

    async def _check_stop_losses(self):
        """Check for stop-loss triggers"""
        holdings = self.current_situation['holdings']

        for holding_data in holdings:
            holding = holding_data['holding']
            analysis = holding_data['analysis']

            if 'error' in analysis:
                continue

            basic_data = analysis.get('basic_data', {})
            current_price = basic_data.get('current_price', 0)

            if current_price > 0:
                loss_pct = ((current_price - holding.avg_cost) / holding.avg_cost) * 100

                # Stop loss at -15% or if technical breakdown
                technical = analysis.get('technical_analysis', {})
                trend = technical.get('trend_analysis', {})
                overall_trend = trend.get('overall', 'neutral')

                if loss_pct < -15 or (loss_pct < -10 and overall_trend == 'bearish'):
                    action = Action(
                        action_type="sell_all",
                        parameters={
                            'symbol': holding.symbol,
                            'quantity': holding.quantity,
                            'reason': 'stop_loss'
                        },
                        confidence=0.9,
                        reasoning=f"{holding.symbol} down {abs(loss_pct):.1f}% - stop loss triggered"
                    )
                    self.pending_actions.append(action)

    async def _check_buying_opportunities(self):
        """Check for buying opportunities"""
        # This would analyze watchlist stocks for buying opportunities
        # For now, just log that we're checking
        logger.info("Checking for buying opportunities...")

    def _get_target_allocation(self) -> Dict[str, float]:
        """Get target sector allocation based on current goal"""
        if self.current_goal == Goal.MAXIMIZE_RETURNS:
            return {'Technology': 40, 'Healthcare': 20, 'Financials': 15, 'Consumer Discretionary': 25}
        elif self.current_goal == Goal.MINIMIZE_RISK:
            return {'Utilities': 25, 'Consumer Staples': 25, 'Healthcare': 25, 'Financials': 25}
        elif self.current_goal == Goal.INCOME_GENERATION:
            return {'Utilities': 30, 'Real Estate': 25, 'Financials': 25, 'Energy': 20}
        else:  # BALANCED_GROWTH
            return {'Technology': 25, 'Healthcare': 20, 'Financials': 20, 'Consumer Discretionary': 15,
                    'Industrials': 20}

    async def _execute_actions(self, portfolio_id: int):
        """Execute queued actions"""
        self.state = AgentState.EXECUTING

        executed_actions = []

        for action in self.pending_actions:
            try:
                if action.confidence > 0.8:  # Only execute high-confidence actions
                    result = await self._execute_single_action(portfolio_id, action)
                    action.executed = True
                    action.result = result
                    executed_actions.append(action)

                    logger.info(f"Executed action: {action.action_type} - {action.reasoning}")

            except Exception as e:
                logger.error(f"Error executing action {action.action_type}: {e}")
                action.result = {'error': str(e)}

        # Move executed actions to history
        self.action_history.extend(executed_actions)
        self.pending_actions = [a for a in self.pending_actions if not a.executed]

    async def _execute_single_action(self, portfolio_id: int, action: Action) -> Dict[str, Any]:
        """Execute a single action"""
        if action.action_type == "sell_partial":
            # In a real implementation, this would place actual trades
            # For now, we'll just log and update the database
            symbol = action.parameters['symbol']
            quantity = action.parameters['quantity']

            # Remove partial holding
            success = self.portfolio_manager.remove_holding(portfolio_id, symbol, quantity)
            return {'success': success, 'action': 'partial_sell', 'symbol': symbol, 'quantity': quantity}

        elif action.action_type == "sell_all":
            symbol = action.parameters['symbol']
            success = self.portfolio_manager.remove_holding(portfolio_id, symbol)
            return {'success': success, 'action': 'full_sell', 'symbol': symbol}

        elif action.action_type == "rebalance_sector":
            # Rebalancing logic would go here
            return {'success': True, 'action': 'rebalance', 'sector': action.parameters['sector']}

        else:
            return {'success': False, 'error': f'Unknown action type: {action.action_type}'}

    async def _learn_and_adapt(self):
        """Learn from action results and adapt strategy"""
        self.state = AgentState.LEARNING

        # Analyze recent action performance
        recent_actions = [a for a in self.action_history if
                          (datetime.now() - a.timestamp).days < 7]

        successful_actions = [a for a in recent_actions if
                              a.result and a.result.get('success', False)]

        # Update memory with successful strategies
        for action in successful_actions:
            strategy = {
                'action_type': action.action_type,
                'parameters': action.parameters,
                'confidence': action.confidence,
                'reasoning': action.reasoning,
                'timestamp': action.timestamp.isoformat()
            }
            self.memory['successful_strategies'].append(strategy)

        # Keep memory size manageable
        if len(self.memory['successful_strategies']) > 100:
            self.memory['successful_strategies'] = self.memory['successful_strategies'][-100:]

        logger.info(f"Learning complete. {len(successful_actions)} successful actions recorded.")

    async def chat_with_agent(self, message: str, portfolio_id: int) -> str:
        """Natural language interface with the agent"""
        try:
            if not self.mcp_client.is_connected():
                return "I'm currently operating in basic mode. MCP connection needed for full conversational capabilities."

            # Get current context
            portfolio_analysis = await self.portfolio_manager.analyze_portfolio(portfolio_id)

            # Send to MCP for natural language processing
            chat_context = {
                'user_message': message,
                'portfolio_state': portfolio_analysis,
                'agent_memory': self.memory,
                'current_goal': self.current_goal.value,
                'recent_actions': [a.__dict__ for a in self.action_history[-5:]]
            }

            response = await self.mcp_client._send_request("chat_with_agent", {
                "message": message,
                "portfolio_id": portfolio_id
            })

            if response and not response.error:
                return response.result.get('response', 'I understand, but I need more information to help you.')
            else:
                return "I'm having trouble processing your request right now. Please try again."

        except Exception as e:
            logger.error(f"Error in agent chat: {e}")
            return "I encountered an error processing your message. Please try again."

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            'state': self.state.value,
            'goal': self.current_goal.value,
            'risk_tolerance': self.risk_tolerance,
            'pending_actions': len(self.pending_actions),
            'actions_executed_today': len([a for a in self.action_history if
                                           (datetime.now() - a.timestamp).days == 0]),
            'successful_strategies': len(self.memory['successful_strategies']),
            'last_analysis': self.last_analysis.isoformat() if self.last_analysis else None,
            'uptime': datetime.now().isoformat()
        }

    def stop_autonomous_mode(self):
        """Stop autonomous operation"""
        self.state = AgentState.IDLE
        logger.info("Agent stopped autonomous mode")
