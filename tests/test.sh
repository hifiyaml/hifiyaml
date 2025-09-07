#!/bin/bash

rm -rf tmp
mkdir -p tmp
operate.py demo.yaml dump "cost function/observations/observers/0/obs filters/0" > tmp/0.yaml
operate.py demo.yaml dump "cost function/observations/observers/0/obs filters/1" > tmp/1.yaml
operate.py demo.yaml dump "cost function/observations/observers/0/obs filters/2" > tmp/2_0.yaml
operate.py demo.yaml dump "cost function/observations/observers/0/obs filters/2" nodedent > tmp/2_1.yaml
operate.py demo.yaml dump "cost function/observations/observers/0/obs filters/3" > tmp/3.yaml
operate.py demo.yaml dump "cost function/observations/observers/0/obs filters/4" > tmp/4.yaml
operate.py demo.yaml dump "cost function/observations/observers/0/obs filters/5" > tmp/5.yaml
operate.py demo.yaml dump "cost function/observations/observers/0/obs filters/6" > tmp/6.yaml

diff tmp ref
if (( $? == 0 )); then
  echo "test passed, identical results."
else
  echo "test failed, different results!"
fi
