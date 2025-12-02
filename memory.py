import os
import logging
import hashlib
from typing import List, Dict, Any
from google.cloud import firestore
import datetime

class BrandMemory:
    def __init__(self):
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.collection_name = "bch_processed_news"
        if self.project_id:
            self.db = firestore.Client(project=self.project_id)
        else:
            self.db = None
            logging.warning("⚠️ Firestore no inicializado: Faltan env vars.")

    def is_duplicate(self, url: str) -> bool:
        """Verifica si la URL ya fue procesada anteriormente."""
        if not self.db or not url: return False
        
        # Hash determinista de la URL para usar como ID de documento
        doc_id = hashlib.md5(url.encode('utf-8')).hexdigest()
        doc_ref = self.db.collection(self.collection_name).document(doc_id)
        
        try:
            doc = doc_ref.get()
            return doc.exists
        except Exception as e:
            logging.error(f"Error consultando Firestore: {e}")
            return False

    def remember_news(self, news_item: Dict[str, Any]):
        """Guarda la noticia procesada para no repetirla."""
        if not self.db: return
        
        url = news_item.get('link') or news_item.get('url')
        if not url: return

        doc_id = hashlib.md5(url.encode('utf-8')).hexdigest()
        doc_ref = self.db.collection(self.collection_name).document(doc_id)
        
        doc_ref.set({
            "title": news_item.get('title'),
            "url": url,
            "processed_at": firestore.SERVER_TIMESTAMP,
            "sentiment": news_item.get('sentiment', 'unknown')
        })
