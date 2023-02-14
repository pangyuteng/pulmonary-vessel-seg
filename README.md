# pulmonary-vessel-seg

Replicating & archiving a few methods for polumonary vessel segmentation

+ `methods/wasserthal-2022`
```
Wasserthal, Jakob, et al. "TotalSegmentator: robust segmentation of 104 anatomical structures in CT images." arXiv preprint arXiv:2208.05868 (2022).
https://arxiv.org/abs/2208.05868
repo: https://github.com/wasserth/TotalSegmentator
```

+ `methods/poletti-2022`
```
Poletti, Julien, et al. "Automated lung vessel segmentation reveals blood vessel volume redistribution in viral pneumonia." European Journal of Radiology 150 (2022): 110259.
url: https://www.sciencedirect.com/science/article/pii/S0720048X22001097
repo url: https://github.com/fsc-mib/travel
```

+ `methods/knopczynski-2016`
```
Konopczyński, Tomasz, et al. "Automated multiscale 3D feature learning for vessels segmentation in Thorax CT images." 2016 IEEE Nuclear Science Symposium, Medical Imaging Conference and Room-Temperature Semiconductor Detector Workshop (NSS/MIC/RTSD). IEEE, 2016.
url: https://arxiv.org/abs/1901.01562
repo url: https://github.com/konopczynski/Vessel3DDL
dockerized, py3 friendly: https://github.com/pangyuteng/Vessel3DDL/tree/py3
```

+ `methods/bianca-2012`
```
Lassen, Bianca, et al. "Automatic segmentation of the pulmonary lobes from chest CT scans based on fissures, vessels, and bronchi." IEEE transactions on medical imaging 32.2 (2012): 210-222.
url: https://pubmed.ncbi.nlm.nih.gov/23014712
repo: https://github.com/Connor323/Lung-Lobes-Segmentation-in-CT-Scans/blob/master/vessel_segment.py
dockerized: https://github.com/pangyuteng/Lung-Lobes-Segmentation-in-CT-Scans
```

+ `methods/frangi-1998`
```
Frangi, Alejandro F., et al. "Multiscale vessel enhancement filtering." International conference on medical image computing and computer-assisted intervention. Springer, Berlin, Heidelberg, 1998.
url: https://link.springer.com/chapter/10.1007/bfb0056195
repo url: https://github.com/pangyuteng/frangi-filter

Zhou, Chuan, et al. "Automatic multiscale enhancement and segmentation of pulmonary vessels in CT pulmonary angiography images for CAD applications." Medical physics 34.12 (2007): 4567-4577.
url: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2742232
repo url: na

```

#### maybe todos

+ vessel seg with graphcut
+ a/v seperation

#### GUI 1/2 - will give it a try:

+ Slicer3D+VTMK
    + https://lassoan.github.io/SlicerSegmentationRecipes/VesselSegmentationBySubtraction/    
    + https://www.youtube.com/watch?v=caEuwJ7pCWs
    + https://www.youtube.com/watch?v=wS6-4dwZCfo

+ (minimal doc) Angicart or Angicart++
    + https://vsavage.faculty.biomath.ucla.edu/Code/HTML/indexangic.html#beadeveloper
    + https://github.com/jocelynshen/angicart-c
    + https://github.com/andersonju9797/AngicartCPlusPlus
    + https://vsavage.faculty.biomath.ucla.edu/Code/HTML/indexangicplusplus.html

#### GUI 2/2 - i have not looked into this:

+ (not free) Inobiec "vessel tree segmentation tool"
    + https://www.youtube.com/watch?v=RsfSVFGVVLc
    + https://inobitec.com/eng/manual/dicomviewer/segmentation/edit-segmented-structure/#x106-2280006.4.4

+ (may not be user friendly?) VTMK
    + http://www.vmtk.org/documentation/screenshots.html
    + probably not designed for complex structures, such as plumonary vessels?
