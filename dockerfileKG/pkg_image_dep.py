import json
from collections import defaultdict, Counter
from neo4j import GraphDatabase


dep_file = "./dataset/extracted-relationship/image_cmd_pkg.jsonl"

class Neo4jDependencyAnalyzer:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, min_cooccurrence=2, dependency_threshold=0.5):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.min_cooccurrence = min_cooccurrence
        self.dependency_threshold = dependency_threshold
        self.cooccurrence_matrix = defaultdict(Counter)
        self.package_frequency = Counter()
        self.total_images = 0
        self._init_known_dependencies()

    def _init_known_dependencies(self):
        self.known_dependencies = {
            "ros-kinetic-desktop-full": ["ros-kinetic-rviz", "ros-kinetic-gazebo-ros-pkgs"],
            "gazebo7": ["libogre-1.9-dev", "libbullet-dev"],
            "tensorflow": ["numpy", "grpcio"],
            "keras": ["tensorflow", "numpy"],
            "numpy": ["python-dev", "libblas-dev"],
        }
        self.known_conflicts = {
            "tensorflow": ["theano"],
            "gazebo7": ["gazebo9"],
        }

    def load_data_from_file(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
        self.total_images = len(data)
        for image_info in data.values():
            packages = image_info.get("install_pkgs", [])
            for i, pkg1 in enumerate(packages):
                self.package_frequency[pkg1] += 1
                for pkg2 in packages[i + 1:]:
                    self.cooccurrence_matrix[pkg1][pkg2] += 1
                    self.cooccurrence_matrix[pkg2][pkg1] += 1

    def _calculate_dependency_score(self, pkg1, pkg2):
        cooccur_count = self.cooccurrence_matrix[pkg1].get(pkg2, 0)
        return cooccur_count / self.package_frequency[pkg1] if cooccur_count >= self.min_cooccurrence else 0.0

    def analyze_implicit_dependencies(self):
        implicit_deps = {}
        all_packages = list(self.package_frequency.keys())
        for pkg1 in all_packages:
            for pkg2 in all_packages:
                if pkg1 != pkg2:
                    score = self._calculate_dependency_score(pkg1, pkg2)
                    if score >= self.dependency_threshold:
                        implicit_deps[(pkg1, pkg2)] = score
        return implicit_deps

    def _clear_neo4j_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def save_to_neo4j(self):
        self._clear_neo4j_database()
        implicit_deps = self.analyze_implicit_dependencies()
        all_packages = set(self.package_frequency.keys())

        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Package) REQUIRE p.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (i:Image) REQUIRE i.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Command) REQUIRE c.name IS UNIQUE")

            with open(dep_file, "r") as f:
                image_data = json.load(f)

            for image_name, details in image_data.items():
                session.run("MERGE (i:Image {name: $image_name})", image_name=image_name)

                if "father_image" in details:
                    session.run("""
                        MERGE (i1:Image {name: $child_image})
                        MERGE (i2:Image {name: $parent_image})
                        MERGE (i1)-[r:BASED_ON]->(i2)
                        """, child_image=image_name, parent_image=details["father_image"])

                for pkg in details.get("install_pkgs", []):
                    session.run("MERGE (p:Package {name: $pkg_name})", pkg_name=pkg)
                    session.run("""
                        MATCH (i:Image {name: $image_name})
                        MATCH (p:Package {name: $pkg_name})
                        MERGE (i)-[r:INSTALLS]->(p)
                        """, image_name=image_name, pkg_name=pkg)

                for cmd in details.get("used_pkgs", []):
                    session.run("MERGE (c:Command {name: $cmd_name})", cmd_name=cmd)
                    session.run("""
                        MATCH (i:Image {name: $image_name})
                        MATCH (c:Command {name: $cmd_name})
                        MERGE (i)-[r:USES]->(c)
                        """, image_name=image_name, cmd_name=cmd)

            for pkg, deps in self.known_dependencies.items():
                if pkg in all_packages:
                    for dep in deps:
                        if dep in all_packages:
                            session.run("""
                                MATCH (p1:Package {name: $pkg1})
                                MATCH (p2:Package {name: $pkg2})
                                MERGE (p1)-[r:DEPENDS_ON {type: 'explicit'}]->(p2)
                                SET r.confidence = 1.0
                                """, pkg1=pkg, pkg2=dep)

            for (pkg1, pkg2), confidence in implicit_deps.items():
                result = session.run("""
                    MATCH (p1:Package {name: $pkg1})-[r:DEPENDS_ON]->(p2:Package {name: $pkg2})
                    RETURN r
                    """, pkg1=pkg1, pkg2=pkg2)
                if not result.single():
                    session.run("""
                        MATCH (p1:Package {name: $pkg1})
                        MATCH (p2:Package {name: $pkg2})
                        MERGE (p1)-[r:DEPENDS_ON {type: 'implicit'}]->(p2)
                        SET r.confidence = $confidence
                        """, pkg1=pkg1, pkg2=pkg2, confidence=float(confidence))

            for pkg, conflicts in self.known_conflicts.items():
                if pkg in all_packages:
                    for conflict in conflicts:
                        if conflict in all_packages:
                            session.run("""
                                MATCH (p1:Package {name: $pkg1})
                                MATCH (p2:Package {name: $pkg2})
                                MERGE (p1)-[r:CONFLICTS_WITH]->(p2)
                                """, pkg1=pkg, pkg2=conflict)


if __name__ == "__main__":
    analyzer = Neo4jDependencyAnalyzer(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        min_cooccurrence=2,
        dependency_threshold=0.5
    )
    analyzer.load_data_from_file(dep_file)
    analyzer.save_to_neo4j()
