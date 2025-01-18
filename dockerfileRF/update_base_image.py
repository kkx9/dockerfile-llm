from typing import List, Dict

# 示例知识图谱结构
knowledge_graph = {
    "images": {
        "ubuntu:20.04": {
            "size": 29,
            "commands": ["apt-get", "bash", "sh"],
            "packages": ["libc6", "gcc", "make"]
        },
        "ubuntu:22.04": {
            "size": 32,
            "commands": ["apt-get", "bash", "sh"],
            "packages": ["libc6", "gcc", "make"]
        },
        "debian:bullseye-slim": {
            "size": 22,
            "commands": ["apt-get", "bash"],
            "packages": ["libc6", "gcc", "make"]
        },
        "alpine:latest": {
            "size": 5,
            "commands": ["apk", "sh"],
            "packages": ["libc6"]
        },
    },
    "dependencies": {
        "gcc": ["libc6"],
        "make": ["gcc"]
    }
}

def parse_dockerfile(dockerfile_content: str) -> Dict:
    """
    解析 Dockerfile，提取 base image、命令、软件包信息。
    """
    lines = dockerfile_content.strip().split("\n")
    base_image = None
    commands = []
    packages = []

    for line in lines:
        line = line.strip()
        if line.startswith("FROM"):
            base_image = line.split()[1]
        elif line.startswith("RUN"):
            commands.extend(line.replace("RUN", "").strip().split(" "))
        elif line.startswith("ADD") or line.startswith("COPY"):
            commands.append("file_operation")  # 标记文件操作

    # 假设提取的软件包信息直接包含在 commands 中
    packages = [cmd for cmd in commands if cmd in knowledge_graph["dependencies"]]
    return {"base_image": base_image, "commands": commands, "packages": packages}

def is_compatible(target_image: str, commands: List[str], packages: List[str]) -> bool:
    """
    判断目标镜像是否兼容给定的命令和软件包。
    """
    image_info = knowledge_graph["images"].get(target_image)
    if not image_info:
        return False

    # 检查命令支持
    if not all(cmd in image_info["commands"] for cmd in commands):
        return False

    # 检查软件包依赖
    for pkg in packages:
        if pkg not in image_info["packages"]:
            # 检查是否可以通过依赖满足
            required_deps = knowledge_graph["dependencies"].get(pkg, [])
            if not all(dep in image_info["packages"] for dep in required_deps):
                return False

    return True

def suggest_base_image(dockerfile_content: str) -> str:
    """
    根据 Dockerfile 和知识图谱，建议更换为体积更小的兼容镜像。
    """
    parsed = parse_dockerfile(dockerfile_content)
    current_image = parsed["base_image"]
    commands = parsed["commands"]
    packages = parsed["packages"]

    # 获取候选镜像（按大小排序）
    candidate_images = sorted(knowledge_graph["images"].items(), key=lambda x: x[1]["size"])
    
    for target_image, _ in candidate_images:
        if target_image == current_image:
            continue
        if is_compatible(target_image, commands, packages):
            return target_image

    # 没有找到合适的镜像，返回原始镜像
    return current_image

# 示例 Dockerfile
dockerfile = """
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y gcc make
"""

# 建议更换镜像
suggested_image = suggest_base_image(dockerfile)
print(f"Suggested base image: {suggested_image}")
