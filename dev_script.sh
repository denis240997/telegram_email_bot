#!/bin/bash

source <(grep -v '^#' settings.txt | xargs -I {} echo "export {}")

rm /home/hamit/Desktop/inneme/db/email.sqlite
#/home/hamit/Desktop/inneme/env/bin/python /home/hamit/Desktop/inneme/dev_setup.py
/home/hamit/Desktop/inneme/env/bin/python /home/hamit/Desktop/inneme/main.py