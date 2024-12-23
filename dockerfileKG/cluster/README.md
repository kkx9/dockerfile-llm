# Dockerfile分类设计原则
## dockerfile2vec
1. 构建dockerfile ast，预选特殊节点
2. 基于dockerfile ast，提取出ast中path（从预选节点开始，到叶子节点中结束），将path数量同一，作为特征之一
3. 统计pkg安装情况，作为特征之一
4. 统计指令数量，作为特征之一
## DBSCAN分类
使用dbscan算法分类dockerfile