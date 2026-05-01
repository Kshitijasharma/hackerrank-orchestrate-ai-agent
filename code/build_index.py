import os
from dotenv import load_dotenv
load_dotenv()

from retriever import build_retriever

if __name__ == "__main__":
    print("========================================")
    print("    Building Cached Embedding Index     ")
    print("========================================")
    
    # build_retriever will automatically trigger the generation
    # and save the embeddings to data/embeddings.npy
    build_retriever()
    
    print("\n✅ Index successfully built and cached to data/embeddings.npy!")
