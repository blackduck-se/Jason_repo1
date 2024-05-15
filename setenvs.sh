#!/bin/bash

# NOTE: Run the script using source, i.e. source ./set_env.sh to ensure variables are set in the parent shell
export POLARIS_PROJECT_NAME='<POLARIS PROJECT NAME TO IMPORT>'   # <-- Polaris Project name to pull DAST Results from 
export POLARIS_URL='<POLARIS URL>'                  # <-- Polaris URL to connect to and pull results from.
export POLARIS_API_KEY='<YOUR POLARIS API KEY>'     # <-- Polaris API Key
export SRM_URL='<SRM URL>'                          # <-- SRM URL 
export SRM_API_KEY='<YOUR SRM API KEY>'             # <-- SRM Admin API key