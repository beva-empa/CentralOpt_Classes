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


def network_capacities():
    input_path = 'system_config.xlsx'
    network_info = pd.read_excel(input_path, sheet_name='Network', header=None, skiprows=2)
    network_info = network_info.drop([0], axis=1).transpose()
    network_info = network_info.drop([2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15], axis=1)
    node1 = network_info[0].tolist()
    node2 = network_info[1].tolist()
    node_cap = network_info[6].tolist()
    bigM = 10 ** 7

    netlen = len(network_info)
    tech_details = np.array(range(bigM, (2 * netlen) + bigM))
    tech_details = np.repeat(tech_details, 3)
    tech_details = tech_details.reshape(2 * netlen, 3)
    tech_details = pd.DataFrame(tech_details, columns=['node1', 'node2', 'value'])
    tech_details = tech_details.apply(pd.to_numeric)

    for i in range(2 * netlen):
        if i < netlen:
            tech_details['node1'] = tech_details['node1'].replace(i + bigM, node1[i])
            tech_details['node2'] = tech_details['node2'].replace(i + bigM, node2[i])
            tech_details['value'] = tech_details['value'].replace(i + bigM, node_cap[i])
        else:
            tech_details['node1'] = tech_details['node1'].replace(i + bigM, node2[i - netlen])
            tech_details['node2'] = tech_details['node2'].replace(i + bigM, node1[i - netlen])
            tech_details['value'] = tech_details['value'].replace(i + bigM, node_cap[i - netlen])

    return tech_details


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
              storage_elecout_final, elec_net, list_techs, list_storage, date_info, time_info, num_hubs):
    worksheet = workbook.add_worksheet('final power')

    header = []
    header.extend(['date', 'time'])

    for i in range(num_hubs):
        demstr = 'demand ' + str(i + 1)
        header.extend([demstr])
        header.extend(list_techs[i])
        header.extend(['grid input', 'grid output'])

        if 'Battery' in list_storage[i]:
            header.extend(['Battery input', 'Battery output'])

        for k in range(num_hubs):
            if k != i:
                templ = ['To hub' + str(k + 1)]
                header.extend(templ)

        for k in range(num_hubs):
            if k != i:
                templ = ['From hub' + str(k + 1)]
                header.extend(templ)

    header = [header]

    for row_num, item in enumerate(header):
        worksheet.write_row(row_num, 0, item)

    xl_final = []

    for i in range(len(date_info)):
        xl_data = []
        xl_data.extend(date_info[i])
        xl_data.extend(time_info[i])

        for j in range(num_hubs):
            xl_data.extend([demand_power_final[i][j]])
            xl_data.extend(power_final[i][j])
            xl_data.extend([0])
            xl_data.extend([grid_in_final[i][j]])
            xl_data.extend([grid_out_final[i][j]])

            if 'Battery' in list_storage[j]:
                xl_data.extend([storage_elecin_final[i][j]])
                xl_data.extend([storage_elecout_final[i][j]])

            xl_data.extend(elec_net[i][j])

        xl_final.append(xl_data)

    for row_num, item in enumerate(xl_final, 1):
        worksheet.write_row(row_num, 0, item)


def saveHeat(workbook, demand_heat_final, heat_final, storage_heatin_final, storage_heatout_final, heat_net, list_techs,
             list_storage, date_info, time_info, num_hubs):
    worksheet = workbook.add_worksheet('final heat')

    header = []
    header.extend(['date', 'time'])

    for i in range(num_hubs):
        demstr = 'demand ' + str(i + 1)
        header.extend([demstr])
        header.extend(list_techs[i])

        if 'heat_storage' in list_storage[i]:
            header.extend(['Storage input', 'Storage output'])

        for k in range(num_hubs):
            if k != i:
                templ = ['To hub' + str(k + 1)]
                header.extend(templ)

        for k in range(num_hubs):
            if k != i:
                templ = ['From hub' + str(k + 1)]
                header.extend(templ)

    header = [header]

    for row_num, item in enumerate(header):
        worksheet.write_row(row_num, 0, item)

    xl_final = []

    for i in range(len(date_info)):
        xl_data = []
        xl_data.extend(date_info[i])
        xl_data.extend(time_info[i])

        for j in range(num_hubs):
            xl_data.extend([demand_heat_final[i][j]])
            xl_data.extend(heat_final[i][j])
            xl_data.extend([0])

            if 'heat_storage' in list_storage[j]:
                xl_data.extend([storage_heatin_final[i][j]])
                xl_data.extend([storage_heatout_final[i][j]])

            xl_data.extend(heat_net[i][j])

        xl_final.append(xl_data)

    for row_num, item in enumerate(xl_final, 1):
        worksheet.write_row(row_num, 0, item)


