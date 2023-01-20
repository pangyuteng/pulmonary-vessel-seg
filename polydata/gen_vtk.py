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

    # https://kitware.github.io/vtk-examples/site/Cxx/Modelling/SmoothDiscreteMarchingCubes
    dmc = vtk.vtkDiscreteMarchingCubes()
    dmc.SetInputConnection(threshold.GetOutputPort())
    dmc.GenerateValues(1, 1, 1)
    dmc.Update()

    print('smoothing polydata')
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

    print('computing normal')
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(decimate.GetOutputPort())
    normals.Update()
    
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())
    #lut = vtk.vtkLookupTable()
    #mapper.SetLookupTable(lut)
    #mapper.SetScalarRange(0, lut.GetNumberOfColors())
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
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    main(input_file,output_file)




"""
from vtk.util.colors import salmon
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
print(position,focal_point,view_up,)


"""
