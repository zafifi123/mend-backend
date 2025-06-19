from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class MLRecommendation:
    symbol: str
    action: str
    confidence: float
    reasoning: str
    risk_level: str
    timeframe: str
    price_target: float
    stop_loss: float

@dataclass
class LlamaRecommendation:
    symbol: str
    action: str
    confidence: float
    reasoning: str
    risk_level: str
    timeframe: str
    price_target: float
    stop_loss: float

@dataclass
class CombinedRecommendation:
    symbol: str
    action: str
    confidence: float
    reasoning: str
    risk_level: str
    timeframe: str
    price_target: float
    stop_loss: float
    ml_confidence: float
    llama_confidence: float
    consensus_score: float 