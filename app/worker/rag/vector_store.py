import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple
import json
import os
from datetime import datetime

class FinancialVectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the vector store for financial documents."""
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.documents = []
        self.document_metadata = []
        
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store."""
        texts = []
        metadata = []
        
        for doc in documents:
            # Combine title and content for embedding
            text = f"{doc.get('title', '')} {doc.get('content', '')}"
            texts.append(text)
            metadata.append({
                'title': doc.get('title', ''),
                'content': doc.get('content', ''),
                'source': doc.get('source', ''),
                'date': doc.get('date', ''),
                'symbol': doc.get('symbol', ''),
                'type': doc.get('type', '')  # news, earnings, analyst_report, etc.
            })
        
        # Generate embeddings
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Initialize or update FAISS index
        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        
        # Store documents and metadata
        self.documents.extend(texts)
        self.document_metadata.extend(metadata)
    
    def search(self, query: str, k: int = 5, symbol_filter: str = None) -> List[Dict[str, Any]]:
        """Search for relevant documents."""
        if self.index is None:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.document_metadata):
                metadata = self.document_metadata[idx]
                
                # Apply symbol filter if specified
                if symbol_filter and metadata.get('symbol') != symbol_filter:
                    continue
                
                results.append({
                    'score': float(score),
                    'title': metadata['title'],
                    'content': metadata['content'],
                    'source': metadata['source'],
                    'date': metadata['date'],
                    'symbol': metadata['symbol'],
                    'type': metadata['type']
                })
        
        return results
    
    def save(self, filepath: str):
        """Save the vector store to disk."""
        if self.index is not None:
            faiss.write_index(self.index, f"{filepath}.index")
        
        with open(f"{filepath}.metadata.json", 'w') as f:
            json.dump(self.document_metadata, f)
    
    def load(self, filepath: str):
        """Load the vector store from disk."""
        if os.path.exists(f"{filepath}.index"):
            self.index = faiss.read_index(f"{filepath}.index")
        
        if os.path.exists(f"{filepath}.metadata.json"):
            with open(f"{filepath}.metadata.json", 'r') as f:
                self.document_metadata = json.load(f)

# Sample financial documents for testing
SAMPLE_DOCUMENTS = [
    {
        'title': 'Apple Q4 Earnings Beat Expectations',
        'content': 'Apple reported strong Q4 earnings with iPhone sales up 15% year-over-year. Services revenue continues to grow at 25% annually.',
        'source': 'Reuters',
        'date': '2024-01-15',
        'symbol': 'AAPL',
        'type': 'earnings'
    },
    {
        'title': 'Tesla Production Challenges in Q3',
        'content': 'Tesla faced supply chain issues affecting Model 3 production. However, demand remains strong with record pre-orders.',
        'source': 'Bloomberg',
        'date': '2024-01-10',
        'symbol': 'TSLA',
        'type': 'news'
    },
    {
        'title': 'Market Volatility Expected Due to Fed Meeting',
        'content': 'Federal Reserve meeting this week expected to cause market volatility. Analysts predict potential rate hike pause.',
        'source': 'CNBC',
        'date': '2024-01-12',
        'symbol': 'MARKET',
        'type': 'market_analysis'
    }
] 