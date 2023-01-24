import sys
import SimpleITK as sitk

lung_file = sys.argv[1]
vessel_file = sys.argv[2]

lung_obj = sitk.ReadImage(lung_file)
vsl_obj = sitk.ReadImage(vessel_file)

lung = sitk.GetArrayFromImage(lung_obj)
vsl = sitk.GetArrayFromImage(vsl_obj)    

vsl[lung==0]=0
vsl_obj = sitk.GetArrayFromImage(vsl)
vsl_obj.CopyInformation(lung_obj)

sitk.WriteImage(vsl_obj,vessel_file)
