import chromadb
from chromadb.utils import embedding_functions

# Initialize persistent/in-memory chroma client
chroma_client = chromadb.Client()

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

# Seed documents if empty
if collection.count() == 0:
    collection.add(
        ids=[d["id"] for d in ENTERPRISE_DOCS],
        documents=[d["doc"] for d in ENTERPRISE_DOCS]
    )

def query_support_kb(query_text: str, n_results: int = 2) -> dict:
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    if results and results.get("documents") and results["documents"][0]:
        retrieved_texts = results["documents"][0]
        matched_ids = results["ids"][0]
        return {
            "matched_ids": matched_ids,
            "context": " | ".join(retrieved_texts)
        }
    return {
        "matched_ids": [],
        "context": "No matching enterprise knowledge base documentation found."
    }
def query_knowledge_base(query_text: str, n_results: int = 2):
    # If your function was named query_support_kb or similar, call it here:
    if "query_support_kb" in globals():
        return query_support_kb(query_text, n_results)
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    if results and results.get("documents") and results["documents"][0]:
        return {
            "matched_ids": results["ids"][0],
            "context": " | ".join(results["documents"][0])
        }
    return {
        "matched_ids": [],
        "context": "No matching knowledge base documentation found."
    }
def initialize_chroma_db():
    """Startup initialization helper to verify or seed the collection."""
    if collection.count() == 0:
        collection.add(
            ids=[d["id"] for d in ENTERPRISE_DOCS],
            documents=[d["doc"] for d in ENTERPRISE_DOCS]
        )
    return True