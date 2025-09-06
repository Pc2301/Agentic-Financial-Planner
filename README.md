# MCP-Powered Financial Analyst

A comprehensive financial analysis tool powered by Model Context Protocol (MCP) that provides intelligent financial insights, portfolio management, and risk assessment capabilities.

## Features

- **MCP Integration**: Leverages Model Context Protocol for enhanced AI-powered analysis
- **Financial Data Analysis**: Real-time stock prices, market trends, and financial ratios
- **Portfolio Management**: Track and analyze investment portfolios
- **Risk Assessment**: Calculate VaR, Sharpe ratio, and other risk metrics
- **Technical Analysis**: Moving averages, RSI, MACD, and more indicators
- **Reporting**: Generate comprehensive financial reports
- **Interactive Dashboard**: Web-based interface for financial analysis
- **Real-time Updates**: Live market data integration

## Architecture Diagram


## Code Structure

```
financial-analyst/
├── src/
│   ├── mcp/              # MCP integration layer
│   ├── data/             # Data fetching and processing
│   ├── analysis/         # Financial analysis modules
│   ├── portfolio/        # Portfolio management
│   ├── risk/             # Risk assessment tools
│   └── web/              # Web interface
├── config/               # Configuration files
├── tests/                # Test suite
└── docs/                 # Documentation
```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd financial-analyst

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
python src/main.py
```

## Usage

1. **Start the Application**: Run `python src/main.py`
2. **Access Dashboard**: Open `http://localhost:8080` in your browser
3. **Add Stocks**: Use the interface to add stocks to your watchlist
4. **Analyze Portfolio**: View comprehensive analysis and risk metrics
5. **Generate Reports**: Export detailed financial reports

## API Keys Required

- **Alpha Vantage**: For stock market data
- **Financial Modeling Prep**: For financial statements
- **News API**: For financial news sentiment analysis

## License

MIT License
