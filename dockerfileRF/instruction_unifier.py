import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class InstructionUnifier:
    """指令功能统一器"""

    # 预定义的命令替换规则
    COMMAND_REPLACEMENTS = {
        # apt系列命令统一
        r'apt\s+install': 'apt-get install -y',
        r'apt-get\s+install(?!\s+-y)': 'apt-get install -y',

        # 文件操作命令统一
        r'wget\s+([^\s]+)\s+-O\s+([^\s]+)': r'curl -L \1 -o \2',

        # 权限设置统一
        r'chmod\s+[0-7]{3,4}\s+([^\s]+)': r'chmod 755 \1',

        # 解压缩命令统一
        r'tar\s+-xzvf': 'tar -xzf',
        r'unzip\s+([^\s]+)\s+-d\s+([^\s]+)': r'tar -xzf \1 -C \2',
    }

    # 参数顺序规范
    PARAMETER_ORDER = {
        'apt-get': ['update', 'install', '-y', '--no-install-recommends'],
        'curl': ['-L', '-o', '--fail', '--silent', '--show-error'],
        'tar': ['-xzf', '-C'],
    }

    def __init__(self, knowledge_graph: Dict):
        """
        初始化指令功能统一器

        Args:
            knowledge_graph: 加载的知识图谱数据
        """
        self.knowledge_graph = knowledge_graph
        self._build_command_standards()

    def _build_command_standards(self):
        """从知识图谱构建命令标准"""
        self.command_standards = {}

        for command_data in self.knowledge_graph.get("commands", []):
            cmd_name = command_data["name"]
            self.command_standards[cmd_name] = {
                "preferred_name": command_data.get("preferred_name", cmd_name),
                "parameter_order": command_data.get("parameter_order", []),
                "required_options": command_data.get("required_options", []),
            }

    def unify_instruction(self, instruction_type: str, instruction_content: str) -> str:
        """
        统一指令的功能实现

        Args:
            instruction_type: 指令类型 (如 "RUN", "COPY"等)
            instruction_content: 指令内容

        Returns:
            统一后的指令内容
        """
        if instruction_type != "RUN":
            return instruction_content

        try:
            # 1. 应用命令替换规则
            unified_content = instruction_content
            for pattern, replacement in self.COMMAND_REPLACEMENTS.items():
                unified_content = re.sub(pattern, replacement, unified_content)

            # 2. 标准化参数顺序
            commands = unified_content.split('&&')
            standardized_commands = []

            for cmd in commands:
                cmd = cmd.strip()
                if not cmd:
                    continue

                # 分离命令和参数
                parts = cmd.split()
                if not parts:
                    continue

                cmd_name = parts[0]
                params = parts[1:]

                # 查找命令标准
                standard = self.command_standards.get(cmd_name, {})
                preferred_name = standard.get("preferred_name", cmd_name)
                param_order = standard.get("parameter_order", [])

                # 重新排序参数
                ordered_params = []
                remaining_params = params.copy()

                # 首先添加预定义的参数顺序
                for param in param_order:
                    if param in remaining_params:
                        ordered_params.append(param)
                        remaining_params.remove(param)

                # 然后添加剩余参数
                ordered_params.extend(remaining_params)

                # 重建命令
                standardized_cmd = f"{preferred_name} {' '.join(ordered_params)}"
                standardized_commands.append(standardized_cmd)

            # 3. 合并多命令
            return ' && '.join(standardized_commands)

        except Exception as e:
            logger.error("Error unifying instruction '%s': %s", instruction_content, str(e), exc_info=True)
            return instruction_content