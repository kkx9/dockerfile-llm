# from pymining import seqmining

# # 输入序列数据
# sequences = [
#     ['A', 'B', 'C'],
#     ['A', 'D'],
#     ['A', 'B', 'D', 'E'],
#     ['B', 'C'],
#     ['A', 'B', 'D']
# ]

# # 使用 PrefixSpan 挖掘频繁序列
# freq_seqs = seqmining.freq_seq_enum(sequences, min_support=2)
# print(list(freq_seqs))

import pandas as pd
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.frequent_patterns import association_rules

# 假设事务数据是从树形结构提取的路径
transactions = [
    ['A', 'B', 'C'],
    ['A', 'D'],
    ['A', 'B', 'D', 'E'],
    ['B', 'C'],
    ['A', 'B', 'D']
]

# 使用 FP-Growth 找到频繁项集
from mlxtend.preprocessing import TransactionEncoder
te = TransactionEncoder()
te_ary = te.fit(transactions).transform(transactions)
df = pd.DataFrame(te_ary, columns=te.columns_)
frequent_itemsets = fpgrowth(df, min_support=0.1, use_colnames=True)

# 生成关联规则
rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.8, num_itemsets=10)
print(rules)