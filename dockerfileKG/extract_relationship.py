import json
import lzma
import os
import re
import tqdm


def resolve_variable(value, docker_args):
    regex = r"\$\{[^\$]+\}|\$[^\f\n\r\t\v\$:/\s\(\|\"\']+"
    matches = re.finditer(regex, value)
    match_str = set()
    for match in matches:
        match_str.add(match.group())
    for s in match_str:
        var_name = s.strip('$').lstrip('{').rstrip('}')
        if var_name in docker_args.keys():
            value = value.replace(s, docker_args.get(var_name, value))
    return value


def process_line(line):
    data = json.loads(line)
    baseimages = {}
    curBaseIMage = ""
    docker_args = {}
    for item in data['children']:
        if item['type'] == 'DOCKER-ARG' or item['type'] == 'DOCKER-ENV':
            try:
                docker_args[item['children'][0]['value']] = item['children'][1]['value']
            except Exception as e:
                continue
            continue
        if item['type'] == 'DOCKER-FROM':
            if len(item['children']) == 1:
                baseimage = f"{item['children'][0]['value']}:latest"
            else:
                name, repo, tag = "", "", ""
                for i in range(0, len(item['children'])):
                    try:
                        if item['children'][i]['type'] == 'DOCKER-IMAGE-NAME':
                            name = resolve_variable(item['children'][i]['value'], docker_args)
                        if item['children'][i]['type'] == 'DOCKER-IMAGE-TAG':
                            tag = resolve_variable(item['children'][i]['value'], docker_args)
                        if item['children'][i]['type'] == 'DOCKER-IMAGE-REPO':
                            repo = resolve_variable(item['children'][i]['value'], docker_args)
                    except Exception as e:
                        continue
                if len(repo) == 0 and len(tag) == 0:
                    baseimage = name
                elif len(repo) == 0:
                    baseimage = f"{name}:{tag}"
                elif len(tag) == 0:
                    baseimage = f"{repo}/{name}:latest"
                else: 
                    baseimage = f"{repo}/{name}:{tag}"
            curBaseIMage = baseimage
            if baseimage not in baseimages:
                baseimages[baseimage] = {
                    "used_pkgs": [],
                    "install_pkgs": []
                }
            continue

        if item['type'] == 'DOCKER-RUN' and len(curBaseIMage) > 0:
            if 'install_pkg' in item:
                install_pkgs = item['install_pkg']
                resolved_pkgs = []
                for i in range(len(install_pkgs)):
                    pkgs = install_pkgs[i].split()
                    resolved_pkgs.extend(pkgs)
                baseimages[curBaseIMage]["install_pkgs"].extend(resolved_pkgs)
            if 'used_pkg' in item:
                used_pkgs = item['used_pkg']
                baseimages[curBaseIMage]["used_pkgs"].extend(used_pkgs)


    for baseimage in baseimages:
        install_pkgs = baseimages[baseimage]["install_pkgs"]
        baseimages[baseimage]["used_pkgs"] = [
            pkg for pkg in baseimages[baseimage]["used_pkgs"] if pkg not in install_pkgs
        ]

    return baseimages

def process_jsonl_file(input_file, output_file):

    with lzma.open(input_file, 'rt') as infile, open(output_file, 'w') as outfile:
        all_results = {}
        all_lines = infile.readlines()
        for line in tqdm.tqdm(all_lines, desc="Extract Relationship", unit="files"):
            processed_data = process_line(line)
            for baseimage, data in processed_data.items():
                if baseimage not in all_results:
                    all_results[baseimage] = {
                        "used_pkgs": [],
                        "install_pkgs": []
                    }    
                all_results[baseimage]["used_pkgs"].extend(data["used_pkgs"])
                all_results[baseimage]["install_pkgs"].extend(data["install_pkgs"])

        for baseimage, data in all_results.items():
            data['used_pkgs'] = list(set(data['used_pkgs']))
            data['install_pkgs'] = list(set(data['install_pkgs']))
            json.dump({baseimage: data}, outfile)
            outfile.write('\n')


if __name__ == '__main__':
    # input_file = './dataset/abstraction/output.jsonl.xz'
    # output_file = './dataset/extracted-relationship/image_cmd_pkg_new.jsonl'

    input_file = './dataset/dockerfile-ast/4-abstract-out-arch/gold.jsonl.xz'
    output_file = './dataset/extracted-relationship/image_cmd_pkg_gold.jsonl'

    process_jsonl_file(input_file, output_file)

    input_file = './dataset/dockerfile-ast/4-abstract-out-arch/github.jsonl.xz'
    output_file = './dataset/extracted-relationship/image_cmd_pkg_github.jsonl'

    process_jsonl_file(input_file, output_file)
