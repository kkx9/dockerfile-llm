import logging
from typing import List, Dict, Tuple, Set
import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict

logger = logging.getLogger(__name__)


class InstructionSharingOptimizer:
    """指令共享优化器"""

    def __init__(self, knowledge_graph: Dict):
        """
        初始化指令共享优化器

        Args:
            knowledge_graph: 加载的知识图谱数据
        """
        self.knowledge_graph = knowledge_graph
        self.common_instructions = self._analyze_common_instructions()

    def _analyze_common_instructions(self) -> Dict[str, List[Tuple[str, float]]]:
        """
        分析知识图谱中的常见指令模式

        Returns:
            字典，键为指令类型，值为(指令模式, 频率)列表
        """
        instruction_stats = defaultdict(list)

        # 从知识图谱中统计指令频率
        for dockerfile_data in self.knowledge_graph.get("dockerfiles", []):
            for instruction in dockerfile_data["instructions"]:
                inst_type = instruction["type"]
                inst_content = instruction["content"]
                instruction_stats[inst_type].append(inst_content)

        # 对每种指令类型进行聚类分析
        common_patterns = {}
        for inst_type, contents in instruction_stats.items():
            if inst_type == "RUN":
                # 对RUN指令进行更精细的分析
                vectors = [self._vectorize_run_instruction(c) for c in contents]
                clusters = self._cluster_instructions(vectors, contents)
                common_patterns[inst_type] = [
                    (pattern, len(members) / len(contents))
                    for pattern, members in clusters.items()
                ]
            else:
                # 对其他指令类型进行简单频率统计
                freq = defaultdict(int)
                for c in contents:
                    freq[c] += 1
                common_patterns[inst_type] = [
                    (k, v / len(contents))
                    for k, v in sorted(freq.items(), key=lambda x: x[1], reverse=True)
                ]

        return common_patterns

    def _vectorize_run_instruction(self, instruction: str) -> np.ndarray:
        """
        将RUN指令转换为向量表示 (简化版)

        Args:
            instruction: RUN指令内容

        Returns:
            指令的向量表示
        """
        words = instruction.split()
        unique_words = list(set(words))
        vector = np.zeros(len(unique_words))
        word_to_idx = {word: i for i, word in enumerate(unique_words)}

        for word in words:
            vector[word_to_idx[word]] += 1

        return vector

    def _cluster_instructions(self, vectors: List[np.ndarray], contents: List[str],
                              eps: float = 0.5, min_samples: int = 5) -> Dict[str, List[str]]:
        """
        对指令进行聚类

        Args:
            vectors: 指令向量列表
            contents: 指令内容列表
            eps: DBSCAN参数
            min_samples: DBSCAN参数

        Returns:
            字典，键为聚类中心指令，值为该聚类中的指令列表
        """
        if not vectors:
            return {}

        # 使用DBSCAN聚类
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(vectors)

        # 组织聚类结果
        clusters = defaultdict(list)
        for idx, label in enumerate(clustering.labels_):
            if label != -1:  # 忽略噪声点
                clusters[label].append(contents[idx])

        # 找出每个聚类的中心指令
        cluster_centers = {}
        for label, members in clusters.items():
            # 简单的中心选择: 选择与所有成员平均距离最小的指令
            avg_distances = []
            for member in members:
                member_vec = self._vectorize_run_instruction(member)
                dist = sum(np.linalg.norm(member_vec - self._vectorize_run_instruction(m))
                           for m in members) / len(members)
                avg_distances.append((dist, member))

            # 选择平均距离最小的作为中心
            center = min(avg_distances, key=lambda x: x[0])[1]
            cluster_centers[center] = members

        return cluster_centers

    def get_shared_instructions(self, instruction_type: str, threshold: float = 0.1) -> List[str]:
        """
        获取可共享的指令模式

        Args:
            instruction_type: 指令类型 (如 "RUN", "COPY"等)
            threshold: 频率阈值，只返回频率高于此值的指令

        Returns:
            可共享的指令模式列表
        """
        return [
            pattern for pattern, freq in self.common_instructions.get(instruction_type, [])
            if freq >= threshold
        ]