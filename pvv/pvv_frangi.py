import os
import sys
import ast
import json
import numpy as np
import SimpleITK as sitk
from skimage.morphology import skeletonize
from skimage.segmentation import watershed
from scipy import ndimage
from skimage.measure import label, regionprops
from tqdm import tqdm
import imageio

from utils import resample_img

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


# radius 
>>> [r for r in np.linspace(0.25,5,10)]

# area
>>> [np.pi*(r**2) for r in np.linspace(0.25,5,10)]

# sigma
>>> [r*2/2.355 for r in np.linspace(0.25,5,10)]

# area
>>> [a for a in np.linspace(1,20,20)]

# radius 
>>> [np.sqrt(a/np.pi) for a in np.linspace(1,20,20)]

# sigma
>>> [np.sqrt(a/np.pi)*2/2.355 for a in np.linspace(1,20,20)]

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
    image = 255*image
    image[lung_mask==0]=0
    myimg_obj = sitk.GetImageFromArray(image)
    myimg_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(myimg_obj,f"{outdir}/debug-myimg.nii.gz")

    #radius_list = [r for r in np.linspace(0.25,5,10)]
    radius_list = [0.3,0.5,0.75,1,1.1,1.3,1.4,1.75,2,3,4] # tweaked so 2 or more r can be mapped to the 3 classes of pvv.
    sigma_list = [r*2/2.355 for r in radius_list]
    arr_list = []
    for radius_mm,sigma_mm in zip(radius_list,sigma_list):
        print(f'sigma: {sigma_mm}')
        sigma = np.ones(3)*sigma_mm
        #
        # https://simpleitk.org/doxygen/v1_2/html/classitk_1_1simple_1_1SmoothingRecursiveGaussianImageFilter.html
        # sigma is measured in the units of image spacing
        # 
        sigma = sigma/np.array(spacing) # (no real need since we set spacing to 1^3mm)
        print(sigma)
        gaussian = sitk.SmoothingRecursiveGaussianImageFilter()
        gaussian.SetSigma(sigma)
        # 
        # pvv varies obviously if you opt to use image_obj or vessel_obj
        # 
        smoothed = gaussian.Execute(vessel_obj)

        '''
        ref. on sitk.ObjectnessMeasureImageFilter
        https://simpleitk.org/doxygen/latest/html/sitkObjectnessMeasureImageFilter_8h_source.html
        https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ObjectnessMeasureImageFilter.html
        http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.110.7722&rep=rep1&type=pdf
        https://github.com/InsightSoftwareConsortium/ITK/blob/f84720ee0823964bd135de8eb973acc40c1e70e1/Modules/Filtering/ImageFeature/include/itkHessianToObjectnessMeasureImageFilter.h 
        https://github.com/InsightSoftwareConsortium/ITK/blob/f84720ee0823964bd135de8eb973acc40c1e70e1/Modules/Filtering/ImageFeature/include/itkHessianToObjectnessMeasureImageFilter.hxx

        per https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6214740/pdf/nihms982442.pdf
        Multiscale vessel enhancement filtering
        set alpha 0.53, beta 0.61 # gamma was not metioned.

        https://pubmed.ncbi.nlm.nih.gov/32741657
        https://pubmed.ncbi.nlm.nih.gov/25227036
        set alpha 0.5, beta 0.5, c 20 ?? likely not the same equation.
        
        Jimenez-Carretero, Daniel, et al. "3D Frangi-based lung vessel enhancement filter penalizing airways." 2013 IEEE 10th International Symposium on Biomedical Imaging. IEEE, 2013.
        alpha 0.5, beta 0.5, c 500

        argmax 
        https://www.sciencedirect.com/science/article/pii/S1361841519301598
        '''
        myfilter = sitk.ObjectnessMeasureImageFilter()
        myfilter.SetBrightObject(True)
        myfilter.SetObjectDimension(1) # 1: lines (vessels),
        myfilter.SetAlpha(0.5)
        myfilter.SetBeta(0.5)
        myfilter.SetGamma(500.0)
        tmp_obj = myfilter.Execute(smoothed)
        tmp_arr = sitk.GetArrayFromImage(tmp_obj)
        min_val,max_val = np.min(tmp_arr[vsl_mask==1]),np.max(tmp_arr[vsl_mask==1])
        tmp_arr = (tmp_arr-min_val)/(max_val-min_val)
        arr_list.append(tmp_arr)
        new_obj = sitk.GetImageFromArray(tmp_arr)
        new_obj.CopyInformation(tmp_obj)
        if debug:
            sitk.WriteImage(new_obj,f"{outdir}/debug-radius-{radius_mm:06.2f}.nii.gz")

    arr = np.argmax(np.array(arr_list),axis=0)
    arr = arr.astype(np.int16)
    arr[vsl_mask==0]=-1
    print(np.unique(arr))
    mapper_dict = {n:r for n,r in enumerate(radius_list)}
    map_func = np.vectorize(lambda x: float(mapper_dict.get(x,0)))
    radius = map_func(arr)
    print(radius.dtype)

    qia_obj = sitk.GetImageFromArray(radius)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-radius.nii.gz")

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

    method = 'naive'
    idx_list = list(np.unique(branch))
    th = 50000
    if len(idx_list) < th:
        method = 'vectorize'

    print(f'regionprops... method: {method} since len(idx_list) {len(idx_list)} < {th}')
    if method == 'vectorize':
        props = regionprops(branch,intensity_image=radius)
        #mapper_dict = {p.label:np.pi*(p.mean_intensity**2) for p in props}
        mapper_dict = {p.label:np.pi*(p.max_intensity**2) for p in props}
        print('area...')
        map_func = np.vectorize(lambda x: float(mapper_dict.get(x,0)))
        area = map_func(ws_branch)
    else:
        area = np.zeros_like(ws_branch).astype(float)
        for idx in tqdm(idx_list):
            if idx == 0:
                continue
            radius_values = radius[branch==idx]
            #tmp_radius = np.max(radius_values)
            tmp_radius = np.mean(radius_values)
            tmp_area = np.pi*(tmp_radius**2)
            area[ws_branch==idx]=tmp_area
    print(area.dtype)
    qia_obj = sitk.GetImageFromArray(area)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-area.nii.gz")

    arr = area[ws_branch>0]
    print(np.min(arr),np.max(arr))
    hist, bin_edges = np.histogram(arr,bins=20,range=(0,20))
    hist = np.round(hist,2)
    hist = hist / np.sum(hist)
    hist = hist.tolist()
    hist_dict = {f'area-lt-{k}mm2-frangi':v for k,v in zip(bin_edges[1:],hist)}
    print(hist_dict)

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

    lung_obj = sitk.ReadImage(lung_file)
    qia_obj = sitk.Resample(qia_obj, lung_obj, sitk.Transform(), sitk.sitkNearestNeighbor, 0, qia_obj.GetPixelID())

    spacing = qia_obj.GetSpacing()
    cc_per_voxel = np.prod(spacing)*0.001
    pvv = sitk.GetArrayFromImage(qia_obj)
    lung = sitk.GetArrayFromImage(lung_obj)
    pvv[lung==0]=0 # resample is yielding non-0 values near image border.
    qia_obj = sitk.GetImageFromArray(pvv)
    qia_obj.CopyInformation(lung_obj)
    sitk.WriteImage(qia_obj,f"{outdir}/pvv.nii.gz")

    print('mip...')
    print(np.unique(pvv))
    mip = np.max(pvv,axis=1)*80
    mip = mip.astype(np.uint8)
    print(np.unique(mip))
    mip_file = f"{outdir}/mip.png"
    imageio.imwrite(mip_file,mip)

    mydict = {
        'pvv5-frangi-prct': float(np.sum(pvv==1)/np.sum(pvv>0)),
        'pvv10-frangi-prct': float(np.sum(pvv==2)/np.sum(pvv>0)),
        'pvv10+-frangi-prct': float(np.sum(pvv==3)/np.sum(pvv>0)),
        'pvv5-frangi-cc': float(np.sum(pvv==1)*cc_per_voxel),
        'pvv10-frangi-cc': float(np.sum(pvv==2)*cc_per_voxel),
        'pvv10+-frangi-cc': float(np.sum(pvv==3)*cc_per_voxel),
    }
    mydict.update(hist_dict)

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

python pvv_frangi.py img.nii.gz lung.nii.gz wasserthal.nii.gz outdir-frangi True

"""