# SRM MAST Findings Import
- [SRM MAST Findings Import](#srm-mast-findings-import)
- [Overview](#overview)
- [Pre-requisites](#pre-requisites)
- [Project Composition](#project-composition)
- [Importing MAST Results into SRM](#importing-mast-results-into-srm)
  - [Step 1 - Configure Parameters](#step-1---configure-parameters)
  - [Step 2 - Set up Python Requirements](#step-2---set-up-python-requirements)
  - [Step 3 - Run the Import Script](#step-3---run-the-import-script)
  - [(Optional) Step 3 - Build Docker Image](#optional-step-3---build-docker-image)

# Overview
This project is used to assist in importing Mobile Application Security Testing ([MAST](https://www.synopsys.com/software-integrity/application-security-testing-services/mobile-application-security-testing.html)) results into Software Risk Manager ([SRM](https://www.synopsys.com/software-integrity/software-risk-manager.html)). The python scripts can be used as a standalone script, or packaged into a docker container.

**NOTE:** MAST results are published in CSV, Word/PDF, and json format. This project only works on json formatted results.

Since the MAST results are not published in a way where they can be pulled from a source there is no option to utilize the Tool Orchestration feature in SRM to create a custom connector to fully automate importing MAST results. 

This project is provided to assist users when importing results from MAST services into Software Risk Manager (SRM) it does not represent any extension of licensed functionality of Synopsys SIG software itself and is provided as-is, without warranty or liability of any kind.

**NOTE:** Only a limited set of test data has been used to develop the parser, errors or missing fields may result from some input files.  As more details are known the parser will be updated accordingly.

# Pre-requisites
The following pre-requisites should be met:

* This guide assumes that you already have SRM set up and configured, details for SRM on k8s can be found [here](https://github.com/synopsys-sig/srm-k8s/blob/main/docs/DeploymentGuide.md).
* Optionally, if you would like to build and use the docker container, you will need to ensure you have docker installed and are able to create docker images steps to install docker can be found [here](https://docs.docker.com/engine/install/).
* This project uses python for scripting, ensure you have python 3 installed, you can follow the steps [here](https://www.python.org/downloads/)
* This project also requires an SRM api key with at minimum the create role on the project that you wish to import results to. Follow the steps [here](https://sig-product-docs.synopsys.com/bundle/srm/page/user_guide/Settings/api_keys_administration.html) to create an SRM API Key if you don't already have one.
* At least one set of MAST findings in json format.

# Project Composition
The table below describes the different scripts and artifacts used to import the MAST findings into SRM: 

| Script Name    | Description |
| -------- | ------- |
| convert_mast_results.py | Python script used to convert the json formatted MAST findings into SRM XML format.     |
| srmPost.py    | Python script used to create a project and optionally a branch in SRM and upload the SRM formatted XML to the project/branch.  If the project/branch already exists, the existing project/branch will be used. If no branch is provided the default branch will be used. |
| import_mast_results.py    | Wrapper python script used to combine the functionality of the other python scripts, used to simplify the process to calling a single script.    |
| setenvs.sh | Bash script used to set environment variables for inputs into the script. This is optional as all parameters can be passed into the script via the CLI.     |
| docker/docker_build.sh | Bash script used to build the docker image used to facilitate importing the results.     |
| docker/Dockerfile | Dockerfile used to build the container.     |
| docker/env_vars.env | Docker environment variable file used to populate the environment variables for running the import in the docker container.     |
| docker/requirements.txt | Python requirements.txt file used to install required python packages for running the scripts.     |

# Importing MAST Results into SRM

Clone the srm-custom-connectors project and cd to the mast directory:

```
git clone https://github.com/srm-se/srm-custom-connectors.git
cd srm-custom-connectors/mast
```

## Step 1 - Configure Parameters
The first step will be to set some environment variables that the other scripts will use as parameters, this helps simplify passing the data to the scripts.

Edit the setenvs.sh script and set the following variables with your information:

``` 
#!/bin/bash

# NOTE: Run the script using source, i.e. source ./setenvs.sh to ensure variables are set in the parent shell
export SRM_URL=""                  # <-- SRM URL, Full SRM URL here, e.g. https://testing.srm.synopsys.com/
export SRM_API_KEY=""              # <-- SRM Admin API key
export SRM_PROJECT_NAME=""         # <-- The SRM project name to upload results to, if not provided as an environment variable this will need to be set when invoking the script.
export SRM_PROJECT_BRANCH_NAME=""  # <-- Optional, The SRM project branch to run the analysis on, default branch is used if not provided.
```

Once you've updated the script with your settings, source the script to set the variables for your shell:
``` 
source ./setenvs.sh
```

## Step 2 - Set up Python Requirements
Next we will ensure we have the correct python libraries installed to run the scripts. This can be done by running the following command:

``` 
pip install -r docker/requirements.txt
```

## Step 3 - Run the Import Script
**NOTE:** This script imports functionality from the srmPost.py script located in the parent directory, if you move this file ensure you also put the srmPost.py script from the parent directory to the same location, or adjust the sys.path.append('../') import to include the directory where the srmPost.py script is located.

We are now ready to run the script to import the results into SRM.  If you have set the environment variables in step 1, all you need to do is pass the path to the MAST json results file:

Run the import_mast_results.py script:
``` 
python3 import_mast_results.py path/to/mast-findings.json
```

You should see an output similar to the following:
``` 
Converting data.json to SRM XML format...
Converting issues to SRM XML format...
Uploading results to https://testing.srm.synopsys.com/ project demo...
demo created successfully.
File uploaded successfully.
```

You should now be able to login to SRM and view the findings for the project.

Full help of the import_mast_results.py can be seen below:

```
usage: import_mast_results.py [-h] [--srmProjectName SRMPROJECTNAME] [--srmURL SRMURL] [--srmAPIKey SRMAPIKEY] [--projectBranchName PROJECTBRANCHNAME] sourcePath

positional arguments:
  sourcePath            Location of the MAST json results file to be imported into SRM.

optional arguments:
  -h, --help            show this help message and exit
  --srmProjectName SRMPROJECTNAME
                        Name of the project in SRM to import the results to, if the project does not exist it will be created. If not provided, the value of the   
                        SRM_PROJECT_NAME environment variable is used.
  --srmURL SRMURL       SRM URL to import the results to. If not provided, the value of the SRM_URL environment variable is used.
  --srmAPIKey SRMAPIKEY
                        The SRM API Key used to authenticate to SRM. If not provided, the value of the SRM_API_KEY environment variable is used.
  --projectBranchName PROJECTBRANCHNAME
                        Optional, SRM project branch name to run the analysis on, if the branch does not currently exist, if will be created with the default      
                        branch as the parent. If not provided, the value of the SRM_PROJECT_BRANCH_NAME environment variable is used if that is not set the        
                        default project branch will be used.
```

## (Optional) Step 3 - Build Docker Image
In some cases it may be desirable to have a docker container capable of just taking the input file and the script parameters to send the results to SRM (for example if your environment can not meet the pre-requisites above).

Once we've verified our credentials and ability to post results to SRM just by running the scripts we are now ready to build the docker container.  A script is provided to help assist in building the container.

Open the docker_build.sh script in the docker directory and modify the variables for your settings:

```
# Docker Build Variables
IMAGE_NAME="srm-custom-connector-mast"  #<-- Name of the image to build
IMAGE_TAG="1.0"                         #<-- Image Tag
REG="myregistry:5000"                   #<-- Registry to push the image to after being built, SRM must be able to pull images from this registry.
BUILD_CONTAINER=true                    #<-- Set to true to build the container, set to false if the container has already been built and you just want to run it with different inputs
CA_CERT="cert-mgr-ca.crt"               #<-- If you need to add a CA cert to the image, put the filename to copy here, if this is not needed set this to ""

# Docker Run Variables
RUN_CONTAINER=true                  #<-- Set to true to run the container after building
MOUNT_PATH="/tmp/mast"              #<-- Path to the directory containing the MAST results to import
IMPORT_FILE="data.json"             #<-- filename to import, must be in the MOUNT_PATH directory
ENV_VAR_FILE="env_vars.env"         #<-- Name of the environment variable file used to populate the values for srm url, project name, api key, and optionally branch name.
ADD_HOST=""                         #<-- If you need to add any hostfile entries to access the source or SRM server, it should be in this format: --add-host <HOSTNAME>:<IP ADDRESS> e.g. --add-host demotest.srm.synopsys.com:192.156.13.47
RUNTIME_CMD="/home/sig-user/import_mast_results.py /data/${IMPORT_FILE}"  #<-- Command for the container to run at startup, this typically does not need to be changed.

```

After updating the variables, in order to run the container edit the env_vars.env file to set the enviornment variables for the docker container.

**NOTE:** DO NOT put quotes around the variables or any comments or the variables won't be read properly.
```
SRM_URL=<Full SRM URL here, e.g. https://testing.srm.synopsys.com/>
SRM_API_KEY=<SRM API Key>
SRM_PROJECT_NAME=<SRM Project Name>
SRM_PROJECT_BRANCH_NAME=<Optionally, SRM Project Branch name, leave blank or omit if not providing a branch name>
```

Ensure the RUN_CONTAINER variable is set to true and run the docker build script:

``` 
./docker_build.sh
...
+ docker run --add-host home-lab.srm.synopsys.com:192.168.1.40 --env-file env_vars.env -it srm-custom-connector-example:v1.3
```

You should see an output similar to the following:

```
Converting /data/data.json to SRM XML format...
Converting issues to SRM XML format...
Uploading results to https://home-lab.srm.synopsys.com/ project mast-example15...
File uploaded successfully.
```
