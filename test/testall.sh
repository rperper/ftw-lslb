#!/bin/bash
echo 'Test all rules and write to test.out'
rm test.out
for d in /usr/local/lslb/conf/coreruleset/tests/regression/tests/*/ ; do
       py.test -vs --tb=short ./CRS_Tests.py --config=lslb --ruledir=$d>>test.out
done

