import sys
import numpy as np
from scipy import ndimage
import SimpleITK as sitk

lung_file = sys.argv[1]
vessel_file = sys.argv[2]

lung_obj = sitk.ReadImage(lung_file)
vsl_obj = sitk.ReadImage(vessel_file)

lung = sitk.GetArrayFromImage(lung_obj)
vsl = sitk.GetArrayFromImage(vsl_obj)    

lung = ndimage.binary_erosion(lung,iterations=5).astype(np.uint8)
vsl[lung==0]=0
vsl = vsl.astype(np.uint8)
vsl_obj = sitk.GetImageFromArray(vsl)
vsl_obj.CopyInformation(lung_obj)

sitk.WriteImage(vsl_obj,vessel_file)
