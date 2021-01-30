
from scipy.io import loadmat
from matplotlib.cbook import boxplot_stats
import numpy as np
import datetime as dt
import pandas as pd
import math
import os
from ehub_results import *
import matplotlib.lines as mlines

# Optimisation configuration for rolling 24h horizon
opt_config = {
    'pred_horzn': 24,  # 24 Prediction horizon in hours
    'num_opt_var': 22,  # 22 Total steps
}

base_results_path = './ehub/result/'
base_input_path ='./ehub/case/'


def configure_capacities(hub, pareto_point):

    capacities_master = pd.DataFrame()
    capacities_stor_master = pd.DataFrame()

    results_path = base_results_path + scenario + '/pareto' + str(pareto_point)
    result_file = results_path + '/results.txt'
    param_file = results_path + '/params.txt'


    # READING EHUB INPUT FILE
    input_path = base_input_path + scenario + '.xlsx'

    energy_carriers = pd.read_excel(input_path,sheet_name='Energy Carriers', header=None, skiprows=3)
    conversion_techs = pd.read_excel(input_path,sheet_name='Conversion Techs', header=None, skiprows=2,skipfooter=20)
    storage_techs = pd.read_excel(input_path,sheet_name='Storage Techs', header=None, skiprows=2,skipfooter=15)

    energy_carriers2 = energy_carriers[0].tolist()
    conversion_techs2 = conversion_techs.drop([0],axis=1).transpose()
    conversion_techs2 = conversion_techs2[0].tolist()
    storage_techs2 = storage_techs.drop([0],axis=1).transpose()
    storage_techs2 = storage_techs2[0].tolist()





    capacities_ehub, storage_ehub = get_ehub_result_hub(pareto_point, scenario)

    list_techs = capacities_ehub.loc[((capacities_ehub.hub == hub) & (capacities_ehub.value > 0)), 'tech'].values.tolist()
    # conversion capacities (pp5 R1_1 of 8pp)


    if 'solar_PV' in list_techs:
        max_PV_capacity     = math.ceil(capacities_ehub.loc[((capacities_ehub.hub == hub) & (capacities_ehub.tech == 'solar_PV')), 'value'].squeeze())
        min_PV_capacity     = 0
    else:
        max_PV_capacity     = 0
        min_PV_capacity     = 0

    if 'solar_PVT' in list_techs:
        max_PVT_capacity    = math.ceil(capacities_ehub.loc[((capacities_ehub.hub == hub) & (capacities_ehub.tech == 'solar_PVT')), 'value'].squeeze())
        min_PVT_capacity    = 0
    else:
        max_PVT_capacity     = 0
        min_PVT_capacity    = 0

    if 'Gas_CHP_unit_1' in list_techs:
        max_CHP1_capacity    = math.ceil(capacities_ehub.loc[((capacities_ehub.hub == hub) & (capacities_ehub.tech == 'Gas_CHP_unit_1')), 'value'].squeeze())
        min_CHP1_capacity    = 0
    else:
        max_CHP1_capacity    = 0
        min_CHP1_capacity    = 0

    if 'Gas_CHP_unit_2' in list_techs:
        max_CHP2_capacity    = math.ceil(capacities_ehub.loc[((capacities_ehub.hub == hub) & (capacities_ehub.tech == 'Gas_CHP_unit_2')), 'value'].squeeze())
        min_CHP2_capacity    = 0 # max_CHP1_capacity
    else:
        max_CHP2_capacity    = 0
        min_CHP2_capacity    = 0

    if 'GSHP_2' in list_techs:
        max_GSHP_capacity   = math.ceil(capacities_ehub.loc[((capacities_ehub.hub == hub) & (capacities_ehub.tech == 'GSHP_2')), 'value'].squeeze())
        min_GSHP_capacity   = 0
    else:
        max_GSHP_capacity   = 0
        min_GSHP_capacity   = 0

    if 'GSHP_1' in list_techs:
        max_GSHP_capacity   += math.ceil(capacities_ehub.loc[((capacities_ehub.hub == hub) & (capacities_ehub.tech == 'GSHP_1')), 'value'].squeeze())
        min_GSHP_capacity   = 0


    if 'gas_boiler_1' in list_techs:
        max_gas1_capacity    = math.ceil(capacities_ehub.loc[((capacities_ehub.hub == hub) & (capacities_ehub.tech == 'gas_boiler_1')), 'value'].squeeze())
        min_gas1_capacity    = 0
    else:
        max_gas1_capacity    = 0
        min_gas1_capacity    = 0

    if 'gas_boiler_2' in list_techs:
        max_gas2_capacity    = math.ceil(capacities_ehub.loc[((capacities_ehub.hub == hub) & (capacities_ehub.tech == 'gas_boiler_2')), 'value'].squeeze())
        min_gas2_capacity    = 0 # max_gas1_capacity
    else:
        max_gas2_capacity    = 0
        min_gas2_capacity    = 0

    df_bc['solar_totalHubArea_potential'] = df_bc['solar_roof'] * solar_area[hub]
    df_bc['solar_potential_PV'] = df_bc['solar_roof'] * max_PV_capacity / 0.15
    df_bc['solar_potential_PVT'] = df_bc['solar_roof'] * max_PVT_capacity / 0.18

    # storage capacities

    if isinstance(storage_ehub.loc[((storage_ehub.hub == hub) & (storage_ehub.tech == 'Battery') & (storage_ehub.ec == 'elec')), 'value'].squeeze(), float) :
        ebat_max = storage_ehub.loc[((storage_ehub.hub == hub) & (storage_ehub.tech == 'Battery') & (storage_ehub.ec == 'elec')), 'value'].squeeze()
    else:  ebat_max = 0


    if isinstance(storage_ehub.loc[((storage_ehub.hub == hub) & (storage_ehub.tech == 'heat_storage') & (storage_ehub.ec == 'heat')), 'value'].squeeze(), float) :
        thermal_storage_max = storage_ehub.loc[((storage_ehub.hub == hub) & (storage_ehub.tech == 'heat_storage') & (storage_ehub.ec == 'heat')), 'value'].squeeze()
    else: thermal_storage_max = 0


    return list_techs, capacities_ehub, storage_ehub, ebat_max, thermal_storage_max, max_PV_capacity, min_PV_capacity, max_PVT_capacity, min_PVT_capacity, max_CHP1_capacity, min_CHP1_capacity, max_CHP2_capacity, min_CHP2_capacity, max_gas1_capacity, min_gas1_capacity, max_gas2_capacity, min_gas2_capacity, max_GSHP_capacity, min_GSHP_capacity

