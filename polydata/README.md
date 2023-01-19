
git clone git@github.com:pangyuteng/public-scratch.git
cd public-scratch/doccker/dcm
bash build_and_push.sh


docker pull pangyuteng/dcm:latest

docker run -it -u $(id -u):$(id -g) \
    -w $PWD -v /mnt:/mnt \
    pangyuteng/dcm:latest bash

python gen_vtk.py lung_vessels.nii.gz lung_vessels.vtk


https://www.google.com/search?q=pangyuteng+isosurface&oq=pangyuteng+isosurface&aqs=chrome.0.69i59j69i60.2198j0j7&sourceid=chrome&ie=UTF-8

https://discourse.itk.org/t/save-and-write-a-vtk-polydata-file/2516/8

