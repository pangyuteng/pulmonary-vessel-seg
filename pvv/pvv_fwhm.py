import os
import sys
import ast
import json
import numpy as np
import SimpleITK as sitk
from skimage.morphology import skeletonize
from skimage.segmentation import watershed
from scipy import ndimage
from scipy.ndimage import distance_transform_edt
from skimage.measure import label, regionprops
from tqdm import tqdm
import imageio
from pvv_dist import resample_img

'''
https://en.wikipedia.org/wiki/Normal_distribution
https://en.wikipedia.org/wiki/Full_width_at_half_maximum
assuming vessel intensity can be fitted with a guassian distribution curve
we can use FWHM as diameter.
so if we have a sigma of 1mm, then diameter would be 2.355*1 mm

“BVX”, where “X” indicates a range of vessel sizes in mm2 (BV5 is the volume of blood contained in
vessels between 1.25 and 5 mm2 cross-sectional area, BV5-10
between 5 and 10 mm2, and BV10 > 10 mm2)
https://journals.physiology.org/doi/pdf/10.1152/japplphysiol.00458.2022

approximate diameter using FWHM which is ~ 2.355*sigma
https://en.wikipedia.org/wiki/Full_width_at_half_maximum

diameter = 2*radius = 2.355*sigma

radius = sigma*2.355/2
area = pi*(radius^2)

radius = np.sqrt(area/pi)
sigma = radius*2/2.355
sigma = np.sqrt(area/pi)*2/2.355

'''

def estimate_radius(image_file,lung_file,vessel_file,outdir,debug):
    
    os.makedirs(outdir,exist_ok=True)
    pvv_file = os.path.join(outdir,'pvv.nii.gz')
    json_file = os.path.join(outdir,'results-frangi.json')
    if os.path.exists(json_file):
        print(f'skip! {json_file} found')
        return

    og_image_obj = sitk.ReadImage(image_file)
    lung_obj = sitk.ReadImage(lung_file)
    vessel_obj = sitk.ReadImage(vessel_file)
    
    out_spacing = [1.0,1.0,1.0]
    image_obj = resample_img(og_image_obj, out_spacing, is_label=False)
    lung_obj = resample_img(lung_obj, out_spacing, is_label=True)
    vessel_obj = resample_img(vessel_obj, out_spacing, is_label=True)

    image = sitk.GetArrayFromImage(image_obj)
    lung_mask = sitk.GetArrayFromImage(lung_obj)
    vsl_mask = sitk.GetArrayFromImage(vessel_obj)

    spacing = image_obj.GetSpacing()
    origin = image_obj.GetOrigin()
    direction = image_obj.GetDirection()
    
    min_val,max_val = -1000,1000
    image = image.astype(np.float)
    image = (image-min_val)/(max_val-min_val)
    image = image.clip(0,1)
    image[lung_mask==0]=0
    myimg_obj = sitk.GetImageFromArray(image)
    myimg_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(myimg_obj,f"{outdir}/debug-myimg.nii.gz")

    print('bs_field (appx radius)...')
    bs_field = distance_transform_edt(vsl_mask>0)
    bs_field = bs_field.astype(float)*out_spacing[0]
    print(bs_field.dtype)
    qia_obj = sitk.GetImageFromArray(bs_field)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-bs_field.nii.gz")

    print('skeletonize...')
    skeleton = skeletonize(vsl_mask)
    skeleton = skeleton.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(skeleton)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-skeleton.nii.gz")

    print('intersection...')
    # determine branching point
    # ref https://www.mathworks.com/matlabcentral/fileexchange/67600-branch-points-from-3d-logical-skeleton?s_tid=blogs_rc_5
    weights = np.ones((3,3,3))
    intersection = ndimage.convolve(skeleton,weights) > 3

    intersection = intersection.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(intersection)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-intersection.nii.gz")

    print('label...')
    branch = np.copy(skeleton)
    branch[intersection==1]=0
    branch = label(branch)
    branch = branch.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(branch)
    qia_obj.CopyInformation(image_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/debug-branch.nii.gz")

    print('watershed...')
    ws_branch = watershed(vsl_mask*-1, branch, mask=vsl_mask>0)
    ws_branch = ws_branch.astype(np.int16)

    qia_obj = sitk.GetImageFromArray(ws_branch)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-watershed_labels.nii.gz")

    props = regionprops(branch,intensity_image=bs_field)
    for p in props:
        print(dir(p))
        print(p.coords)
        print(p.label,p.mean_intensity)
        sys.exit(1)

    # qia_obj = sitk.GetImageFromArray(radius)
    # qia_obj.CopyInformation(image_obj)
    # if debug:
    #     sitk.WriteImage(qia_obj,f"{outdir}/debug-radius.nii.gz")

    print('regionprops...')
    props = regionprops(branch,intensity_image=bs_field)
    mapper_dict = {p.label:np.pi*(p.mean_intensity**2) for p in props}

    print('area...')
    map_func = np.vectorize(lambda x: float(mapper_dict.get(x,0)))
    area = map_func(ws_branch)
    print(area.dtype)
    qia_obj = sitk.GetImageFromArray(area)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-area.nii.gz")

    print('pvv...')
    pvv = np.zeros_like(area)
    pvv[np.logical_and(area>0,area<=5)]=1
    pvv[np.logical_and(area>5,area<10)]=2
    pvv[area>=10]=3
    pvv = pvv.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(pvv)
    qia_obj.CopyInformation(image_obj)

    qia_obj = sitk.GetImageFromArray(pvv)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-pvv.nii.gz")

    qia_obj = resample_img(qia_obj, og_image_obj.GetSpacing(), is_label=True)
    sitk.WriteImage(qia_obj,f"{outdir}/pvv.nii.gz")
    
    spacing = qia_obj.GetSpacing()
    cc_per_voxel = np.prod(spacing)*0.001
    pvv = sitk.GetArrayFromImage(qia_obj)

    print('mip...')
    mip = np.max(pvv,axis=1)*80
    mip_file = f"{outdir}/mip.png"
    imageio.imwrite(mip_file,mip)

    mydict = {
        'pvv5-fwhm-prct': float(np.sum(pvv==1)/np.sum(pvv>0)),
        'pvv10-fwhm-prct': float(np.sum(pvv==2)/np.sum(pvv>0)),
        'pvv10+-fwhm-prct': float(np.sum(pvv==3)/np.sum(pvv>0)),
        'pvv5-fwhm-cc': float(np.sum(pvv==1)*cc_per_voxel),
        'pvv10-fwhm-cc': float(np.sum(pvv==2)*cc_per_voxel),
        'pvv10+-fwhm-cc': float(np.sum(pvv==3)*cc_per_voxel),
    }
    with open(json_file,'w') as f:
        f.write(json.dumps(mydict))


if __name__ == "__main__":
    image_file = sys.argv[1]
    lung_file = sys.argv[2]
    vessel_file = sys.argv[3]
    outdir = sys.argv[4]
    debug = ast.literal_eval(sys.argv[5])
    estimate_radius(image_file,lung_file,vessel_file,outdir,debug)

"""

docker run -it -u $(id -u):$(id -g) -w $PWD \
    -v /cvibraid:/cvibraid -v /radraid:/radraid \
    pangyuteng/ml:latest bash

python pvv_fwhm.py img.nii.gz lung.nii.gz wasserthal.nii.gz outdir-fwhm True

"""