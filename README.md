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

 - geo_em files for [AFR-18](https://meteo.unican.es/work/CORDEX-CORE-CMIP6/cordex-core_AFR-18_geo_ems.tar.gz), [WAS-18](https://meteo.unican.es/work/CORDEX-CORE-CMIP6/cordex-core_WAS-18_geo_ems.tar.gz), and [SAM-12](https://meteo.unican.es/work/CORDEX-CORE-CMIP6/cordex-core_SAM-12_geo_ems.tar.gz) are prepared with MODIS LULC, ovelayed with LCZ (geo_em.d01_{domain}_LCZ_params.nc). These geo_em files also unclude [HWSD](https://www.wdc-climate.de/ui/entry?acronym=WRF_NOAH_HWSD_world_TOP_ST_v121) top soil texture, and monthly LAI based on 15-year (1999-2014) montly means of LAI data from SPOT sattelite.
 - The geo_em files for [AFR-18](https://meteo.unican.es/work/CORDEX-CORE-CMIP6/cordex-core_AFR-18_geo_ems.tar.gz), [WAS-18](https://meteo.unican.es/work/CORDEX-CORE-CMIP6/cordex-core_WAS-18_geo_ems.tar.gz), and [SAM-12](https://meteo.unican.es/work/CORDEX-CORE-CMIP6/cordex-core_SAM-12_geo_ems.tar.gz) are prepared using MODIS LULC and overlaid with LCZ (geo_em.d01_{domain}_LCZ_params.nc). These geo_em files also include [HWSD](https://www.wdc-climate.de/ui/entry?acronym=WRF_NOAH_HWSD_world_TOP_ST_v121) topsoil texture and monthly LAI based on 15-year (1999–2014) monthly averages of LAI data from SPOT satellite observations downloaded from [CDS](https://cds.climate.copernicus.eu/datasets/satellite-lai-fapar?tab=download).

...

