import sys
import vtk

def main(input_file,output_file):
    
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

    dmc = vtk.vtkDiscreteMarchingCubes()
    dmc.SetInputConnection(threshold.GetOutputPort())
    dmc.GenerateValues(1, 1, 1)
    dmc.Update()


    #vtkNew<vtkDiscreteMarchingCubes> discrete;
    #discrete->SetInputData(blob);
    #discrete->GenerateValues(n, 1, n);

    smoothingIterations = 15;
    passBand = 0.001;
    featureAngle = 120.0;
    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInputConnection()
  vtkNew<vtkWindowedSincPolyDataFilter> smoother;
  smoother->SetInputConnection(discrete->GetOutputPort());
  smoother->SetNumberOfIterations(smoothingIterations);
  smoother->BoundarySmoothingOff();
  smoother->FeatureEdgeSmoothingOff();
  smoother->SetFeatureAngle(featureAngle);
  smoother->SetPassBand(passBand);
  smoother->NonManifoldSmoothingOn();
  smoother->NormalizeCoordinatesOn();
  smoother->Update();

  
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(smoother.GetOutputPort())
    #vtkSmartPointer<vtkLookupTable> lut = MakeColors(n);
    #mapper->SetLookupTable(lut);
    #mapper->SetScalarRange(0, lut->GetNumberOfColors());
    mapper.Update()

    # >> >   mapper->SetInputConnection(aPlane->GetOutputPort());
    # >> >   mapper->SetScalarRange(0, tableSize - 1);
    # >> >   mapper->SetLookupTable(lut);
    # >> >   mapper->Update();
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileName(output_file)
    writer.SetInputData(mapper.GetInput())
    writer.Write()

    print(input_file,output_file)

if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    main(input_file,output_file)

"""
import sys
import numpy as np
import vtk
from vtk.util.colors import salmon


reader = vtk.vtkNIFTIImageReader()
reader.SetFileName('example.nii.gz')
reader.Update()

threshold = vtk.vtkImageThreshold ()
threshold.SetInputConnection(reader.GetOutputPort())
threshold.ThresholdByLower(50)  #th
threshold.ReplaceInOn()
threshold.SetInValue(0)  # set all values below th to 0
threshold.ReplaceOutOn()
threshold.SetOutValue(1)  # set all values above th to 1
threshold.Update()

'''
voi = vtk.vtkExtractVOI()
voi.SetInputConnection(threshold.GetOutputPort()) 
voi.SetVOI(0,95, 0,95, 0,59)
voi.SetSampleRate(1,1,1)
#voi.SetSampleRate(3,3,3)
voi.Update()#necessary for GetScalarRange()
srange= voi.GetOutput().GetScalarRange()#needs Update() before!
print("Range", srange)
'''

dmc = vtk.vtkDiscreteMarchingCubes()
dmc.SetInputConnection(threshold.GetOutputPort())
#dmc.SetInputConnection(voi.GetOutputPort())
dmc.GenerateValues(1, 1, 1)
dmc.Update()

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(dmc.GetOutputPort())
mapper.Update()

actor = vtk.vtkActor()
actor.SetMapper(mapper)
mapper.ScalarVisibilityOff()

actor.GetProperty().SetColor(salmon)
actor.GetProperty().SetOpacity(0.5)
actor.RotateX(90)

renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetOffScreenRendering(1)
renderWindow.AddRenderer(renderer)

renderer.AddActor(actor)
renderer.SetBackground(1.0, 1.0, 1.0)

center = actor.GetCenter()

camera = renderer.MakeCamera()
camera.SetPosition(0,0,800)
camera.SetFocalPoint(center)

renderer.SetActiveCamera(camera)
renderWindow.Render()

focal_point = camera.GetFocalPoint()
view_up = camera.GetViewUp()
position = camera.GetPosition() 

axis = [0,0,0]
axis[0] = -1*camera.GetViewTransformMatrix().GetElement(0,0)
axis[1] = -1*camera.GetViewTransformMatrix().GetElement(0,1)
axis[2] = -1*camera.GetViewTransformMatrix().GetElement(0,2)

print(position,focal_point,view_up,)

print(camera.GetViewTransformMatrix())
print(camera.GetViewTransformMatrix().GetElement(0,0))
print(camera.GetViewTransformMatrix().GetElement(0,1))
print(camera.GetViewTransformMatrix().GetElement(0,2))

"""