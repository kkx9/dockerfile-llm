from typing import List, Dict, Optional
from pydantic import BaseModel
from enum import Enum


class EntityType(str, Enum):
    IMAGE = "Image"
    PACKAGE = "Package"
    COMMAND = "Command"
    OPTION = "Option"
    FILE = "File"


class RelationType(str, Enum):
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"
    REQUIRES = "requires"
    RECOMMENDS = "recommends"
    CONFLICTS_WITH = "conflicts_with"
    COMMON_WITH = "common_with"


class Entity(BaseModel):
    id: str
    type: EntityType
    name: str
    description: Optional[str] = None
    properties: Dict[str, str] = None


class Relation(BaseModel):
    source_id: str
    target_id: str
    type: RelationType
    weight: float = 1.0
    properties: Dict[str, str] = None


class KnowledgeGraph(BaseModel):
    entities: Dict[str, Entity] = None
    relations: List[Relation] = None

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def get_related_entities(self, entity_id: str, relation_type: Optional[RelationType] = None) -> List[Entity]:
        related_entities = []
        for rel in self.relations:
            if rel.source_id == entity_id and (relation_type is None or rel.type == relation_type):
                target_entity = self.get_entity(rel.target_id)
                if target_entity:
                    related_entities.append(target_entity)
        return related_entities

    def get_subgraph(self, entity_ids: List[str], depth: int = 1) -> "KnowledgeGraph":
        subgraph = KnowledgeGraph()
        visited = set()

        def traverse(current_ids: List[str], current_depth: int):
            if current_depth > depth:
                return
            for entity_id in current_ids:
                if entity_id in visited:
                    continue
                entity = self.get_entity(entity_id)
                if entity:
                    subgraph.entities[entity_id] = entity
                    visited.add(entity_id)
                    for rel in self.relations:
                        if rel.source_id == entity_id:
                            subgraph.relations.append(rel)
                            traverse([rel.target_id], current_depth + 1)

        traverse(entity_ids, 0)
        return subgraph