def saveCost(workbook, tech_cost_final, storage_cost_final, final_cost_final, grid_cost_final, date_info, time_info,
             num_hubs):
    worksheet = workbook.add_worksheet('final cost')

    header = []
    header.extend(['date', 'time'])

    for i in range(num_hubs):

        header.extend(['tech cost ' + str(i + 1), 'grid cost ' + str(i + 1),
                       'storage cost ' + str(i + 1), 'final cost ' + str(i + 1)])

    header = [header]

    for row_num, item in enumerate(header):
        worksheet.write_row(row_num, 0, item)

    xl_final = []

    for i in range(len(date_info)):
        xl_data = []
        xl_data.extend(date_info[i])
        xl_data.extend(time_info[i])

        for j in range(num_hubs):
            xl_data.extend([tech_cost_final[i][j]])
            xl_data.extend([grid_cost_final[i][j]])
            xl_data.extend([storage_cost_final[i][j]])
            xl_data.extend([final_cost_final[i][j]])

        xl_final.append(xl_data)

    for row_num, item in enumerate(xl_final, 1):
        worksheet.write_row(row_num, 0, item)


def saveStorage(workbook, storage_heat_final, storage_elec_final, battery_depth_final, SOC_elec, SOC_therm,
                storage_elecin_final, storage_elecout_final, storage_heatin_final, storage_heatout_final,
                list_storage, date_info, time_info, num_hubs):

    worksheet = workbook.add_worksheet('final storage')

    header = []
    header.extend(['date', 'time'])

    for i in range(num_hubs):
        if 'heat_storage' in list_storage[i]:
            header.extend(['thermal level - hub '+str(i+1), 'thermal SOC - hub '+str(i+1),
                           'thermal inp - hub '+str(i+1), 'thermal out - hub '+str(i+1)])

        if 'Battery' in list_storage[i]:
            header.extend(
                ['Battery level - hub '+str(i+1), 'Battery SOC - hub '+str(i+1), 'Battery inp - hub '+str(i+1),
                 'Battery out - hub '+ str(i+1), 'Batt 0-20% - hub '+str(i+1), 'Batt 20-40% - hub '+str(i+1),
                 'Batt 40-60% - hub '+str(i+1), 'Batt 60-80% - hub '+str(i+1)])

    header = [header]

    for row_num, item in enumerate(header):
        worksheet.write_row(row_num, 0, item)

    xl_final = []

    for i in range(len(date_info)):
        xl_data = []
        xl_data.extend(date_info[i])
        xl_data.extend(time_info[i])

        for j in range(num_hubs):
            if 'heat_storage' in list_storage[j]:
                xl_data.extend([storage_heat_final[i][j]])
                xl_data.extend([SOC_therm[i][j]])
                xl_data.extend([storage_heatin_final[i][j]])
                xl_data.extend([storage_heatout_final[i][j]])

            if 'Battery' in list_storage[j]:
                xl_data.extend([storage_elec_final[i][j]])
                xl_data.extend([SOC_elec[i][j]])
                xl_data.extend([storage_elecin_final[i][j]])
                xl_data.extend([storage_elecout_final[i][j]])
                xl_data.extend(battery_depth_final[i][j])

        xl_final.append(xl_data)

    for row_num, item in enumerate(xl_final, 1):
        worksheet.write_row(row_num, 0, item)


def saveChp(workbook, CHP_ontime_final, CHP_offtime_final, list_techs, date_info, time_info, num_hubs):

    worksheet = workbook.add_worksheet('final CHP')

    header = []
    header.extend(['date', 'time'])

    for i in range(num_hubs):
        if 'Gas_CHP_unit_2' in list_techs[i]:
            header.extend(['CHP on time - hub '+str(i+1), 'CHP off time - hub '+str(i+1)])

    header = [header]

    for row_num, item in enumerate(header):
        worksheet.write_row(row_num, 0, item)

    xl_final = []

    for i in range(len(date_info)):
        xl_data = []
        xl_data.extend(date_info[i])
        xl_data.extend(time_info[i])

        for j in range(num_hubs):
            if 'Gas_CHP_unit_2' in list_techs[j]:
                xl_data.extend([CHP_ontime_final[i][j]])
                xl_data.extend([CHP_offtime_final[i][j]])

        xl_final.append(xl_data)

    for row_num, item in enumerate(xl_final, 1):
        worksheet.write_row(row_num, 0, item)

