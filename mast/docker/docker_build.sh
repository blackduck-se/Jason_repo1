#!/bin/sh
set -x
set -e

# Docker Build Variables
IMAGE_NAME="srm-custom-connector-mast"  #<-- Name of the image to build
IMAGE_TAG="1.0"                         #<-- Image Tag
REG="myregistry:5000"                   #<-- Registry to push the image to after being built, SRM must be able to pull images from this registry.
BUILD_CONTAINER=true                    #<-- Set to true to build the container, set to false if the container has already been built and you just want to run it with different inputs
CA_CERT=""                              #<-- If you need to add a CA cert to the image, put the filename to copy here, if this is not needed set this to ""

# Docker Run Variables
RUN_CONTAINER=true                  #<-- Set to true to run the container after building
MOUNT_PATH="/tmp/mast"              #<-- Path to the directory containing the MAST results to import
IMPORT_FILE="data.json"             #<-- filename to import, must be in the MOUNT_PATH directory
ENV_VAR_FILE="env_vars.env"         #<-- Name of the environment variable file used to populate the values for srm url, project name, api key, and optionally branch name.
ADD_HOST=""                         #<-- If you need to add any hostfile entries to access the source or SRM server, it should be in this format: --add-host <HOSTNAME>:<IP ADDRESS> e.g. --add-host demotest.srm.synopsys.com:192.156.13.47
RUNTIME_CMD="/home/sig-user/import_mast_results.py /data/${IMPORT_FILE}"  #<-- Command for the container to run at startup, this typically does not need to be changed.

# copy files from parent directory needed in the docker image:
cp ../../srmPost.py .
cp ../convert_mast_results.py .
cp ../import_mast_results.py .

 # Build and Tag container:
if [ "$BUILD_CONTAINER" = true ]; then
    docker build --build-arg CA_CERT=${CA_CERT} -t ${IMAGE_NAME}:${IMAGE_TAG} .
    docker image ls | grep ${IMAGE_NAME}
fi

# remove files that were copied
rm srmPost.py
rm convert_mast_results.py
rm import_mast_results.py

# Push to remote registry, if a registry is defined:
if [ -n "$REG" ]; then
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REG}/${IMAGE_NAME}:${IMAGE_TAG}
    docker push ${REG}/${IMAGE_NAME}:${IMAGE_TAG}
fi

# Run container if necesary:
if [ "$RUN_CONTAINER" = true ]; then
    docker run  ${ADD_HOST} --mount type=bind,src=$MOUNT_PATH,dst=/data  --env START_CMD="${RUNTIME_CMD}" --env-file $ENV_VAR_FILE -it ${IMAGE_NAME}:${IMAGE_TAG}
fi

