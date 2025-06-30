import ast
import lzma
import multiprocessing
from gensim.models import Word2Vec


def code_to_vector(ast_sequence, model):
    # 如果词不在词汇表中，跳过
    vectors = [model.wv[word] for word in ast_sequence if word in model.wv]
    return sum(vectors) / len(vectors) if vectors else None

def path2vec(paths):
    w2v_model = Word2Vec(sentences=paths, vector_size=50, window=5, min_count=1, workers=4)

    # 计算每个代码片段的向量表示
    code_vectors = [code_to_vector(seq, w2v_model) for seq in paths]

    return code_vectors


if __name__ == '__main__':
    with lzma.open('../../dataset/all-path/gold.jsonl.xz', mode='wt') as file:
            pool = multiprocessing.Pool()

            all_lines = file.readlines()
            length = len(all_lines)

            subtrees_list = pool.imap(path2vec, all_lines, chunksize=500)
