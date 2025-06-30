from torch import util
from typing import List, Dict, Optional
from .models import Entity, EntityType, Relation, RelationType, KnowledgeGraph
import json
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer


class KnowledgeGraphService:
    def __init__(self, graph_data_path: str, embedding_model_name: str = 'all-MiniLM-L6-v2'):
        self.graph = self._load_graph(graph_data_path)
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self._build_entity_index()

    def _load_graph(self, data_path: str) -> KnowledgeGraph:
        """Load knowledge graph from JSON file"""
        with open(data_path, 'r') as f:
            data = json.load(f)

        graph = KnowledgeGraph()
        for entity_data in data['entities']:
            entity = Entity(**entity_data)
            graph.entities[entity.id] = entity

        for relation_data in data['relations']:
            relation = Relation(**relation_data)
            graph.relations.append(relation)

        return graph

    def _build_entity_index(self):
        """Build index for entity embeddings"""
        self.entity_ids = []
        self.entity_texts = []
        for entity_id, entity in self.graph.entities.items():
            self.entity_ids.append(entity_id)
            self.entity_texts.append(f"{entity.name} {entity.description or ''}")

        self.entity_embeddings = self.embedding_model.encode(self.entity_texts, convert_to_tensor=True)

    def search_entities(self, query: str, top_k: int = 5) -> List[Entity]:
        """Search entities by semantic similarity"""
        query_embedding = self.embedding_model.encode(query, convert_to_tensor=True)
        scores = util.pytorch_cos_sim(query_embedding, self.entity_embeddings)[0]
        top_indices = scores.topk(top_k).indices.tolist()

        results = []
        for idx in top_indices:
            entity_id = self.entity_ids[idx]
            entity = self.graph.get_entity(entity_id)
            if entity:
                results.append(entity)

        return results

    def get_dependency_subgraph(self, entity_ids: List[str], depth: int = 2) -> KnowledgeGraph:
        """Get subgraph containing dependencies of given entities"""
        return self.graph.get_subgraph(entity_ids, depth)

    def validate_dependencies(self, entities: List[Entity]) -> Dict[str, List[str]]:
        """Validate dependencies between entities and return conflicts"""
        conflicts = {}
        entity_ids = {e.id for e in entities}

        for entity in entities:
            # Check for conflicting dependencies
            conflicting_relations = [
                rel for rel in self.graph.relations
                if rel.source_id == entity.id and rel.type == RelationType.CONFLICTS_WITH
            ]

            for rel in conflicting_relations:
                if rel.target_id in entity_ids:
                    if entity.id not in conflicts:
                        conflicts[entity.id] = []
                    conflicts[entity.id].append(rel.target_id)

        return conflicts