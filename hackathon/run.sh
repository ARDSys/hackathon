#!/bin/bash

PYTHONPATH="./:$PYTHONPATH" uv run biohack_attack/generate_hypothesis.py ../evaluation/Autoimmunity.json \
  --output custom_output_dir \
  --num-hypotheses 3 \
  --num-threads 8 \
  --top-k 2 \
  --max-iterations 1

PYTHONPATH="./:$PYTHONPATH" uv run biohack_attack/generate_hypothesis.py ../evaluation/BTK_Inhibitors.json \
  --output custom_output_dir \
  --num-hypotheses 3 \
  --num-threads 8 \
  --top-k 2 \
  --max-iterations 1

PYTHONPATH="./:$PYTHONPATH" uv run biohack_attack/generate_hypothesis.py ../evaluation/Novel_Therapeutic_Approaches.json \
  --output custom_output_dir \
  --num-hypotheses 3 \
  --num-threads 8 \
  --top-k 2 \
  --max-iterations 1
