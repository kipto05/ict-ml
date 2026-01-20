# Setup Files Collection

## 1. README.md

```markdown
# ICT ML Trading Bot

An institutional-grade automated trading system combining Inner Circle Trader (ICT) methodology with machine learning for MT5.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-development-yellow.svg)

## 🎯 Features

- **MT5 Integration**: Multi-account support with real-time streaming
- **ICT Concepts**: Market structure, liquidity, FVG, order blocks
- **Machine Learning**: Classification, regression, and RL models
- **Multi-Timeframe Analysis**: HTF bias → LTF execution
- **Smart Risk Management**: Dynamic position sizing and protection
- **Advanced Backtesting**: Tick-level accuracy with optimization
- **Real-time Dashboard**: React-based UI with live charts

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │
┌────────▼────────┐
│   FastAPI       │
│   REST API      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ Data  │ │  ML   │
│ Layer │ │ Layer │
└───┬───┘ └──┬────┘
    │        │
┌───▼────────▼────┐
│   Execution     │
│   Engine        │
└─────────────────┘
         │
    ┌────▼────┐
    │   MT5   │
    └─────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MetaTrader 5 installed
- PostgreSQL 14+
- Redis 7+
- Node.js 18+ (for frontend)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ict-ml-trading-bot.git
cd ict-ml-trading-bot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements/base.txt
pip install -r requirements/ml.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your MT5 credentials and settings
```

5. **Setup database**
```bash
python scripts/setup_database.py
```

6. **Run the application**
```bash
# Backend
python src/api/main.py

# Frontend (separate terminal)
cd frontend
npm install
npm start
```

### Docker Setup (Recommended)

```bash
docker-compose up -d
```

Access the application at `http://localhost:3000`

## 📖 Documentation

- [Product Requirements Document](docs/PRD.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [User Guide](docs/USER_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

## 📊 Development Status

### Phase 1: Foundation ✅
- [x] Project structure
- [x] MT5 connector
- [ ] Time handling
- [ ] Database setup

### Phase 2: ICT Logic Engine 🚧
- [ ] Market structure detection
- [ ] Liquidity detection
- [ ] FVG detection
- [ ] Order blocks
- [ ] Multi-timeframe analysis

### Phase 3: Machine Learning 📋
- [ ] Feature engineering
- [ ] Model training
- [ ] Backtesting framework

### Phase 4+: Coming Soon...

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational purposes only. Trading involves substantial risk. Past performance does not guarantee future results.

## 📧 Contact

- GitHub Issues: [Report bugs](https://github.com/yourusername/ict-ml-trading-bot/issues)
- Email: your.email@example.com

## 🙏 Acknowledgments

- ICT community
- MetaTrader 5
- Open source ML libraries
```


