# dockerfile refactor
## refactoring rules (TODO)
1. update base image, reduce the size of the image built from dockerfile.
2. sort instructions, efficiently utilize cache.
3. multi build stage, reduce the size of the final image.
4. combine or split commands, efficiently utilize cache.