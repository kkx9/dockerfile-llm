import json
from mlxtend.frequent_patterns import apriori, association_rules
import pandas as pd

# 示例AST数据
ast_data = '''
[
    {
        "children": [
            {
                "children": [
                    {
                        "children": [],
                        "type": "DOCKER-IMAGE-NAME:%%FROM%%"
                    }
                ],
                "type": "DOCKER-FROM"
            },
            {
                "children": [
                    {
                        "children": [
                            {
                                "children": [],
                                "type": "UNKNOWN"
                            }
                        ],
                        "type": "BASH-SCRIPT"
                    }
                ],
                "type": "DOCKER-RUN"
            },
            {
                "children": [
                    {
                        "children": [
                            {
                                "children": [
                                    {
                                        "children": [],
                                        "type": "SC-SET-F-E"
                                    },
                                    {
                                        "children": [],
                                        "type": "SC-SET-F-U"
                                    },
                                    {
                                        "children": [],
                                        "type": "SC-SET-F-X"
                                    }
                                ],
                                "type": "SC-SET"
                            },
                            {
                                "children": [
                                    {
                                        "children": [
                                            {
                                                "children": [],
                                                "type": "UNKNOWN"
                                            }
                                        ],
                                        "type": "BASH-REDIRECT-COMMAND"
                                    },
                                    {
                                        "children": [
                                            {
                                                "children": [
                                                    {
                                                        "children": [
                                                            {
                                                                "children": [],
                                                                "type": "ABS-MAYBE-PATH"
                                                            },
                                                            {
                                                                "children": [],
                                                                "type": "ABS-PATH-ABSOLUTE"
                                                            }
                                                        ],
                                                        "type": "BASH-LITERAL"
                                                    }
                                                ],
                                                "type": "BASH-PATH"
                                            }
                                        ],
                                        "type": "BASH-REDIRECT-OVERWRITE"
                                    }
                                ],
                                "type": "BASH-REDIRECT-REDIRECTS"
                            }
                        ],
                        "type": "BASH-REDIRECT"
                    },
                    {
                        "children": [
                            {
                                "children": [
                                    {
                                        "children": [],
                                        "type": "BASH-OP"
                                    }
                                ],
                                "type": "BASH-CONDITION-OP"
                            },
                            {
                                "children": [
                                    {
                                        "children": [
                                            {
                                                "children": [
                                                    {
                                                        "children": [],
                                                        "type": "BASH-OP"
                                                    }
                                                ],
                                                "type": "BASH-CONDITION-UNARY-OP"
                                            },
                                            {
                                                "children": [
                                                    {
                                                        "children": [
                                                            {
                                                                "children": [],
                                                                "type": "ABS-MAYBE-PATH"
                                                            },
                                                            {
                                                                "children": [],
                                                                "type": "ABS-PATH-ABSOLUTE"
                                                            }
                                                        ],
                                                        "type": "BASH-LITERAL"
                                                    }
                                                ],
                                                "type": "BASH-CONDITION-UNARY-EXP"
                                            }
                                        ],
                                        "type": "BASH-CONDITION-UNARY"
                                    }
                                ],
                                "type": "BASH-CONDITION-EXP"
                            }
                        ],
                        "type": "BASH-CONDITION"
                    },
                    {
                        "children": [
                            {
                                "children": [
                                    {
                                        "children": [],
                                        "type": "BASH-LITERAL"
                                    },
                                    {
                                        "children": [],
                                        "type": "BASH-LITERAL"
                                    }
                                ],
                                "type": "BASH-CONCAT"
                            }
                        ],
                        "type": "SC-CHMOD-MODE"
                    },
                    {
                        "children": [
                            {
                                "children": [
                                    {
                                        "children": [],
                                        "type": "ABS-MAYBE-PATH"
                                    },
                                    {
                                        "children": [],
                                        "type": "ABS-PATH-ABSOLUTE"
                                    }
                                ],
                                "type": "BASH-LITERAL"
                            }
                        ],
                        "type": "SC-CHMOD-PATH"
                    }
                ],
                "type": "SC-CHMOD-PATHS"
            }
        ],
        "file_sha": "017789060b7322901b9e742ff3e86b9f0ba5aea2",
        "type": "DOCKER-FILE"
    }
]
'''

# 解析AST数据
ast = json.loads(ast_data)

# 提取节点类型的函数
def extract_node_types(node):
    node_types = []
    node_type = node.get('type')
    if node_type:
        node_types.append(node_type)
        for child in node.get('children', []):
            node_types.extend(extract_node_types(child))
    return node_types

# 提取所有节点类型
node_types = extract_node_types(ast[0])

# 转换为适合关联规则挖掘的格式
data = pd.DataFrame([{node_type: 1 for node_type in node_types}]).fillna(0)

# 使用Apriori算法挖掘频繁项集
frequent_itemsets = apriori(data, min_support=0.1, use_colnames=True)

# 挖掘关联规则
rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.5)

# 打印关联规则
print(rules)