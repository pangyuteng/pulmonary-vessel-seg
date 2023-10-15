#!/bin/bash

export workdir=$1
export dicomdir=$2
echo workdir ${workdir}
echo dicomdir ${dicomdir}
cd ${workdir}

ConvertDicom --dir ${dicomdir} -o CT.nrrd
GenerateMedianFilteredImage -i CT.nrrd -o CT-median.nrrd
GeneratePartialLungLabelMap --ict CT-median.nrrd -o partialLungLabelMap.nrrd
/root/miniconda2/bin/python /ChestImagingPlatform/Scripts/cip_compute_vessel_particles.py \
    -i CT.nrrd -l partialLungLabelMap.nrrd -o particles.vtk \
    -s 0.625 -r WholeLung,RightLung,LeftLung \
    --tmpDir=${workdir}
