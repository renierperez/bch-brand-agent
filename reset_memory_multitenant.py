import os
from google.cloud import firestore
import logging

logging.basicConfig(level=logging.INFO)

def reset_brand_memory(brand_id):
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        logging.error("GOOGLE_CLOUD_PROJECT not set.")
        return

    db = firestore.Client(project=project_id)
    collection_name = f"{brand_id}_processed_news"
    
    logging.info(f"🗑️ Clearing memory for {brand_id} ({collection_name})...")
    
    docs = db.collection(collection_name).stream()
    deleted = 0
    for doc in docs:
        doc.reference.delete()
        deleted += 1
        
    logging.info(f"✅ Deleted {deleted} documents for {brand_id}.")

if __name__ == "__main__":
    reset_brand_memory("banco_chile")
    reset_brand_memory("banco_estado")
