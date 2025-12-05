import os
import logging
from typing import List, Dict, Any
import requests

def search_social_media(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Monitors social media (X/Twitter) for mentions of the brand.
    Args:
        query: Search query (e.g., 'Banco de Chile').
        limit: Number of results to return.
    """
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        return [{"error": "SerpApi key not found."}]
    
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": f"(site:twitter.com OR site:linkedin.com OR site:facebook.com OR site:instagram.com OR site:reddit.com) {query}",
        "api_key": api_key,
        "num": limit
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = []
        for result in data.get("organic_results", []):
            results.append({
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet"),
                "date": result.get("date") or result.get("time_ago")
            })
        logging.info(f"📱 SerpApi Social Search for '{query}' found {len(results)} results.")
        for res in results[:3]: # Log first 3 for verification
            logging.info(f"   - [Social] {res.get('title')} ({res.get('link')})")
        return results
    except Exception as e:
        logging.error(f"SerpApi failed: {str(e)}")
        return [{"error": str(e)}]

def search_financial_news(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Monitors financial news for mentions of the brand."""
    # Placeholder for actual financial news API (e.g., Bloomberg, NewsAPI)
    # For now, uses Google Search limited to financial sites
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        return [{"error": "SerpApi key not found."}]
    
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": f"site:df.cl OR site:elmercurio.com {query}",
        "api_key": api_key,
        "num": limit
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = []
        for result in data.get("organic_results", []):
            results.append({
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": result.get("snippet"),
                "date": result.get("date") or result.get("time_ago")
            })
        return results
    except Exception as e:
        logging.error(f"SerpApi failed: {str(e)}")
        return [{"error": str(e)}]

def vertex_ai_search(query: str) -> str:
    """Uses Vertex AI Grounding with Google Search for fresh, reliable info.
    This is preferred over SerpApi for deep analysis.
    """
    try:
        from vertexai.generative_models import GenerativeModel, Tool
        import vertexai.preview.generative_models as generative_models
        
        # Initialize Vertex AI (assumes env vars set in Cloud Run)
        model = GenerativeModel("gemini-2.5-pro")
        # Workaround for SDK compatibility with google_search
        tools = [Tool.from_dict({'google_search': {}})]
        
        response = model.generate_content(query, tools=tools)
        return response.text
    except ImportError:
        return "Vertex AI SDK not installed. Fallback to SerpApi."
    except Exception as e:
        logging.error(f"Vertex AI Search failed: {str(e)}")
        return f"Error: {str(e)}"

def store_in_bigquery(data: List[Dict[str, Any]]):
    """Stores structured data in BigQuery for Looker Studio dashboards."""
    try:
        from google.cloud import bigquery
        client = bigquery.Client()
        table_id = f"{os.environ.get('GOOGLE_CLOUD_PROJECT')}.brand_monitoring.mentions"
        
        errors = client.insert_rows_json(table_id, data)
        if errors == []:
            return "Data inserted successfully."
        else:
            return f"Errors inserting data: {errors}"
    except ImportError:
        return "BigQuery SDK not installed."
    except Exception as e:
        return f"BigQuery error: {str(e)}"
