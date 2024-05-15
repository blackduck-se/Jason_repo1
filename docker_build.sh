#!/bin/sh
set -x
set -e

# Docker Build Variables
IMAGE_NAME="srm-custom-connector-example"  #<-- Name of the image to build
IMAGE_TAG="v1.3"                           #<-- Image Tag
REG="myregistry:5000"                      #<-- Registry to push the image to after being built, SRM must be able to pull images from this registry.
CA_CERT=""                                 #<-- If you need to add a CA cert to the image, put the filename to copy here, if this is not needed set this to ""
RUNTIME="toolOrchestration"                #<-- To build as a standalone docker container (i.e not running through tool Orchestration, set to "standalone", to build the container for running through tool orchestration set to "toolOrchestration".)

# Docker Run Variables
RUN_CONTAINER=true                         #<-- Set to true to run the container after building
ADD_HOST=""                                #<-- If you need to add any hostfile entries to access the source or SRM server, it should be in this format: --add-host <HOSTNAME>:<IP ADDRESS> e.g. --add-host demotest.srm.synopsys.com:192.156.13.47

# Set CMD for docker image
if [ "$RUNTIME" = "standalone" ]; then
    RUNTIME_CMD="/home/sig-user/import_scan_results.py"
else
    RUNTIME_CMD="sh"
fi

 # Build and Tag container:
docker build --build-arg CA_CERT=${CA_CERT} --build-arg RUNTIME=${RUNTIME_CMD} -t ${IMAGE_NAME}:${IMAGE_TAG} .
docker image ls | grep ${IMAGE_NAME}

# Push to remote registry, if a registry is defined:
if [ -n "$REG" ]; then
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REG}/${IMAGE_NAME}:${IMAGE_TAG}
    docker push ${REG}/${IMAGE_NAME}:${IMAGE_TAG}
fi

# Run container if necesary:
if [ "$RUN_CONTAINER" = true ]; then
    docker run  ${ADD_HOST} --env-file test_env_vars.env -it ${IMAGE_NAME}:${IMAGE_TAG}
fi
