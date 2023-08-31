#!/bin/bash
echo 'Test all rules and write to test.out'
pgrep lslb
if [ "$?" = "0" ]; then
    echo "You must have the load balancer stopped before running the test."
    exit 1
fi
rm /usr/local/lslb/logs/*
rm test.out
/usr/local/lslb/bin/lslbd
sleep 5
start=$(date +%s)
for d in /usr/local/lslb/conf/coreruleset/tests/regression/tests/*/ ; do
       py.test -vs --tb=short ./CRS_Tests.py --config=lslb --ruledir=$d>>test.out
done
end=$(date +%s)
echo "Test time: $(($end-$start)) seconds"
pkill lslb
