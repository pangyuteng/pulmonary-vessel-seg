import os
import sys
import ast
import logging
logger = logging.getLogger(__file__)

import vtk
import numpy as np
import SimpleITK as sitk

"""
import imageio
def generate_mip(ct_data, mask_data, file_out):

    ct_data = ct_data.clip(-1000,1000)
    ct_mip = np.sum(ct_data,axis=-2)
    mymin,mymax = np.min(ct_mip),np.max(ct_mip)
    ct_mip = ((ct_mip-mymin)/(mymax-mymin)).clip(0,1)*255

    mask_mip = (np.max(mask_data,axis=-2)/104).clip(0,1)*255

    mythumbnail = np.concatenate([ct_mip,mask_mip],axis=1)
    mythumbnail = mythumbnail.astype(np.uint8)

    imageio.imwrite(file_out,mythumbnail)
"""

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
    else:
        raise NotImplementedError()

"""
python viz_utils.py downsample img.nii.gz img-downsampled.nii.gz False
python viz_utils.py downsample lung_vessels.nii.gz lung_vessels-downsampled.nii.gz True
python viz_utils.py stl lung_vessels-downsampled.nii.gz lung_vessels-downsampled.stl
python viz_utils.py stl lung_vessels.nii.gz lung_vessels.stl

"""