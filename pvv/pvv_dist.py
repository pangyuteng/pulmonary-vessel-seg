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
import imageio
from tqdm import tqdm

from utils import resample_img

# ref 
#
#  BVV computation https://www.nature.com/articles/s41598-023-31470-6
#

def main(mask_file,outdir,debug):
    os.makedirs(outdir,exist_ok=True)
    
    pvv_file = os.path.join(outdir,'pvv.nii.gz')
    json_file = os.path.join(outdir,'results-dt.json')
    if os.path.exists(json_file):
        print(f'skip! {json_file} found')
        return

    print('ReadMask...')
    og_mask_obj = sitk.ReadImage(mask_file)
    print(og_mask_obj.GetSize())
    print(og_mask_obj.GetSpacing())
    print(og_mask_obj.GetDirection())

    print('resample_img...')
    target_spacing=[0.6,0.6,0.6]

    mask_obj = resample_img(og_mask_obj, target_spacing, is_label=True)
    print(mask_obj.GetSize())
    print(mask_obj.GetSpacing())
    print(mask_obj.GetDirection())
    if debug:
        sitk.WriteImage(mask_obj,f"{outdir}/debug-mask.nii.gz")

    spacing = mask_obj.GetSpacing()
    origin = mask_obj.GetOrigin()
    direction = mask_obj.GetDirection()
    
    vsl_mask = sitk.GetArrayFromImage(mask_obj)
    print(vsl_mask.dtype)
    # alternative to frangi-filter, diameter can be estimated with "distance transform" if speed is a concern.
    print('skeletonize...')
    skeleton = skeletonize(vsl_mask)
    skeleton = skeleton.astype(np.int16)

    qia_obj = sitk.GetImageFromArray(skeleton)
    qia_obj.CopyInformation(mask_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-skeleton.nii.gz")

    print('bs_field (appx radius)...')
    bs_field = distance_transform_edt(vsl_mask>0)
    bs_field = bs_field.astype(float)*target_spacing[0]
    print(bs_field.dtype)
    qia_obj = sitk.GetImageFromArray(bs_field)
    qia_obj.CopyInformation(mask_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-bs_field.nii.gz")

    arr = bs_field[np.where(bs_field>0)]
    print(np.min(arr),np.max(arr))
    hist, bin_edges = np.histogram(arr,bins=12,range=(0,6))
    hist = np.round(hist,2)
    hist = hist / np.sum(hist)
    hist = hist.tolist()
    hist_dict = {f'radius-lt-{k}mm':v for k,v in zip(bin_edges[1:],hist)}
    print(hist_dict)
    '''
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
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-intersection.nii.gz")

    print('label...')
    branch = np.copy(skeleton)
    branch[intersection==1]=0
    branch = label(branch)
    branch = branch.astype(np.int32)
    qia_obj = sitk.GetImageFromArray(branch)
    qia_obj.CopyInformation(mask_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-branch.nii.gz")
    
    # watershed
    print('watershed...')
    ws_branch = watershed(vsl_mask*-1, branch, mask=vsl_mask>0)
    ws_branch = ws_branch.astype(np.int16)

    qia_obj = sitk.GetImageFromArray(ws_branch)
    qia_obj.CopyInformation(mask_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-watershed_labels.nii.gz")

    method = 'naive'
    idx_list = list(np.unique(branch))
    th = 50000
    if len(idx_list) < th:
        method = 'vectorize'

    print(f'regionprops... method: {method} since len(idx_list) {len(idx_list)} < {th}')
    if method == 'vectorize':
        # faster, but much more memory intensitve:
        props = regionprops(branch,intensity_image=bs_field)
        mapper_dict = {p.label:np.pi*(p.mean_intensity**2) for p in props}
        print('area...')
        map_func = np.vectorize(lambda x: float(mapper_dict.get(x,0)))
        area = map_func(ws_branch)
    else:
        area = np.zeros_like(ws_branch).astype(float)
        for idx in tqdm(idx_list):
            if idx == 0:
                continue
            bs_values = bs_field[branch==idx]
            tmp_radius = np.mean(bs_values)
            tmp_area = np.pi*(tmp_radius**2)
            area[ws_branch==idx]=tmp_area
    print(area.dtype)
    qia_obj = sitk.GetImageFromArray(area)
    qia_obj.CopyInformation(mask_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-area.nii.gz")
    
    print('pvv...')
    pvv = np.zeros_like(area)
    pvv[np.logical_and(area>0,area<=5)]=1
    pvv[np.logical_and(area>5,area<10)]=2
    pvv[area>=10]=3
    pvv = pvv.astype(np.int16)
    qia_obj = sitk.GetImageFromArray(pvv)
    qia_obj.CopyInformation(mask_obj)
    if debug:
        sitk.WriteImage(qia_obj,os.path.join(outdir,'debug-pvv.nii.gz'))
    
    print('resample...')
    qia_obj = sitk.Resample(qia_obj, og_mask_obj, sitk.Transform(), sitk.sitkNearestNeighbor, 0, mask_obj.GetPixelID())
    sitk.WriteImage(qia_obj,pvv_file)

    spacing = qia_obj.GetSpacing()
    cc_per_voxel = np.prod(spacing)*0.001

    pvv = sitk.GetArrayFromImage(qia_obj)
    
    print('mip...')
    mip = np.max(pvv,axis=1)*80
    mip_file = f"{outdir}/mip.png"
    imageio.imwrite(mip_file,mip)

    mydict = {
        'pvv5-dt-prct': float(np.sum(pvv==1)/np.sum(pvv>0)),
        'pvv10-dt-prct': float(np.sum(pvv==2)/np.sum(pvv>0)),
        'pvv10+-dt-prct': float(np.sum(pvv==3)/np.sum(pvv>0)),
        'pvv5-dt-cc': float(np.sum(pvv==1)*cc_per_voxel),
        'pvv10-dt-cc': float(np.sum(pvv==2)*cc_per_voxel),
        'pvv10+-dt-cc': float(np.sum(pvv==3)*cc_per_voxel),
        'hist': hist,
    }
    # TODO: add cc to above
    
    with open(json_file,'w') as f:
        f.write(json.dumps(mydict))
    print('pvv_dist.py done')

if __name__ == "__main__":
    mask_file = sys.argv[1]
    outdir = sys.argv[2]
    debug = ast.literal_eval(sys.argv[3])
    main(mask_file,outdir,debug)

"""

docker run -it -u $(id -u):$(id -g) -w $PWD \
    -v /cvibraid:/cvibraid -v /radraid:/radraid \
    pangyuteng/ml:latest bash

python pvv_dist.py wasserthal.nii.gz outdir-dt

"""
