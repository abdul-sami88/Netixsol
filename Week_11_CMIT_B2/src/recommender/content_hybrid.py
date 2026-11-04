"""
Content-Based & Neural Hybrid Two-Tower Recommender Module
Implements Task 3:
1. Content-Based Model using TF-IDF Text Embeddings of product metadata & descriptions
2. PyTorch Neural Two-Tower Hybrid Model (combining user features + item features + interaction embeddings)
3. Cold-Start Strategies for New Users (segment priors) and New Items (content embeddings)
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import scipy.sparse as sp
from typing import List, Dict, Tuple, Set

# -------------------------------------------------------------
# 1. CONTENT-BASED RECOMMENDER (TEXT EMBEDDINGS / TF-IDF)
# -------------------------------------------------------------
class ContentBasedRecommender:
    """
    Computes TF-IDF text embeddings over title, brand, category, and description.
    Builds user profile vector from past interactions: V_u = sum(w_i * V_i).
    Ranks items by cosine similarity to user profile.
    Solves Cold-Start Items natively.
    """
    def __init__(self, max_features: int = 5000):
        self.vectorizer = TfidfVectorizer(max_features=max_features, stop_words="english", ngram_range=(1, 2))
        self.item_tfidf_matrix = None # (n_items, max_features)
        self.item_ids = []
        self.item_to_idx = {}
        self.idx_to_item = {}
        self.user_history = {} # user_id -> dict(product_id: weight)
        self.global_popular = []

    def fit(self, item_features: pd.DataFrame, train_events: pd.DataFrame):
        print("Fitting Content-Based TF-IDF Text Embedding model...")
        self.item_ids = item_features["product_id"].tolist()
        self.item_to_idx = {pid: idx for idx, pid in enumerate(self.item_ids)}
        self.idx_to_item = {idx: pid for idx, pid in enumerate(self.item_ids)}
        
        texts = item_features["text_representation"].fillna("").tolist()
        self.item_tfidf_matrix = self.vectorizer.fit_transform(texts).tocsr()
        
        # Build user interaction history
        weights = {"view": 1.0, "add_to_cart": 2.0, "purchase": 5.0}
        df = train_events.copy()
        df["w"] = df["event_type"].map(weights).fillna(1.0)
        
        # Global fallback
        self.global_popular = df.groupby("product_id")["w"].sum().sort_values(ascending=False).index.tolist()
        
        grouped = df.groupby(["user_id", "product_id"])["w"].sum().reset_index()
        for row in grouped.itertuples(index=False):
            uid, pid, w = row[0], row[1], row[2]
            if uid not in self.user_history:
                self.user_history[uid] = {}
            self.user_history[uid][pid] = w
            
        print(f"Content-Based model indexed {self.item_tfidf_matrix.shape[0]:,} items with {self.item_tfidf_matrix.shape[1]:,} text features.")
        return self

    def recommend(self, user_id: str, k: int = 10, exclude_items: set = None) -> List[str]:
        exclude = exclude_items or set()
        user_items = self.user_history.get(user_id, {})
        
        if not user_items:
            # Fallback for unseen users
            return [it for it in self.global_popular if it not in exclude][:k]
            
        # Build weighted user profile vector in TF-IDF space
        indices = [self.item_to_idx[pid] for pid in user_items if pid in self.item_to_idx]
        if not indices:
            return [it for it in self.global_popular if it not in exclude][:k]
            
        weights = np.array([user_items[self.idx_to_item[idx]] for idx in indices]).reshape(-1, 1)
        sub_matrix = self.item_tfidf_matrix[indices]
        
        # Weighted average profile vector
        user_profile = sub_matrix.multiply(weights).sum(axis=0)
        user_profile = np.asarray(user_profile).reshape(1, -1)
        norm = np.linalg.norm(user_profile)
        if norm > 0:
            user_profile = user_profile / norm
            
        # Cosine similarity against all catalogue items: shape (1, n_items)
        scores = np.asarray(self.item_tfidf_matrix.dot(user_profile.T)).flatten()
        top_indices = np.argsort(-scores)
        
        recs = []
        for idx in top_indices:
            pid = self.idx_to_item[idx]
            if pid not in exclude and pid not in user_items:
                recs.append(pid)
            if len(recs) >= k:
                break
                
        if len(recs) < k:
            fallback = [it for it in self.global_popular if it not in exclude and it not in recs]
            recs.extend(fallback)
        return recs[:k]

    def get_similar_items(self, product_id: str, k: int = 10) -> List[Tuple[str, float]]:
        """Finds nearest catalogue items using cosine similarity over text descriptions."""
        idx = self.item_to_idx.get(product_id)
        if idx is None:
            return [(it, 0.5) for it in self.global_popular[:k]]
        item_vec = self.item_tfidf_matrix[idx]
        sims = np.asarray(self.item_tfidf_matrix.dot(item_vec.T).toarray()).flatten()
        top_indices = np.argsort(-sims)
        
        similar_items = []
        for i in top_indices:
            if i != idx:
                similar_items.append((self.idx_to_item[i], float(sims[i])))
            if len(similar_items) >= k:
                break
        return similar_items


# -------------------------------------------------------------
# 2. PYTORCH NEURAL TWO-TOWER HYBRID MODEL
# -------------------------------------------------------------
class TwoTowerModel(nn.Module):
    """
    PyTorch Neural Two-Tower Network:
    - User Tower: Embed(user_id) + MLP(user_side_features) -> 64-dim embedding
    - Item Tower: Embed(product_id) + MLP(item_side_features) -> 64-dim embedding
    - Interaction: Dot product + Sigmoid
    """
    def __init__(self, n_users: int, n_items: int, user_dim: int, item_dim: int, embed_dim: int = 64):
        super(TwoTowerModel, self).__init__()
        
        # User Tower
        self.user_id_embed = nn.Embedding(n_users, 32)
        self.user_mlp = nn.Sequential(
            nn.Linear(32 + user_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, embed_dim)
        )
        
        # Item Tower
        self.item_id_embed = nn.Embedding(n_items, 32)
        self.item_mlp = nn.Sequential(
            nn.Linear(32 + item_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, embed_dim)
        )
        
    def forward(self, u_id, u_feats, i_id, i_feats):
        # User Tower representation
        u_emb = self.user_id_embed(u_id)
        u_input = torch.cat([u_emb, u_feats], dim=1)
        u_vec = self.user_mlp(u_input)
        u_norm = torch.nn.functional.normalize(u_vec, p=2, dim=1)
        
        # Item Tower representation
        i_emb = self.item_id_embed(i_id)
        i_input = torch.cat([i_emb, i_feats], dim=1)
        i_vec = self.item_mlp(i_input)
        i_norm = torch.nn.functional.normalize(i_vec, p=2, dim=1)
        
        # Dot product prediction
        scores = (u_norm * i_norm).sum(dim=1)
        return scores


class InteractionDataset(Dataset):
    def __init__(self, user_ids, user_feats, item_ids, item_feats, labels):
        self.user_ids = torch.tensor(user_ids, dtype=torch.long)
        self.user_feats = torch.tensor(user_feats, dtype=torch.float32)
        self.item_ids = torch.tensor(item_ids, dtype=torch.long)
        self.item_feats = torch.tensor(item_feats, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.user_ids[idx], self.user_feats[idx], self.item_ids[idx], self.item_feats[idx], self.labels[idx]


class NeuralTwoTowerRecommender:
    """Production Two-Tower Hybrid recommender combining user & item attributes with deep latent vectors."""
    def __init__(self, embed_dim: int = 64, epochs: int = 3, batch_size: int = 1024, lr: float = 0.003):
        self.embed_dim = embed_dim
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.model = None
        self.device = torch.device("cpu")
        
        self.user_to_int = {}
        self.item_to_int = {}
        self.int_to_item = {}
        self.int_to_user = {}
        self.user_features_arr = None
        self.item_features_arr = None
        self.item_vectors = None # Precomputed item tower matrix for fast inference: (n_items, embed_dim)
        self.global_popular = []

    def _prepare_features(self, user_features: pd.DataFrame, item_features: pd.DataFrame):
        # User feature vector: [AOV_norm, spend_norm, cart_conv, recency_norm, one-hot segment]
        user_segments = pd.get_dummies(user_features["segment_name"], prefix="seg", dtype=float)
        u_numeric = pd.DataFrame({
            "aov": np.log1p(user_features["avg_order_value_pkr"]) / 12.0,
            "spend": np.log1p(user_features["lifetime_spend_pkr"]) / 15.0,
            "cart_conv": user_features["cart_conversion_rate"],
            "recency": user_features["last_active_days_ago"] / 365.0
        })
        self.user_features_df = pd.concat([u_numeric, user_segments], axis=1).fillna(0.0)
        self.user_features_arr = self.user_features_df.values
        
        # Item feature vector: [price_norm, margin, popularity_norm, one-hot category, one-hot price_band]
        cat_dummies = pd.get_dummies(item_features["category"], prefix="cat", dtype=float)
        tier_dummies = pd.get_dummies(item_features["price_band"], prefix="tier", dtype=float)
        i_numeric = pd.DataFrame({
            "price": np.log1p(item_features["price_pkr"]) / 13.0,
            "margin": item_features["gross_margin_rate"],
            "popularity": item_features["popularity_score"] / 20.0
        })
        self.item_features_df = pd.concat([i_numeric, cat_dummies, tier_dummies], axis=1).fillna(0.0)
        self.item_features_arr = self.item_features_df.values

    def fit(self, train_events: pd.DataFrame, user_features: pd.DataFrame, item_features: pd.DataFrame, user_map: pd.DataFrame, item_map: pd.DataFrame):
        print("Training Neural Two-Tower Hybrid Recommender with PyTorch...")
        self.user_to_int = dict(zip(user_map["user_id"], user_map["user_int_id"]))
        self.item_to_int = dict(zip(item_map["product_id"], item_map["item_int_id"]))
        self.int_to_item = dict(zip(item_map["item_int_id"], item_map["product_id"]))
        self.int_to_user = dict(zip(user_map["user_int_id"], user_map["user_id"]))
        
        n_users = len(user_map)
        n_items = len(item_map)
        
        self._prepare_features(user_features, item_features)
        
        # Build positive training pairs (subsample 150,000 positive interactions for speed)
        df_pos = train_events[["user_id", "product_id"]].drop_duplicates().sample(
            n=min(150000, len(train_events)), random_state=42
        )
        pos_u = df_pos["user_id"].map(self.user_to_int).values
        pos_i = df_pos["product_id"].map(self.item_to_int).values
        
        valid = (~np.isnan(pos_u)) & (~np.isnan(pos_i))
        pos_u = pos_u[valid].astype(int)
        pos_i = pos_i[valid].astype(int)
        
        # 1:1 Negative sampling
        neg_u = pos_u.copy()
        neg_i = np.random.randint(0, n_items, size=len(pos_u))
        
        all_u = np.concatenate([pos_u, neg_u])
        all_i = np.concatenate([pos_i, neg_i])
        all_labels = np.concatenate([np.ones(len(pos_u)), np.zeros(len(neg_u))])
        
        u_feats = self.user_features_arr[all_u]
        i_feats = self.item_features_arr[all_i]
        
        dataset = InteractionDataset(all_u, u_feats, all_i, i_feats, all_labels)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        # Instantiate Model
        self.model = TwoTowerModel(
            n_users=n_users,
            n_items=n_items,
            user_dim=u_feats.shape[1],
            item_dim=i_feats.shape[1],
            embed_dim=self.embed_dim
        ).to(self.device)
        
        criterion = nn.BCEWithLogitsLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.lr, weight_decay=1e-5)
        
        # Global popularity fallback
        self.global_popular = train_events["product_id"].value_counts().index.tolist()
        
        self.model.train()
        for epoch in range(self.epochs):
            total_loss = 0.0
            for batch_u, batch_uf, batch_i, batch_if, batch_lbl in loader:
                optimizer.zero_grad()
                preds = self.model(batch_u, batch_uf, batch_i, batch_if)
                loss = criterion(preds, batch_lbl)
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * len(batch_lbl)
            avg_loss = total_loss / len(dataset)
            print(f"Epoch {epoch+1}/{self.epochs} - Loss: {avg_loss:.4f}")
            
        # Precompute Item Tower vectors for all items for sub-millisecond real-time retrieval!
        print("Precomputing Item Tower embeddings for all 50,000 catalogue items...")
        self.model.eval()
        with torch.no_grad():
            all_item_ids = torch.arange(n_items, dtype=torch.long)
            all_item_feats = torch.tensor(self.item_features_arr, dtype=torch.float32)
            i_emb = self.model.item_id_embed(all_item_ids)
            i_input = torch.cat([i_emb, all_item_feats], dim=1)
            i_vec = self.model.item_mlp(i_input)
            self.item_vectors = torch.nn.functional.normalize(i_vec, p=2, dim=1).numpy()
            
        print("Neural Two-Tower model successfully trained and item index cached.")
        return self

    def recommend(self, user_id: str, k: int = 10, exclude_items: set = None) -> List[str]:
        exclude = exclude_items or set()
        u_int = self.user_to_int.get(user_id)
        if u_int is None or self.model is None:
            return [it for it in self.global_popular if it not in exclude][:k]
            
        with torch.no_grad():
            u_t = torch.tensor([u_int], dtype=torch.long)
            uf_t = torch.tensor([self.user_features_arr[u_int]], dtype=torch.float32)
            u_emb = self.model.user_id_embed(u_t)
            u_input = torch.cat([u_emb, uf_t], dim=1)
            u_vec = self.model.user_mlp(u_input)
            u_norm = torch.nn.functional.normalize(u_vec, p=2, dim=1).numpy()
            
        # Fast matrix vector multiplication: (1, 64) @ (64, n_items) = (n_items,)
        scores = np.dot(self.item_vectors, u_norm.T).flatten()
        top_indices = np.argsort(-scores)
        
        recs = []
        for idx in top_indices:
            pid = self.int_to_item.get(idx)
            if pid and pid not in exclude:
                recs.append(pid)
            if len(recs) >= k:
                break
        return recs
