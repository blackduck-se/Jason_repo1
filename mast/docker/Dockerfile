# This example uses the official python image on debian linux.
FROM python:3.9.19-bullseye as base
ARG CA_CERT=""
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

# Install the python requirements from the requirements.txt file and other required python here:
RUN pip install --upgrade pip && pip install yq && pip install --requirement /tmp/requirements.txt && python -m nltk.downloader -d /usr/local/share/nltk_data brown

# Set any environment variables here, for example by default we set the home directory to the user we create, tell python to use the container trust store for CA certs
ENV HOME="/home/sig-user"
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Switch to the new user and set the working directory:
USER sig-user
WORKDIR /home/sig-user

# Copy over any scripts needed to run the integration and set the proper permissions and ownership, Update this section with any new scripts:
COPY --chown=sig-user:sig-user srmPost.py "/home/sig-user"
COPY --chown=sig-user:sig-user convert_mast_results.py "/home/sig-user"
COPY --chown=sig-user:sig-user import_mast_results.py "/home/sig-user"

RUN ls -l /home/sig-user

# We pass in the entrypoint start command from the docker_build.sh script allowing us to easily switch between standalone mode and tool Orchestration mode.
CMD ${START_CMD};
