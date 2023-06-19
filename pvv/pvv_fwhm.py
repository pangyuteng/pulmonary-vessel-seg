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
from utils import resample_img,extract_slice


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
    json_file = os.path.join(outdir,'results-fwhm.json')
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
    image = ((image-min_val)/(max_val-min_val)).clip(0,1)*255
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
    bcsa_dict = {}
    fwhm_dict = {}
    slice_png_list = []
    for p in tqdm(props):
        for n,coord in enumerate(p.coords[:-1]):
            mystart = p.coords[n]
            myend = p.coords[n+1]
            #print(mystart,myend)
            slice_center = image_obj.TransformContinuousIndexToPhysicalPoint([int(mystart[2]),int(mystart[1]),int(mystart[0])])
            slice_end = image_obj.TransformContinuousIndexToPhysicalPoint([int(myend[2]),int(myend[1]),int(myend[0])])
            slice_normal = np.array(slice_end)-np.array(slice_center)
            slice_spacing = (1,1,1)
            slice_radius = p.mean_intensity*2
            is_label = True
            #print(slice_center,slice_normal,slice_spacing,slice_radius,is_label)
            myslice = extract_slice(vessel_obj,slice_center,slice_normal,slice_spacing,slice_radius,is_label)
            myarr = sitk.GetArrayFromImage(myslice).squeeze().astype(np.uint8)
            mylabel = label(myarr)
            cidx=int(mylabel.shape[0]/2)
            myarea = np.sum(mylabel==mylabel[cidx,cidx]) # mm^2
            # this is not FWHM YET.
            bcsa_dict[p.label] = myarea
            is_label = False
            myslice = extract_slice(myimg_obj,slice_center,slice_normal,slice_spacing,slice_radius,is_label)
            myarr = sitk.GetArrayFromImage(myslice).squeeze().astype(np.uint8)
            png_file = f'{outdir}/slice-{p.label}.png'
            imageio.imsave(png_file,myarr)
            slice_png_list.append(png_file)

        if p.label > 1000:
            break

    with open(f'{outdir}/index.html','w') as f:
        for slice_png in slice_png_list:
            mystr = f'<img loading="lazy" alt="...", scr="{slice_png}" width="256px" height="256px"/>\n'
            f.write(mystr)

    print('area...')
    map_func = np.vectorize(lambda x: float(bcsa_dict.get(x,0)))
    area = map_func(ws_branch)
    print(area.dtype)
    qia_obj = sitk.GetImageFromArray(area)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-bcs-area.nii.gz")

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
        sitk.WriteImage(qia_obj,f"{outdir}/debug-bcs-pvv.nii.gz")

    qia_obj = resample_img(qia_obj, og_image_obj.GetSpacing(), is_label=True)
    sitk.WriteImage(qia_obj,f"{outdir}/bcs-pvv.nii.gz")
    
    spacing = qia_obj.GetSpacing()
    cc_per_voxel = np.prod(spacing)*0.001
    pvv = sitk.GetArrayFromImage(qia_obj)

    print('mip...')
    mip = (np.max(pvv,axis=1)*80).astype(np.uint8)
    mip_file = f"{outdir}/mip.png"
    imageio.imwrite(mip_file,mip)

    mydict = {
        'pvv5-bcsa-prct': float(np.sum(pvv==1)/np.sum(pvv>0)), # binary-cross-sectional-area
        'pvv10-bcsa-prct': float(np.sum(pvv==2)/np.sum(pvv>0)),
        'pvv10+-bcsa-prct': float(np.sum(pvv==3)/np.sum(pvv>0)),
        'pvv5-bcsa-cc': float(np.sum(pvv==1)*cc_per_voxel),
        'pvv10-bcsa-cc': float(np.sum(pvv==2)*cc_per_voxel),
        'pvv10+-bcsa-cc': float(np.sum(pvv==3)*cc_per_voxel),
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