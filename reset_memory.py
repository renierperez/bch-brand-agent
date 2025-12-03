import os
from google.cloud import firestore

def delete_collection(coll_ref, batch_size):
    docs = list(coll_ref.limit(batch_size).stream())
    deleted = 0

    if len(docs) > 0:
        for doc in docs:
            print(f'Deleting doc {doc.id} => {doc.to_dict()}')
            doc.reference.delete()
            deleted = deleted + 1

        if len(docs) >= batch_size:
            return delete_collection(coll_ref, batch_size) + deleted
    return deleted

def reset_memory():
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT env var not set.")
        return

    db = firestore.Client(project=project_id)
    collection_name = "bch_processed_news"
    coll_ref = db.collection(collection_name)

    print(f"🗑️ Deleting all documents in collection '{collection_name}'...")
    deleted_count = delete_collection(coll_ref, 10)
    print(f"✅ Deleted {deleted_count} documents. Memory reset complete.")

if __name__ == "__main__":
    reset_memory()
