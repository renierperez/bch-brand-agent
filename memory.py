import os
import logging
import hashlib
from typing import List, Dict, Any
from google.cloud import firestore
import datetime
from config import BRAND

class BrandMemory:
    def __init__(self, project_id: str = None):
        self.db = None
        if not project_id:
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            
        if project_id:
            try:
                self.db = firestore.Client(project=project_id)
                # Colecciones dinámicas basadas en la marca
                self.collection_name = f"{BRAND['id']}_processed_news"
                self.history_collection = f"{BRAND['id']}_brand_history"
            except Exception as e:
                logging.error(f"Error connecting to Firestore: {e}")
        else:
            logging.warning("⚠️ Firestore no inicializado: Faltan env vars.")

    def is_news_processed(self, url: str) -> bool:
        """Verifica si la noticia ya fue procesada."""
        if not self.db: return False
        
        docs = self.db.collection(self.collection_name).where("url", "==", url).stream()
        return any(True for _ in docs)

    def remember_news(self, news_item: dict):
        """Guarda la noticia en memoria."""
        if not self.db: return
        
        try:
            self.db.collection(self.collection_name).add({
                "url": news_item['link'],
                "title": news_item['title'],
                "processed_at": firestore.SERVER_TIMESTAMP,
                "sentiment": "unknown" 
            })
        except Exception as e:
            logging.error(f"Error saving to memory: {e}")

    def save_daily_summary(self, score: int):
        """Guarda el Brand Health Index del día."""
        if not self.db: return
        
        try:
            # Usamos timestamp como ID para historial cronológico
            doc_ref = self.db.collection(self.history_collection).document()
            doc_ref.set({
                "timestamp": firestore.SERVER_TIMESTAMP,
                "brand_index": score,
                "date_str": datetime.datetime.now().strftime("%Y-%m-%d")
            })
        except Exception as e:
            logging.error(f"Error guardando historial: {e}")

    def get_history_stats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Recupera el historial de Brand Health Index para el gráfico."""
        if not self.db: return []
        
        try:
            docs = self.db.collection(self.history_collection)\
                .order_by("timestamp", direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
            
            history = []
            for doc in docs:
                data = doc.to_dict()
                history.append({
                    "date": data.get("timestamp"), # Datetime object
                    "score": data.get("brand_index", 0)
                })
            
            # Reordenamos para que el gráfico vaya de izquierda (pasado) a derecha (presente)
            return sorted(history, key=lambda x: x['date'])
        except Exception as e:
            logging.error(f"Error recuperando historial: {e}")
            return []
