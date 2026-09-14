import os
import pymongo
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URL") or "mongodb://localhost:27017/support_tickets_db"
DB_NAME = "support_tickets_db"

try:
    # Initialize PyMongo client with server selection timeout
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    # Ping server to confirm connection
    client.admin.command("ping")
    
    # Extract database name if specified in URI, otherwise default
    if "/" in MONGO_URI.replace("mongodb://", "").replace("mongodb+srv://", ""):
        parsed_db = MONGO_URI.split("/")[-1].split("?")[0]
        if parsed_db:
            DB_NAME = parsed_db
            
    db = client[DB_NAME]
    print(f"[Database Notice] Connected to MongoDB at {MONGO_URI} (db: {DB_NAME})")
except Exception as err:
    print(f"[Database Notice] Local MongoDB connection failed ({err}). Using mock in-memory fallback.")
    try:
        import mongomock
        client = mongomock.MongoClient()
        db = client[DB_NAME]
    except Exception as mock_err:
        raise RuntimeError(f"Failed to initialize both PyMongo and mongomock: {mock_err}")

tickets_collection = db["tickets"]

def get_db():
    """Dependency helper to get the database instance."""
    return db