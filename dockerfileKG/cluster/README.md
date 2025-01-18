# Dockerfile分类设计原则
## dockerfile2vec
1. 构建dockerfile ast
2. 训练dockerfile tokenizer
```bash
python tokenizer_trainer.py
```
3. 准备微调数据集
```bash
python tokenized.py
```
4. 基于dockerfile ast，微调codebert，得到dockerbert
```bash
python run_mlm.py --model_name_or_path /home/yuehang/project/codebert-base/ \
    --tokenizer_name /home/yuehang/project/dockerfile-llm/dockerfileKG/cluster/ast2vec/dockerfile_ast_tokenizer \
    --train_file /home/yuehang/project/dockerfile-llm/dockerfileKG/dataset/tokenized/train.txt \
    --validation_file /home/yuehang/project/dockerfile-llm/dockerfileKG/dataset/tokenized/eval.txt \
    --line_by_line \
    --pad_to_max_length \
    --per_device_train_batch_size 8 \
    --per_device_eval_batch_size 8 \
    --do_train \
    --do_eval \
    --output_dir /home/yuehang/project/dockerfilebert
```
5. 使用dockerbert将dockerfile ast转化为特征向量
```bash
python encoder.py --pooling <pooling_policy>
```
## DBSCAN分类
使用dbscan/kmeans算法分类dockerfile
```bash
python kmeans_cluster.py
```