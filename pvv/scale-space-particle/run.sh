#!/bin/bash

echo $1

cd /cvibraid/cvib2/Temp/ptengtmp

#ConvertDicom --dir dicom -o CT.nrrd
#GenerateMedianFilteredImage -i CT.nrrd -o CT-median.nrrd
#GeneratePartialLungLabelMap --ict CT-median.nrrd -o partialLungLabelMap.nrrd

# python /ChestImagingPlatform/Scripts/cip_compute_vessel_particles.py \
#     -i CT.nrrd -l partialLungLabelMap.nrrd \
#     -r WholeLung -r LeftLung -r RightLung -o particles.vtk \
#     --perm -s 0.625 --tmpDir=/cvibraid/cvib2/Temp/ptengtmp

python /ChestImagingPlatform/Scripts/cip_compute_vessel_particles.py \
    -i CT.nrrd -l partialLungLabelMap.nrrd -o particles.vtk \
    -s 0.625 -r WholeLung,RightLung,LeftLung \
    --tmpDir=/cvibraid/cvib2/Temp/ptengtmp