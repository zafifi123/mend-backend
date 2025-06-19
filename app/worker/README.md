# Trading Recommendation System

A comprehensive trading recommendation system that combines classical ML, RAG (Retrieval-Augmented Generation), and Llama 3 LLM to generate daily trade recommendations.

## Architecture

The system uses Temporal workflows to orchestrate the following components:

1. **Data Collection**: Fetches market data from yfinance
2. **Classical ML Analysis**: Uses technical indicators and statistical models
3. **RAG System**: Retrieves relevant financial context using vector embeddings
4. **Llama 3 Integration**: Generates recommendations using local Llama 3 model
5. **Ensemble Combination**: Combines all analyses for final recommendations

## Prerequisites

1. **Docker and Docker Compose**
2. **Python 3.8+** (for local development)
3. **Git**

## Quick Start with Docker Compose

### 1. Clone and Setup

```bash
git clone <your-repo>
cd worker
```

### 2. Start All Services

```bash
# Start all services (production)
docker-compose up -d

# Or start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

### 3. Monitor Services

```bash
# View logs
docker-compose logs -f worker

# Check service status
docker-compose ps
```

### 4. Access Services

- **Temporal Web UI**: http://localhost:8233
- **Grafana**: http://localhost:3000 (admin/admin)
- **pgAdmin**: http://localhost:8080 (admin@trading.com/admin)
- **Redis Commander**: http://localhost:8081
- **Jupyter Lab**: http://localhost:8888

## Manual Setup (Alternative)

### 1. Install Dependencies

```bash
cd worker
pip install -r requirements.txt
```

### 2. Start Temporal Server

```bash
# Using Docker
docker run --rm -p 7233:7233 temporalio/auto-setup:1.22.0

# Or using Temporal CLI
temporal server start-dev
```

### 3. Start Ollama with Llama 3

```bash
# Install Ollama first, then:
ollama pull llama3
ollama serve
```

### 4. Start PostgreSQL

```bash
# Using Docker
docker run --name trading-postgres \
  -e POSTGRES_DB=trading_app \
  -e POSTGRES_USER=trading_user \
  -e POSTGRES_PASSWORD=trading_password \
  -p 5432:5432 \
  -d postgres:15

# Initialize database schema
psql -h localhost -U trading_user -d trading_app -f database_schema.sql
```

## Usage

### 1. Start the Worker

```bash
# With Docker Compose
docker-compose up worker

# Or manually
cd worker
python temporal/worker.py
```

### 2. Schedule Daily Recommendations

```bash
# With Docker Compose
docker-compose exec worker python scheduler.py

# Or manually
cd worker
python scheduler.py
```

### 3. Run Manual Test

```bash
# With Docker Compose
docker-compose exec worker python scheduler.py manual

# Or manually
cd worker
python scheduler.py manual
```

## Configuration

### Environment Variables

The system uses the following environment variables:

```bash
# Temporal
TEMPORAL_HOST=temporal:7233

# Ollama
OLLAMA_HOST=ollama:11434

# Database
DATABASE_URL=postgresql://trading_user:trading_password@postgres:5432/trading_app

# Development
DEBUG=true
LOG_LEVEL=DEBUG
```

### Stock Symbols

Edit `temporal/activities/data_collection.py` to modify the list of stocks to analyze:

```python
symbols = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
    # Add your preferred stocks here
]
```

### Llama 3 Model

The system is configured to use Llama 3. You can change the model variant in `temporal/activities/llama_analysis.py`:

```python
payload = {
    "model": "llama3",  # or "llama3:8b", "llama3:70b"
    # ...
}
```

### Analysis Weights

In `temporal/activities/combine_recommendations.py`, adjust the weights:

```python
ml_weight = 0.6      # Weight for ML analysis
llama_weight = 0.4   # Weight for Llama analysis
```

## Docker Compose Services

### Core Services

- **temporal**: Temporal server for workflow orchestration
- **postgres**: PostgreSQL database
- **ollama**: Ollama with Llama 3 models
- **worker**: Python worker service

### Optional Services

- **redis**: Caching layer
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboard
- **pgadmin**: Database management
- **jupyter**: Data analysis environment

## Development

### Development Mode

```bash
# Start with development overrides
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# This includes:
# - Source code mounting for live reload
# - Additional development tools
# - Debug logging
# - Jupyter notebook environment
```

### Testing

```bash
# Run tests
docker-compose exec worker pytest

# Run specific test
docker-compose exec worker pytest tests/test_ml_analysis.py
```

### Code Quality

```bash
# Format code
docker-compose exec worker black .

# Lint code
docker-compose exec worker flake8 .

# Type checking
docker-compose exec worker mypy .
```

## Monitoring

### Temporal Web UI

Access the Temporal Web UI at `http://localhost:8233` to monitor workflows.

### Grafana Dashboards

Access Grafana at `http://localhost:3000` (admin/admin) for:
- Workflow execution metrics
- System performance
- Recommendation statistics

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f worker
docker-compose logs -f temporal
```

## Troubleshooting

### Common Issues

1. **Llama 3 Model Not Found**
   ```bash
   # Check available models
   docker-compose exec ollama ollama list
   
   # Pull specific model
   docker-compose exec ollama ollama pull llama3:8b
   ```

2. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose exec postgres pg_isready -U trading_user
   
   # Reset database
   docker-compose down -v
   docker-compose up -d
   ```

3. **Temporal Connection Issues**
   ```bash
   # Check Temporal status
   curl http://localhost:8233
   
   # Restart Temporal
   docker-compose restart temporal
   ```

### Performance Optimization

1. **Memory Issues**
   ```bash
   # Increase Docker memory limit
   # Or reduce number of stocks analyzed
   ```

2. **Model Loading**
   ```bash
   # Use smaller Llama 3 variant
   # llama3:8b instead of llama3:70b
   ```

## Production Deployment

### Environment Variables

Create a `.env` file for production:

```bash
# Production settings
DEBUG=false
LOG_LEVEL=INFO
TEMPORAL_HOST=temporal:7233
OLLAMA_HOST=ollama:11434
DATABASE_URL=postgresql://trading_user:trading_password@postgres:5432/trading_app
```

### Security Considerations

1. **Change default passwords**
2. **Use secrets management**
3. **Enable SSL/TLS**
4. **Restrict network access**

### Scaling

```bash
# Scale worker instances
docker-compose up -d --scale worker=3

# Use external database
# Use managed Temporal service
# Use cloud-based Ollama
```

## API Integration

The recommendations are available via the FastAPI backend:

```bash
# Get latest recommendations
curl http://localhost:8000/api/recommendations

# Get recommendations for specific symbol
curl http://localhost:8000/api/recommendations/AAPL

# Get recommendation statistics
curl http://localhost:8000/api/recommendations/stats
```

## Future Enhancements

1. **Real-time Updates**: WebSocket integration
2. **Advanced ML Models**: Deep learning integration
3. **Sentiment Analysis**: Advanced news analysis
4. **Portfolio Optimization**: Multi-asset recommendations
5. **Backtesting**: Historical performance validation
6. **Risk Management**: Advanced risk assessment 