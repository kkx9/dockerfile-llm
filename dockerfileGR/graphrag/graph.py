import networkx as nx

# 创建图
G = nx.DiGraph()

# 添加指令间依赖关系
G.add_edge('apt-get update', 'apt-get install', weight=3)

# 添加软件包间的依赖关系
G.add_edge('curl', 'libcurl', weight=5)
G.add_edge('wget', 'libssl', weight=4)

# 添加命令和基础镜像间的关系
G.add_edge('apt-get', 'FROM ubuntu:20.04', weight=2)
G.add_edge('apt', 'FROM ubuntu:20.04', weight=2)

# 添加软件包和基础镜像的关系
G.add_edge('libcurl', 'ubuntu:20.04', weight=5)
G.add_edge('libssl', 'ubuntu:20.04', weight=5)

# 可视化知识图谱
import matplotlib.pyplot as plt
nx.draw(G, with_labels=True, node_size=5000, node_color="skyblue", font_size=10)
plt.savefig('graph.png')
