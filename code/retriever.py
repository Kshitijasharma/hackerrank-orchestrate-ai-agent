import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from openai import AzureOpenAI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data")
EMBEDDINGS_CACHE = os.path.join(DATA_PATH, "embeddings.npy")

# -----------------------------
# Azure OpenAI client (embeddings)
# -----------------------------
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# -----------------------------
# 1. Load corpus
# -----------------------------
def load_corpus():
    docs = []

    for root, dirs, files in os.walk(DATA_PATH):
        # Sort directories and files to guarantee deterministic order across runs
        dirs.sort()
        files.sort()
        for file in files:
            if file.endswith((".txt", ".md", ".html", ".json")):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                    if content:
                        docs.append(content)

    print("Total docs loaded:", len(docs))
    return docs

# -----------------------------
# 2. Build TF-IDF index
# -----------------------------
def build_sparse_index(docs):
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(docs)
    return vectorizer, matrix

# -----------------------------
# 3. Dense embeddings
# -----------------------------
def get_embeddings(texts, batch_size=50):
    import time
    print(f"DEBUG: Generating embeddings for {len(texts)} documents in batches of {batch_size}...")
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        # Truncate each text to 8,000 characters. 
        # Dense data (like code or JSON) can have a 1:1 char-to-token ratio. 8000 chars guarantees it stays under 8192 tokens.
        truncated_batch = [t[:8000] for t in batch]
        
        print(f"DEBUG: Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} ({i} to {min(i+batch_size, len(texts))})...")
        try:
            response = client.embeddings.create(
                model=EMBEDDING_DEPLOYMENT,
                input=truncated_batch
            )
            all_embeddings.extend([d.embedding for d in response.data])
            time.sleep(0.5) # small sleep to help avoid rate limits
        except Exception as e:
            print(f"ERROR in embedding batch: {e}")
            raise e
            
    print(f"DEBUG: Successfully generated {len(all_embeddings)} embeddings.")
    return np.array(all_embeddings)

# -----------------------------
# 4. Initialize hybrid index
# -----------------------------
class HybridRetriever:
    def __init__(self, docs):
        self.docs = docs

        print("DEBUG: Building TF-IDF index...")
        # Sparse
        self.vectorizer, self.tfidf_matrix = build_sparse_index(docs)

        print("DEBUG: Checking for cached embeddings...")
        if os.path.exists(EMBEDDINGS_CACHE):
            print("DEBUG: Loading cached embeddings from disk (0 tokens used!)...")
            self.doc_embeddings = np.load(EMBEDDINGS_CACHE)
        else:
            print("DEBUG: Generating dense embeddings...")
            self.doc_embeddings = get_embeddings(docs)
            np.save(EMBEDDINGS_CACHE, self.doc_embeddings)
            print("DEBUG: Saved new embeddings to cache.")

    def retrieve(self, query, top_k=3, alpha=0.6):
        # ----- Sparse score -----
        q_sparse = self.vectorizer.transform([query])
        sparse_scores = (self.tfidf_matrix @ q_sparse.T).toarray().ravel()

        # ----- Dense score -----
        q_embed = get_embeddings([query])[0]
        dense_scores = np.dot(self.doc_embeddings, q_embed)

        # ----- Hybrid score -----
        combined = alpha * dense_scores + (1 - alpha) * sparse_scores

        # Top-k
        idxs = np.argsort(combined)[::-1][:top_k]

        results = [self.docs[i][:500] for i in idxs]
        return "\n\n".join(results)

# -----------------------------
# 5. Public API
# -----------------------------
def build_retriever():
    docs = load_corpus()
    return HybridRetriever(docs)