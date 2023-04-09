#!/bin/bash

source <(grep -v '^#' settings.txt | xargs -I {} echo "export {}")

/home/hamit/Desktop/inneme/env/bin/python /home/hamit/Desktop/inneme/main.py