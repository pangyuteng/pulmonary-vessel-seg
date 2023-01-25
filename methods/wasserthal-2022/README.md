
## manually run `wasserthal-2022` option 1.

+ install TotalSegmentator using instructions provided in original repo (pip or docker):
```
https://github.com/wasserth/TotalSegmentator
```

## manually run `wasserthal-2022` option 2, 

+ use prebuilt container with weights:
```
https://github.com/pangyuteng/totalsegmentator-and-friends/tree/main/assess/
docker-with-weights
```

```
docker pull pangyuteng/totalsegmentator:latest
docker run -it -u $(id -u):$(id -g) -w $PWD -v /mnt:/mnt \
    pangyuteng/totalsegmentator:latest bash
bash inference.sh ...
```

