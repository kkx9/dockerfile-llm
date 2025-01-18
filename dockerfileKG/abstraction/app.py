import copy
import re
import yaml
import dockerfile
import os
import sys
import json
import lzma
import replace_bash_variable
import find_dependency
import tqdm
from shutil import copyfile


DATA_DIR = '../dataset/dockerfile-ast/'

def walk(res,num,ta):
    print(ta + str(num) +" command is :")
    for k,v in res.items():
        if k != 'children':
            print(ta+k+" : "+str(v))
    for i in range(len(res['children'])):
        walk(res['children'][i], num+i+1,ta+" \t")

def walk_cmd(cmd):
    ans = cmd['type'] + ' '
    if 'value' in cmd:
        ans += cmd['value'] + ' '
    for subcmd in cmd['children']:
        ans += walk_cmd(subcmd)
    return ans
def middleware():
    with lzma.open(f'{DATA_DIR}2-parsed-dockerfile-arch/gold.jsonl.xz', mode='wt') as out_file:
        with lzma.open(f'{DATA_DIR}2-parsed-dockerfile/gold.jsonl.xz', mode='rt') as file:
            lines = file.readlines()
            result = []
            for line in tqdm.tqdm(lines, total=len(lines), desc="Generating"):
                tmp = json.loads(line)
                try:
                    replace_bash_variable.calcCompact(tmp)
                    result.append(json.dumps(tmp))
                except Exception as e:
                    with open('error.log', 'a') as f:
                        f.write(f"{tmp['file_sha']}, err: {e}\n") 
            for item in tqdm.tqdm(result, total=len(result), desc="Saving"):
                out_file.write('{}\n'.format(item))

    with lzma.open(f'{DATA_DIR}2-parsed-dockerfile-arch/github.jsonl.xz', mode='wt') as out_file:
        with lzma.open(f'{DATA_DIR}2-parsed-dockerfile/github.jsonl.xz', mode='rt') as file:
            lines = file.readlines()
            result = []
            for line in tqdm.tqdm(lines, total=len(lines), desc="Generating"):
                tmp = json.loads(line)
                try:
                    replace_bash_variable.calcCompact(tmp)
                    result.append(json.dumps(tmp))
                except Exception as e:
                    with open('error.log', 'a') as f:
                        f.write(f"{tmp['file_sha']}, err: {e}\n")
            for item in tqdm.tqdm(result, total=len(result), desc="Saving"):
                out_file.write('{}\n'.format(item))
        


def checkout():
    find_dependency.init()
    with lzma.open(f'{DATA_DIR}3-parsed-dockerfile-arch/gold.jsonl.xz', mode='rt') as f:
        with lzma.open(f'{DATA_DIR}4-abstract-out-arch/gold.jsonl.xz', mode='wt') as out_file:
            lines = f.readlines()
            for line in tqdm.tqdm(lines, total=len(lines), desc="Generating"):
                replace_bash_variable.clean()
                find_dependency.clean()
                file_dict = json.loads(line)

                replace_bash_variable.assign_pair = {}
                replace_bash_variable.learnAndReplaceVariable(file_dict)
                replace_bash_variable.calcCompact(file_dict)
                
                replace_bash_variable.findURL(file_dict)
                replace_bash_variable.abstract_tree(file_dict)
                replace_bash_variable.split_dockerfile(file_dict)
                
                find_dependency.find_dep(file_dict)
                out_file.write('{}\n'.format(json.dumps(file_dict)))


    with lzma.open(f'{DATA_DIR}3-parsed-dockerfile-arch/github.jsonl.xz', mode='rt') as f:
        with lzma.open(f'{DATA_DIR}4-abstract-out-arch/github.jsonl.xz', mode='wt') as out_file:
            lines = f.readlines()
            for line in tqdm.tqdm(lines, total=len(lines), desc="Generating"):
                replace_bash_variable.clean()
                find_dependency.clean()
                file_dict = json.loads(line)

                replace_bash_variable.assign_pair = {}
                replace_bash_variable.learnAndReplaceVariable(file_dict)
                replace_bash_variable.calcCompact(file_dict)
                
                replace_bash_variable.findURL(file_dict)
                replace_bash_variable.abstract_tree(file_dict)
                replace_bash_variable.split_dockerfile(file_dict)
                
                find_dependency.find_dep(file_dict)
                out_file.write('{}\n'.format(json.dumps(file_dict)))
            
def check(tmp):
    if tmp['type'] == 'UNKNOWN':
        return True
    for item in tmp['children']:
        if check(item):
            return True

def printResult():
    with lzma.open('abstract-out/output.jsonl.xz', mode='rt') as f:
        lines = f.readlines()
        for line in lines:
            tmp = json.loads(line)
            if tmp['file_sha'] == '2.dockerfile':
                continue
            if check(tmp):
                print(tmp['file_sha'])

def checkResult():
    with lzma.open('p2-out/output.jsonl.xz', mode='rt') as f:
        lines = f.readlines()
        for line in lines:
            tmp = json.loads(line)
            if tmp['file_sha'] == '2.dockerfile':
                continue
            if check(tmp):
                print(tmp['file_sha'])

def main():
    if str(sys.argv[1]) == 'middleware':
        middleware()
    elif str(sys.argv[1]) == 'print':
        printResult()
    else:
        checkout()
        # checkResult()

if __name__ == '__main__':
    main()