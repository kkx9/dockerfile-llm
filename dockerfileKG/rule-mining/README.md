# Dockerfile 关联规则挖掘

本项目专注于从 Dockerfile 中挖掘关联规则。主要思路是使用 Dockerfile AST（抽象语法树）并应用增量式 FP-Growth 算法来发现关联规则。这种方法还支持在新数据到来时对规则进行增量更新。

## 概述

1. **Dockerfile AST**：将 Dockerfile 解析为 AST 表示，以提取有意义的模式。
2. **增量式 FP-Growth**：使用增量式 FP-Growth 算法从提取的模式中挖掘关联规则。
3. **增量更新**：随着新的 Dockerfile 添加到数据集中，增量更新已挖掘的规则。

## 步骤

1. **解析 Dockerfile**：
    - 使用解析器将 Dockerfile 转换为抽象语法树（AST）。
    - 从 AST 中提取有意义的模式和特征。

2. **挖掘关联规则**：
    - 将提取的模式作为输入，应用增量式 FP-Growth 算法。
    - 挖掘出频繁项集和关联规则。
    - 评估规则的支持度和置信度，以确保其有效性。

3. **更新规则**：
    - 当新的 Dockerfile 数据到来时，重新解析并提取模式。
    - 使用增量式 FP-Growth 算法更新现有的频繁项集和关联规则。
    - 确保新规则与旧规则的一致性和准确性。
