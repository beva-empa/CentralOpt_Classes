import pandas as pd
import numpy as np
import math
import datetime as dt
from matplotlib.cbook import boxplot_stats
import xlsxwriter


#
def import_capacities():
    input_path = 'system_config.xlsx'
    capacities_path = 'max_capacity.txt'

    energy_carriers = pd.read_excel(input_path, sheet_name='Energy Carriers', header=None, skiprows=3)
    energy_carriers = energy_carriers[0].tolist()

    conversion_info = pd.read_excel(input_path, sheet_name='Conversion Techs', header=None, skiprows=2)
    conversion_info = conversion_info.drop([0], axis=1).transpose()
    conversion_info = conversion_info.drop([1, 2, 3, 4, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19], axis=1)

    storage_info = pd.read_excel(input_path, sheet_name='Storage Techs', header=None, skiprows=2)
    storage_info = storage_info.drop([0], axis=1).transpose()
    storage_info = storage_info.drop([1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15], axis=1)

    conversion_tech = conversion_info[0].tolist()
    conversion_eff = conversion_info[8].tolist()
    conversion_outshare = conversion_info[10].tolist()
    conversion_hub = conversion_info[20].tolist()

    storage_tech = storage_info[0].tolist()
    storage_hub = storage_info[16].tolist()
    storage_stateff = storage_info[9].tolist()
    storage_cyceff = storage_info[10].tolist()

    techlen = len(conversion_tech)
    tech_details = np.array(range(1, techlen + 1))
    tech_details = np.repeat(tech_details, 4)
    tech_details = tech_details.reshape(techlen, 4)
    tech_details = pd.DataFrame(tech_details, columns=['tech', 'eff', 'outshare', 'hub'])
    tech_details = tech_details.apply(pd.to_numeric)

    storelen = len(storage_tech)
    storage_details = np.array(range(1, storelen + 1))
    storage_details = np.repeat(storage_details, 4)
    storage_details = storage_details.reshape(storelen, 4)
    storage_details = pd.DataFrame(storage_details, columns=['tech', 'stateff', 'cyceff', 'hub'])
    storage_details = storage_details.apply(pd.to_numeric)

    for i in range(techlen):
        tech_details['tech'] = tech_details['tech'].replace(i + 1, conversion_tech[i])
        tech_details['eff'] = tech_details['eff'].replace(i + 1, conversion_eff[i])
        tech_details['outshare'] = tech_details['outshare'].replace(i + 1, conversion_outshare[i])
        tech_details['hub'] = tech_details['hub'].replace(i + 1, conversion_hub[i])
        i = i + 1

    for i in range(storelen):
        storage_details['tech'] = storage_details['tech'].replace(i + 1, storage_tech[i])
        storage_details['stateff'] = storage_details['stateff'].replace(i + 1, storage_stateff[i])
        storage_details['cyceff'] = storage_details['cyceff'].replace(i + 1, storage_cyceff[i])
        storage_details['hub'] = storage_details['hub'].replace(i + 1, storage_hub[i])
        i = i + 1

    lines = []
    cap_conv = []
    cap_stor = []

    with open(capacities_path, 'rt') as in_file:
        for line in in_file:
            lines.append(line)

    for row in lines:

        if row.find('CapTech') >= 0:
            row2 = row.split(sep=' ')
            cap_conv.append(row2[1:4])

        if row.find("CapStg") >= 0:
            row2 = row.split(sep=" ")
            cap_stor.append(row2[1:5])

    capacities_conv = pd.DataFrame(cap_conv, columns=['hub', 'tech', 'value'])
    capacities_conv = capacities_conv.apply(pd.to_numeric)
    capacities_stor = pd.DataFrame(cap_stor, columns=['hub', 'tech', 'drop', 'value'])
    capacities_stor = capacities_stor.apply(pd.to_numeric)
    i = 1
    for label in conversion_tech:
        capacities_conv['tech'] = capacities_conv['tech'].replace(i, label)
        i = i + 1

    i = 1
    for label in storage_tech:
        capacities_stor['tech'] = capacities_stor['tech'].replace(i, label)
        i = i + 1

    capacities_stor = capacities_stor.drop(['drop'], axis=1)
    capacities_stor = capacities_stor[capacities_stor.value != 0]
    capacities_conv = capacities_conv[capacities_conv.value != 0]

    return capacities_conv, capacities_stor, tech_details, storage_details


