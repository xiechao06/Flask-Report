#!/bin/bash

rm example/temp.db
cd example
python make_test_data.py
cd ..
