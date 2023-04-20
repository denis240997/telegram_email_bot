#!/bin/bash

source <(grep -v '^#' /app/volume/settings.txt | xargs -I {} echo "export {}")

python -m app.main