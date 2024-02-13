#!/usr/bin/env bash

# Prints each command before execution
set -o xtrace

helm upgrade --install \
    ${JOB_NAME} ./build/helm/celery-helm \
    -f build/${DEPLOYMENT_ENV}.values.yaml \
    --set-string "image.tag=${BUILD_NUMBER}"
