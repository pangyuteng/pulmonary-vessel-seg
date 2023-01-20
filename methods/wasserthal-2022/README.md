
## inference
```
git clone git@github.com:pangyuteng/totalsegmentator-and-friends.git 
cd totalsegmentator-and-friends/assess/docker-with-weights
bash build_and_push.sh

docker run -it -u $(id -u):$(id -g) \
    -w $PWD -v /mnt:/mnt \
    pangyuteng/totalsegmentator:latest bash

TotalSegmentator -i tmp/img.nii.gz -o tmp/segmentations
TotalSegmentator -i tmp/img.nii.gz -o tmp/segmentations -ta lung_vessels
```

