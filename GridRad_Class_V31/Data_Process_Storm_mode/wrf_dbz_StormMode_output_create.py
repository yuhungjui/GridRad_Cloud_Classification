
# ## Storm Mode/Precipitation (Cloud) Type Classification Output for 3D Reflectivity from derived dBZ of WRF Simulations.
# 
# Storm Mode Classification starts from the Composite dBZ (Rain Area) identification, and add another mode: 
# Ordinary (Non-Deep) Convective Cores (OCC) to represent shallow conveciton.
# Output the Storm Mode Classification information (1:DCC; 2:OCC; 3:WCC; 4:DWCC; 5:BSR) to CONUS dBZ data.
# 
# For [High Resolution WRF Simulations of the Current and Future Climate of North America]
# (https://rda.ucar.edu/datasets/ds612.0/).
#
# How to run:
# python wrf_dbz_StormMode_output.py [CTRL3D/PGW3D] [start_date_yyyymmdd] [end_date_yyyymmdd]
# 
# Hungjui Yu 20211105


import sys
import time
import datetime as dt
import pytz
from netCDF4 import (Dataset, MFDataset)
import numpy as np
import xarray as xr
import pandas as pd
import wrf
modules_path = '/glade/work/hungjui/Research_Test/WRF_dBZ_Cloud_Classification/WRF_dBZ_Class_CONUS1/Modules'
if ( modules_path not in sys.path ):
    sys.path = [modules_path] + sys.path
    # print(sys.path)
import storm_mode_class5 as stm


# %%
# **Set input files paths and names:**

def set_input_names(file_date):

    file_path_1_conus = '/gpfs/fs1/collections/rda/data/ds612.0'
    file_path_1_dbz = '/glade/scratch/hungjui/DATA_WRF_CONUS_1_dBZ_v1.0'
    file_path_2 = '/' + wrf_sim_type # '/CTRL3D'
    file_path_3 = '/{}'.format(file_date.strftime('%Y'))

    file_names = dict( dbz = file_path_1_dbz
                           + file_path_2 
                           + file_path_3 
                           + '/wrf3d_d01_' + wrf_sim_type[0:-2] + '_dbz_{}.nc'.format(file_date.strftime('%Y%m%d'))
                       , Z = file_path_1_conus
                           + file_path_2 
                           + file_path_3 
                           + '/wrf3d_d01_' + wrf_sim_type[0:-2] + '_Z_{}.nc'.format(file_date.strftime('%Y%m%d'))
                     )
    
    return file_names

# %%
# ### Main Function:
# %%

