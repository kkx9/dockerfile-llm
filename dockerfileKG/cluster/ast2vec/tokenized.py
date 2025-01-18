import lzma
import json
import random

def extract_tokens(ast):
                tokens = []
                tokens.append(f"@@{ast['type']}@@")
                if "value" in ast:
                    tokens.append(f"@@{ast['value']}@@")
                for child in ast.get("children", []):
                    tokens.extend(extract_tokens(child))
                return tokens

def tokenize_ast_data(ast_file, output_file):
    with open(output_file, mode="wt") as out_file:
        with lzma.open(ast_file, mode="rt") as file:
            texts = []
            for line in file:
                ast = json.loads(line.strip())
                tokens = extract_tokens(ast)
                tokenized_text = " ".join(tokens)
                out_file.write(tokenized_text + "\n")



if __name__ == "__main__":
    tokenizer_path = "dockerfile_ast_tokenizer.json"
    tokenize_ast_data(
        ast_file="../../dataset/dockerfile-ast/gold.jsonl.xz",
        output_file="../../dataset/tokenized/all.txt"
    )
    tokenize_ast_data(
        ast_file="../../dataset/dockerfile-ast/github.jsonl.xz",
        output_file="../../dataset/tokenized/all.txt"
    )

    
    with open("../../dataset/tokenized/all.txt", mode="rt") as file:
        all_lines = file.readlines()
        random.shuffle(all_lines)
        train_lines = all_lines[:int(len(all_lines) * 0.8)]
        eval_lines = all_lines[int(len(all_lines) * 0.8):]

    with open("../../dataset/tokenized/train.txt", mode="wt") as file:
        file.writelines(train_lines)

    with open("../../dataset/tokenized/eval.txt", mode="wt") as file:
        file.writelines(eval_lines)