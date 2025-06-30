import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger(__name__)


@dataclass
class BaseImage:
    """基础镜像数据类"""
    name: str
    tag: str
    size: float  # in MB
    packages: List[str]
    vector: Optional[np.ndarray] = None


class BaseImageOptimizer:
    """基础镜像优化器"""

    def __init__(self, knowledge_graph: Dict):
        """
        初始化基础镜像优化器

        Args:
            knowledge_graph: 加载的知识图谱数据
        """
        self.knowledge_graph = knowledge_graph
        self.model = AutoModel.from_pretrained("codebert-base")
        self.tokenizer = AutoTokenizer.from_pretrained("codebert-base")
        self.base_images = self._load_base_images()

    def _load_base_images(self) -> List[BaseImage]:
        """从知识图谱加载基础镜像数据"""
        images = []
        for image_data in self.knowledge_graph.get("images", []):
            image = BaseImage(
                name=image_data["name"],
                tag=image_data["tag"],
                size=image_data["size"],
                packages=image_data["packages"]
            )
            image.vector = self._get_image_embedding(image)
            images.append(image)
        return images

    def _get_image_embedding(self, image: BaseImage) -> np.ndarray:
        """获取镜像的向量表示"""
        text = f"{image.name}:{image.tag} {' '.join(image.packages)}"
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).detach().numpy()[0]

    def find_optimal_base_image(self, current_image: str, required_packages: List[str]) -> Optional[BaseImage]:
        """
        寻找最优的基础镜像替换

        Args:
            current_image: 当前使用的基础镜像 (格式: name:tag)
            required_packages: 需要的软件包列表

        Returns:
            最优的基础镜像对象，如果没有找到则返回None
        """
        try:
            # 获取当前镜像的向量表示
            current_name, current_tag = current_image.split(":") if ":" in current_image else (current_image, "latest")
            current_image_vec = self._get_image_embedding(
                BaseImage(name=current_name, tag=current_tag, size=0, packages=[])
            )

            # 计算与所有基础镜像的相似度
            similarities = []
            for image in self.base_images:
                sim = cosine_similarity([current_image_vec], [image.vector])[0][0]

                # 检查是否包含所有需要的软件包
                missing_packages = set(required_packages) - set(image.packages)
                package_coverage = 1 - len(missing_packages) / len(required_packages) if required_packages else 1

                # 综合评分 (相似度 * 包覆盖率 * (1/size))
                score = sim * package_coverage * (1 / (image.size + 1))
                similarities.append((score, image))

            # 按评分排序
            similarities.sort(key=lambda x: x[0], reverse=True)

            # 返回评分最高的镜像
            return similarities[0][1] if similarities else None

        except Exception as e:
            logger.error("Error finding optimal base image: %s", str(e), exc_info=True)
            return None