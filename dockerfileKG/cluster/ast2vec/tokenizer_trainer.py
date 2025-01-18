import lzma
from tokenizers import Tokenizer, models, trainers, pre_tokenizers, normalizers, decoders
from transformers import RobertaTokenizerFast
import json
from collections import Counter

def train_ast_tokenizer_no_split(vocab_size=30000, output_path="tokenizer.json"):
    """
    训练自定义 Tokenizer，确保 AST 中的 token（包括复合词）不被拆分。
    """
    # 初始化 BPE 模型（禁用子词分割）
    tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))

    # 自定义 Normalizer：不进行标准化
    tokenizer.normalizer = normalizers.Sequence([])

    # 自定义 PreTokenizer：按空格拆分，但不改变 token 的内容
    tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()

    # 添加解码器，用于在输出时移除 `@@`
    tokenizer.decoder = decoders.WordPiece(prefix="@@")

    # 提取所有 token（type 和 value）
    def extract_tokens(ast):
        tokens = []
        tokens.append(f"@@{ast['type']}@@")
        if "value" in ast:
            tokens.append(f"@@{ast['value']}@@")
        for child in ast.get("children", []):
            tokens.extend(extract_tokens(child))
        return tokens

    # 读取 AST 数据，统计所有 token
    token_counter = Counter()
    corpus = []
    with lzma.open('../../dataset/dockerfile-ast/gold.jsonl.xz', mode='rt') as file:
        for line in file:
            ast = json.loads(line.strip())
            tokens = extract_tokens(ast)
            token_counter.update(tokens)
            corpus.append(" ".join(tokens))
    
    with lzma.open('../../dataset/dockerfile-ast/github.jsonl.xz', mode='rt') as file:
        for line in file:
            ast = json.loads(line.strip())
            tokens = extract_tokens(ast)
            token_counter.update(tokens)
            corpus.append(" ".join(tokens))  # 将 tokens 转为单行文本

    # 将频率高的 token 加入特殊词汇表，确保不被拆分
    special_tokens = list(dict(token_counter.most_common(vocab_size // 2)).keys())

    # 定义训练器
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"] + special_tokens
    )

    # 训练 Tokenizer
    tokenizer.train_from_iterator(corpus, trainer)

    # 保存 Tokenizer
    tokenizer.save(output_path)

    print(f"Tokenizer with no splitting saved to {output_path}")

# 示例调用
if __name__ == "__main__":
    train_ast_tokenizer_no_split(
        vocab_size=30000,
        output_path="dockerfile_ast_tokenizer.json"
    )

    custom_tokenizer = Tokenizer.from_file("dockerfile_ast_tokenizer.json")
    custom_tokenizer_hf = RobertaTokenizerFast(tokenizer_object=custom_tokenizer)
    custom_tokenizer_hf.save_pretrained("dockerfile_ast_tokenizer")
