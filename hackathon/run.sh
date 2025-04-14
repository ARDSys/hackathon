#!/bin/bash

PYTHONPATH="./:$PYTHONPATH" uv run biohack_attack/generate_hypothesis.py ../data/Bridge_Therapy.json \
  --output custom_output_dir \
  --num-hypotheses 1 \
  --num-threads 8 \
  --top-k 2 \
  --max-iterations 1
