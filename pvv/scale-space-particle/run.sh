#!/bin/bash


export niftifile=$1
export workdir=$2
echo niftifile ${niftifile}
echo workdir ${workdir}
cd ${workdir}

#ConvertDicom --dir ${dicomdir} -o CT.nrrd
# python /cvibraid/cvib2/apps/personal/pteng/github/pulmonary-vessel-seg/pvv/scale-space-particle/img_convert.py ${niftifile} ${workdir}/CT.nrrd NiftiImageIO

GenerateMedianFilteredImage -i CT.nrrd -o CT-median.nrrd
GeneratePartialLungLabelMap --ict CT-median.nrrd -o partialLungLabelMap.nrrd
/root/miniconda2/bin/python /ChestImagingPlatform/Scripts/cip_compute_vessel_particles.py \
    -i CT.nrrd -l partialLungLabelMap.nrrd -o particles.vtk \
    -s 0.625 -r WholeLung,RightLung,LeftLung \
    --tmpDir=${workdir}
