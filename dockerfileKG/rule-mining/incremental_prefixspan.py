import logging
import cupy as cp
import cudf
import sqlite3
from typing import List, Tuple


logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.DEBUG)


class IncrementalGPUAcceleratedPrefixSpan:
    def __init__(self, db_path: str, min_support: int):
        self.db_path = db_path
        self.min_support = min_support
        self._init_db()
        self.patterns = self._get_patterns()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                pattern TEXT PRIMARY KEY,
                support INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def _save_pattern(self, pattern: Tuple[int], support: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO patterns (pattern, support)
            VALUES (?, ?)
            ON CONFLICT(pattern) DO UPDATE SET support = support + ?
        ''', (",".join(map(str, pattern)), support, support))
        conn.commit()
        conn.close()

    def _get_patterns(self) -> List[Tuple[List[int], int]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT pattern, support FROM patterns')
        patterns = [(list(map(int, pattern.split(","))), support) for pattern, support in cursor.fetchall()]
        conn.close()
        return patterns

    def _project_database(self, sequence: cudf.DataFrame, prefix: List[int]) -> cudf.DataFrame:
        results = []
        for idx, row in enumerate(sequence["data"].values_host):
            try:
                start_idx = row.index(prefix[-1]) + 1
                projected_row = row[start_idx:]
                if projected_row:
                    results.append(projected_row)
            except ValueError:
                pass
        return cudf.DataFrame({"data": results})

    def _mine_patterns(self, sequence: cudf.DataFrame, prefix: List[int]):
        flattened = cp.concatenate([cp.array(row) for row in sequence["data"].to_arrow().to_pylist()])
        item_counts = cp.unique(flattened, return_counts=True)
        indexs = item_counts[1] >= self.min_support
        frequent_items = (item_counts[0][indexs], item_counts[1][indexs])
        logging.info(f"Prefix: {prefix}, Frequent Items: {frequent_items}")
        for idx in range(len(frequent_items[0])):
            item, support = frequent_items[0][idx], frequent_items[1][idx]
            new_prefix = prefix + [item]
            self.patterns.append((tuple(new_prefix), support))

            projected_db = self._project_database(sequence, new_prefix)
            if len(projected_db) > 0:
                self._mine_patterns(projected_db, new_prefix)

    def incremental_mine(self, new_data: List[List[int]]):
        sequences = cudf.DataFrame({"data": new_data})
        self._mine_patterns(sequences, [])

    def get_patterns(self) -> List[Tuple[List[int], int]]:
        return self._get_patterns()


# 示例
if __name__ == "__main__":
    # 数据初始化
    db_path = "patterns.db"
    min_support = 2
    gpu_prefixspan = IncrementalGPUAcceleratedPrefixSpan(db_path, min_support)

    # 初始数据
    initial_data = [
        [1, 2, 3],
        [1, 3, 4, 5],
        [1, 2, 4],
        [2, 3, 5],
    ]
    gpu_prefixspan.incremental_mine(initial_data)

    # 输出历史模式
    print("Initial Patterns:")
    for pattern, support in gpu_prefixspan.get_patterns():
        print(f"Pattern: {pattern}, Support: {support}")

    # 增量数据
    new_data = [
        [1, 2, 5],
        [1, 3],
        [2, 4, 5],
    ]
    gpu_prefixspan.incremental_mine(new_data)

    # 输出更新后的模式
    print("\nUpdated Patterns:")
    for pattern, support in gpu_prefixspan.get_patterns():
        print(f"Pattern: {pattern}, Support: {support}")
