

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
https://aapm.onlinelibrary.wiley.com/doi/pdf/10.1002/mp.13659


```


+ hessian vesselness 
```
https://pubmed.ncbi.nlm.nih.gov/32741657
```