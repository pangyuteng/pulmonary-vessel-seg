
# what is BV5, BV5-10, BV10+ ??



# methodologies.


# per methods - published data compared to out method...




# actually compute





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

"Pulmonary vessels were automatically identified, segmented, and measured. Total blood vessel volume (TBV) and the aggregate vessel volume for vessels less than 5 mm(2) (BV5) were calculated for all lobes. The lobe-specific BV5 measures were normalized to the TBV of that lobe and the nonvascular tissue volume (BV5/T(issue)V) to calculate lobe-specific BV5/TBV and BV5/T(issue)V ratios"  https://pubmed.ncbi.nlm.nih.gov/23656466

# published BV values

### keywords: "bv5 bv10 pulmonary"

+ "Assessment of small pulmonary blood vessels in COVID-19 patients using HRCT"

    BV5/TBV: 57% , BV5-10/TBV:20% , BV>10/TBV:23% ( normal )

+ "Pruning of the pulmonary vasculature in asthma. The Severe Asthma Research Program (SARP) cohort"
 
    BV<=5/TBV: 62% , BV<=10/TBV 74% ()  ( normal )

+ "Pulmonary Vascular Morphology as an Imaging Biomarker in Chronic Thromboembolic Pulmonary Hypertension"

    BV5/TBV 58% , BV>10/TBV 0.28% (normal)

+ "Altered pulmonary blood volume distribution as a biomarker for predicting outcomes in COVID-19 disease"

    + BV5%: 30%, BV5-10%: 25%, BV10%: 45% (covid negative)

### keywords: "pvv5 pulmonary"

+ "Mortality prediction in idiopathic pulmonary fibrosis: evaluation of computer-based CT analysis with conventional severity measures"

    + not reported, using it as a factor.

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

https://aapm.onlinelibrary.wiley.com/doi/pdf/10.1002/mp.13659

pvv_dist.py

```


+ hessian vesselness 
```
https://pubmed.ncbi.nlm.nih.gov/32741657

pvv_frangi.py

```


https://github.com/amy-tabb/CurveSkel-Tabb-Medeiros
https://github.com/amy-tabb/CurveSkel-Tabb-Medeiros-2018