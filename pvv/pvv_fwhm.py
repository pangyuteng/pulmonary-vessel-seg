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
from utils import resample_img,extract_slice,estimate_radius_fwhm


def main_fwhm(image_file,vessel_file,outdir,debug):
    
    os.makedirs(outdir,exist_ok=True)
    bcsa_json_file = os.path.join(outdir,'results-bcsa.json')
    fwhm_json_file = os.path.join(outdir,'results-fwhm.json')
    if os.path.exists(bcsa_json_file) and os.path.exists(fwhm_json_file):
        print(f'skip! {bcsa_json_file} {fwhm_json_file} found')
        return

    og_image_obj = sitk.ReadImage(image_file)
    vessel_obj = sitk.ReadImage(vessel_file)
    
    out_spacing = [1.0,1.0,1.0]
    image_obj = resample_img(og_image_obj, out_spacing, is_label=False)
    vessel_obj = resample_img(vessel_obj, out_spacing, is_label=True)

    image = sitk.GetArrayFromImage(image_obj)
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

    qia_obj = sitk.GetImageFromArray(ws_branch.astype(np.uint8))
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-watershed_labels.nii.gz")
    
    props = regionprops(branch,intensity_image=bs_field)
    bcsa_area = np.zeros_like(branch.astype(np.float))
    fwhm_area = np.zeros_like(branch.astype(np.float))
    bcsa_dict = {}
    fwhm_dict = {}
    binary_png_list = []
    slice_png_list = []
    mask_png_list = []
    counter = 0
    for p in tqdm(sorted(props,key=lambda x: x.mean_intensity,reverse=True)):
        for n,coord in enumerate(p.coords[:-1]):


            # TODO:
            # vessel tangent estimated from adjacent skeleton points is flawed since skeleton is discrete.
            # skeleton needs to be smoothed/pruned/clean-up then
            # can be consider to be used as vessel centerlines and derive slice normal

            mystart = p.coords[n]
            myend = p.coords[n+1]
            slice_center = image_obj.TransformContinuousIndexToPhysicalPoint([int(mystart[2]),int(mystart[1]),int(mystart[0])])
            slice_end = image_obj.TransformContinuousIndexToPhysicalPoint([int(myend[2]),int(myend[1]),int(myend[0])])
            slice_normal = np.array(slice_end)-np.array(slice_center)

            #slice_normal = np.diff(p.coords,axis=0)
            #slice_normal = np.mean(slice_normal,axis=0)
            #print(slice_normal,slice_normalOG)
            
            slice_spacing = (1,1,1) # out of laziness, maintain voxel size at 1mm^3
            slice_radius = p.mean_intensity
            
            #print(slice_center,slice_normal,slice_spacing,slice_radius,is_label)

            ##### estimate area from cross-sectional area of vessel mask ('binary-cross-sectional-area')
            is_label = True
            factor = 3
            myslice = extract_slice(vessel_obj,slice_center,slice_normal,slice_spacing,slice_radius,is_label,factor=factor)
            myarr = sitk.GetArrayFromImage(myslice).squeeze().astype(np.uint8)

            if False:
                png_file = f'{outdir}/slice-binary-{p.label}.png'
                imageio.imsave(png_file,255*myarr)
                binary_png_list.append(png_file)
            mylabel = label(myarr)
            cidx=int(mylabel.shape[0]/2)
            myarea = np.sum(mylabel==mylabel[cidx,cidx]) # mm^2 # because slice spacing is 1x1 mm^2
            if p.label not in bcsa_dict.keys():
                bcsa_dict[p.label] = []
            bcsa_dict[p.label].append(myarea)
            bcsa_area[coord[0],coord[1],coord[2]] = myarea

            ##### estimate area using fwhm
            
            is_label = False
            factor = 3
            slice_spacing = (1,1,1)
            slice_radius_init = slice_radius
            radius_factor = 1
            myslice = extract_slice(myimg_obj,slice_center,slice_normal,slice_spacing,slice_radius,is_label,factor=factor)
            myarr = sitk.GetArrayFromImage(myslice).squeeze().astype(np.uint8)

            pred_radius, pred_mask = estimate_radius_fwhm(myarr.astype(float),slice_radius_init)
            
            myarea = np.pi * ((pred_radius*radius_factor)**2)
            if p.label not in fwhm_dict.keys():
                fwhm_dict[p.label] = []
            fwhm_dict[p.label].append(myarea)
            fwhm_area[coord[0],coord[1],coord[2]] = myarea

            if False:
                png_file = f'{outdir}/slice-{p.label}.png'
                imageio.imsave(png_file,myarr)
                slice_png_list.append(png_file)
                print(np.unique(pred_mask))
                pred_mask = np.expand_dims(pred_mask,axis=-1)
                myarr = np.expand_dims(myarr,axis=-1)
                tmp = np.concatenate([pred_mask,myarr,myarr],axis=-1)
                png_file = f'{outdir}/slice-mask-{p.label}.png'
                imageio.imsave(png_file,tmp)
                mask_png_list.append(png_file)

        if False:
            counter += 1
            if counter > 1000:
                break

    if False:
        with open(f'{outdir}/index.html','w') as f:
            for slice_png,mask_png,binary_png in zip(slice_png_list,mask_png_list,binary_png_list):
                binary_png = os.path.basename(binary_png)
                slice_png = os.path.basename(slice_png)
                mask_png = os.path.basename(mask_png)
                mystr = f'<img loading="lazy" alt="..." src="{slice_png}" width="256px" height="256px"/>\n'
                f.write(mystr)
                # fwhm
                mystr = f'<img loading="lazy" alt="..." src="{mask_png}" width="256px" height="256px"/>\n'
                f.write(mystr)
                # bcsa
                mystr = f'<img loading="lazy" alt="..." src="{binary_png}" width="256px" height="256px"/><br>\n'
                f.write(mystr)
                
        with open(f'{outdir}/index-bcsa.html','w') as f:
            for slice_png,mask_png,binary_png in zip(slice_png_list,mask_png_list,binary_png_list):
                binary_png = os.path.basename(binary_png)
                slice_png = os.path.basename(slice_png)
                mask_png = os.path.basename(mask_png)
                mystr = f'<img loading="lazy" alt="..." src="{binary_png}" width="256px" height="256px"/>\n'
                f.write(mystr)
        with open(f'{outdir}/index-fwhm.html','w') as f:
            for slice_png,mask_png,binary_png in zip(slice_png_list,mask_png_list,binary_png_list):
                binary_png = os.path.basename(binary_png)
                slice_png = os.path.basename(slice_png)
                mask_png = os.path.basename(mask_png)
                mystr = f'<img loading="lazy" alt="..." src="{mask_png}" width="256px" height="256px"/>\n'
                f.write(mystr)

    print('area...')
    # map_func = np.vectorize(lambda x: float(np.mean(bcsa_dict.get(x,[0]))))
    # area = map_func(ws_branch)
    area = watershed(vsl_mask*-1, bcsa_area.astype(np.int32), mask=vsl_mask>0)
    
    print(area.dtype)
    qia_obj = sitk.GetImageFromArray(area)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-bcsa-area.nii.gz")

    arr = area[ws_branch>0]
    print(np.min(arr),np.max(arr))
    bin_num = 20
    hist, bin_edges = np.histogram(arr,bins=bin_num,range=(0,20))
    hist = np.round(hist,2)
    hist = hist / np.sum(hist)
    hist = hist.tolist()
    hist_dict = {f'area-lt-{k}mm2-bcsa':v for k,v in zip(bin_edges[1:],hist)}
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
        sitk.WriteImage(qia_obj,f"{outdir}/debug-bcsa-pvv.nii.gz")

    qia_obj = resample_img(qia_obj, og_image_obj.GetSpacing(), is_label=True)
    sitk.WriteImage(qia_obj,f"{outdir}/bcsa-pvv.nii.gz")
    
    spacing = qia_obj.GetSpacing()
    cc_per_voxel = np.prod(spacing)*0.001
    pvv_bcsa = sitk.GetArrayFromImage(qia_obj)

    print('mip...')
    mip = (np.max(pvv_bcsa,axis=1)*80).astype(np.uint8)
    mip_file = f"{outdir}/mip_bcsa.png"
    imageio.imwrite(mip_file,mip)

    mydict = {
        'pvv5-bcsa-prct': float(np.sum(pvv_bcsa==1)/np.sum(pvv_bcsa>0)), # binary-cross-sectional-area
        'pvv10-bcsa-prct': float(np.sum(pvv_bcsa==2)/np.sum(pvv_bcsa>0)),
        'pvv10+-bcsa-prct': float(np.sum(pvv_bcsa==3)/np.sum(pvv_bcsa>0)),
        'pvv5-bcsa-cc': float(np.sum(pvv_bcsa==1)*cc_per_voxel),
        'pvv10-bcsa-cc': float(np.sum(pvv_bcsa==2)*cc_per_voxel),
        'pvv10+-bcsa-cc': float(np.sum(pvv_bcsa==3)*cc_per_voxel),
    }
    mydict.update(hist_dict)
    with open(bcsa_json_file,'w') as f:
        f.write(json.dumps(mydict, indent=4))

    print('area...')
    # map_func = np.vectorize(lambda x: float(np.mean(fwhm_dict.get(x,[0]))))
    # area = map_func(ws_branch)
    area = watershed(vsl_mask*-1, fwhm_area.astype(np.int32), mask=vsl_mask>0)

    print(area.dtype)
    qia_obj = sitk.GetImageFromArray(area)
    qia_obj.CopyInformation(image_obj)
    if debug:
        sitk.WriteImage(qia_obj,f"{outdir}/debug-fwhm-area.nii.gz")

    arr = area[ws_branch>0]
    print(np.min(arr),np.max(arr))
    hist, bin_edges = np.histogram(arr,bins=bin_num,range=(0,20))
    hist = np.round(hist,2)
    hist = hist / np.sum(hist)
    hist = hist.tolist()
    hist_dict = {f'area-lt-{k}mm2-fwhm':v for k,v in zip(bin_edges[1:],hist)}
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
        sitk.WriteImage(qia_obj,f"{outdir}/debug-fwhm-pvv.nii.gz")

    qia_obj = resample_img(qia_obj, og_image_obj.GetSpacing(), is_label=True)
    sitk.WriteImage(qia_obj,f"{outdir}/fwhm-pvv.nii.gz")
    
    spacing = qia_obj.GetSpacing()
    cc_per_voxel = np.prod(spacing)*0.001
    pvv_fwhm = sitk.GetArrayFromImage(qia_obj)

    print('mip...')
    mip = (np.max(pvv,axis=1)*80).astype(np.uint8)
    mip_file = f"{outdir}/mip_fwhm.png"
    imageio.imwrite(mip_file,mip)

    mydict = {
        'pvv5-fwhm-prct': float(np.sum(pvv_fwhm==1)/np.sum(pvv_fwhm>0)), # binary-cross-sectional-area
        'pvv10-fwhm-prct': float(np.sum(pvv_fwhm==2)/np.sum(pvv_fwhm>0)),
        'pvv10+-fwhm-prct': float(np.sum(pvv_fwhm==3)/np.sum(pvv_fwhm>0)),
        'pvv5-fwhm-cc': float(np.sum(pvv_fwhm==1)*cc_per_voxel),
        'pvv10-fwhm-cc': float(np.sum(pvv_fwhm==2)*cc_per_voxel),
        'pvv10+-fwhm-cc': float(np.sum(pvv_fwhm==3)*cc_per_voxel),
    }
    mydict.update(hist_dict)

    with open(fwhm_json_file,'w') as f:
        f.write(json.dumps(mydict, indent=4))
    print('pvv_fwhm.py done')

if __name__ == "__main__":
    image_file = sys.argv[1]
    vessel_file = sys.argv[2]
    outdir = sys.argv[3]
    debug = ast.literal_eval(sys.argv[4])
    main_fwhm(image_file,vessel_file,outdir,debug)

"""

docker run -it -u $(id -u):$(id -g) -w $PWD \
    -v /cvibraid:/cvibraid -v /radraid:/radraid \
    pangyuteng/ml:latest bash

python pvv_fwhm.py img.nii.gz wasserthal.nii.gz outdir-fwhm True

"""