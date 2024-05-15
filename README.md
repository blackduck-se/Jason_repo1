# SRM Custom Connector Framework Example
- [SRM Custom Connector Framework Example](#srm-custom-connector-framework-example)
- [Overview](#overview)
- [High Level Steps](#high-level-steps)
- [Pre-requisites](#pre-requisites)
- [SRM Custom Connector Example](#srm-custom-connector-example)
  - [Step 1 - Configure Environment Variables](#step-1---configure-environment-variables)
  - [Step 2 - Verify Settings](#step-2---verify-settings)
  - [Step 3 - Build Docker Image](#step-3---build-docker-image)
  - [Step 4 - Create Scan Request TOML File.](#step-4---create-scan-request-toml-file)
  - [Step 5 - Create the Add-In tool in SRM and Configure a Project](#step-5---create-the-add-in-tool-in-srm-and-configure-a-project)
  - [Step 6 - Run the Analysis](#step-6---run-the-analysis)
- [Using/Extending the Framework for Other Tools](#usingextending-the-framework-for-other-tools)
  - [Modifying Python Scripts for other Integrations](#modifying-python-scripts-for-other-integrations)
    - [Pulling Data From a 3rd Party Tool](#pulling-data-from-a-3rd-party-tool)
    - [Converting the data to SRM XML Format](#converting-the-data-to-srm-xml-format)
    - [Posting Results To SRM](#posting-results-to-srm)
    - [Modify the Wrapper Python Script](#modify-the-wrapper-python-script)
    - [Create a requirements.txt Python File](#create-a-requirementstxt-python-file)
  - [Updating the Docker Container](#updating-the-docker-container)
    - [Updating the Dockerfile](#updating-the-dockerfile)
    - [Updating the docker\_build.sh Script](#updating-the-docker_buildsh-script)
      - [Explanation Of the Docker Build Variables](#explanation-of-the-docker-build-variables)
      - [Explanation of the Docker Run Variables](#explanation-of-the-docker-run-variables)
      - [Testing/Running The Container](#testingrunning-the-container)
      - [Building the Container For SRM](#building-the-container-for-srm)
    - [Creating a Scan Request TOML File](#creating-a-scan-request-toml-file)
    - [Creating a Project Specific TOML Configuration File](#creating-a-project-specific-toml-configuration-file)
      - [Updating the configureToolService.py Script](#updating-the-configuretoolservicepy-script)
    - [Verifying the Add in tool and Project Configuration](#verifying-the-add-in-tool-and-project-configuration)

# Overview
While SRM boasts over 130+ integrations for pulling in results from third party tools into SRM, there will always be some cases where there is a missing integration.  This project is meant to lay out a framework that can be used to create a custom connector, going one step further than providing a script to parse results into SRM XML format.  This framework can be utilized to have SRM run an analysis to grab some 3rd party results, convert the results to SRM XML format and finally store those results within an SRM project. The analysis can then be scheduled to run and not require any custom steps in a CI/CD pipeline or manually done via the UI.

# High Level Steps
Successfully building and configuring a "custom connector" in SRM consists of the following steps:

1.  Creating a script or a set of scripts that accomplishes the following tasks:
    * Pulls data from a 3rd party tool
    * Converts the export from the 3rd party tool into SRM XML format.
2. Package the scripts into a docker container that can be run by SRM.
3. Create a new add-in tool in SRM, and configure it to use the docker container created in step 2.
4. Create a scan request TOML file used to configure the scan.
5. Configure an SRM project to utilize the custom add-in tool.
6. Run an analysis for the project using the add-in tool.

# Pre-requisites 
In order to utilize this framework, it takes advantage of the tool orchestration feature of SRM.  This means the approach can only be used with a Kubernetes deployment of SRM (i.e. this cannot be used with the binary installer or docker compose installations). The Tool Orchestration feature of SRM must also be enabled and licensed. A third party tool to pull results from should also be available.

The following pre-requisites should be met, prior to working through the example:

* This guide assumes that you already have SRM set up and configured with Tool Orchestration running in Kubernetes deployment details for SRM on k8s can be found [here](https://github.com/synopsys-sig/srm-k8s/blob/main/docs/DeploymentGuide.md).
* Since we need to build a docker container, you will need to ensure you have docker installed and are able to create docker images steps to install docker can be found [here](https://docs.docker.com/engine/install/ubuntu/).
* The docker image we create will need to be pushed to a container registry that SRM can pull from.
* This example uses python for scripting, ensure you have python 3 installed, you can follow the steps [here](https://www.python.org/downloads/)
* This example pulls fDAST results from polaris and brings them into SRM, therefore you will need access to Polaris with at least one project that has had fDAST analysis run. The scripts utilize a Polaris API Key to authenticate to Polaris, ensure you have a Polaris API Key you can use to interface with Polairs.
* This example also requires an SRM api key with Admin privileges, used to make configuration changes to SRM.  Follow the steps [here](https://sig-product-docs.synopsys.com/bundle/srm/page/user_guide/Settings/api_keys_administration.html) to create an SRM API Key if you don't already have one.


# SRM Custom Connector Example
In this example, we will be writing a custom connector to pull results from a Fast DAST Polaris run into SRM. 

The following scripts have been prepared for this example:

| Script Name    | Description |
| -------- | ------- |
| pull_dast_results.py  | Python script used to pull a json export from Polaris.  The Polaris project must have at least one DAST analysis.  |
| convert_dast_results.py | Python script used to convert the json export from the pull_dast_results.py script to SRM XML Format.     |
| srmPost.py    | Python script used to create a project into SRM and post SRM XML results to it.  While the final solution does not utilize this script it can be used to test prior to building the docker container.    |
| import_scan_results.py    | Wrapper python script used to combine the functionality of the previous three python scripts, used for simplicity.    |
| setenvs.sh | Bash script used to set environment variables.     |
| docker_build.sh | Bash script used to build the docker image that SRM will use to run the connector.     |
| docker_build.sh | Bash script used to build the docker image that SRM will use to run the connector.     |
| configureToolService.py | Python script used to configure SRM with the add-in tool, and configure a project in SRM to utilize the tool.     |

We will first exercise the scripts outside of SRM to ensure everything is working prior to building the docker container.

## Step 1 - Configure Environment Variables

The first step will be to set some environment variables that the other scripts will use as parameters, this helps simplify passing the data to the scripts.

Open the setenvs.sh script and set the following variables with your information:

``` 
# NOTE: Run the script using source, i.e. source ./set_env.sh to ensure variables are set in the parent shell
export POLARIS_PROJECT_NAME='<POLARIS PROJECT NAME TO IMPORT>'   # <-- Polaris Project name to pull DAST Results from 
export POLARIS_URL='<POLARIS URL>'                  # <-- Polaris URL to connect to and pull results from.
export POLARIS_API_KEY='<YOUR POLARIS API KEY>'     # <-- Polaris API Key
export SRM_URL='<SRM URL>'                          # <-- SRM URL 
export SRM_API_KEY='<YOUR SRM API KEY>'             # <-- SRM Admin API key
```

Once you've updated the script with your settings, source the script to set the variables for your shell:
``` 
source setenvs.sh
```

## Step 2 - Verify Settings
Next we will ensure we can pull data from Polaris and push it to SRM, we can do this by running the import_scan_results.py script.  If you set the environment variables in the previous step we do not need to pass in any parameters to this script.

Prior to running the scripts, first ensure you have installed the python requirements by running the following command:

``` 
pip install -r requirements.txt
```

Run the import_scan_results.py script:
``` 
python3 import_scan_results.py
```

You should see an output similar to the following:
``` 
Portfolio ID: 567848cb-9ea0-4243-b3b4-0a08fed80507
Portfolio Item ID: da623f7a-8463-4af1-be0c-57e38d295441
Portfolio DAST SubItem ID: 47e707bb-3b08-4fec-afac-7df34beeea93
Writing issue json file...
Successfully wrote sourceExport.json
Converting issues to SRM XML format...
File uploaded successfully.
```

You should now be able to login to SRM and view the findings for the project.

## Step 3 - Build Docker Image
Once we've verified our credentials and ability to post results to SRM just by running the scripts we are now ready to build the docker container.  A script is provided to help assist in building the container.

The docker container can be built in two different "modes":
1. Standalone, this creates a docker container that can be run from anywhere and pulls, converts, and pushes the results to SRM.  This is convenient for testing your docker image prior to loading it into SRM, but SRM cannot use it in this mode as a custom connector.
2. ToolOrchestration, this is how you will want to build the image for running it as a custom connector for SRM. 

We will first build the container in Standalone mode and ensure it is functional prior to building it for tool orchestration.

Open the docker_build.sh script and modify the variables for your settings:

```
# Docker Build Variables
IMAGE_NAME="srm-custom-connector-example"   #<-- Name of the image to build
IMAGE_TAG="v1.3"                            #<-- Image Tag
REG="myregistry:5000"                       #<-- Registry to push the image to after being built, SRM must be able to pull images from this registry.
CA_CERT=""                   #<-- If you need to add a CA cert to the image, put the filename to copy here
RUNTIME="standalone"                        #<-- To build as a standalone docker container (not running through tool Orchestration, set to True, if running inside of Tool Orchestration set to false.)

# Docker Run Variables
RUN_CONTAINER=true                         #<-- Set to true to run the container after building
ADD_HOST=""                                #<-- If you need to add any hostfile entries to access the source or SRM server, it should be in this format: --add-host <HOSTNAME>:<IP ADDRESS> e.g. ADD_HOST="--add-host demotest.srm.synopsys.com:192.156.13.47"
```

After updating the variables, in order to run the container edit the test_env_vars.env file to set the enviornment variables for the docker container.

**NOTE:** DO NOT put quotes around the variables.
```
POLARIS_URL=<POLARIS URL>
POLARIS_PROJECT_NAME=<POLARIS PROJECT NAME TO IMPORT>
POLARIS_API_KEY=<YOUR POLARIS API KEY>
SRM_URL=<SRM URL>
SRM_API_KEY=<YOUR SRM API KEY>
SRM_PROJECT_NAME=<OPTIONAL IF LEFT BLANK, THE POLARIS PROJECT NAME WILL BE USED AS THE SRM PROJECT NAME>
```

Ensure the RUN_CONTAINER variable is set to true and run the docker build script:

``` 
./docker_build.sh
...
+ docker run --add-host home-lab.srm.synopsys.com:192.168.1.40 --env-file test_env_vars.env -it srm-custom-connector-example:v1.3
Portfolio ID: 567848cb-9ea0-4243-b3b4-0a08fed80507
Portfolio Item ID: da623f7a-8463-4af1-be0c-57e38d295441
Portfolio DAST SubItem ID: 47e707bb-3b08-4fec-afac-7df34beeea93
Writing issue json file...
Successfully wrote sourceExport.json
Converting issues to SRM XML format...
File uploaded successfully.
```

Now that we have verified the docker container, re-run the docker_build.sh script but first update the RUNTIME variable to "toolOrchestration" this will rebuild the image to run within SRM.
```
./docker_build.sh
```

## Step 4 - Create Scan Request TOML File.
Once we've verified our docker container, the next step is to create the scan request TOML file.  This file tells SRM how to run the docker image we just built for Polaris.
Documentation for the scan request file can be found [here](https://sig-product-docs.synopsys.com/bundle/srm/page/user_guide/Analysis/scan_request_file.html)

The scan request file, for this example doesn't need to be modified much, only the second line should be modified to tell SRM where to pull the docker container from we build in the previous step.  Ensure the imageName variable has been set appropriately to where you pushed the image when running the docker_build.sh script.  The imageName variable should be updated by concatenating the REG, IMAGE_NAME, and IMAGE_TAG variables of the docker_build.sh script, i.e. $REG/$IMAGE_NAME:$IMAGE_TAG

Edit the scan_request_file.txt:
``` 
[request]
# Ensure this is updated to match the docker_build.sh script $REG/$IMAGE_NAME:$IMAGE_TAG
imageName = "localhost:5000/srm-custom-connector-example:v1.3"    

# Set to the working directory of the docker image, this should not need to be changed if using the provided dockerfile.
workDirectory = "/home/sig-user"

# The preShellCmd is used to run anything necessary to prior to creating the SRM XML file, in our example we use the preShellCmd to pull the DAST results from polaris by running the pull_dast_results.py script.
preShellCmd='''
    export POLARIS_API_KEY=$(cat workflow-secrets/polariskey/apikey)
    export POLARIS_URL=$(/usr/local/bin/tomlq -r '.polaris.url' config/request.toml)
    export POLARIS_PROJECT_NAME=$(/usr/local/bin/tomlq -r '.polaris.project' config/request.toml)
    # first pull the results
    export ExportFile="sourceExport.json"
    /home/sig-user/pull_dast_results.py --fileName ${ExportFile} --projectName ${POLARIS_PROJECT_NAME} --url ${POLARIS_URL}
'''

# The shellCmd is used to execute the command that will create the SRM XML file, in our example we run the convert_dast_results.py script to create the SRM XML file.
shellCmd = '''
source=$(ls /home/sig-user)
  # Second, convert the data to SRM XML Format
  export ImportFile="sourceSRMXML.xml"
  /home/sig-user/convert_dast_results.py --inputFileName ${ExportFile} --outputFileName ${ImportFile}
'''
resultFilePath = "/home/sig-user/sourceSRMXML.xml"    # <-- This tells SRM where the SRM XML file will be once the shellCmd is finished.
securityActivities = ['dast']                         # <-- This tells SRM which type of tool or findings these are e.g. sca, sast, dast, etc.
```

## Step 5 - Create the Add-In tool in SRM and Configure a Project
Now that the docker container is build, and the scan request file is completed, we are now ready to add the tool to SRM.  While this can be done via the SRM UI, we also provide the configureToolService.py script to configure the tool AND create a project and create project specific settings.

The configureToolService.py script performs the following functions:
1. Creates the Add-in Tool in SRM, and configures it using the scan request file.
2. Creates a new project or configures an existing project in SRM to enable the add-in and applies the project specific settings to the configuration (using the POLARIS_PROJECT_NAME variable).
3. Adds a secret to the project (polaris api key) and associates the secret with the tool.

If you have the enviornment variables set from step 1, you do not need to pass in any parameters into the script (unless you want to override the current variables). 

Run the configureToolService.py script:

``` 
./configureToolService.py 
Successfully retrieved list of tool ids
Creating add in tool...
Successfully created add in tool
Checking if SH-Demo exists...
SH-Demo found...
Successfully created project secret
Successfully configured tool config for project: 7
```

In the above example, the script created the add-in tool with our docker container and configured it using the scan request file, found an existing project SH-Demo in SRM (that matched the same polaris project name) configured the project to use the tool, and added the project specific scan settings for the tool (polaris URL, polaris api key, and polaris project name)

This can be verified by going to the SRM UI, and selecting the "Configure Tool Service" option of the SH-Demo project in SRM.

## Step 6 - Run the Analysis
Now that we have everything configured and a project created the last step is to run an analysis using our tool.

In the SRM UI select "New Analysis" on the project you associated the tool with.  You should see "Polaris Dast" already checked.  Select Begin Analysis.

After the analysis runs you should see all the findings in the project.

# Using/Extending the Framework for Other Tools

The above example showed how to register a pre-built integration into SRM, the real benefit though is extending this framework to cover other 3rd party tools.

In order to do that, while a lot of the existing stuff here can be re-used the following things will need to be modified:
## Modifying Python Scripts for other Integrations
In this example there are 4 python scripts used to pull data, convert the data, and send the data to SRM:

| Script Name    | Description |
| -------- | ------- |
| pull_dast_results.py  | Python script used to pull a json export from Polaris.  The Polaris project must have at least one DAST analysis.  |
| convert_dast_results.py | Python script used to convert the json export from the pull_dast_results.py script to SRM XML Format.     |
| srmPost.py    | Python script used to create a project into SRM and post SRM XML results to it.  While the final solution does not utilize this script it can be used to test prior to building the docker container.    |
| import_scan_results.py    | Wrapper python script used to combine the functionality of the previous three python scripts, used for simplicity.    |


Looking at the scripts above the process is split into 3 steps:
1. A script to pull findings from a 3rd party tool and storing the results in the tools native format.
2. A script used to take the output of the first script and convert the findings to SRM XML Format
3. A script used to take the SRM formatted results and upload them to an existing project or create a new project and upload the results to that project.

Steps 1 and 2 can be combined into a single script if desired and need not be separated.

### Pulling Data From a 3rd Party Tool
In the provided example the pull_dast_results.py script is used to export fDAST findings from a polaris project and store the resulting json file locally. For other integrations, this script will either need to be heavily modified or a new script written that provides the same functionality for the 3rd party tool in use.

The requirements are fairly straight forward:
1. Connect to the 3rd party tool (including any authentication required).
2. Query the tool to retrieve a list of findings is a file format.
3. Write the file (in whatever format it comes in) on the filesystem.

When creating the script used to pull data, you must consider the following:
1. Credentials or API keys used to authenticate to a 3rd party tool - Any credentials used will need to be created as project secrets in SRM
2. Consider using environment variables are parameters - Using Environment Variables for the parameters will make testing the docker container easier and prevents the need to hardcode credentials and/or API keys.
3. The result of the script should be a file that can be converted into SRM XML format and used as an input into the next step.
4. Try to avoid using protocols other than HTTP, since this must ultimately run in a K8s environment, using protocols other than HTTP requests can make implementation in K8s difficult (i.e. try not to use scp, direct database interactions, etc.) If that is your only option than some modifications to the K8s environment may be required.

### Converting the data to SRM XML Format
The next step is to convert the results from the 3rd party tool into SRM XML format. In the given example the convert_dast_results.py script implements this functionality and can be used as an example to go off of. It is expected that this script will need to be heavily modified/re-written for each integration and consists of the bulk of the work.

The SRM XML schema can be found in the srm-xml directory of this project: [here](srm-xml/).

The requirements for this script are the following:
1. Input the 3rd party tool export format.
2. Convert the findings to SRM XML format.
3. Output an SRM XML formatted xml document.

### Posting Results To SRM
The srmPost.py script does not contain any integration specific details and is just used to create a project in SRM (if it doesn't already exist) and post the SRM XML formatted results to the project.  This script does not typically need to be modified for new integrations.

### Modify the Wrapper Python Script
Since we split the functionality into 3 steps for testing in the docker container it's easiest to call a single script, so having a wrapper to tie the three steps together is ideal.  In this example the import_scan_results.py script is used to call the 3 scripts sequentially. Updates to this script should be very minimal.

The requirements for this script:
1. Import the scripts used for steps 1-3
2. Accept any/all parameters needed for the three scripts **NOTE** Consider using environment variables for default values as this makes testing the docker container very easy.

### Create a requirements.txt Python File
Once all the python scripts are completed, since we need to package these in a container, we need to make sure the correct python dependencies get installed.  The easiest way to do that is to generate a requirements.txt file and then install those same dependencies when building the docker container. A requirements.txt file already exists for this example, but should be updated when any new import statements are added to the modified python scripts. To generate an updated requirements.txt file run the following command:

``` 
pip install pipreqs
pipreqs /path/to/project --force
```

The first command installs pipreqs, a dependency to generate the requirements.txt file, while the second command generates the file:

``` 
pip install pipreqs
pipreqs .
```

## Updating the Docker Container
Since this ultimately needs to run in a container so SRM can run the analysis, after you've tested/verified the python scripts, the next step is to build the docker container.
There are two parts to modifying the container:
1. Updating the Dockerfile
2. Updating the docker_build.sh script

### Updating the Dockerfile
The docker file will almost always need to be updated to support other integrations if you examine the example docker file there are comments where things should be updated:

``` 
# This example uses the official python image on debian linux.
FROM python:3.9.19-bullseye as base
ARG CA_CERT=""
ARG RUNTIME="sh"
USER root

# Update and install packages here, ADD any packages here that are required for your integration.
RUN apt-get update \
    && apt-get install -y jq \
    && rm -rf /var/lib/apt/lists/*

# Add a user, so our container doesn't run as root:
RUN useradd -ms /bin/bash sig-user

# Copy the requirements.txt file and any cert files needed:
COPY requirements.txt $CA_CERT* /tmp/

# If a custom certificate needs to be added to the container we update the trust store with it here:
RUN if [ -z "$CA_CERT" ] ; then echo No cert provided ; else ls -l /tmp && cp /tmp/$CA_CERT /usr/local/share/ca-certificates && update-ca-certificates; fi

# Install the python requirements from the requirements.txt file here:
RUN pip install --requirement /tmp/requirements.txt && python -m nltk.downloader -d /usr/local/share/nltk_data brown

# Set any environment variables here, for example by default we set the home directory to the user we create, tell python to use the container trust store for CA certs
ENV HOME="/home/sig-user"
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV START_CMD=${RUNTIME}

# Switch to the new user and set the working directory:
USER sig-user
WORKDIR /home/sig-user

# Copy over any scripts needed to run the integration and set the proper permissions and ownership, Update this section with any new scripts:
COPY --chown=sig-user:sig-user srmPost.py "/home/sig-user"
COPY --chown=sig-user:sig-user pull_dast_results.py "/home/sig-user"
COPY --chown=sig-user:sig-user convert_dast_results.py "/home/sig-user"
COPY --chown=sig-user:sig-user import_scan_results.py "/home/sig-user"

# We pass in the entrypoint start command from the docker_build.sh script allowing us to easily switch between standalone mode and tool Orchestration mode.
CMD ${START_CMD};
```

### Updating the docker_build.sh Script
The docker_build.sh script is used to build the container that will run the integration and push that container to a registry. This script should require fairly minimal modifications for other integrations, mainly setting the variables appropriately:

#### Explanation Of the Docker Build Variables
1. SRM will need to be able to pull the image from a registry, the script will automatically push the image to a registry if the REG variable is populated with a valid registry to push the image to.
2. The IMAGE_NAME should be set to a name that uniquely identifies the integration
3. IMAGE_TAG is just the tag for the image, this is typically used to version the image
4. CA_CERT if you need to add a CA certificate for connecting to the 3rd party instance or your SRM instance set this to the file name of the certificate (ensure it is in pem format) and ensure the cert file is in the same directory as the Dockerfile.
5. RUNTIME there are two ways to build the container, for running with Tool Orchestration or Standalone (i.e. a standalone container that does not need to be run within SRM).  It is recommended to first build the container in standalone mode and run it to test to ensure it executes successfully as debugging within Tool Orchestration can be a bit cumbersome. **NOTE:** The docker container must be built in toolOrchestration mode prior to loading it into SRM.

#### Explanation of the Docker Run Variables
The Docker run variables only apply when the RUNTIME variable is set to standalone, and used to help test the container prior to loading it into SRM.
1. RUN_CONTAINER when set to true the container will be run after being built (this is the easiest way to test the container after building it)
2. ADD_HOST when running the docker container in standalone mode, you may need to add entries to the host file if DNS is not in place for the third party tool or your SRM instance.  Populate this variable with any host file entries needed.

```
# Docker Build Variables
IMAGE_NAME="srm-custom-connector-example"  #<-- Name of the image to build, update this to a unique name for the integration
IMAGE_TAG="v1.3"                           #<-- Image Tag
REG="myregistry:5000"                      #<-- Registry to push the image to after being built, SRM must be able to pull images from this registry.
CA_CERT=""                                 #<-- If you need to add a CA cert to the image, put the filename to copy here, if this is not needed set this to ""
RUNTIME="standalone"                #<-- To build as a standalone docker container (i.e not running through tool Orchestration, set to "standalone", to build the container for running through tool orchestration set to "toolOrchestration".)

# Docker Run Variables
RUN_CONTAINER=true                         #<-- Set to true to run the container after building
ADD_HOST=""                                #<-- If you need to add any host file entries to access the source or SRM server, it should be in this format: --add-host <HOSTNAME>:<IP ADDRESS> e.g. --add-host demotest.srm.synopsys.com:172.156.13.47
```
#### Testing/Running The Container
After making the needed updates to the Dockerfile and to the docker_build.sh script you should test your container prior to building it in toolOrchestration runtime mode, this will allow you to troubleshoot and debug issues faster than when it is running through SRM.

To test the container:
1. Edit the test_env_vars.env file to update/add any tool specific variables. **NOTE:** DO NOT put quotes around the variables in this file.
2. Run the docker_build.sh script with RUNTIME=standalone and RUN_CONTAINER=true

Your container should run and execute your scripts, if there are any issues, fix them and repeat the steps to ensure the container works as expected.

#### Building the Container For SRM
Once you are happy with the container, it should be rebuilt with:
``` 
RUNTIME="toolOrchestration"
RUN_CONTAINER=false
```

This will rebuild the container with the appropriate settings for being executed by the Tool Orchestration framework within SRM.

### Creating a Scan Request TOML File
The SRM Tool Orchestration framework uses a scan request TOML file for configuration.  Official documentation on the Scan Request file format can be found [here](https://sig-product-docs.synopsys.com/bundle/srm/page/user_guide/Analysis/scan_request_file.html).  The Scan Request File defines the behavior for the custom add in tool.

Let's look at the Scan Request File for this example and make any changes/updates needed:

```
# The request heading is required for the file it tells SRM that this is a configuration for a build in tool, do not edit this line.
[request]
# The imageName tells SRM where to pull the container from, this should be set according to the image name and tag, and registry you pushed the image to in the build_docket.sh script in the following format: "${REG}/${IMAGE_NAME}:${IMAGE_TAG}"
imageName = "myregistry:5000/srm-custom-connector-example:v1.3"

# The workDirectory variable should be set to the WORKDIR directory of the container, typically this value does not need to change if you didn't edit that line in the docker file.
workDirectory = "/home/sig-user"

# The preShellCmd is the set of commands that should be run prior to converting the results to SRM XML format, so for example, pulling the data from the 3rd party tool.  In this example we also parse the TOML file to populate some environment variables that we use as parameters to the script used to pull the data from Polaris. It is important to note that in this section we are calling the pull_dast_results.py script directly (we are not using the wrapper because we don't need to use the srmPost.py script as SRM will import the results into the project for us.)
preShellCmd='''
    export POLARIS_API_KEY=$(cat workflow-secrets/polariskey/apikey)
    export POLARIS_URL=$(/usr/local/bin/tomlq -r '.polaris.url' config/request.toml)
    export POLARIS_PROJECT_NAME=$(/usr/local/bin/tomlq -r '.polaris.project' config/request.toml)
    # first pull the results
    export ExportFile="sourceExport.json"
    /home/sig-user/pull_dast_results.py --fileName ${ExportFile} --projectName ${POLARIS_PROJECT_NAME} --url ${POLARIS_URL} --apiKey ${POLARIS_API_KEY}
'''

# The shell command tells the tool Orchestration framework what to do to convert the results to SRM format, in our example that is calling the conver_dast_results.py script, again we use the environment variables we parsed from the TOML file in the preShellCmd above as parameters here.
shellCmd = '''
source=$(ls /home/sig-user)
  # Second, convert the data to SRM XML Format
  export ImportFile="sourceSRMXML.xml"
  /home/sig-user/convert_dast_results.py --inputFileName ${ExportFile} --outputFileName ${ImportFile} --polarisAPIKey ${POLARIS_API_KEY}
'''

# The resultFilePath tells the Tool Orchestration framework where to find the SRM XML formatted file, which is the result of the shellCmd operation.
resultFilePath = "/home/sig-user/sourceSRMXML.xml"

# The securityActivities variable tells the Tool Orchestration framework what security activities supported by this tool (e.g., sca, sast, dast) in our example we are dealing with a DAST tool, this should be updated to the 3rd party tool type.
securityActivities = ['dast']
```

**Note:** This example doesn't use all of the parameters in the Scan Request file, refer to the official documentation [here](https://sig-product-docs.synopsys.com/bundle/srm/page/user_guide/Analysis/scan_request_file.html) to familiarize yourself with all of the options that can be included in a Scan Request File.

### Creating a Project Specific TOML Configuration File

The Scan Request TOML File above applies general tool specific configurations to SRM for running the add in tool. However, there will almost alway be project specific settings for each project that will utilize the tool. For example, in our Polaris DAST implementation the Polaris URL and the Project Name will be different for each fDAST project we want to import into SRM, therefore, we cannot put that information into the Scan Request file as that is global for the tool.

Project specific configurations can also be defined, in our example, the following TOML format is used to define project specific settings:

```
[polaris]
project="SH-Demo"
url="https://poc.polaris.synopsys.com"
```
As described above these settings define the project name and the polaris URL for the project we want to import into SRM.

The project specific TOML file will be combined with the Scan Request TOML file when Tool Orchestration kicks off the analysis. If you recall from the previous section, the preShellcmd looks like this:

``` 
preShellCmd='''
    export POLARIS_API_KEY=$(cat workflow-secrets/polariskey/apikey)
    export POLARIS_URL=$(/usr/local/bin/tomlq -r '.polaris.url' config/request.toml)
    export POLARIS_PROJECT_NAME=$(/usr/local/bin/tomlq -r '.polaris.project' config/request.toml)
    # first pull the results
    export ExportFile="sourceExport.json"
    /home/sig-user/pull_dast_results.py --fileName ${ExportFile} --projectName ${POLARIS_PROJECT_NAME} --url ${POLARIS_URL} --apiKey ${POLARIS_API_KEY}
'''
```
The POLARIS_URL and POLARIS_PROJECT_NAME are being parsed from the request.toml file (the scan request file) but isn't defined in the scan request file, that is because when we add the project specific settings they will be combined with the scan request file.

We create the project specific portion of the TOML file when we configure the tool within the SRM project, while this can be done via the UI, a python script configureToolService.py is supplied to do this for you.

The configureToolService.py performs the following:
1. Register the built in tool with SRM (if it doesn't already exist)
2. Create a project in SRM or (if the project already exists) configures the tool for the project including defining the project specific TOML file
3. Creates any project secrets needed for the tool to run (i.e. any credentials in our case this is the Polaris API Key).

Again the UI can be used to perform all of the above steps, however if you plan on adding/modifying several projects to use the build in tool, using the API is a much more efficient way to adding in all of the needed configurations.

#### Updating the configureToolService.py Script
The configureToolService.py script will most likely need to be modified for a different 3rd party tool than the provided example here.

The first thing to modify is the parameters the tool accepts:
``` 
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--polarisURL', default=os.environ.get('POLARIS_URL'), help='Path to the .xml file')
    parser.add_argument('--polarisProjectName', default=os.environ.get('POLARIS_PROJECT_NAME'), help='Polaris project name to to pull DAST results from')
    parser.add_argument('--polarisApiKey', default=os.environ.get('POLARIS_API_KEY'), help='Polaris API Key')    
    parser.add_argument('--srmProjectName', default=None, help='SRM project name to create or add configuration to, if left blank the Polaris Project name will be used')
    parser.add_argument('--srmURL', default=os.environ.get('SRM_URL'), help='URL for SRM')
    parser.add_argument('--apiKey', default=os.environ.get('SRM_API_KEY'), help='SRM API key for authentication')
    parser.add_argument('--addInToolName', default="Polaris DAST", help='Name of the add in tool to create, or assign to the project if it already exists')
    args = parser.parse_args()
```

Add/Remove/Update any existing parameters the --srmURL, --apiKey, --srmProjectName, and --addinToolName parameters should always exist as the script needs to know what the toolName to add is, the srm URL (to post updates to) the project to create or modify, and the SRM apiKey to authenticate to SRM to make changes (the SRM api key should have admin permissions.)

The rest of the parameters can be removed/updated, or new ones added to meet the requirements for the 3rd party tool.

There is only one method in the script that needs to be updated for other 3rd party tools:
- configure_tool_service

The other methods are generic and perform the functionality required to register the tool (using the scan request file previously created.), add the project (if needed).  The only specifics that need to be modified are the project specific configuration for the tool which include:
- secrets (i.e. credentials)
- project specific TOML configuration file.

Let's take a look at the configure_tool_service method:
``` 
    # Add project secret
    # Add any project secrets needed for the integration, the credential value is the 3rd parameter, the secretName and secretKey values result in the directory and file name that has the credential that gets mounted to the container.
    # From the scan request file above: export POLARIS_API_KEY=$(cat workflow-secrets/polariskey/apikey) this populates the POLARIS_API_KEY variable from the contents of the file in the workflow-secrets/polariskey/apikey where polariskey is the secretName and apikey being the secret key.
    # You can call this method as many times as you need to add any number of secrets required for the integration.
    secretName="polariskey"
    secretKey="apikey"
    secretId = add_project_secret(srmURL, headers, polarisApiKey, projectId, secretName, secretKey)

    # Add tool configuration
    # Here we dynamically create the project specific TOML config file, here we add the [polaris] heading followed by the two properties polaris project name and polaris url.
    tomlConfig=f"[polaris]\nproject=\"{polarisProjectName}\"\nurl=\"{polarisURL}\""
    
    # Update the allowedSecrets with the secretIds result from the add_project_secret method, you can update the list with as many as you created above.
    jsonBody = {
        "newContent": tomlConfig,
        "allowedSecrets": [ secretId ],
        "isEnabled": True
    }

    # Finally we post the project configuration to the project in SRM, the remaining lines of this method should not need to be updated.
    response = requests.post(f"{srmURL}srm/x/toolservice/addin-tools/{projectId}/{toolId}", json=jsonBody, headers=headers)
    if response.status_code != 200:
        print("ERROR: Failed to configure tool configuration for project: "+str(projectId)+", HTTP Response: " + str(response.status_code))
        print("ERROR: Error Message: " + response.text)
    else:
        print("Successfully configured tool config for project: "+str(projectId))
```
The other methods used are generic and should work for all other integrations.

You can now run the configureToolService.py script to add in the tool to SRM and update/create a project to use the tool.

This script can then be run as many times as needed to add the project configuration to SRM, the tool will only be created one time.

### Verifying the Add in tool and Project Configuration
After running the configureToolService.py script we can now log into the SRM UI and verify our updates.
1. Login to SRM as an Admin user
2. Go to Settings-> Add-In Tools - You should see the tool in the list
3. Select edit on the tool you added to see the scan request file and other configurations verify they are correct
4. Go to the project list in SRM
5. Select Configure Tool Service for the project
6. Select the tool from the list that was added
7. Verify the secrets and project specific TOML configuration.

Now you can run an analysis:
1. Return to the project list
2. Select "New Analysis" on the project you added tool configuration to
3. Under "Runnable Dynamic Tools" you should see the Add-in Tool you added already selected
4. Select Begin Analysis

SRM will then run a job utilizing the Tool Orchestration framework to import the findings from the third party tool.


