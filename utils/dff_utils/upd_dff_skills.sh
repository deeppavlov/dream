#!/bin/bash

# change current directory to executable script directory
cd "$(dirname "$0")"
cd ../../skills

updating_files="README.md server.py test_server.py test.sh"
for file in README.md server.py test_server.py test.sh; do
    for skill in dff_*_skill ; do
        cp dff_template/$file $skill
    done
done
