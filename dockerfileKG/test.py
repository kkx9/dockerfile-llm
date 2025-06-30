import json

# 数据示例
data = [['DOCKER-FILE', 'DOCKER-FROM', 'DOCKER-IMAGE-NAME'], ['DOCKER-FILE', 'DOCKER-RUN', 'BASH-SCRIPT', 'UNKNOWN'], ['DOCKER-FILE', 'DOCKER-FROM', 'DOCKER-IMAGE-NAME'], ['DOCKER-FILE', 'DOCKER-RUN', 'BASH-SCRIPT', 'UNKNOWN']]

# 转换为 JSON 格式并保存到文件
with open('output.json', 'w') as f:
    f.write(json.dumps(data))
    f.write(json.dumps(data) + '\n')
