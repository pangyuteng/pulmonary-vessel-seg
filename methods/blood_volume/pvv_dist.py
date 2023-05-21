import os
import sys
import json
import numpy as np
import SimpleITK as sitk
from skimage.morphology import skeletonize
from skimage.segmentation import watershed
from scipy import ndimage
from scipy.ndimage.morphology import distance_transform_edt
from skimage.measure import label, regionprops
import imageio
from tqdm import tqdm

# ref 
#
#  BVV computation https://www.nature.com/articles/s41598-023-31470-6
#
#  skeletonization alternative https://github.com/amy-tabb/CurveSkel-Tabb-Medeiros-2018
#

def resample_img(itk_image, out_spacing, is_label=False):
    
    # Resample images to 2mm spacing with SimpleITK
    original_spacing = itk_image.GetSpacing()
    original_size = itk_image.GetSize()

    out_size = [
        int(np.round(original_size[0] * (original_spacing[0] / out_spacing[0]))),
        int(np.round(original_size[1] * (original_spacing[1] / out_spacing[1]))),
        int(np.round(original_size[2] * (original_spacing[2] / out_spacing[2])))]

    resample = sitk.ResampleImageFilter()
    resample.SetOutputSpacing(out_spacing)
    resample.SetSize(out_size)
    resample.SetOutputDirection(itk_image.GetDirection())
    resample.SetOutputOrigin(itk_image.GetOrigin())
    resample.SetTransform(sitk.Transform())
    resample.SetDefaultPixelValue(itk_image.GetPixelIDValue())

    if is_label:
        resample.SetInterpolator(sitk.sitkNearestNeighbor)
    else:
        resample.SetInterpolator(sitk.sitkLinear)

    return resample.Execute(itk_image)

def main(image_file,mask_file,outdir,target_spacing=[0.6,0.6,0.6]):
    os.makedirs(outdir,exist_ok=True)
    print('ReadImage...')
    image_obj = sitk.ReadImage(image_file)
    mask_obj = sitk.ReadImage(mask_file)
    print('resample_img...')
    if target_spacing is not None:
        image_obj = resample_img(image_obj, target_spacing, is_label=False)
        sitk.WriteImage(image_obj,f"{outdir}/img.nii.gz")
        mask_obj = resample_img(mask_obj, target_spacing, is_label=True)
        sitk.WriteImage(mask_obj,f"{outdir}/mask.nii.gz")

    spacing = mask_obj.GetSpacing()
    origin = mask_obj.GetOrigin()
    direction = mask_obj.GetDirection()
    
    vsl_mask = sitk.GetArrayFromImage(mask_obj)
    
    # alternative to frangi-filter, diameter can be estimated with "distance transform" if speed is a concern.
    print('skeletonize...')
    skeleton = skeletonize(vsl_mask)
    skeleton = skeleton.astype(np.int16)

    qia_obj = sitk.GetImageFromArray(skeleton)
    qia_obj.CopyInformation(mask_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/skeleton.nii.gz")
    print('bs_field...')
    bs_field = distance_transform_edt(vsl_mask>0)
    bs_field = bs_field.astype(np.int16)

    qia_obj = sitk.GetImageFromArray(bs_field)
    qia_obj.CopyInformation(mask_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/bs_field.nii.gz")
    '''
    # radius
    >>> [r for r in np.arange(1,6,1)]
    [1, 2, 3, 4, 5]
    # area
    >>> [np.pi*(r**2) for r in np.arange(1,6,1)]
    [3.141592653589793, 12.566370614359172, 28.274333882308138, 50.26548245743669, 78.53981633974483]


    # radius
    >>> [np.round(r,2) for r in np.arange(0.6,5,.6)]
    [0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 4.2, 4.8]
    # area
    >>> [np.round(np.pi*(r**2),2) for r in np.arange(0.6,5,.6)]
    [1.13, 4.52, 10.18, 18.1, 28.27, 40.72, 55.42, 72.38]

    '''

    # with skeleton as input
    # for each point in skeleton
    # determine if part of edge (a branch) or node (intersection)
    # for each edge determine radius
    # redraw volume/surface using branch radius and length
    # compute bvv5,bvv10,bvv10+

    print('intersection...')
    # determine branching point
    # ref https://www.mathworks.com/matlabcentral/fileexchange/67600-branch-points-from-3d-logical-skeleton?s_tid=blogs_rc_5
    weights = np.ones((3,3,3))
    intersection = ndimage.convolve(skeleton,weights) > 3
    intersection = intersection.astype(np.int16)
    
    qia_obj = sitk.GetImageFromArray(intersection)
    qia_obj.CopyInformation(mask_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/intersection.nii.gz")

    print('label...')
    branch = np.copy(skeleton)
    branch[intersection==1]=0
    branch = label(branch)
    branch = branch.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(branch)
    qia_obj.CopyInformation(mask_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/branch.nii.gz")
    
    # watershed
    print('watershed...')
    ws_branch = watershed(vsl_mask*-1, branch, mask=vsl_mask>0)
    ws_branch = ws_branch.astype(np.int16)

    qia_obj = sitk.GetImageFromArray(ws_branch)
    qia_obj.CopyInformation(mask_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/watershed_labels.nii.gz")

    radius = np.zeros_like(ws_branch)
    print('regionprops...')
    props = regionprops(branch,intensity_image=bs_field)
    print('radius...')
    for p in tqdm(props):
        radius[ws_branch==p.label] = p.mean_intensity

    qia_obj = sitk.GetImageFromArray(radius)
    qia_obj.CopyInformation(mask_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/radius.nii.gz")
    
    pvv = np.zeros_like(radius)
    pvv[np.logical_and(radius>0,radius<=1.5)]=1
    pvv[np.logical_and(radius>1.5,radius<2.5)]=2
    pvv[radius>=2.5]=3
    pvv = pvv.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(pvv)
    qia_obj.CopyInformation(mask_obj)
    pvv_file = os.path.join(outdir,'pvv.nii.gz')
    sitk.WriteImage(qia_obj,pvv_file)
    
    #pvv_obj = sitk.ReadImage(pvv_file)
    #pvv = sitk.GetArrayFromImage(pvv_obj)
    mip = np.max(pvv,axis=1)*80
    mip_file = f"{outdir}/mip.png"
    imageio.imwrite(mip_file,mip)

    mydict = {
        'pvv5-dt': float(np.sum(pvv==1)/np.sum(pvv>0)),
        'pvv10-dt': float(np.sum(pvv==2)/np.sum(pvv>0)),
        'pvv10+-dt': float(np.sum(pvv==3)/np.sum(pvv>0)),
    }
    json_file = f"{outdir}/dist_transform.json"
    with open(json_file,'w') as f:
        f.write(json.dumps(mydict))


if __name__ == "__main__":
    image_file = sys.argv[1]
    mask_file = sys.argv[2]
    outdir = sys.argv[3]
    main(image_file,mask_file,outdir)

"""

docker run -it -u $(id -u):$(id -g) -w $PWD \
    -v /cvibraid:/cvibraid -v /radraid:/radraid \
    pangyuteng/ml:latest bash

python pvv_dist.py img.nii.gz wasserthal.nii.gz outdir-dt

"""