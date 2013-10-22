#!/bin/sh
# This is a poor man's solution, just grep for all occassion of unittests
status=0

for test_py in $(grep --recursive --files-with-match 'import\s*unittest' munin/)
do
    echo '--> Running:' ${test_py}
    python ${test_py} 
    current_status=${?}
    echo '--> exit status was:' ${current_status}
    if [ ${current_status} -ne 0 ] 
        then
            status=${current_status}
    fi
done

echo '==> Test Exit Status is:' ${status}
exit ${status}
