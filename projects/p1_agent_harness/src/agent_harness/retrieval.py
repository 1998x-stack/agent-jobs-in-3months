"""Minimal deterministic policy lookup. NOT RAG or grounded retrieval."""
POLICIES = {"refund": "Refunds require policy checks and human approval."}

def lookup_policy(topic: str) -> str:
    return POLICIES.get(topic, "No matching policy; request clarification.")
