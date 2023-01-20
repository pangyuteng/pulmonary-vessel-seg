
## manually run `wasserthal-2022` option 1.

+ use the options provided in original repo, either install or use pre-built docker container:

 https://github.com/wasserth/TotalSegmentator


## manually run `wasserthal-2022` option 2, 

+ use prebuilt container with weights from https://github.com/pangyuteng/totalsegmentator-and-friends/tree/main/assess/docker-with-weights 

```

docker pull pangyuteng/totalsegmentator:latest
docker run -it -u $(id -u):$(id -g) \
    -w $PWD -v /mnt:/mnt \
    pangyuteng/totalsegmentator:latest bash

bash inference.sh image.nii.gz lung_vessels.nii.gz


```

