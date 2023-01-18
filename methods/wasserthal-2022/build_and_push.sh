#!/bin/bash

export DOCKER_BUILDKIT=1
docker build -t totalsegmentator:latest .
docker push pangyuteng/totalsegmentator:latest
