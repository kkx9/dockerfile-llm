from collections import defaultdict
import itertools

class IncrementalFPGrowth:
    def __init__(self, min_support, min_confidence=0.5, min_lift=1.0):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.min_lift = min_lift
        self.frequent_itemsets = []
        self.tree = None
        
    def fit(self, data):
        """
        初始构建 FP-tree 并提取频繁项集
        :param data: 训练数据集，每个 Dockerfile 为一个事务，指令为事务中的项
        """
        self.tree, frequent_itemsets = self.build_fp_tree(data)
        self.frequent_itemsets = frequent_itemsets
        self.association_rules = self.generate_association_rules(frequent_itemsets)
        
    def update(self, new_data):
        """
        增量更新FP-tree
        :param new_data: 新的 Dockerfile 数据（事务）
        """
        self.tree, frequent_itemsets = self.build_fp_tree(new_data, self.tree)
        self.frequent_itemsets.extend(frequent_itemsets)
        self.frequent_itemsets = self.prune(self.frequent_itemsets)
        self.association_rules = self.generate_association_rules(self.frequent_itemsets)
        
    def build_fp_tree(self, data, tree=None):
        """
        构建 FP-tree 并提取频繁项集
        :param data: 输入的 Dockerfile 数据集
        :param tree: 现有的 FP-tree，增量更新时传入
        :return: 更新后的 FP-tree 和频繁项集
        """
        item_counts = defaultdict(int)
        for transaction in data:
            for item in transaction:
                item_counts[item] += 1
        
        # 过滤出频繁项
        frequent_items = {item for item, count in item_counts.items() if count / len(data) >= self.min_support}
        new_tree = tree if tree else defaultdict(dict)
        
        # 将新数据插入到现有的 FP-tree 中
        for transaction in data:
            sorted_transaction = [item for item in transaction if item in frequent_items]
            sorted_transaction.sort(key=lambda x: item_counts[x], reverse=True)
            self.insert_transaction_to_tree(sorted_transaction, new_tree)
        
        # 提取频繁项集
        frequent_itemsets = self.extract_frequent_itemsets(new_tree)
        return new_tree, frequent_itemsets
    
    def insert_transaction_to_tree(self, transaction, tree):
        """
        插入一个事务到 FP-tree 中
        :param transaction: 当前事务
        :param tree: FP-tree
        """
        if not transaction:
            return
        first_item = transaction[0]
        if first_item not in tree:
            tree[first_item] = defaultdict(int)
        # 将剩余的事务转换为元组作为字典键
        tree[first_item][tuple(transaction[1:])] += 1
        self.insert_transaction_to_tree(transaction[1:], tree[first_item])
    
    def extract_frequent_itemsets(self, tree):
        """
        从 FP-tree 中提取频繁项集
        :param tree: FP-tree
        :return: 频繁项集列表
        """
        itemsets = []
        for node, children in tree.items():
            if isinstance(children, defaultdict):
                itemsets.append([node])
                itemsets.extend([[node] + child for child in self.extract_frequent_itemsets(children)])
        return itemsets
    
    def prune(self, itemsets):
        """
        去除不频繁的项集
        :param itemsets: 频繁项集
        :return: 修剪后的频繁项集
        """
        return [itemset for itemset in itemsets if len(itemset) > 1]

    def generate_association_rules(self, frequent_itemsets):
        """
        从频繁项集中生成关联规则
        :param frequent_itemsets: 频繁项集
        :return: 关联规则列表
        """
        rules = []
        for itemset in frequent_itemsets:
            if len(itemset) > 1:  # 仅考虑长度大于1的项集
                # 生成所有非空的子集
                subsets = list(itertools.chain(*[itertools.combinations(itemset, r) for r in range(1, len(itemset))]))
                for subset in subsets:
                    # 计算 A -> B 的支持度、置信度和提升度
                    left = set(subset)
                    right = set(itemset) - left
                    if left and right:
                        support = self.calculate_support(left, right)
                        confidence = self.calculate_confidence(left, right)
                        lift = self.calculate_lift(left, right)
                        
                        if confidence >= self.min_confidence and lift >= self.min_lift:
                            rules.append((left, right, support, confidence, lift))
        return rules

    def calculate_support(self, left, right):
        """
        计算支持度
        """
        return self.calculate_itemset_support(left.union(right))

    def calculate_itemset_support(self, itemset):
        """
        计算项集的支持度
        """
        count = sum(1 for transaction in self.frequent_itemsets if set(itemset).issubset(transaction))
        return count / len(self.frequent_itemsets)

    def calculate_confidence(self, left, right):
        """
        计算置信度
        """
        support_left = self.calculate_itemset_support(left)
        support_left_right = self.calculate_itemset_support(left.union(right))
        return support_left_right / support_left if support_left > 0 else 0

    def calculate_lift(self, left, right):
        """
        计算提升度
        """
        support_left = self.calculate_itemset_support(left)
        support_right = self.calculate_itemset_support(right)
        support_left_right = self.calculate_itemset_support(left.union(right))
        return support_left_right / (support_left * support_right) if support_left > 0 and support_right > 0 else 0

# 使用示例
dockerfile_data = [
    ['FROM ubuntu', 'RUN apt-get update', 'RUN apt-get install'],
    ['FROM debian', 'RUN apt-get update', 'RUN apt-get install'],
    ['FROM ubuntu', 'RUN apt-get install curl', 'RUN apt-get install'],
    ['FROM debian', 'RUN apt-get update', 'RUN apt-get install curl', 'RUN apt-get install vim']
]

# 初始化增量式FP-growth模型
fp_growth = IncrementalFPGrowth(min_support=0.5)

# 初次训练
fp_growth.fit(dockerfile_data)

# 新的Dockerfile数据
new_dockerfile_data = [['FROM ubuntu', 'RUN apt-get install vim', 'RUN apt-get update']]

# 增量更新
fp_growth.update(new_dockerfile_data)

# 输出频繁项集
print("Frequent Itemsets:", fp_growth.frequent_itemsets)

# 输出关联规则
print("Association Rules:")
for rule in fp_growth.association_rules:
    left, right, support, confidence, lift = rule
    print(f"Rule: {left} -> {right}, Support: {support:.2f}, Confidence: {confidence:.2f}, Lift: {lift:.2f}")