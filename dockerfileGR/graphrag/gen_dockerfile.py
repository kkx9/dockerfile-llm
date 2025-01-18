from openai import OpenAI


base_url = "http://127.0.0.1:8000/v1/"
client = OpenAI(api_key="EMPTY", base_url=base_url)


def function_chat():
    messages = [{"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris?"}]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    response = client.chat.completions.create(
        model="chatglm3-6b",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    if response:
        content = response.choices[0].message.content
        print(content)
    else:
        print("Error:", response.status_code)


def generate_description(model="chatglm3-6b", prompt=None, sys_prompt=None, use_stream=False):
    messages = []
    if sys_prompt:
        messages.append({"role": "system", "content": sys_prompt})
    if prompt:
        messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=use_stream,
        max_tokens=8192,
        temperature=0.8,
        presence_penalty=1.1,
        top_p=0.8)
    if response:
        if use_stream:
            for chunk in response:
                print(chunk.choices[0].delta.content)
        else:
            content = response.choices[0].message.content
            print(content)
    else:
        print("Error:", response.status_code)


example_dockerfile = """
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y python3 python3-pip
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
CMD ["python3", "app.py"]
"""


if __name__ == "__main__":
    sys_prompt = "You are a dockerfile expert, please generate a dockerfile according to my description. Without any extra information, just a dockerfile.\n\n"

    # demo for generating a dockerfile, without hints the generated dockerfile may not correct.
    prompt = sys_prompt + "I need a python application that contain flask, and could connect to PostgreSQL database."
    knowledge_context = """
    You should follow the rules below:
    1. Base Image: python:3.8
    2. pip3 install flask, psycopg2, no requirements.txt file
    3. Recommended Commands: RUN apt-get update, COPY . /app, EXPOSE 5000
    """
    prompt = prompt + knowledge_context
    print(prompt)
    generate_description(model="chatglm3-6b-base", prompt=None, sys_prompt=prompt, use_stream=False)

