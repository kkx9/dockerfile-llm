#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Build
docker build -t parse-phase-3:v0 \
  -f "${DIR}/generate/Dockerfile" "${DIR}/generate"

# Run with volume mounts
time docker run \
  -it \
  --rm \
  -v "${DIR}/../dataset/dockerfile-ast/2-parsed-dockerfile-arch:/mnt/inputs" \
  -v "${DIR}/../dataset/dockerfile-ast/3-parsed-dockerfile-arch:/mnt/outputs" \
  parse-phase-3:v0
