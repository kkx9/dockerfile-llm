# dockerfile generator
## llama本地部署apiserver
1. 启动controller
```bash
python -m fastchat.serve.controller \
    --host localhost \
    --port 21001
```
2. 启动Llama-3-8B-Instruct
```bash
CUDA_VISIBLE_DEVICES="0" python -m fastchat.serve.model_worker \ 
    --model-path /home/yuehang/.cache/modelscope/hub/LLM-Research/Meta-Llama-3-8B-Instruct \
    --host localhost \
    --port 21002 \
    --worker-address "http://localhost:21002" \
    --gpus "0"
```
3. 启动openai_api_server
```bash
python -m fastchat.serve.openai_api_server \
    --host localhost \
    --port 21003 \
    --controller-address http://localhost:21001
```