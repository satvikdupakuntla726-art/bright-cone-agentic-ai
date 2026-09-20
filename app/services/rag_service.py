import os
import chromadb
from chromadb.utils import embedding_functions

# Initialize persistent chroma client targeting local chroma_db directory
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
os.makedirs(CHROMA_DIR, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

# Embedding function default
emb_fn = embedding_functions.DefaultEmbeddingFunction()

collection = chroma_client.get_or_create_collection(
    name="brightcone_support_kb",
    embedding_function=emb_fn
)

# Comprehensive Enterprise Knowledge Base
ENTERPRISE_DOCS = [
    {
        "id": "policy_billing_refund",
        "doc": "Billing Policy: Automated refunds are strictly prohibited without human Level-2 financial approval. Duplicate charges are audited within 48 hours. Direct card chargebacks must be reviewed by the risk escalation desk."
    },
    {
        "id": "policy_subscription_cancellation",
        "doc": "Subscription Policy: Users can cancel monthly plans anytime under Billing Settings. Annual enterprise contracts require 30-day written cancellation notice."
    },
    {
        "id": "policy_account_security",
        "doc": "Account Security: Passwords must contain at least 10 characters including uppercase, lowercase, numeric, and special symbols. Reset links are delivered via registered 2FA email and expire in 15 minutes."
    },
    {
        "id": "kb_api_rate_limits",
        "doc": "Technical API Limits: Developer tier rate limit is 60 requests per minute. Enterprise tier supports up to 10,000 requests per minute. HTTP 429 Too Many Requests indicates throttling."
    },
    {
        "id": "kb_webhooks_integration",
        "doc": "Technical Webhooks: Webhook callbacks mandate HTTPS with valid TLS certificates. BrightCone signs each webhook payload with HMAC-SHA256 headers for authentication."
    },
    {
        "id": "policy_data_deletion",
        "doc": "Compliance & Privacy: GDPR and CCPA account data deletion requests have a mandatory 14-day grace window before irreversible database purging."
    }
]

def _load_faq_docs():
    """Load additional FAQ entries from app/data/faq.txt if available."""
    docs = []
    faq_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "faq.txt")
    if os.path.exists(faq_path):
        try:
            with open(faq_path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f, start=1):
                    clean_line = line.strip()
                    if clean_line:
                        docs.append({
                            "id": f"faq_{idx}",
                            "doc": clean_line
                        })
        except Exception as e:
            print(f"[RAG Notice] Could not read faq.txt: {e}")
    return docs

def initialize_chroma_db():
    """Startup initialization helper to seed documents from enterprise policies and faq.txt."""
    all_docs = ENTERPRISE_DOCS + _load_faq_docs()
    existing_ids = set(collection.get()["ids"]) if collection.count() > 0 else set()
    
    new_docs = [d for d in all_docs if d["id"] not in existing_ids]
    if new_docs:
        collection.add(
            ids=[d["id"] for d in new_docs],
            documents=[d["doc"] for d in new_docs]
        )
    return True

# Initialize on module load
try:
    initialize_chroma_db()
except Exception as err:
    print(f"[RAG Notice] Seeding warning: {err}")

def query_knowledge_base(query_text: str, n_results: int = 2) -> dict:
    """Query ChromaDB vector store for relevant enterprise documentation."""
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=min(n_results, max(1, collection.count()))
        )
        if results and results.get("documents") and results["documents"][0]:
            retrieved_texts = results["documents"][0]
            matched_ids = results["ids"][0]
            return {
                "matched_ids": matched_ids,
                "context": " | ".join(retrieved_texts)
            }
    except Exception as e:
        print(f"[RAG Notice] Query error: {e}")
        
    return {
        "matched_ids": [],
        "context": "No matching enterprise knowledge base documentation found."
    }

# Backward compatibility alias
query_support_kb = query_knowledge_base