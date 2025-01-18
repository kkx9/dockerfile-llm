from neo4j import GraphDatabase

class DockerfileKnowledgeGraph:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def close(self):
        self.driver.close()
    
    def create_dockerfile_entity(self, session, dockerfile_name, version, created_at):
        query = """
        CREATE (d:Dockerfile {name: $dockerfile_name, version: $version, created_at: $created_at})
        """
        session.run(query, dockerfile_name=dockerfile_name, version=version, created_at=created_at)
    
    def create_image_entity(self, session, image_name, version, size, base_image):
        query = """
        CREATE (i:Image {name: $image_name, version: $version, size: $size, base_image: $base_image})
        """
        session.run(query, image_name=image_name, version=version, size=size, base_image=base_image)
    
    def create_command_entity(self, session, command_name, description):
        query = """
        CREATE (c:Command {name: $command_name, description: $description})
        """
        session.run(query, command_name=command_name, description=description)
    
    def create_package_entity(self, session, package_name, version, description):
        query = """
        CREATE (p:Package {name: $package_name, version: $version, description: $description})
        """
        session.run(query, package_name=package_name, version=version, description=description)
    
    def create_relationship(self, session, node1, node2, relationship_type, properties=None):
        # 关系的属性是可选的
        query = f"""
        MATCH (a), (b)
        WHERE a.name = $node1_name AND b.name = $node2_name
        CREATE (a)-[r:{relationship_type}]->(b)
        """
        
        if properties:
            query = query + " SET r += $properties"
        
        session.run(query, node1_name=node1, node2_name=node2, properties=properties)

    def create_dockerfile_graph(self):
        with self.driver.session() as session:
            # 创建 Dockerfile 实体
            self.create_dockerfile_entity(session, "example_dockerfile", "1.0", "2022-01-01")
            
            # 创建镜像实体
            self.create_image_entity(session, "ubuntu:20.04", "latest", "64MB", "ubuntu:18.04")
            self.create_image_entity(session, "python:3.8", "latest", "200MB", "ubuntu:20.04")
            
            # 创建命令实体
            self.create_command_entity(session, "RUN apt-get update", "Update the package list")
            self.create_command_entity(session, "RUN apt-get install -y python3", "Install python3")
            
            # 创建软件包实体
            self.create_package_entity(session, "python3", "3.8", "Python programming language")
            
            # 创建关系
            self.create_relationship(session, "ubuntu:20.04", "python3", "CONTAINS")
            self.create_relationship(session, "python:3.8", "python3", "USES")
            self.create_relationship(session, "ubuntu:20.04", "RUN apt-get update", "RUNS")
            self.create_relationship(session, "python:3.8", "RUN apt-get install -y python3", "RUNS")
            self.create_relationship(session, "RUN apt-get install -y python3", "python3", "DEPENDS_ON")
            
            # 更多的创建实体和关系操作...

if __name__ == "__main__":
    # Neo4j连接信息
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "password"
    
    # 创建图数据库实例
    graph = DockerfileKnowledgeGraph(uri, username, password)
    
    # 创建知识图谱
    graph.create_dockerfile_graph()
    
    # 关闭数据库连接
    graph.close()
