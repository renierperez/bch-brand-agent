import os
import logging
from typing import List, Dict, Any
from google.cloud import firestore
import datetime

class BrandMemory:
    def __init__(self):
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if self.project_id:
            self.db = firestore.Client(project=self.project_id)
        else:
            self.db = None
            logging.warning("Firestore client not initialized: GOOGLE_CLOUD_PROJECT not set.")

    def store_mention(self, mention_id: str, source: str, text: str, sentiment: str, urgency: str):
        if not self.db:
            return
        
        doc_ref = self.db.collection("brand_mentions").document(mention_id)
        doc_ref.set({
            "source": source,
            "text": text,
            "sentiment": sentiment,
            "urgency": urgency,
            "timestamp": firestore.SERVER_TIMESTAMP
        })

    def get_recent_context(self, hours: int = 24) -> Dict[str, Any]:
        if not self.db:
            return {"error": "Firestore not available"}
        
        cutoff_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
        query = self.db.collection("brand_mentions").where("timestamp", ">=", cutoff_time)
        docs = query.stream()
        
        mentions = []
        for doc in docs:
            mentions.append(doc.to_dict())
        
        if not mentions:
            return {"total_mentions": 0, "avg_sentiment": 0, "status": "no data"}
        
        total_mentions = len(mentions)
        negative_mentions = sum(1 for m in mentions if m.get("sentiment") == "negativo")
        
        return {
            "total_mentions": total_mentions,
            "negative_mentions": negative_mentions,
            "negative_ratio": negative_mentions / total_mentions if total_mentions > 0 else 0,
            "status": "data available"
        }
