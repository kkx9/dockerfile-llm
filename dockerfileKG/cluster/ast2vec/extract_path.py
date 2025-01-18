import json
import lzma
import multiprocessing
import tqdm


def extract_all_subtrees(ast_str):
    ast_json = json.loads(ast_str)
    subtrees = [ast_json]

    for child in ast_json.get("children", []):
        subtrees.extend(extract_all_subtrees(json.dumps(child)))

    return subtrees


def extract_paths(ast, current_path=None):
    if current_path is None:
        current_path = []

    current_path.append(ast["type"])

    if not ast.get("children", []):
        return [current_path]

    paths = []
    for child in ast["children"]:
        paths.extend(extract_paths(child, current_path[:]))  # 注意复制路径以防止递归污染

    return paths

if __name__ == '__main__':
    with lzma.open('../../dataset/all-path/gold.jsonl.xz', mode='wt') as out_file:
        with lzma.open('../../dataset/dockerfile-ast/gold.jsonl.xz', mode='rt') as file:
            pool = multiprocessing.Pool()

            all_lines = file.readlines()
            length = len(all_lines)

            subtrees_list = pool.imap(extract_all_subtrees, all_lines, chunksize=500)

            for subtrees in tqdm.tqdm(subtrees_list, total=length, desc="Generating"):
                paths = []
                for subtree in subtrees:
                    paths.extend(extract_paths(subtree))
                out_file.write(json.dumps(paths) + "\n")

    with lzma.open('../../dataset/all-path/github.jsonl.xz', mode='wt') as out_file:
        with lzma.open('../../dataset/dockerfile-ast/github.jsonl.xz', mode='rt') as file:
            pool = multiprocessing.Pool()

            all_lines = file.readlines()
            length = len(all_lines)

            subtrees_list = pool.imap(extract_all_subtrees, all_lines, chunksize=500)

            for subtrees in tqdm.tqdm(subtrees_list, total=length, desc="Generating"):
                paths = []
                for subtree in subtrees:
                    paths.extend(extract_paths(subtree))
                out_file.write(json.dumps(paths) + "\n")
