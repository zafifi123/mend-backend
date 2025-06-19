import requests
import json
from typing import Dict, List, Any
from temporalio import activity
import asyncio
import aiohttp
import os
from temporal.models import LlamaRecommendation

@activity.defn
async def generate_llama_recommendations(
    market_data: Dict[str, Any], 
    rag_context: Dict[str, List[Dict[str, Any]]]
) -> List[LlamaRecommendation]:
    """Generate recommendations using Llama with RAG context."""
    
    recommendations = []
    
    for symbol, data in market_data.items():
        try:
            # Get RAG context for this symbol
            context_docs = rag_context.get(symbol, [])
            
            # Create prompt with context
            prompt = create_llama_prompt(symbol, data, context_docs)
            
            # Call Llama API
            response = await call_llama_api(prompt)
            
            # Parse Llama response
            recommendation = parse_llama_response(symbol, response, data)
            
            if recommendation:
                recommendations.append(recommendation)
                
        except Exception as e:
            print(f"Error generating Llama recommendation for {symbol}: {e}")
            continue
    
    # Sort by confidence
    recommendations.sort(key=lambda x: x.confidence, reverse=True)
    return recommendations

def create_llama_prompt(symbol: str, data: Dict[str, Any], context_docs: List[Dict[str, Any]]) -> str:
    """Create a comprehensive prompt for Llama with RAG context."""
    
    # Format technical indicators
    tech = data.get('technical_indicators', {})
    tech_summary = f"""
Technical Indicators for {symbol}:
- Current Price: ${data.get('current_price', 0):.2f}
- RSI: {tech.get('rsi', 0):.1f}
- MACD: {tech.get('macd', 0):.4f}
- Price vs SMA20: {tech.get('price_vs_sma20', 0):.1f}%
- Price vs SMA50: {tech.get('price_vs_sma50', 0):.1f}%
- Volume: {data.get('volume', 0):,}
- Market Cap: ${data.get('market_cap', 0):,.0f}
- P/E Ratio: {data.get('pe_ratio', 0):.1f}
- Beta: {data.get('beta', 0):.2f}
- Sector: {data.get('sector', 'N/A')}
"""
    
    # Format RAG context
    context_summary = ""
    if context_docs:
        context_summary = "\nRelevant Market Context:\n"
        for i, doc in enumerate(context_docs[:3], 1):  # Top 3 most relevant
            context_summary += f"{i}. {doc.get('title', '')}: {doc.get('content', '')[:200]}...\n"
    
    prompt = f"""You are an expert financial analyst. Based on the following data, provide a trading recommendation for {symbol}.

{tech_summary}{context_summary}

Please provide your analysis in the following JSON format:
{{
    "action": "BUY/SELL/HOLD",
    "confidence": 0.85,
    "reasoning": "Detailed explanation of your recommendation",
    "risk_level": "LOW/MEDIUM/HIGH",
    "timeframe": "1-3 days/3-7 days/1-2 weeks",
    "price_target": 150.00,
    "stop_loss": 140.00
}}

Consider:
1. Technical indicators (RSI, MACD, moving averages)
2. Market context and recent news
3. Sector performance and market conditions
4. Risk management principles
5. Current market volatility

Provide a well-reasoned recommendation based on the data provided."""

    return prompt

async def call_llama_api(prompt: str) -> str:
    """Call Llama API via HTTP."""
    
    # Get Ollama host from environment variable
    ollama_host = os.getenv('OLLAMA_HOST', 'localhost:11434')
    url = f"http://{ollama_host}/api/generate"
    
    payload = {
        "model": "llama3",  # Updated to llama3
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,  # Lower temperature for more consistent responses
            "top_p": 0.9,
            "max_tokens": 500
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '')
                else:
                    print(f"Llama API error: {response.status}")
                    return ""
    except Exception as e:
        print(f"Error calling Llama API: {e}")
        return ""

def parse_llama_response(symbol: str, response: str, data: Dict[str, Any]) -> LlamaRecommendation:
    """Parse Llama's response and extract recommendation."""
    
    try:
        # Try to extract JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response[json_start:json_end]
            parsed = json.loads(json_str)
            
            return LlamaRecommendation(
                symbol=symbol,
                action=parsed.get('action', 'HOLD'),
                confidence=float(parsed.get('confidence', 0.5)),
                reasoning=parsed.get('reasoning', 'No reasoning provided'),
                risk_level=parsed.get('risk_level', 'MEDIUM'),
                timeframe=parsed.get('timeframe', '3-7 days'),
                price_target=float(parsed.get('price_target', data.get('current_price', 0))),
                stop_loss=float(parsed.get('stop_loss', data.get('current_price', 0) * 0.95))
            )
        else:
            # Fallback parsing if JSON extraction fails
            return parse_fallback_response(symbol, response, data)
            
    except Exception as e:
        print(f"Error parsing Llama response for {symbol}: {e}")
        return parse_fallback_response(symbol, response, data)

def parse_fallback_response(symbol: str, response: str, data: Dict[str, Any]) -> LlamaRecommendation:
    """Fallback parsing if JSON extraction fails."""
    
    current_price = data.get('current_price', 0)
    
    # Simple keyword-based parsing
    response_lower = response.lower()
    
    if 'buy' in response_lower:
        action = 'BUY'
        confidence = 0.7
    elif 'sell' in response_lower:
        action = 'SELL'
        confidence = 0.7
    else:
        action = 'HOLD'
        confidence = 0.5
    
    # Extract reasoning
    reasoning = response[:200] + "..." if len(response) > 200 else response
    
    # Determine risk level
    if 'high risk' in response_lower or 'volatile' in response_lower:
        risk_level = 'HIGH'
    elif 'low risk' in response_lower or 'stable' in response_lower:
        risk_level = 'LOW'
    else:
        risk_level = 'MEDIUM'
    
    # Determine timeframe
    if 'short' in response_lower or 'day' in response_lower:
        timeframe = '1-3 days'
    elif 'week' in response_lower:
        timeframe = '1-2 weeks'
    else:
        timeframe = '3-7 days'
    
    # Calculate price targets
    if action == 'BUY':
        price_target = current_price * 1.05
        stop_loss = current_price * 0.95
    elif action == 'SELL':
        price_target = current_price * 0.95
        stop_loss = current_price * 1.05
    else:
        price_target = current_price
        stop_loss = current_price * 0.95
    
    return LlamaRecommendation(
        symbol=symbol,
        action=action,
        confidence=confidence,
        reasoning=reasoning,
        risk_level=risk_level,
        timeframe=timeframe,
        price_target=price_target,
        stop_loss=stop_loss
    )

@activity.defn
async def test_llama_connection() -> Dict[str, Any]:
    """Test connection to Llama API."""
    
    test_prompt = "Hello, please respond with 'OK' if you can see this message."
    
    try:
        response = await call_llama_api(test_prompt)
        return {
            "status": "success",
            "response": response,
            "connected": True
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "connected": False
        } 