#!/bin/bash

TAG="$(git log -n 1 | grep commit | cut -b 8-)"

docker build -t "tactical-rmm-webhooks:$TAG" .
docker tag "tactical-rmm-webhooks:$TAG" "tactical-rmm-webhooks:latest"