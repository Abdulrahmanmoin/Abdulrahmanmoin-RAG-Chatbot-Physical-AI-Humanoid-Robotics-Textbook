
import sys
print("Starting script...", flush=True)
try:
    import sentence_transformers
    print("Imported sentence_transformers", flush=True)
    import qdrant_client
    print("Imported qdrant_client", flush=True)
except Exception as e:
    print(f"Import error: {e}", flush=True)
print("Done.", flush=True)
