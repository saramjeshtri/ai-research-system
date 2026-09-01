#!/bin/bash
for Q in \
 "What EU grant calls are currently open for small AI startups?" \
 "What are the main EU AI regulations startups must comply with in 2026?" \
 "Which accelerator or incubator programs in Europe fund early-stage AI companies?" ; do
  echo ""
  echo "###################################################################"
  python3 run_flow.py "$Q"
  echo ""
done
