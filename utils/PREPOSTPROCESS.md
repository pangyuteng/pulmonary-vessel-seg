## get `img.nii.gz` from 
```
https://github.com/pangyuteng/frangi-filter.git
python demo.py
series-instance-uid 
1.3.6.1.4.1.14519.5.2.1.6279.6001.113679818447732724990336702075
part of LUNA16 dataset
```
## for visualization, convert to .vtk or .stl
```
cd ../polydata
python gen_vtk.py lung_vessels.nii.gz lung_vessels.stl
```