#
# why convert vtk to nifti?
# i want to compare vessel-segmentation of other methods 
# with estapar's scale-scale-particles output.
# and also figure out what "scale" in the vtk means.
# 
import sys
import numpy as np
import vtk
import SimpleITK as sitk

nrrd_io = "NrrdImageIO"
input_nrrd_file = sys.argv[1]
input_vtk_file = sys.argv[2]

reader = sitk.ImageFileReader()
reader.SetImageIO(nrrd_io)
reader.SetFileName(input_nrrd_file)
img_obj = reader.Execute()
#print(dir(img_obj))

reader = vtk.vtkPolyDataReader()
reader.SetFileName(input_vtk_file)
reader.ReadAllVectorsOn()
reader.ReadAllScalarsOn()
reader.Update()
polydata = reader.GetOutput()

# print(dir(polydata))
# for idx in range(polydata.GetNumberOfCells()):
#     pts = polydata.GetCell(idx).GetPoints()
#     print(polydata.GetPointData())
#     #print(dir(pts))
#     np_pts = np.array([pts.GetPoint(x) for x in range(pts.GetNumberOfPoints())])
#     print(np_pts)
#     break
    

'''

python vtk2nifti.py \
    /radraid/pteng/tmp/scale-space-particles/vessel12/01/CT.nrrd \
    /radraid/pteng/tmp/scale-space-particles/vessel12/01/particles.vtk_wholeLungVesselParticles.vtk

'''
