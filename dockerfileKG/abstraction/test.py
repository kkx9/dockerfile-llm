import json
import lzma


file_sha = "023b9a07f0ef13ae4128449c950c856c2ed5d71c"

with lzma.open('/home/yuehang/project/binnacle-icse2020/datasets/2-phase-2-dockerfile-asts/github.jsonl.xz', mode='rt') as file:
    lines = file.readlines()
    for line in lines:
        data = json.loads(line)
        if data["file_sha"] == file_sha:
            print(file_sha)
            with open("log.json", "wt") as out_file:
                out_file.write(json.dumps(data, indent=4))
            break