import json
from typing import List, Dict, Optional
from pydantic import BaseModel
from ..knowldeg_graph import models, knowledge_graph_service
# from models import Entity, KnowledgeGraph
# from knowledge_graph_service import KnowledgeGraphService
import openai

Entity, KnowledgeGraph,  EntityType = models.Entity, models.KnowledgeGraph, models.EntityType
KnowledgeGraphService = knowledge_graph_service.KnowledgeGraphService


class ClarificationPrompt(BaseModel):
    user_requirement: str
    candidate_instructions: List[str]
    knowledge_subgraph: Optional[KnowledgeGraph] = None


class RequirementClarificationService:
    def __init__(self, kg_service: KnowledgeGraphService, openai_api_key: str):
        self.kg_service = kg_service
        openai.api_key = openai_api_key

    def generate_candidate_instructions(self, user_requirement: str) -> List[str]:
        """Generate candidate Dockerfile instructions based on user requirement"""
        prompt = f"""
        You are an expert in Docker and containerization. Given the following user requirement, 
        generate 3 different possible Dockerfile implementations. Each implementation should 
        use different base images and approaches where applicable.

        User Requirement: {user_requirement}

        Return the 3 Dockerfiles as a JSON list of strings.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )

        try:
            candidates = json.loads(response.choices[0].message.content)
            if isinstance(candidates, list) and len(candidates) == 3:
                return candidates
        except:
            pass

        # Fallback if JSON parsing fails
        return [
            response.choices[0].message.content.split("\n\n")[0],
            response.choices[0].message.content.split("\n\n")[1],
            response.choices[0].message.content.split("\n\n")[2]
        ]

    def analyze_and_rank_candidates(self, user_requirement: str, candidates: List[str]) -> List[str]:
        """Analyze candidate instructions using knowledge graph and rank them"""
        # Extract entities from each candidate
        candidate_entities = []
        for candidate in candidates:
            entities = self._extract_entities_from_dockerfile(candidate)
            candidate_entities.append(entities)

        # Validate dependencies for each candidate
        ranked_candidates = []
        for i, (candidate, entities) in enumerate(zip(candidates, candidate_entities)):
            conflicts = self.kg_service.validate_dependencies(entities)
            if not conflicts:
                ranked_candidates.append((candidate, len(entities)))
            else:
                # Penalize candidates with conflicts
                ranked_candidates.append((candidate, len(entities) - len(conflicts) * 2))

        # Sort by score (higher is better)
        ranked_candidates.sort(key=lambda x: x[1], reverse=True)
        return [candidate for candidate, score in ranked_candidates]

    def _extract_entities_from_dockerfile(self, dockerfile: str) -> List[Entity]:
        """Extract entities (images, packages, commands) from Dockerfile"""
        # This is a simplified version - in practice would use AST parsing
        entities = []
        lines = dockerfile.split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("FROM"):
                image = line.split()[1].split(":")[0]
                entities.append(Entity(
                    id=f"image:{image}",
                    type=EntityType.IMAGE,
                    name=image
                ))
            elif line.startswith("RUN"):
                # Extract packages from install commands
                if "apt-get install" in line:
                    packages = line.split("apt-get install")[1].split()
                    for pkg in packages:
                        if pkg not in ["-y", "--no-install-recommends"]:
                            entities.append(Entity(
                                id=f"package:{pkg}",
                                type=EntityType.PACKAGE,
                                name=pkg
                            ))

        return entities

    def clarify_requirement(self, user_requirement: str) -> ClarificationPrompt:
        """Main method to clarify user requirement"""
        candidates = self.generate_candidate_instructions(user_requirement)
        ranked_candidates = self.analyze_and_rank_candidates(user_requirement, candidates)

        # Get knowledge subgraph for the best candidate
        best_candidate_entities = self._extract_entities_from_dockerfile(ranked_candidates[0])
        subgraph = self.kg_service.get_dependency_subgraph([e.id for e in best_candidate_entities])

        return ClarificationPrompt(
            user_requirement=user_requirement,
            candidate_instructions=ranked_candidates,
            knowledge_subgraph=subgraph
        )