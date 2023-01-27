import os
import sys
import ast
import logging
logger = logging.getLogger(__file__)

import imageio
import numpy as np
import SimpleITK as sitk
import vtk

def generate_thumbnail(image_file, out_png_file, mask_file=None,min_max_val=None,axis_list=[1],flip=None):
    if image_file:
        img_obj = sitk.ReadImage(image_file)
        image = sitk.GetArrayFromImage(img_obj)
        if flip:
            image = np.flip(image,axis=flip)
    if mask_file:
        mask_obj = sitk.ReadImage(mask_file)
        mask = sitk.GetArrayFromImage(mask_obj)
        if flip:
            mask = np.flip(mask,axis=flip)
    else:
        mask = None

    if min_max_val is not None:
        min_val, max_val = min_max_val
        image = image.clip(min_val,max_val)
    else:
        min_val, max_val = np.min(image),np.max(image)

    image = ((image-min_val)/(max_val-min_val)).clip(0,1)
    if mask is not None:
        image[mask==0]=0

    mylist = []
    for axis in axis_list:
        mip = np.sum(image,axis=axis)
        min_val, max_val = np.min(mip),np.max(mip)
        mip = mip.squeeze()
        mip = (255.*(mip-min_val)/(max_val-min_val)).clip(0,255)
        mylist.append(mip)

    mythumbnail = np.concatenate(mylist,axis=1)
    mythumbnail = mythumbnail.astype(np.uint8)

    imageio.imwrite(out_png_file,mythumbnail)

# MIN_VAL,MAX_VAL = -1000, 1000 # all purpose
MIN_VAL,MAX_VAL = -1200, 200 # lungs ~W:1400 L:-500

def gen_downsample(input_file, output_file, 
    out_spacing=[1.0, 1.0, 10.0], is_label=False,use_compression=True):
    
    reader = sitk.ImageFileReader()
    reader.SetFileName(input_file)
    source_img = reader.Execute()

    original_spacing = source_img.GetSpacing()
    original_size = source_img.GetSize()

    out_size = [
        int(np.round(original_size[0] * (original_spacing[0] / out_spacing[0]))),
        int(np.round(original_size[1] * (original_spacing[1] / out_spacing[1]))),
        int(np.round(original_size[2] * (original_spacing[2] / out_spacing[2])))]

    resample = sitk.ResampleImageFilter()
    resample.SetOutputSpacing(out_spacing)
    resample.SetSize(out_size)
    resample.SetOutputDirection(source_img.GetDirection())
    resample.SetOutputOrigin(source_img.GetOrigin())
    resample.SetTransform(sitk.Transform())
    print(source_img.GetPixelIDValue())
    resample.SetDefaultPixelValue(source_img.GetPixelIDValue())

    if is_label:
        resample.SetInterpolator(sitk.sitkNearestNeighbor)
    else:
        resample.SetInterpolator(sitk.sitkBSpline)

    resampled_img = resample.Execute(source_img)
    writer = sitk.ImageFileWriter()    
    writer.SetFileName(output_file)
    writer.SetUseCompression(use_compression)
    writer.Execute(resampled_img)
    
def gen_stl(input_file,output_file):
    reader = vtk.vtkNIFTIImageReader()
    reader.SetFileName(input_file)
    reader.Update()

    threshold = vtk.vtkImageThreshold ()
    threshold.SetInputConnection(reader.GetOutputPort())
    threshold.ThresholdByLower(0)
    threshold.ReplaceInOn()
    threshold.SetInValue(1)
    threshold.ReplaceOutOn()
    threshold.SetOutValue(0)
    threshold.Update()

    # https://kitware.github.io/vtk-examples/site/Cxx/Modelling/SmoothDiscreteMarchingCubes
    dmc = vtk.vtkDiscreteMarchingCubes()
    dmc.SetInputConnection(threshold.GetOutputPort())
    dmc.GenerateValues(1, 1, 1)
    dmc.Update()

    logger.debug('smoothing polydata')
    smoothingIterations = 1
    passBand = 0.001
    featureAngle = 120.0
    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInputConnection(dmc.GetOutputPort())
    smoother.SetNumberOfIterations(smoothingIterations)
    smoother.BoundarySmoothingOff()
    smoother.FeatureEdgeSmoothingOff()
    smoother.SetFeatureAngle(featureAngle)
    smoother.SetPassBand(passBand)
    smoother.NonManifoldSmoothingOn()
    smoother.NormalizeCoordinatesOn()
    smoother.Update()

    reduction = 0.9
    decimate = vtk.vtkQuadricDecimation()
    decimate.SetInputConnection(smoother.GetOutputPort())
    decimate.SetTargetReduction(reduction)
    decimate.Update()

    logger.debug('computing normal')
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(decimate.GetOutputPort())
    normals.Update()
    
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    mapper.Update()

    if output_file.endswith(".vtk"):
        writer = vtk.vtkPolyDataWriter()
        writer.SetFileName(output_file)
        writer.SetInputData(mapper.GetInput())
        writer.Write()
    elif output_file.endswith(".stl"):
        writer = vtk.vtkSTLWriter()
        writer.SetFileName(output_file)
        writer.SetInputData(mapper.GetInput())
        writer.Write()
    else:
        raise NotImplementedError()

    print(input_file,output_file)

if __name__ == "__main__":
    action = sys.argv[1]
    if action == 'downsample':
        input_nifti_file = sys.argv[2]
        output_nifti_file = sys.argv[3]
        is_label = ast.literal_eval(sys.argv[4])
        gen_downsample(input_nifti_file,output_nifti_file,is_label=is_label)
    elif action == 'downsample222':
        input_nifti_file = sys.argv[2]
        output_nifti_file = sys.argv[3]
        is_label = ast.literal_eval(sys.argv[4])
        gen_downsample(input_nifti_file,output_nifti_file,is_label=is_label,out_spacing=[2,2,2])
    elif action == 'stl':
        input_nifti_file = sys.argv[2]
        output_stl_file = sys.argv[3]
        gen_stl(input_nifti_file,output_stl_file)
    elif action == 'thumbnail':
        image_file = sys.argv[2]
        mask_file = sys.argv[3]
        flip = ast.literal_eval(sys.argv[4])
        out_png_file = sys.argv[5]
        generate_thumbnail(image_file, out_png_file, mask_file=mask_file,min_max_val=None,axis_list=[1],flip=flip)
    else:
        raise NotImplementedError()


    
"""
python viz_utils.py downsample img.nii.gz img-downsampled.nii.gz False
python viz_utils.py downsample lung_vessels.nii.gz lung_vessels-downsampled.nii.gz True
python viz_utils.py stl lung_vessels-downsampled.nii.gz lung_vessels-downsampled.stl
python viz_utils.py stl lung_vessels.nii.gz lung_vessels.stl

"""