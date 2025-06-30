from py2neo import Graph, Node, Relationship


class DockerfileKnowledgeGraph:
    def __init__(self, uri):
        # 连接 Neo4j 数据库
        self.graph = Graph(uri)

    def create_dockerfile_entity(self, dockerfile_name, version, created_at):
        dockerfile_node = Node("Dockerfile", name=dockerfile_name, version=version, created_at=created_at)
        self.graph.create(dockerfile_node)

    def create_image_entity(self, image_name, version, size, base_image):
        image_node = Node("Image", name=image_name, version=version, size=size, base_image=base_image)
        self.graph.create(image_node)

    def create_command_entity(self, command_name, description):
        command_node = Node("Command", name=command_name, description=description)
        self.graph.create(command_node)

    def create_package_entity(self, package_name, version, description):
        package_node = Node("Package", name=package_name, version=version, description=description)
        self.graph.create(package_node)

    def create_relationship(self, node1_label, node1_name, node2_label, node2_name, relationship_type, properties=None):
        query = f"""
        MATCH (a:{node1_label} {{name: $node1_name}}), (b:{node2_label} {{name: $node2_name}})
        MERGE (a)-[r:{relationship_type}]->(b)
        """
        if properties:
            query += " SET r += $properties"
        self.graph.run(query, node1_name=node1_name, node2_name=node2_name, properties=properties)

    def create_dockerfile_graph(self):
        # 创建 Dockerfile 实体
        self.create_dockerfile_entity("example_dockerfile", "1.0", "2022-01-01")

        # 创建镜像实体
        self.create_image_entity("ubuntu:20.04", "latest", "64MB", "ubuntu:18.04")
        self.create_image_entity("python:3.8", "latest", "200MB", "ubuntu:20.04")

        # 创建命令实体
        self.create_command_entity("RUN apt-get update", "Update the package list")
        self.create_command_entity("RUN apt-get install -y python3", "Install python3")

        # 创建软件包实体
        self.create_package_entity("python3", "3.8", "Python programming language")

        # 创建关系
        self.create_relationship("Image", "ubuntu:20.04", "Package", "python3", "CONTAINS")
        self.create_relationship("Image", "python:3.8", "Package", "python3", "USES")
        self.create_relationship("Image", "ubuntu:20.04", "Command", "RUN apt-get update", "RUNS")
        self.create_relationship("Image", "python:3.8", "Command", "RUN apt-get install -y python3", "RUNS")
        self.create_relationship("Command", "RUN apt-get install -y python3", "Package", "python3", "DEPENDS_ON")


if __name__ == "__main__":
    # Neo4j连接信息
    uri = "bolt://localhost:7687"

    # 创建图数据库实例
    graph = DockerfileKnowledgeGraph(uri)

    # 创建知识图谱
    graph.create_dockerfile_graph()
