from typing import List, Dict, Optional
from pydantic import BaseModel
from ..knowldeg_graph import models, knowledge_graph_service
# from models import Entity, KnowledgeGraph
# from knowledge_graph_service import KnowledgeGraphService
import openai

Entity, KnowledgeGraph,  EntityType, RelationType = models.Entity, models.KnowledgeGraph, models.EntityType, models.RelationType
KnowledgeGraphService = knowledge_graph_service.KnowledgeGraphService


class RAGPrompt(BaseModel):
    user_requirement: str
    knowledge_context: str
    bash_context: Optional[str] = None


class RetrievalAugmentedGenerationService:
    def __init__(self, kg_service: KnowledgeGraphService, openai_api_key: str):
        self.kg_service = kg_service
        openai.api_key = openai_api_key
        self.bash_context_db = self._load_bash_context()

    def _load_bash_context(self) -> Dict[str, str]:
        """Load bash command context examples"""
        # In practice, this would load from a database or file
        return {
            "curl download": "When downloading files with curl, it's recommended to use -L to follow redirects and -sS for silent mode with error reporting.",
            "package installation": "For Debian-based systems, use 'apt-get update && apt-get install -y --no-install-recommends' to install packages efficiently.",
            "file extraction": "Use 'tar -xzf' for .tar.gz files and 'unzip' for .zip files. Clean up the archive after extraction."
        }

    def _get_bash_context(self, dockerfile: str) -> str:
        """Get relevant bash context for the Dockerfile"""
        # Simple keyword matching - could be enhanced with embeddings
        context = []
        lines = dockerfile.split("\n")

        for line in lines:
            if "curl" in line and "curl download" not in context:
                context.append(self.bash_context_db["curl download"])
            if "apt-get install" in line and "package installation" not in context:
                context.append(self.bash_context_db["package installation"])
            if "tar -xzf" in line or "unzip" in line and "file extraction" not in context:
                context.append(self.bash_context_db["file extraction"])

        return "\n".join(context)

    def _knowledge_graph_to_text(self, subgraph: KnowledgeGraph) -> str:
        """Convert knowledge subgraph to text description"""
        knowledge_text = []

        # Group by entity type
        images = []
        packages = []
        commands = []

        for entity in subgraph.entities.values():
            if entity.type == EntityType.IMAGE:
                images.append(entity.name)
            elif entity.type == EntityType.PACKAGE:
                packages.append(entity.name)
            elif entity.type == EntityType.COMMAND:
                commands.append(entity.name)

        if images:
            knowledge_text.append(f"Base Images: {', '.join(images)}")
        if packages:
            knowledge_text.append(f"Required Packages: {', '.join(packages)}")
        if commands:
            knowledge_text.append(f"Common Commands: {', '.join(commands)}")

        # Add important relations
        relation_descriptions = {
            RelationType.DEPENDS_ON: "depends on",
            RelationType.REQUIRES: "requires",
            RelationType.CONFLICTS_WITH: "conflicts with"
        }

        for rel in subgraph.relations:
            if rel.type in relation_descriptions:
                source = subgraph.entities[rel.source_id].name
                target = subgraph.entities[rel.target_id].name
                knowledge_text.append(f"{source} {relation_descriptions[rel.type]} {target}")

        return "\n".join(knowledge_text)

    def generate_dockerfile(self, prompt: RAGPrompt) -> str:
        """Generate Dockerfile using RAG approach"""
        system_prompt = f"""
        You are an expert Dockerfile generator. Given the user requirements and the 
        following knowledge context, generate a high-quality Dockerfile that follows 
        best practices.

        Knowledge Context:
        {prompt.knowledge_context}

        Bash Command Best Practices:
        {prompt.bash_context or "None provided"}

        The Dockerfile should:
        1. Use appropriate base image
        2. Install all required dependencies
        3. Follow security best practices
        4. Optimize for build caching and image size
        5. Include necessary configuration
        """

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt.user_requirement}
            ],
            temperature=0.3,  # Lower temperature for more deterministic output
            max_tokens=2000
        )

        return response.choices[0].message.content