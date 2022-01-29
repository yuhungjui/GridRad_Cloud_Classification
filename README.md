# GridRad dBZ Cloud Type (Storm Mode) Classification

This project classifies the cloud type based on the 3D reflectivity from [GridRad dataset](http://gridrad.org/index.html).

The cloud type classification is based on the methodology in [Houze et al. 2015](https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2015RG000488) which identifies four types of clouds from the TRMM satellite reflectivity, including Deep convective cores (DCCs), Wide convective cores (WCCs), Deep and Wide convective cores (DWCCs), and Broad stratiform regions (BSRs).

Last update - 20220128 - Hungjui Yu

## Specific Dependencies:

* netcdf4
* Numpy
* xarray
* pandas

## Cloud Type (Storm Mode) Classification Process Flow Chart:

![](https://github.com/yuhungjui/GridRad_Cloud_Classification/blob/main/Storm_Mode_Flow.png)
