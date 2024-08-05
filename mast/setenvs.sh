#!/bin/bash

# NOTE: Run the script using source, i.e. source ./setenvs.sh to ensure variables are set in the parent shell

export SRM_URL=""                  # <-- SRM URL, Full SRM URL here, e.g. https://testing.srm.synopsys.com/
export SRM_API_KEY=""              # <-- SRM Admin API key
export SRM_PROJECT_NAME=""         # <-- The SRM project name to upload results to, if not provided as an environment variable this will need to be set when invoking the script.
export SRM_PROJECT_BRANCH_NAME=""  # <-- Optional, The SRM project branch to run the analysis on, default branch is used if not provided.