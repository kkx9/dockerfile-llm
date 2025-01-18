import argparse
import logging
import numpy as np
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel


DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.DEBUG)


parser = argparse.ArgumentParser(description="Run Dockerfile embedding extraction.")
parser.add_argument('--pooling', type=str, default='first_last_avg', choices=['first_last_avg', 'last_avg', 'last2avg', 'last3avg', 'cls'], help='Pooling method to use.')
args = parser.parse_args()


def build_model(model_path='/mnt/sevenT/yuehang/dockerfilebert'):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModel.from_pretrained(model_path)
    model = model.to(DEVICE)
    return tokenizer, model


def run(samples, tokenizer, model, pooling, max_length=512):
    dockerfile_embeddings = []
    samples = tqdm(samples)
    for sample in samples:
        with torch.no_grad():
            inputs = tokenizer(sample, return_tensors="pt", padding="max_length", truncation=True,  max_length=max_length)
            inputs['input_ids'] = inputs['input_ids'].to(DEVICE)
            inputs['attention_mask'] = inputs['attention_mask'].to(DEVICE)
            hidden_states = model(**inputs, return_dict=True, output_hidden_states=True).hidden_states

            if pooling == 'first_last_avg':
                output_hidden_state = (hidden_states[-1] + hidden_states[1]).mean(dim=1)
            elif pooling == 'last_avg':
                output_hidden_state = (hidden_states[-1]).mean(dim=1)
            elif pooling == 'last2avg':
                output_hidden_state = (hidden_states[-1] + hidden_states[-2]).mean(dim=1)
            elif pooling == 'last3avg':
                output_hidden_state = (hidden_states[-1] + hidden_states[-2] + hidden_states[-3]).mean(dim=1)
            elif pooling == 'cls':
                output_hidden_state = (hidden_states[-1])[:, 0, :]
            else:
                raise Exception("unknown pooling {}".format(pooling))
            
            vec = output_hidden_state.cpu().numpy()[0]
            dockerfile_embeddings.append(vec)

    # 转为numpy数组
    dockerfile_embeddings = np.array(dockerfile_embeddings)
    np.save(f"{pooling}_embeddings.npy", dockerfile_embeddings)


if __name__ == "__main__":
    tokenizer, model = build_model()
    with open("/home/yuehang/project/dockerfile-llm/dockerfileKG/dataset/tokenized/all.txt", "r") as f:
        samples = f.readlines()
        run(samples, tokenizer, model, pooling=args.pooling)