def CHP_operation(Pmax_CHP, Eff_CHP, PEff_CHP, QEff_CHP, n_CHP, min_cap_CHP):
    CHP_fuelcap = Pmax_CHP / Eff_CHP

    AP = n_CHP * min_cap_CHP * CHP_fuelcap
    AQ = 0

    BP = CHP_fuelcap * min_cap_CHP * PEff_CHP
    BQ = CHP_fuelcap * min_cap_CHP * QEff_CHP

    CP = CHP_fuelcap * PEff_CHP
    CQ = CHP_fuelcap * QEff_CHP

    DQ = AQ + (CQ - BQ)
    DP = AP + (CP - BP)

    EP = n_CHP * CHP_fuelcap
    EQ = 0

    CHP_points = np.array([[AQ, BQ, CQ, DQ, EQ], [AP, BP, CP, DP, EP]])

    return CHP_points


grid_config = {
    'high_tariff': 0.18,  # [CHF/kWh]
    'low_tariff': 0.13,  # [CHF/kWh]
    'feed_in_tariff': 0.05,  # [CHF/kWh]
}


def get_data(start_time):
    df_bc = pd.concat([pd.read_csv('demandsABC.csv', encoding='ISO-8859-1')])
    df_bc['timestamp'] = pd.date_range(start=start_time, periods=len(df_bc), tz='Europe/Zurich',
                                       freq="60min").to_pydatetime().tolist()  # Create data range with local time
    df_bc.set_index('timestamp', inplace=True)
    df_bc['dayinyear'] = df_bc.index.dayofyear

    df_bc['feed_in_tariff'] = grid_config['feed_in_tariff']
    df_bc['el_tariff'] = grid_config['low_tariff']

    df_bc.loc[((7 <= df_bc.index.hour) & (df_bc.index.hour <= 20) & (df_bc.index.dayofweek < 5)), 'el_tariff'] = \
        grid_config['high_tariff']
    df_bc.loc[((7 <= df_bc.index.hour) & (df_bc.index.hour <= 13) & (df_bc.index.dayofweek == 5)), 'el_tariff'] = \
        grid_config['high_tariff']
    return df_bc


def savePower(workbook, demand_power_final, power_final, grid_in_final, grid_out_final, storage_elecin_final,
              storage_elecout_final, list_techs, list_storage, date_info, time_info):

    worksheet = workbook.add_worksheet('final power')

    header = []
    header.extend(['date', 'time', 'demand'])
    header.extend(list_techs)
    header.extend(['grid input', 'grid output'])

    if 'Battery' in list_storage:
        header.extend(['Battery input', 'Battery output'])
    header = [header]

    for row_num, item in enumerate(header):
        worksheet.write_row(row_num, 0, item)

    for row_num, item in enumerate(date_info, 1):
        worksheet.write_row(row_num, 0, item)

    for row_num, item in enumerate(time_info, 1):
        worksheet.write_row(row_num, 1, item)

    for row_num, item in enumerate(demand_power_final, 1):
        worksheet.write_row(row_num, 2, item)

    for row_num, item in enumerate(power_final, 1):
        worksheet.write_row(row_num, 3, item)

    for row_num, item in enumerate(grid_in_final, 1):
        worksheet.write_row(row_num, len(list_techs) + 3, item)

    for row_num, item in enumerate(grid_out_final, 1):
        worksheet.write_row(row_num, len(list_techs) + 4, item)

    if 'Battery' in list_storage:

        for row_num, item in enumerate(storage_elecin_final, 1):
            worksheet.write_row(row_num, len(list_techs) + 5, item)

        for row_num, item in enumerate(storage_elecout_final, 1):
            worksheet.write_row(row_num, len(list_techs) + 6, item)


