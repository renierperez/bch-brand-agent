import requests
import logging
from datetime import datetime

def get_economic_indicators():
    """Obtiene indicadores económicos de Chile (UF, USD, EUR) desde mindicador.cl"""
    api_url = "https://mindicador.cl/api"
    
    for attempt in range(3):
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            break
        except Exception as e:
            logging.warning(f"Intento {attempt+1} fallido obteniendo indicadores: {e}")
            if attempt == 2:
                return None
    
    try:
        # Extraemos y formateamos solo lo que nos interesa
        indicators = {
            "UF": {
                "value": f"${data['uf']['valor']:,.2f}",
                "trend": "neutral" # Podrías comparar con el día anterior si quisieras
            },
            "Dolar": {
                "value": f"${data['dolar']['valor']:,.2f}",
                "name": "Dólar Obs."
            },
            "Euro": {
                "value": f"${data['euro']['valor']:,.2f}",
                "name": "Euro"
            },
            "UTM": { # Dato extra útil para bancos
                "value": f"${data['utm']['valor']:,.0f}",
                "name": "UTM"
            }
        }
        return indicators

    except Exception as e:
        logging.error(f"Error obteniendo indicadores económicos: {e}")
        # Fallback elegante para no romper el reporte
        return None
