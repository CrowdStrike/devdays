# /bin/bash

docker run --privileged=true --rm \
        -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
        -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
        -e FALCON_CLOUD="$CS_CLOUD" \
        -e AWS_DEFAULT_REGION \
        -e AWS_CONTAINER_CREDENTIALS_RELATIVE_URI \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro \
        quay.io/crowdstrike/cloud-tools-image \
        bash -xc "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${REPO_URI}; falcon-node-sensor-push ${REPO_URI}"