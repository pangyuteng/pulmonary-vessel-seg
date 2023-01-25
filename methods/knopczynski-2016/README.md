

+ (optional) pull repo and follow docker/readme to build container
```
git clone git@github.com:pangyuteng/Vessel3DDL.git
cd Vessel3DDL
git checkout py3
...
docker tag vessel3ddl:inference pangyuteng/vessel3ddl:inference
docker push pangyuteng/vessel3ddl:inference
```

+ perform inference

```
docker pull pangyuteng/vessel3ddl:inference
docker run -it -u $(id -u):$(id -g) -w $PWD -v /mnt:/mnt \
    pangyuteng/vessel3ddl:inference bash
bash inference.sh ...
```