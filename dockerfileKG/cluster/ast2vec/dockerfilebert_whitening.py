import logging
import numpy as np
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel


DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

MAX_LENGTH = 512
BATCH_SIZE = 256
DATA_PATH = '/home/yuehang/project/dockerfile-llm/dockerfileKG/dataset/tokenized/all.txt'
logging.basicConfig(format='%(asctime)s : %(message)s', level=logging.DEBUG)


MODEL_ZOOS = {

    'BERTbase-whiten-256(target)': {
        'encoder': '/mnt/sevenT/yuehang/dockerfilebert',
        'pooling': 'first_last_avg',
        'n_components': 256,
    },

    'BERTlarge-whiten-384(target)': {
        'encoder': '/mnt/sevenT/yuehang/dockerfilebert',
        'pooling': 'first_last_avg',
        'n_components': 384,
    },

}

def ast_to_vec(ast, tokenizer, model, pooling, max_length):
    with torch.no_grad():
        inputs = tokenizer(ast, return_tensors="pt", padding="max_length", truncation=True,  max_length=max_length)
        inputs['input_ids'] = inputs['input_ids'].to(DEVICE)
        # inputs['token_type_ids'] = inputs['token_type_ids'].to(DEVICE)
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
    return vec


def asts_to_vecs(asts, tokenizer, model, pooling, max_length, verbose=True):
    vecs = []
    if verbose:
        asts = tqdm(asts)
    for ast in asts:
        vec = ast_to_vec(ast, tokenizer, model, pooling, max_length)
        vecs.append(vec)
    assert len(asts) == len(vecs)
    vecs = np.array(vecs)
    return vecs

def compute_kernel_bias(vecs):
    """计算kernel和bias
    最后的变换：y = (x + bias).dot(kernel)
    """
    vecs = np.concatenate(vecs, axis=0)
    mu = vecs.mean(axis=0, keepdims=True)
    cov = np.cov(vecs.T)
    u, s, vh = np.linalg.svd(cov)
    W = np.dot(u, np.diag(1/np.sqrt(s)))
    return W, -mu

def transform_and_normalize(vecs, kernel, bias):
    """应用变换，然后标准化
    """
    if not (kernel is None or bias is None):
        vecs = (vecs + bias).dot(kernel)
    return normalize(vecs)


def normalize(vecs):
    """标准化
    """
    return vecs / (vecs**2).sum(axis=1, keepdims=True)**0.5

def prepare(params, samples):
    vecs = asts_to_vecs(samples, params['tokenizer'], params['encoder'], \
            params['pooling'], MAX_LENGTH, verbose=True)
    kernel, bias = compute_kernel_bias([vecs])
    kernel = kernel[:, :params['n_components']]
    params['whiten'] = (kernel, bias)
    logging.info('Get whiten kernel and bias from {} samples.'.format(len(samples)))
    return None


def batcher(params, batch):
    embeddings = []
    for ast in batch:
        vec = ast_to_vec(ast, params['tokenizer'], \
                params['encoder'], params['pooling'], MAX_LENGTH)
        embeddings.append(vec)
    embeddings = np.vstack(embeddings)
    embeddings = transform_and_normalize(embeddings, 
            kernel=params['whiten'][0],
            bias=params['whiten'][1]
        )  # whitening
    logging.info('Embedding {} samples.'.format(len(batch)))
    return embeddings


def embed(params, samples):
    embeddings = []
    with tqdm(total=len(samples), desc="Processing Data", unit="item") as pbar:
        for i in range(0, len(samples), params['batch_size']):
            batch = samples[i: i + params['batch_size']]
            embeddings.append(batcher(params, batch))
            pbar.update(len(batch))
    embeddings = np.vstack(embeddings)
    logging.info('Totally embedding {} samples.'.format(len(samples)))
    return embeddings


def build_model(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model = model.to(DEVICE)
    return tokenizer, model


def run(model_name, data_path=DATA_PATH):

    model_config = MODEL_ZOOS[model_name]
    logging.info(f"{model_name} configs: {model_config}")

    tokenizer, encoder = build_model(model_config['encoder'])
    logging.info("Building {} tokenizer and model successfuly.".format(model_config['encoder']))

    params = {
            'tokenizer': tokenizer,
            'encoder': encoder,
            'pooling': model_config['pooling'],
            'n_components': model_config['n_components'],
            'batch_size': BATCH_SIZE
        }

    with open(data_path, 'r') as f:
        samples = f.readlines()
    prepare(params, samples)
    embeddings = embed(params, samples)
    save_embedding(embeddings, model_name)


def save_embedding(embeddings, model_name):
    np.save(f"{model_name}_embeddings.npy", embeddings)
    logging.info(f"Saved embeddings to {model_name}_embeddings.npy")

def run_all_model():

    for model_name in MODEL_ZOOS:
        run(model_name, DATA_PATH)


if __name__ == '__main__':
    run_all_model()