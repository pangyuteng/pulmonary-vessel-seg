
# what is BV5, BV5-10, BV10+ ??

# published methodologies can be lumped to the below few methods.

+ area from binary vessel masks - computed from axial slices. (for references see https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10023743)

+ distance transform from binary vessel mask (ref https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10023743 https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7308498 )

+ compute cross-sectional area of binary vessel mask (ref https://pubmed.ncbi.nlm.nih.gov/35334245)

+ radius can be estimated using Frangi's multi-scale vesselness filter (ref https://link.springer.com/chapter/10.1007/bfb0056195 )

+ scale-space-particle (ref https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3670102)

# using Vessel12 dataset we compute Blood-Volume-X BVX or Pulmonary-Vessel-like-Volume-X (PVVX)

```
mean pvv5-dt-prct 83.35 prct pvv5-frangi-prct 78.87 prct
mean pvv10-dt-prct 9.91 prct pvv10-frangi-prct 11.18 prct
mean pvv10+-dt-prct 6.74 prct pvv10+-frangi-prct 9.95 prct

mean pvv5-dt-cc 276.19 cc pvv5-frangi-cc 259.07 cc
mean pvv10-dt-cc 32.33 cc pvv10-frangi-cc 36.2 cc
mean pvv10+-dt-cc 22.3 cc pvv10+-frangi-cc 32.85 cc

n=23
```

<a href="test/viz.md">visualization of the resulting PVVX for Vessel12 dataset see </a>


# published BV values

    ### keywords used:

        + "bv5 bv10 pulmonary"
        + "blood vessel bv5 bv10"
        + "pvv5 pulmonary"

    ### values:

+ John, Joyce, et al. "Pulmonary vessel volume in idiopathic pulmonary fibrosis compared with healthy controls aged> 50 years." Scientific Reports 13.1 (2023): 4422.

https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10023743

BV5/TBV: 2% , BV5-10/TBV:11% , BV>10/TBV:85% ( control n=59 ) ??? OUTLIER VALUE!!

method summary: distance transform from binary vessel mask

+ Lins, Muriel, et al. "Assessment of small pulmonary blood vessels in COVID-19 patients using HRCT." Academic radiology 27.10 (2020): 1449-1455.

https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7381940

BV5/TBV: 57% , BV5-10/TBV:20% , BV>10/TBV:23% ( normal n=107 )

method summary: compute cross-sectional area of binary vessel mask

+ Morris, Michael F., et al. "Altered pulmonary blood volume distribution as a biomarker for predicting outcomes in COVID-19 disease." European Respiratory Journal 58.3 (2021).

BV5/TBV: 30%, BV5-10/TBV: 25%, BV10/TBV: 45% (covid negative, n=195)

method summary: compute cross-sectional area of binary vessel mask

+ Poletti, Julien, et al. "Automated lung vessel segmentation reveals blood vessel volume redistribution in viral pneumonia." European Journal of Radiology 150 (2022): 110259.

https://pubmed.ncbi.nlm.nih.gov/35334245

BV5/TBV: 18.4%, BV5-10/TBV: 70.8%, BV10/TBV: 10.8% (normal, n=248)

method summary: compute cross-sectional area of binary vessel mask

+ Estépar, Raúl San José, et al. "Computed tomographic measures of pulmonary vascular morphology in smokers and their clinical implications." American journal of respiratory and critical care medicine 188.2 (2013): 231-239.

https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3778757

RLung BV5/TBV: 58% (n=85)

method summary: scale-space-particle (Chest Imaging Platform)

+ Ash, Samuel Y., et al. "Pruning of the pulmonary vasculature in asthma. The Severe Asthma Research Program (SARP) cohort." American journal of respiratory and critical care medicine 198.1 (2018): 39-50.

https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6034125

BV<=5/TBV: 62% , BV<=10/TBV 74%  ( normal n=237)

method summary: scale-space-particle (Chest Imaging Platform)

+ Rahaghi, F. N., et al. "Pulmonary vascular morphology as an imaging biomarker in chronic thromboembolic pulmonary hypertension." Pulmonary circulation 6.1 (2016): 70-81.

https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4860553

BV5/TBV 58% , BV>10/TBV 28% (normal, N = 15)

method summary: scale-space-particle (Chest Imaging Platform)


+ Shimizu, Kaoruko, et al. "Relationships of computed tomography-based small vessel indices of the lungs with ventilation heterogeneity and high transfer coefficients in non-smokers with asthma." Frontiers in physiology 14 (2023): 1137603.

https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10014854

did not report BV5/TBV, reported BV5 ~125 mL (non-smokers n=117)



+ "Automatic pulmonary vessel segmentation on noncontrast chest CT: deep learning algorithm developed using spatiotemporally matched virtual noncontrast images and low-keV contrast-enhanced vessel maps"

    + PVV5 63% (Gold 1)
# Blood Volume (BVx) algos

+ scale-space-particles

```
San Jose Estepar RRJ, Krissian K, Schultz T, Washko GR, Kindlmann GL.Computational vascular morphometry for the assessment of pulmonary vascular disease based on scale-space particles. In: Biomedical Imaging (ISBI), 2012 9th IEEE International Symposium on. IEEE; 2012. pp. 1479–1482
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3670102

"The particle system solution is computed iteratively to minimize the system energy, which is a sum of inter-particle energy and energy associated with a particle’s location within the image domain. The inter-particle energy is a quartic polynomial with a tunable potential well, chosen to quickly induce regular sampling. The potential well also serves the purpose of making particle population control (adding particles to fill gaps in the vessel sampling) part of the same over-all energy minimization that moves particles into a uniform sampling. Particles are removed when the strength of the ridge line feature (as quantified by the middle Hessian eigenvalue λ2) falls below a pre-specified threshold that depends on image contrast. Following the general guidelines of [6], particle system computation proceeds in three steps: densely and uniformly sampling the two-dimensional manifold swept out in scale-space by the ridge lines, moving points to the scale of maximal feature strength, and then redistributing points to create a uniform vessel sampling."

https://pubmed.ncbi.nlm.nih.gov/23656466
https://www.atsjournals.org/doi/full/10.1164/rccm.201301-0162OC
https://www.atsjournals.org/doi/suppl/10.1164/rccm.201301-0162OC?role=tab
http://people.cs.uchicago.edu/~glk/ssp

https://github.com/acil-bwh/ChestImagingPlatform/issues/34

docker pull acilbwh/chestimagingplatform:1.5


```

+ distance transform

```

https://www.nature.com/articles/s41598-023-31470-6

pvv_dist.py

```


+ hessian vesselness 
```
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7381940

pvv_frangi.py

```





# misc notes

```



area = pi*r^2

area 5 mm^2 , r = np.sqrt(5/np.pi) = 1.26 mm

area 10 mm^2 , r = np.sqrt(10/np.pi) = 1.78

if voxel width is .6 mm^3  (BV5)

|1|   radius ~ 0.5*0.6  = 0.3mm  (BV5)

|1|1| radius ~ 1*0.6 = 0.6 mm  (BV5)

|1|2|1| radius ~ 1.5*0.6 = 0.9 mm (BV5)

|1|2|3|2|1| radius ~ 2.5*0.6 = 1.5 mm (BV5-10)

|1|2|3|4|3|2|1| radius ~ 3.5*0.6 = 2.1 mm (BV10+)


--

|1|   radius ~ 1*0.6   --> 

|1|1| radius ~ 1*0.6 = .6mm (BV5)

|1|2|1| radius ~ 2*0.6 = 1.2 mm (BV5)

|1|2|3|2|1| radius ~ 3*0.6 = 1.8 (BV5-10)

|1|2|3|4|3|2|1| radius ~ 4*0.6 = 2.4 mm (BV10+)




```

```

alternative skeletonization method

https://github.com/amy-tabb/CurveSkel-Tabb-Medeiros

https://github.com/amy-tabb/CurveSkel-Tabb-Medeiros-2018

```
