import os
import logging
from typing import Dict, Any

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Analyzes sentiment of a given text.
    In a real scenario, this would use a specialized NLP model.
    For this MVP, we use a simple keyword-based approach or call a LLM.
    Here we will simulate it, but in production, it should call Gemini.
    """
    # Simple simulation for MVP
    text_lower = text.lower()
    negative_keywords = ["caída", "fraude", "malo", "fome", "peor", "problema", "no funciona", "estafa"]
    positive_keywords = ["bueno", "excelente", "gracias", "mejor", "rápido"]
    
    score = 0
    for kw in negative_keywords:
        if kw in text_lower:
            score -= 1
    for kw in positive_keywords:
        if kw in text_lower:
            score += 1
            
    sentiment = "neutral"
    urgency = "Verde"
    
    if score < 0:
        sentiment = "negativo"
        urgency = "Amarillo"
        if score < -2:
            urgency = "Rojo"
    elif score > 0:
        sentiment = "positivo"
        
    return {
        "score": score,
        "sentiment": sentiment,
        "urgency": urgency
    }
