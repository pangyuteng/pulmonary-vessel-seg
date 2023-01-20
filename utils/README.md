
git clone git@github.com:pangyuteng/public-scratch.git
cd public-scratch/doccker/dcm
bash build_and_push.sh


docker pull pangyuteng/dcm:latest

docker run -it -u $(id -u):$(id -g) \
    -w $PWD -v /mnt:/mnt \
    pangyuteng/dcm:latest bash

cp ../tmp/segmentations/lung_vessels.nii.gz ../prototype-view && \
cp ../../Papaya/tests/data/series.nii.gz ../prototype-view

python gen_vtk.py ../prototype-view/series.nii.gz ../prototype-view/series.vtk && \
python gen_vtk.py lung_vessels.nii.gz ../prototype-view/lung_vessels.vtk && \
ls ../prototype-view/*.vtk -lh

python gen_vtk.py ../prototype-view/series.nii.gz  ../prototype-view/series.stl && \

python gen_vtk.py lung_vessels.nii.gz ../prototype-view/lung_vessels.stl && \
ls ../prototype-view/*.stl -lh

http://www.vmtk.org/tutorials/SurfaceForMeshing.html

https://www.google.com/search?q=pangyuteng+isosurface&oq=pangyuteng+isosurface&aqs=chrome.0.69i59j69i60.2198j0j7&sourceid=chrome&ie=UTF-8

https://discourse.itk.org/t/save-and-write-a-vtk-polydata-file/2516/8

https://github.com/pyushkevich/itksnap/blob/3ff1eb1d9e2318ac9820ace939e1551502efc8f4/Logic/Mesh/VTKMeshPipeline.cxx