import logging
from typing import List, Dict, Optional
from base_image_optimizer import BaseImageOptimizer
from instruction_sharing import InstructionSharingOptimizer
from instruction_unifier import InstructionUnifier
from instruction_sequencer import InstructionSequencer

logger = logging.getLogger(__name__)


class DockerfileRefactorController:
    """Dockerfile重构控制器"""

    def __init__(self, knowledge_graph: Dict):
        """
        初始化重构控制器

        Args:
            knowledge_graph: 加载的知识图谱数据
        """
        self.knowledge_graph = knowledge_graph
        self.base_image_optimizer = BaseImageOptimizer(knowledge_graph)
        self.instruction_sharing = InstructionSharingOptimizer(knowledge_graph)
        self.instruction_unifier = InstructionUnifier(knowledge_graph)
        self.instruction_sequencer = InstructionSequencer(knowledge_graph)

    def parse_dockerfile(self, dockerfile_content: str) -> List[Dict]:
        """
        解析Dockerfile内容为结构化指令列表

        Args:
            dockerfile_content: Dockerfile内容

        Returns:
            结构化指令列表，每个元素是{"type": 指令类型, "content": 内容}的字典
        """
        instructions = []

        for line in dockerfile_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 简单解析指令类型和内容
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                inst_type = parts[0].upper()
                content = parts[1]
                instructions.append({"type": inst_type, "content": content})
            elif len(parts) == 1:
                instructions.append({"type": parts[0].upper(), "content": ""})

        return instructions

    def refactor_dockerfile(self, dockerfile_content: str) -> str:
        """
        重构Dockerfile内容

        Args:
            dockerfile_content: 原始Dockerfile内容

        Returns:
            重构后的Dockerfile内容
        """
        try:
            # 1. 解析Dockerfile
            instructions = self.parse_dockerfile(dockerfile_content)
            if not instructions:
                return dockerfile_content

            logger.info("Original instructions: %s", [inst["type"] for inst in instructions])

            # 2. 优化基础镜像
            base_image = self._get_base_image(instructions)
            if base_image:
                required_packages = self._get_required_packages(instructions)
                optimal_image = self.base_image_optimizer.find_optimal_base_image(
                    base_image, required_packages
                )

                if optimal_image and optimal_image.name != base_image.split(":")[0]:
                    # 替换基础镜像
                    for inst in instructions:
                        if inst["type"] == "FROM":
                            inst["content"] = f"{optimal_image.name}:{optimal_image.tag}"
                            break
                    logger.info("Replaced base image %s with %s:%s",
                                base_image, optimal_image.name, optimal_image.tag)

            # 3. 统一指令功能
            for i in range(len(instructions)):
                if instructions[i]["type"] == "RUN":
                    instructions[i]["content"] = self.instruction_unifier.unify_instruction(
                        instructions[i]["type"], instructions[i]["content"]
                    )

            # 4. 优化指令顺序
            instructions = self.instruction_sequencer.optimize_instruction_order(instructions)
            logger.info("Optimized instruction order: %s", [inst["type"] for inst in instructions])

            # 5. 应用最佳实践
            instructions = self._apply_best_practices(instructions)

            # 6. 重建Dockerfile内容
            refactored_content = "\n".join(
                f"{inst['type']} {inst['content']}".strip()
                for inst in instructions
            )

            return refactored_content

        except Exception as e:
            logger.error("Error refactoring Dockerfile: %s", str(e), exc_info=True)
            return dockerfile_content

    def _get_base_image(self, instructions: List[Dict]) -> Optional[str]:
        """获取当前使用的基础镜像"""
        for inst in instructions:
            if inst["type"] == "FROM":
                return inst["content"]
        return None

    def _get_required_packages(self, instructions: List[Dict]) -> List[str]:
        """获取需要的软件包列表"""
        packages = set()

        for inst in instructions:
            if inst["type"] == "RUN":
                content = inst["content"].lower()
                if "apt-get install" in content or "apk add" in content or "yum install" in content:
                    # 简单提取软件包名称 (实际应用中应该更精确)
                    parts = content.split()
                    for i, part in enumerate(parts):
                        if part in ["install", "add"] and i + 1 < len(parts):
                            packages.update(parts[i + 1:])
                            break

        return list(packages)

    def _apply_best_practices(self, instructions: List[Dict]) -> List[Dict]:
        """应用最佳实践"""
        refactored_instructions = []
        run_commands = []

        for inst in instructions:
            if inst["type"] == "RUN":
                # 合并连续的RUN指令
                run_commands.append(inst["content"])
            else:
                # 如果有待合并的RUN指令，先合并
                if run_commands:
                    refactored_instructions.append({
                        "type": "RUN",
                        "content": " && ".join(run_commands)
                    })
                    run_commands = []
                refactored_instructions.append(inst)

        # 处理最后可能的RUN指令
        if run_commands:
            refactored_instructions.append({
                "type": "RUN",
                "content": " && ".join(run_commands)
            })

        # 添加清理缓存的指令
        for i in range(len(refactored_instructions)):
            if (refactored_instructions[i]["type"] == "RUN" and
                    ("apt-get install" in refactored_instructions[i]["content"] or
                     "apk add" in refactored_instructions[i]["content"])):
                # 在软件安装后添加清理命令
                content = refactored_instructions[i]["content"]
                if "apt-get" in content:
                    content += " && rm -rf /var/lib/apt/lists/*"
                elif "apk" in content:
                    content += " && rm -rf /var/cache/apk/*"
                refactored_instructions[i]["content"] = content

        return refactored_instructions