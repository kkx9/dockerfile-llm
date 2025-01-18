import json
import lzma
import numpy as np


if __name__ == '__main__':
    # all_length = []
    # with lzma.open('../../dataset/all-path/gold.jsonl.xz', mode='rt') as file:
    #     all_lines = file.readlines()
    #     for line in all_lines:
    #         # print(line)
    #         paths = json.loads(line)
    #         path_lengths = [len(path) for path in paths]
    #         all_length.extend(path_lengths)

    # with lzma.open('../../dataset/all-path/github.jsonl.xz', mode='rt') as file:
    #     all_lines = file.readlines()
    #     for line in all_lines:
    #         paths = json.loads(line)
    #         path_lengths = [len(path) for path in paths]
    #         all_length.extend(path_lengths)

    # print(int(np.percentile(all_length, 90))) # 90%的path长度不超过8

    all_length = []
    with open('../../dataset/tokenized/gold.jsonl', mode='rt') as file:
        all_lines = file.readlines()
        for line in all_lines:
            data = json.loads(line)
            all_length.append(len(data['input_ids']))

    with open('../../dataset/tokenized/github.jsonl', mode='rt') as file:
        all_lines = file.readlines()
        for line in all_lines:
            data = json.loads(line)
            all_length.append(len(data['input_ids']))

    print(int(np.percentile(all_length, 75))) # 90% 1213    %80 662   %75  523
