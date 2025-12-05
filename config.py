# config.py
import os
import yaml
import logging

# Variable de entorno que define qué banco estamos procesando
# Default a 'banco_chile' para desarrollo local
CURRENT_BRAND_ID = os.environ.get("BRAND_ID", "banco_chile")

def load_config():
    try:
        with open("brands_config.yaml", "r", encoding="utf-8") as f:
            all_brands = yaml.safe_load(f)
        
        if CURRENT_BRAND_ID not in all_brands:
            raise ValueError(f"❌ Error Fatal: BRAND_ID '{CURRENT_BRAND_ID}' no encontrado en brands_config.yaml")
            
        logging.info(f"📂 Configuración cargada para: {all_brands[CURRENT_BRAND_ID]['name']}")
        return all_brands[CURRENT_BRAND_ID]
        
    except FileNotFoundError:
        logging.error("❌ No se encontró brands_config.yaml")
        raise
    except Exception as e:
        logging.error(f"❌ Error leyendo configuración: {e}")
        raise

# Singleton: Cargamos la configuración una sola vez al importar
BRAND = load_config()
