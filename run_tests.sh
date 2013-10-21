#!/bin/sh
# This is a poor man's solution, just grep for all occassion of unittests
for test_py in $(grep --recursive --files-with-match 'import\s*unittest' munin/)
do
    python ${test_py};
done
