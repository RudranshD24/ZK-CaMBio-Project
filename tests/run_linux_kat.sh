#!/bin/bash
set -e
apt-get update -qq
apt-get install -y -qq g++ python3-dev > /dev/null
pip install --no-cache-dir pybind11 numpy > /dev/null
INCLUDES=$(python3 -m pybind11 --includes)
SUFFIX=$(python3-config --extension-suffix)
g++ -O3 -Wall -shared -std=c++17 -fPIC -ffp-contract=off $INCLUDES cpp/chaos.cpp cpp/bindings.cpp -o /tmp/chaoshash$SUFFIX
PYTHONPATH=/tmp python3 tests/linux_kat_test.py
