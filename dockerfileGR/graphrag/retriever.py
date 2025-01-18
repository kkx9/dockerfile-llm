import networkx as nx
import torch
from transformers import pipeline
from modelscope import snapshot_download

model_id = snapshot_download("LLM-Research/Meta-Llama-3-8B-Instruct")

llm = pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device="cuda:1",
)

# 示例知识图谱
class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_entity(self, entity, entity_type):
        self.graph.add_node(entity, type=entity_type)

    def add_relationship(self, source, target, relationship):
        self.graph.add_edge(source, target, relationship=relationship)

    def search_graph(self, start_entity, demand, max_depth=3):
        """
        图搜索算法，基于需求和实体进行搜索。
        :param start_entity: 起始实体。
        :param demand: 查询需求。
        :param max_depth: 最大搜索深度。
        :return: 搜索结果。
        """
        results = []
        visited = set()
        
        def dfs(node, depth):
            if depth > max_depth or node in visited:
                return
            visited.add(node)
            
            # 判断是否符合需求
            for neighbor in self.graph.neighbors(node):
                edge_data = self.graph.get_edge_data(node, neighbor)
                if demand.lower() in edge_data['relationship'].lower():
                    results.append((node, neighbor, edge_data['relationship']))
                dfs(neighbor, depth + 1)
        
        dfs(start_entity, 0)
        return results

# 初始化知识图谱
kg = KnowledgeGraph()

# 添加实体
kg.add_entity("ubuntu:20.04", "image")
kg.add_entity("node:22-alpine", "image")
kg.add_entity("python3", "package")
kg.add_entity("RUN apt-get install", "command")
kg.add_entity("pip install -r requirements.txt", "command")

# 添加关系
kg.add_relationship("ubuntu:20.04", "python3", "contains")
kg.add_relationship("node:22-alpine", "RUN apt-get install", "supports")
kg.add_relationship("python3", "pip install -r requirements.txt", "used_with")

# 查询解析函数
def extract_query_entities_and_demand(query):
    """
    使用 LLM 提取查询中的实体和需求。
    :param query: 用户查询字符串。
    :return: 实体列表和需求描述。
    """
    query = f"""
        ### Task Description:
        You are a dockerfile expert, please generate a dockerfile according to the demand: [User Query] while adhering to [Answer Requirements].

        ### Answer Requirements:
        1) Please take time to think slowly, understand step by step, and answer questions. Do not skip key steps.
        2) Fully analyze the problem through thinking and exploratory analysis.
        3) Make sure the grammar is correct and the content is complete.
        4) The usage of the COPY command, adhering to the rule: COPY <src> <dts>, with a space required between the source file and the destination file.
        5) Provide no explanations, just source code.

        ### User Query:
        {query}
        """

    prompt = llm.tokenizer.apply_chat_template(
        [{"role": "user", "content": query}], 
        tokenize=False, 
        add_generation_prompt=True
    )



    terminators = [
        llm.tokenizer.eos_token_id,
        llm.tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]


    response = llm(prompt,
        max_new_tokens=1024,
        eos_token_id=terminators,
        do_sample=True,
        temperature=0.6,
        top_p=0.9,
    )
    parsed = response[0]["generated_text"][len(prompt):]
    print(parsed)
    # 简单解析结果，假设实体和需求分行显示
    lines = parsed.splitlines()
    entities = []
    demand = ""
    for line in lines:
        if "Entity:" in line:
            entities.append(line.split(":", 1)[1].strip())
        elif "Demand:" in line:
            demand = line.split(":", 1)[1].strip()
    return entities, demand

# 示例用户查询
query = """
I need a multi-stage Dockerfile that builds a frontend using Node.js and a backend using Go. 
The final image should include all necessary dependencies and optimized size.
"""

# 提取实体和需求
entities, demand = extract_query_entities_and_demand(query)

# 搜索知识图谱
search_results = []
for entity in entities:
    if entity in kg.graph.nodes:
        search_results.extend(kg.search_graph(entity, demand))

# 输出检索结果
print("Search Results:")
for result in search_results:
    print(f"From: {result[0]}, To: {result[1]}, Relation: {result[2]}")
