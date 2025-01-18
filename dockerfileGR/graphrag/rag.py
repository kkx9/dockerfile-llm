# coding=utf-8
import json
from typing import Dict, List
import requests


DEFAULT_MODEL = "Meta-Llama-3-8B-Instruct"


def assistant(content: str):
    return { "role": "assistant", "content": content }

def user(content: str):
    return { "role": "user", "content": content }

def chat_completion(
    messages: List[Dict],
    model = DEFAULT_MODEL,
    temperature: float = 0.6,
    top_p: float = 0.9,
    max_tokens: int = 2048,
    stream: bool = False,
) -> str:
    header = {'Content-Type': 'application/json'}
    data = {
          "messages": messages,
          "temperature": temperature, 
          "top_p" : top_p, 
          "max_tokens": max_tokens, 
          "model": model,
          "stream" : stream,
        #   "n" : 1,
        #   "best_of": 1, 
        #   "presence_penalty": 1.2, 
        #   "frequency_penalty": 0.2,           
        #   "top_k": 50, 
        #   "use_beam_search": False, 
        #   "stop": [], 
        #   "ignore_eos" :False,
        #   "logprobs": None
    }
    response = requests.post(
        url='http://127.0.0.1:21003/v1/chat/completions',
        headers=header,
        data=json.dumps(data).encode('utf-8')
    )
    result = json.loads(response.content)
    return result["choices"][0]["message"]["content"]


def complete_and_print(prompt: str, model: str = DEFAULT_MODEL):
    print("="*50 + f"\n{prompt}\n" + "="*50)
    response = chat_completion(messages=[user(prompt)], model=model)
    print(response, end="\n\n")

# few-shot test
def sentiment(text):
    response = chat_completion(messages=[
        user("You are a sentiment classifier. For each message, give the percentage of positive/netural/negative."),
        user("I liked it"),
        assistant("70% positive 30% neutral 0% negative"),
        user("It could be better"),
        assistant("0% positive 50% neutral 50% negative"),
        user("It's fine"),
        assistant("25% positive 50% neutral 25% negative"),
        user(text),
    ])
    return response


def print_sentiment(text):
    print(f'INPUT: {text}')
    print(sentiment(text))


if __name__ == "__main__":
    # answer = chat_completion(messages=[user("What is the weather in San Francisco?")])
    # print(answer)

    # print_sentiment("I thought it was okay")
    # # More likely to return a balanced mix of positive, neutral, and negative
    # print_sentiment("I loved it!")
    # # More likely to return 100% positive
    # print_sentiment("Terrible service 0/10")
    # # More likely to return 100% negative

    complete_and_print("What time is my dinner reservation on Saturday and what should I wear?")