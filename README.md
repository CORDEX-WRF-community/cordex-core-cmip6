# WRF contribution to CORDEX-CORE-CMIP6

This is the CORDEX-CORE-CMIP6 central repository for the WRF model.
By now, check the [current plans and status](https://cordex-wrf-community.github.io/cordex-core-cmip6/CORDEX-CORE-CMIP6_WRF_status.html).
Check [here](https://wcrp-cordex.github.io/simulation-status/CORDEX_CMIP6_status_by_experiment.html#All-CORDEX-CORE) the status of the whole CORDEX-CORE-CMIP6 experiment.

## Model configuration
Several major points common to the WRF runs across all CORDEX-CORE-CMIP6 domains:

 - The model resolution is ~12 km, and coarser only for larger domains.

 - The urban parameterization scheme switched on in all the runs if possible.

 - Spectral nudging is recommended for larger domains.

 - Aerosols will be read from the input file with data extracted from the forcing models. The tool [aerosols4wrf](https://github.com/AEI-CORDyS/aerosols4wrf) is available to use for creating aerosol (AOD) files. The manual and contact information for support are provided at the same link.

...