def main_function(file_date_time):
    
    ## Set file datetime:
    # file_date_time = dt.datetime(2013, 9, 13, 0, 0, 0, tzinfo=pytz.utc)
    # print('\nProcessing: {}'.format(file_date_time.strftime('%Y%m%d')), end=': ')
    
    ## Set input files paths and names:
    file_name_dict = set_input_names(file_date_time)

    ## Get the 3-hourly time list:
    nc_wrf_Z = Dataset(file_name_dict['Z'], mode='r')
    wrf_3hour_list = wrf.extract_times(nc_wrf_Z, timeidx=wrf.ALL_TIMES, meta=False, do_xtime=False)
    
    ## Open dBZ data array and append calculated data:
    ds_wrf_dbz = xr.open_dataset(file_name_dict['dbz'])
    
    for hi in range(len(wrf_3hour_list)):
        
        ## Get dBZ data:
        da_wrf_dbz = ds_wrf_dbz['dBZ'].isel(Time=hi)
        da_wrf_CSmask = ds_wrf_dbz['CS_mask'].isel(Time=hi)
        
        ## Calculate the max. composite dBZ:
        da_wrf_reflc = da_wrf_dbz.max(dim='bottom_top')
        
        ## Get geopotential height:
        data_wrf_z_unstag = wrf.destagger(wrf.getvar(nc_wrf_Z, 'Z', timeidx=hi, meta=False), 0)
        
        ## Storm Mode Classification (moderate thresholds):
        DCC_mask, OCC_mask, WCC_mask, DWCC_mask, BSR_mask = stm.storm_mode_c5( da_wrf_dbz
                                                                             , da_wrf_reflc
                                                                             , da_wrf_CSmask
                                                                             , data_wrf_z_unstag
                                                                             , 4 # 4-km grid resolution
                                                                             , 'moderate'
                                                                             )
        Storm_Mode_single_m = stm.merge_to_Storm_Mode(DCC_mask, OCC_mask, WCC_mask, DWCC_mask, BSR_mask)
        
        ## Storm Mode Classification (strong thresholds):
        DCC_mask, OCC_mask, WCC_mask, DWCC_mask, BSR_mask = stm.storm_mode_c5( da_wrf_dbz
                                                                             , da_wrf_reflc
                                                                             , da_wrf_CSmask
                                                                             , data_wrf_z_unstag
                                                                             , 4 # 4-km grid resolution
                                                                             , 'strong'
                                                                             )
        Storm_Mode_single_s = stm.merge_to_Storm_Mode(DCC_mask, OCC_mask, WCC_mask, DWCC_mask, BSR_mask)
        
        ## Stack the Storm Mode according to hours:
        if ( hi == 0 ):
            Storm_Mode_m = np.expand_dims(Storm_Mode_single_m, axis=0)
            Storm_Mode_s = np.expand_dims(Storm_Mode_single_s, axis=0)
        else:
            Storm_Mode_m = np.append(Storm_Mode_m, np.expand_dims(Storm_Mode_single_m, axis=0), axis=0)
            Storm_Mode_s = np.append(Storm_Mode_s, np.expand_dims(Storm_Mode_single_s, axis=0), axis=0)

        
    ## Add Storm Mode to dBZ dataset:
    ds_wrf_dbz['Storm_Mode_mod'] = (['Time', 'south_north', 'west_east'], Storm_Mode_m)
    ds_wrf_dbz['Storm_Mode_str'] = (['Time', 'south_north', 'west_east'], Storm_Mode_s)
    
    ds_wrf_dbz.close()
    
    nc_wrf_Z.close()
    
    return ds_wrf_dbz


# %% 
# ### Main Program:
# %%

start = time.time()

## WRF Model Simulation Category:
# wrf_sim_type = 'CTRL3D'
# wrf_sim_type = 'PGW3D'
wrf_sim_type = sys.argv[1]

## Loop through a period:
# target_date_range = pd.date_range(start='2013-9-13', end='2013-9-15', tz=pytz.utc)
target_date_range = pd.date_range(start=sys.argv[2], end=sys.argv[3], tz=pytz.utc)

for dayi in target_date_range:
        
    ## Derive Storm Modes into dBZ dataset:
    ds_wrf_dbz = main_function(dayi)
    
    ## Add attributes to Storm Mode:
    ds_wrf_dbz.Storm_Mode_mod.attrs['long_name'] = 'Storm Mode (moderate thresholds)'
    ds_wrf_dbz.Storm_Mode_mod.attrs['description'] = 'Classified Storm Modes with moderate thresholds (1:DCC; 2:OCC; 3:WCC; 4:DWCC; 5:BSR)'
    
    ds_wrf_dbz.Storm_Mode_str.attrs['long_name'] = 'Storm Mode (strong thresholds)'
    ds_wrf_dbz.Storm_Mode_str.attrs['description'] = 'Classified Storm Modes with strong thresholds (1:DCC; 2:OCC; 3:WCC; 4:DWCC; 5:BSR)'
    
    ## Set output file path and name (to the original dBZ dataset):
    file_name_dict = set_input_names(dayi)
    file_path_name = file_name_dict['dbz']
    
    ds_wrf_dbz.to_netcdf(file_path_name, 'a')
    ds_wrf_dbz.close()

    
end = time.time()

# print("RUNTIME：%f SEC" % (end - start))
# print("RUNTIME：%f MIN" % ((end - start)/60))
# print("RUNTIME：%f HOUR" % ((end - start)/3600))
    
run_time_txt = open('./run_time.log','a')
run_time_txt.write(sys.argv[1] + '\n')
run_time_txt.write(sys.argv[2] + ' - ' + sys.argv[3] + '\n')
run_time_txt.write("RUNTIME：%f SEC \n" % (end - start))
run_time_txt.write("RUNTIME：%f MIN \n" % ((end - start)/60))
run_time_txt.write("RUNTIME：%f HOUR \n" % ((end - start)/3600))




