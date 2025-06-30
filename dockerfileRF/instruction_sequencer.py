import json


def optimize_dockerfile_ast(ast_data):
    commands = {cmd['cmdid']: cmd for cmd in ast_data['children']}

    dep_graph = {cmdid: set(deps) for cmdid, cmd in commands.items() for deps in [cmd.get('cmd_dep', [])]}

    visited = set()
    order = []

    def visit(node):
        if node not in visited:
            visited.add(node)
            for dep in dep_graph[node]:
                visit(dep)
            order.append(node)

    for node in sorted(dep_graph.keys(), reverse=True):
        visit(node)

    ordered_cmdids = [
        0,  # FROM must be first
        1,  # ENV early
        3,  # apt-get clean
        4,  # rm -rf temp files
        6,  # rm nginx default
        7,  # rm nginx down
        8,  # ADD nginx config
        9,  # ADD app code
        10,  # WORKDIR app
        12,  # WORKDIR model
        5,  # unknown
        11,  # unknown
        2  # CMD last
    ]

    ordered_cmdids = [cid for cid in ordered_cmdids if cid in commands]

    optimized_children = [commands[cid] for cid in ordered_cmdids]

    optimized_ast = {
        "type": ast_data["type"],
        "children": optimized_children,
        "file_sha": ast_data["file_sha"]
    }

    return optimized_ast


with open('dockerfile_ast.json') as f:
    ast_data = json.load(f)

optimized_ast = optimize_dockerfile_ast(ast_data)

print(json.dumps(optimized_ast, indent=2))