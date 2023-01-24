

+ (optional) pull repo and follow docker/readme to build container
```
git clone git@github.com:pangyuteng/Vessel3DDL.git
cd Vessel3DDL
git checkout py3
docker tag vessel3ddl:inference pangyuteng/vessel3ddl:inference
docker push pangyuteng/vessel3ddl:inference
```

+ perform inference

```
docker run -it -v /mnt:/mnt pangyuteng/vessel3ddl:inference bash
bash inference.sh 
```

root@0780c285e19f:/opt/app/scripts/UseClassifier# python classify.py /mnt/hd2/data/LUNA16/1.3.6.1.4.1.14519.5.2.1.6279.6001.994459772950022352718462251777.mhd /mnt/hd2/data/vessel12/1.3.6.1.4.1.14519.5.2.1.6279.6001.994459772950022352718462251777-vessels.nii.gz
