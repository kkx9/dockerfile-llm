from collections import defaultdict

class IncrementalPrefixSpan:
    def __init__(self, min_support):
        self.min_support = min_support
        self.global_patterns = defaultdict(int)  # 存储全局频繁模式及其支持度

    def _prefixspan(self, sequences, prefix, min_support):
        """
        核心 PrefixSpan 递归逻辑
        """
        freq_patterns = defaultdict(int)

        for seq in sequences:
            for i, item in enumerate(seq):
                new_prefix = prefix + [item]
                freq_patterns[tuple(new_prefix)] += 1
                rest_seq = seq[i + 1:]
                if rest_seq:
                    self._prefixspan([rest_seq], new_prefix, min_support)

        return {p: c for p, c in freq_patterns.items() if c >= min_support}

    def fit(self, transactions):
        """
        初始挖掘
        """
        print("Performing initial PrefixSpan...")
        new_patterns = self._prefixspan(transactions, [], self.min_support)
        for pattern, support in new_patterns.items():
            self.global_patterns[pattern] += support

    def update(self, new_transactions):
        """
        增量更新
        """
        print("Performing incremental PrefixSpan...")
        new_patterns = self._prefixspan(new_transactions, [], self.min_support)
        for pattern, support in new_patterns.items():
            self.global_patterns[pattern] += support

    def get_patterns(self):
        """
        返回全局频繁模式
        """
        return {pattern: support for pattern, support in self.global_patterns.items() if support >= self.min_support}

# 示例数据
initial_data = [["A", "B", "C"], ["A", "C", "D"], ["B", "C", "E"]]
new_data = [["A", "C", "E"], ["B", "C", "D"]]

# 增量 PrefixSpan 使用
prefixspan = IncrementalPrefixSpan(min_support=2)
prefixspan.fit(initial_data)  # 初始挖掘
prefixspan.update(new_data)  # 增量更新

# 查看结果
patterns = prefixspan.get_patterns()
print("Frequent Patterns:", patterns)
