# Checklist to start running CORDEX-CORE WRF simulations

This guide describes how to prepare and run WPS and WRF for evaluation, historical, and projection
simulations for the CORDEX-CORE workflow. 


## WPS 
   - [ ] Obtain the WPS code ( Note: The v4.6.0-devel branch already contains the required SST update)
Clone the CORDEX WPS repository (includes the SST update): 

```
git clone --recurse-submodules -b v4.6.0-devel https://github.com/CORDEX-WRF-community/WPS.git
```

- [ ] Download geo_em files from the links given in the [CORDEX repository](https://github.com/CORDEX-WRF-community/cordex-core-cmip6/blob/main/README.md)

### Evaluation Runs 
- [ ] Download ERA5 data 
Download ERA5 single‐level and pressure-level data from the Copernicus Climate Data Store [CDS](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=download)
- [ ] Prepare Vtable 
Link the appropriate [Vtable](https://github.com/CORDEX-WRF-community/WPS/blob/v4.5-devel/ungrib/Variable_Tables/Vtable.ERA-interim.pl): 

```
ln -s ./ungrib/Variable_Tables/Vtable.ERA-interim.pl Vtable
```
- [ ] Run WPS components ```ungrib.exe``` and ```metgrid.exe```

- [ ] Adjust lake surface temperature using the script
[tavg_sfc_with_nco.py](https://github.com/CORDEX-WRF-community/cordex-core-cmip6/blob/main/util/tavg_sfc_with_nco.py):

```
python tavg_sfc_with_nco.py "met_em*d01*"
```

### Historical and Projection Runs
- [ ] GCM GRIB data for the requested GCMs are provided by Melissa Bukovsky and the NCAR group. 
Data is available via [Globus Connect Server](https://docs.globus.org/globus-connect-server/v5/)
Request credentials from Melissa Bukovsky. ungrib 
- [ ] Link the appropriate [METGRID.TBL](https://github.com/CORDEX-WRF-community/WPS/tree/v4.6.0-devel/metgrid) for your GCM (for EC-Earth GCM to be uploaded).
- [ ] Run ```metgrid.exe```
- [ ] Adjust lake surface temperature using the script
[tavg_sfc_with_nco.py](https://github.com/CORDEX-WRF-community/cordex-core-cmip6/blob/main/util/tavg_sfc_with_nco.py):

```
python tavg_sfc_with_nco.py "met_em*d01*"
```


- [ ] ⚠️ Important: To ensure correct surface pressure handling, add the following line to the ```&domains``` section of
```namelist.input``` before running ```real.exe``` (this is not necessary for the evaluation run): 

```
sfcp_to_sfcp = .true.,
```
 ## WRF 
- [ ] Clone the WRF v4.6.1.1 code from the CORDEX WRF repository: 

```
git clone --recurse-submodules -b v4.6.1.1-devel https://github.com/CORDEX-WRF-community/WRF.git
```
- [ ] Adjust the calendar to that of your driving GCM before compiling the code
- [ ] Place IO fields Include/exclude file (Add/Delete variables if needed) in you run directory: 
[iofields.txt](https://github.com/CORDEX-WRF-community/cordex-core-cmip6/blob/main/setting/iofields.txt)
- [ ] Link the GHG file corresponding to your driving GCM scenario.
      Example for SSP3‐7.0:
```
ln -s CAMtr_volume_mixing_ratio.SSP370 CAMtr_volume_mixing_ratio
```
- [ ] Add aerosol files corresponding to you driving GCM (e.g., AOD_d01). Tool to genereate the files can be downloaded from [here](https://github.com/AEI-CORDyS/aerosols4wrf). Note that the start date of the AOD file should correspond to the start date of your simuation.

```
auxinput15_inname = 'AOD_d01'
```
- [ ] Edit MPTABLE.TBL and match the CO2 concentration to the one in your CAMtr_volume_mixing_ratio for the simulation year (Check [here](https://github.com/CORDEX-WRF-community/euro-cordex-cmip6/issues/1) for more details). 

- [ ] Run ```wrf.exe```
