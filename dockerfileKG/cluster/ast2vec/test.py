import re
from gensim.models import Word2Vec
import numpy as np

# 示例 Dockerfiles
dockerfiles = [
    """FROM python:3.8
       RUN apt-get update && apt-get install -y python3-pip libssl-dev
       COPY . /app
       CMD ["python3", "/app/main.py"]""",
    """FROM ubuntu:20.04
       RUN apt-get update && apt-get install -y curl vim
       ENTRYPOINT ["/bin/bash"]"""
]


# Step 1: 解析 Dockerfile
def parse_dockerfile(dockerfile):
    # 提取指令序列
    instructions = [line.split()[0] for line in dockerfile.splitlines() if line.strip() and not line.startswith("#")]

    # 提取指令条数
    instruction_count = len(instructions)

    # 提取安装的软件包
    pkgs = []
    for line in dockerfile.splitlines():
        if "install" in line:
            pkgs.extend(re.findall(r'\b\w+\b', line.split("install")[-1]))
    return instructions, instruction_count, pkgs


# 提取所有 Dockerfiles 的特征
dockerfile_features = [parse_dockerfile(df) for df in dockerfiles]

# Step 2: 使用 Word2Vec 对指令和软件包进行嵌入
# 收集所有指令和软件包的语料
paths_corpus = [features[0] for features in dockerfile_features]
packages_corpus = [features[2] for features in dockerfile_features]
total_ins = sum(features[1] for features in dockerfile_features)

# 训练 Word2Vec 模型
instruction_model = Word2Vec(sentences=paths_corpus, vector_size=50, window=5, min_count=1, workers=4)
package_model = Word2Vec(sentences=packages_corpus, vector_size=50, window=5, min_count=1, workers=4)


# Step 3: 生成特征向量
def generate_feature_vector(features, instr_model, pkg_model):
    instructions, instruction_count, pkgs = features

    # 指令向量
    instr_vectors = [instr_model.wv[instr] for instr in instructions if instr in instr_model.wv]
    instruction_vector = np.mean(instr_vectors, axis=0) if instr_vectors else np.zeros(instr_model.vector_size)

    # 包向量
    pkg_vectors = [pkg_model.wv[pkg] for pkg in pkgs if pkg in pkg_model.wv]
    package_vector = np.mean(pkg_vectors, axis=0) if pkg_vectors else np.zeros(pkg_model.vector_size)

    # 整合特征
    return np.concatenate([instruction_vector, [instruction_count/total_ins], package_vector])


# 计算每个 Dockerfile 的特征向量
dockerfile_vectors = [generate_feature_vector(features, instruction_model, package_model) for features in
                      dockerfile_features]

# 输出特征向量
for i, vector in enumerate(dockerfile_vectors):
    print(f"Dockerfile {i + 1} Feature Vector:")
    print(vector)
