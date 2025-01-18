# import transformers
# import torch
# from modelscope import snapshot_download

# model_id = snapshot_download("LLM-Research/Meta-Llama-3-8B-Instruct")

# pipeline = transformers.pipeline(
#     "text-generation",
#     model=model_id,
#     model_kwargs={"torch_dtype": torch.bfloat16},
#     device="cuda",
# )

# messages = [
#     {"role": "system", "content": "You are a dockerfile expert, please generate a dockerfile according to my description. Without any extra information, just a dockerfile."},
#     {"role": "user", "content": "I need a basic environment based on Ubuntu 20.04 to run a Python application. This application has a requirements.txt file listing the required Python libraries. I want to install these dependencies and run a Python script named app.py."},
# ]

# prompt = pipeline.tokenizer.apply_chat_template(
# 		messages, 
# 		tokenize=False, 
# 		add_generation_prompt=True
# )



# terminators = [
#     pipeline.tokenizer.eos_token_id,
#     pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
# ]

# print(prompt)

# outputs = pipeline(
#     prompt,
#     max_new_tokens=256,
#     eos_token_id=terminators,
#     do_sample=True,
#     temperature=0.6,
#     top_p=0.9,
# )
# print(outputs[0]["generated_text"][len(prompt):])


from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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",
)

completion = client.chat.completions.create(
  # extra_headers={
  #   "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
  #   "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
  # },
  model="meta-llama/llama-3.1-405b-instruct:free",
  messages=[
    {
      "role": "user",
      "content": "Give me a dockerfile."
    }
  ]
)
print(completion.choices[0].message.content)