def saveHeat(workbook, demand_heat_final, heat_final, storage_heatin_final, storage_heatout_final, list_techs,
             list_storage, date_info, time_info):
    worksheet = workbook.add_worksheet('final heat')

    header = []
    header.extend(['date', 'time', 'demand'])
    header.extend(list_techs)

    if 'heat_storage' in list_storage:
        header.extend(['storage input', 'storage output'])
    header = [header]

    for row_num, item in enumerate(header):
        worksheet.write_row(row_num, 0, item)

    for row_num, item in enumerate(date_info, 1):
        worksheet.write_row(row_num, 0, item)

    for row_num, item in enumerate(time_info, 1):
        worksheet.write_row(row_num, 1, item)

    for row_num, item in enumerate(demand_heat_final, 1):
        worksheet.write_row(row_num, 2, item)

    for row_num, item in enumerate(heat_final, 1):
        worksheet.write_row(row_num, 3, item)

    if 'heat_storage' in list_storage:

        for row_num, item in enumerate(storage_heatin_final, 1):
            worksheet.write_row(row_num, len(list_techs) + 3, item)

        for row_num, item in enumerate(storage_heatout_final, 1):
            worksheet.write_row(row_num, len(list_techs) + 4, item)


def saveCost(workbook, tech_cost_final, storage_cost_final, final_cost_final, grid_cost_final, date_info, time_info):
    worksheet = workbook.add_worksheet('final cost')

    header = []
    header.extend(['date', 'time', 'tech cost', 'grid cost', 'storage cost', 'final cost'])
    header = [header]

    for row_num, item in enumerate(header):
        worksheet.write_row(row_num, 0, item)

    for row_num, item in enumerate(date_info, 1):
        worksheet.write_row(row_num, 0, item)

    for row_num, item in enumerate(time_info, 1):
        worksheet.write_row(row_num, 1, item)

    for row_num, item in enumerate(tech_cost_final, 1):
        worksheet.write_row(row_num, 2, item)

    for row_num, item in enumerate(grid_cost_final, 1):
        worksheet.write_row(row_num, 3, item)

    for row_num, item in enumerate(storage_cost_final, 1):
        worksheet.write_row(row_num, 4, item)

    for row_num, item in enumerate(final_cost_final, 1):
        worksheet.write_row(row_num, 5, item)


def saveStorage(workbook, storage_heat_final, storage_elec_final, battery_depth_final, SOC_elec, SOC_therm,
                list_storage, date_info, time_info):
    worksheet = workbook.add_worksheet('final storage')

    header = []
    header.extend(['date', 'time'])
    if 'heat_storage' in list_storage:
        header.extend(['thermal level', 'thermal SOC'])

    if 'Battery' in list_storage:
        header.extend(
            ['Battery level', 'Battery SOC', 'Batt - 0-20%', 'Batt - 20-40%', 'Batt - 40-60%', 'Batt - 60-80%'])
    header = [header]

    for row_num, item in enumerate(header):
        worksheet.write_row(row_num, 0, item)

    for row_num, item in enumerate(date_info, 1):
        worksheet.write_row(row_num, 0, item)

    for row_num, item in enumerate(time_info, 1):
        worksheet.write_row(row_num, 1, item)

    i = 2
    if 'heat_storage' in list_storage:
        for row_num, item in enumerate(storage_heat_final, 1):
            worksheet.write_row(row_num, 2, item)

        for row_num, item in enumerate(SOC_therm, 1):
            worksheet.write_row(row_num, 3, item)

        i = i + 2

    if 'Battery' in list_storage:
        for row_num, item in enumerate(storage_elec_final, 1):
            worksheet.write_row(row_num, i, item)

        for row_num, item in enumerate(SOC_elec, 1):
            worksheet.write_row(row_num, i + 1, item)

        for row_num, item in enumerate(battery_depth_final, 1):
            worksheet.write_row(row_num, i + 2, item)


def saveChp(workbook, CHP_ontime_final, CHP_offtime_final, list_techs, date_info, time_info):
    worksheet = workbook.add_worksheet('final CHP runtime')

    header = []
    header.extend(['date', 'time'])

    if 'Gas_CHP_unit_2' in list_techs:
        header.extend(['CHP on time', 'CHP off time'])

    header = [header]

    for row_num, item in enumerate(header):
        worksheet.write_row(row_num, 0, item)

    for row_num, item in enumerate(date_info, 1):
        worksheet.write_row(row_num, 0, item)

    for row_num, item in enumerate(time_info, 1):
        worksheet.write_row(row_num, 1, item)

    for row_num, item in enumerate(CHP_ontime_final, 1):
        worksheet.write_row(row_num, 2, item)

    for row_num, item in enumerate(CHP_offtime_final, 1):
        worksheet.write_row(row_num, 3, item)
