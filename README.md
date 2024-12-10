# dockerfile-llm
旨在利用LLM自动生成Dockerfile
# 系统架构
## 数据预处理
### Dockerfile
1. 从Github爬取官方Dockerfile以及star数量超过1k的仓库的Dockerfile
2. 使用现有的Dockerfile语法检测工具 [Hadolint](https://github.com/hadolint/hadolint) 对Dockerfile进行过滤
3. 将Dockerfile解析成抽象语法树（AST），通过特征提取，将Dockerfile按照不同应用分类（具体算法细节待实现）
4. 对于不同类型的Dockerfile，基于AST做规则挖掘，挖掘其中的普适性规则（如shell命令之间的用法习惯和组合，以及软件安装的依赖等等）
5. 基于挖掘到的规则，并结合官方推荐的best practice，生成Dockerfile领域知识图谱，用于In-Context Learning时上下文检索
### 问答对
1. 从stackoverflow爬取Dockerfile以及shell相关的问题-答案
2. 基于爬取到的答案，生成知识图谱（具体算法细节带实现）
## 调用LLM接口，自动生成Dockerfile
当用户提出需求时，基于知识图谱检索相关上下文，一并作为LLM输入，LLM输出答案，然后调用docker build构建镜像，并测试能否通过用户所给的命令
## Dockerfile自动修复以及优化
1. 若生成的Dockerfile构建失败或者运行命令失败，则收集其日志，用分词技术提取其中的关键字，并查询stackoverflow等相关博客网站，获取最相关的前五个URL，作为上下文一并输入给LLM自动修复
2. 对于正确的dockerfile，基于知识图谱，优化dockerfile结构，使其构建效率更高
3. 最后，将正确的dockerfile加入数据库，重新生成知识图谱
