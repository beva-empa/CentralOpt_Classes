# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import mosek
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import math
import time
import cvxpy as cp
import pickle
import os
import sys
import logging
from comp_classes import *
from test_multi import *
# from visualize_results import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - main - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('log_history.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

num_opt_var = 24
UPmin_CHP = 12
DNmin_CHP = 2

trans_cost = 0.01
P_delta = 0.1
Q_delta = 0.1
num_hubs = 3
BigM = 10 ** 10
hub = 1
beta = 0.003
d_PV = 0.15
d_PVT = 0.18
COP = 4.5
C_Fuel = 0.115
Tstc = 25
Tnoct = 48.3
Tstd = 20
n_CHP = 0.41
min_cap_CHP = 0.42
solar_area = 25700

time_start = dt.datetime(2018, 3, 1, 0, 0, 0)
time_end = dt.datetime(2018, 3, 4, 0, 0, 0)
time_now = time_start
start_time = dt.datetime(2018, 1, 1)

if __name__ == '__main__':

    comp_start = time.perf_counter()

    capacities_conv, capacities_stor, tech_details, storage_details = import_capacities()
    network_cap = network_capacities()
    list_techs = []
    list_storage = []

    for hub in range(1, num_hubs + 1):
        list_techs.append(capacities_conv.loc[((capacities_conv.hub == hub) &
                                               (capacities_conv.value > 0)), 'tech'].values.tolist())
        list_storage.append(capacities_stor.loc[((capacities_stor.hub == hub) &
                                                 (capacities_stor.value > 0)), 'tech'].values.tolist())

    demand_data = get_data(start_time)


    def main_optimize(elec_storage, battery_depth, thermal_storage, CHP_Runtime, CHP_Downtime, capacities_conv,
                      capacities_stor, tech_details, storage_details, network_cap, list_techs, list_storage, time_now):

        comp_list = []
        tran_list = []
        it = 0
        cost = 0
        constr = []

        demand_power = []
        demand_heat = []

        for st in range(1, num_hubs + 1):
            for rt in range(1, num_hubs + 1):
                if st != rt:
                    tran_list.append(trans_pw_ht(num_opt_var, st, rt))

        for item in tran_list:
            Pmax = math.ceil(network_cap.loc[((network_cap.node1 == item.origin) &
                                              (network_cap.node2 == item.recpnt)), 'value'].squeeze())
            for t in range(num_opt_var):
                constr += [item.P_strt[t] >= 0, item.Q_strt[t] >= 0]
                constr += [item.P_strt[t] <= Pmax]
                cost += item.P_strt[t] * trans_cost + item.Q_strt[t] * trans_cost

        for hub in range(1, num_hubs + 1):

            hub_el = 'elec_' + str(hub)
            hub_ht = 'heat_' + str(hub)

            P_Demand = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), hub_el].values.tolist()
            Q_Demand = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), hub_ht].values.tolist()
            Ta = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), 'temp'].values.tolist()
            I_Solar = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), 'solar_roof'].values.tolist()

            Rini_CHP = CHP_Runtime[hub - 1]
            Dini_CHP = CHP_Downtime[hub - 1]

            power_list = []
            heat_list = []

            Qmax_GSHP = 0

            for item in list_techs[hub - 1]:

                if item == 'solar_PV':
                    Pmax_PV = math.ceil(capacities_conv.loc[((capacities_conv.hub == hub) & (
                            capacities_conv.tech == item)), 'value'].squeeze())
                    Eff_PV = math.ceil(tech_details.loc[(tech_details.tech == item), 'eff'].squeeze()) * 0.01
                    Pmin_PV = 0

                    comp_list.append(PV(num_opt_var))

                    power_list.append(comp_list[it].P_PV)

                    for t in range(num_opt_var):
                        comp_list[it].I_PV[t] = I_Solar[t] * (Pmax_PV / d_PV)
                        comp_list[it].TempEff_PV[t] = 1 + ((-beta) * ((Ta[t] - Tstc) +
                                                                      (Tnoct - Ta[t]) * (I_Solar[t] / 0.8)))

                    for t in range(num_opt_var):
                        constr += [comp_list[it].P_PV[t] >= 0,
                                   comp_list[it].P_PV[t] <= (comp_list[it].b_PV[t] * Eff_PV *
                                                             comp_list[it].TempEff_PV[t] * comp_list[it].I_PV[t])]

                    it = it + 1

                elif item == 'solar_PVT':

                    Pmax_PVT = math.ceil(capacities_conv.loc[((capacities_conv.hub == hub) & (
                            capacities_conv.tech == item)), 'value'].squeeze())
                    Eff_PVT = tech_details.loc[(tech_details.tech == item), 'outshare'].squeeze()
                    list1 = Eff_PVT.split(",")
                    li1 = []
                    for t in list1:
                        li1.append(float(t))

                    PEff_PVT = li1[0]
                    QEff_PVT = li1[1]

                    Eff_PVT = tech_details.loc[(tech_details.tech == item), 'eff'].squeeze() * 0.01

                    comp_list.append(PVT(num_opt_var))

                    power_list.append(comp_list[it].P_PVT)
                    heat_list.append(comp_list[it].Q_PVT)

                    for t in range(num_opt_var):
                        comp_list[it].I_PVT[t] = I_Solar[t] * (Pmax_PVT / d_PVT)
                        comp_list[it].TempEff_PVT[t] = 1 + ((-beta) * ((Ta[t] - Tstc) +
                                                                       (Tnoct - Ta[t]) * (I_Solar[t] / 0.8)))

                    for t in range(num_opt_var):
                        constr += [comp_list[it].P_PVT[t] >= 0, comp_list[it].Q_PVT[t] >= 0,
                                   comp_list[it].Out_PVT[t] <= (comp_list[it].b_PVT[t] * Eff_PVT *
                                                                comp_list[it].TempEff_PVT[t] * comp_list[it].I_PVT[t]),
                                   comp_list[it].P_PVT[t] == PEff_PVT * comp_list[it].Out_PVT[t],
                                   comp_list[it].Q_PVT[t] == QEff_PVT * comp_list[it].Out_PVT[t]]

                    it = it + 1

                elif item == 'Gas_CHP_unit_1':

                    Pmax_mCHP = math.ceil(capacities_conv.loc[((capacities_conv.hub == hub) & (
                            capacities_conv.tech == item)), 'value'].squeeze())
                    Pmin_mCHP = 0
                    Eff_mCHP = tech_details.loc[(tech_details.tech == item), 'outshare'].squeeze()

                    list2 = Eff_mCHP.split(",")
                    li = []
                    for k in list2:
                        li.append(float(k))
                    PEff_mCHP = li[0]
                    QEff_mCHP = li[1]
                    Eff_mCHP = tech_details.loc[(tech_details.tech == item), 'eff'].squeeze() * 0.01

                    comp_list.append(mCHP(num_opt_var))

                    power_list.append(comp_list[it].P_mCHP)
                    heat_list.append(comp_list[it].Q_mCHP)

                    for t in range(num_opt_var):
                        cost += comp_list[it].C_mCHP[t]
                        constr += [comp_list[it].Out_mCHP[t] >= comp_list[it].b_mCHP[t] * Pmin_mCHP,
                                   comp_list[it].Out_mCHP[t] <= comp_list[it].b_mCHP[t] * Pmax_mCHP,
                                   comp_list[it].P_mCHP[t] == PEff_mCHP * comp_list[it].Out_mCHP[t],
                                   comp_list[it].Q_mCHP[t] == QEff_mCHP * comp_list[it].Out_mCHP[t],
                                   comp_list[it].C_mCHP[t] == C_Fuel * comp_list[it].F_mCHP[t],
                                   comp_list[it].F_mCHP[t] == comp_list[it].P_mCHP[t] / Eff_mCHP]

                    it = it + 1

                elif item == 'Gas_CHP_unit_2':

                    Pmax_CHP = math.ceil(capacities_conv.loc[((capacities_conv.hub == hub) & (
                            capacities_conv.tech == item)), 'value'].squeeze())
                    Pmin_CHP = 0
                    Eff_CHP = tech_details.loc[(tech_details.tech == item), 'outshare'].squeeze()
                    list2 = Eff_CHP.split(",")
                    li = []
                    for m in list2:
                        li.append(float(m))
                    PEff_CHP = li[0]
                    QEff_CHP = li[1]
                    Eff_CHP = tech_details.loc[(tech_details.tech == item), 'eff'].squeeze() * 0.01
                    CHP_points = CHP_operation(Pmax_CHP, Eff_CHP, PEff_CHP, QEff_CHP, n_CHP, min_cap_CHP)
                    CHP_fuelcap = Pmax_CHP / Eff_CHP

                    P11_CHP = CHP_points[1][0]
                    P12_CHP = CHP_points[1][0]
                    P13_CHP = CHP_points[1][3]
                    P14_CHP = CHP_points[1][4]
                    P21_CHP = CHP_points[1][0]
                    P22_CHP = CHP_points[1][1]
                    P23_CHP = CHP_points[1][2]
                    P24_CHP = CHP_points[1][3]

                    Q11_CHP = CHP_points[0][0]
                    Q12_CHP = CHP_points[0][0]
                    Q13_CHP = CHP_points[0][3]
                    Q14_CHP = CHP_points[0][4]
                    Q21_CHP = CHP_points[0][0]
                    Q22_CHP = CHP_points[0][1]
                    Q23_CHP = CHP_points[0][2]
                    Q24_CHP = CHP_points[0][3]

                    comp_list.append(CHP(num_opt_var))

                    power_list.append(comp_list[it].P_CHP)
                    heat_list.append(comp_list[it].Q_CHP)

                    constr += [comp_list[it].ysum_CHP[0] == comp_list[it].yon_CHP[0],
                               comp_list[it].zsum_CHP[0] == comp_list[it].zoff_CHP[0],
                               comp_list[it].R_CHP[0] == (Rini_CHP + 1) * comp_list[it].b_CHP[0],
                               comp_list[it].D_CHP[0] == (Dini_CHP + 1) * (1 - comp_list[it].b_CHP[0])]

                    if Rini_CHP == 0:
                        constr += [comp_list[it].zoff_CHP[0] == 0, comp_list[it].yon_CHP[0] == comp_list[it].b_CHP[0]]
                    elif Dini_CHP == 0:
                        constr += [comp_list[it].zoff_CHP[0] == 1 - comp_list[it].b_CHP[0],
                                   comp_list[it].yon_CHP[0] == 0]

                    for t in range(num_opt_var):

                        cost += comp_list[it].C_CHP[t]
                        constr += [comp_list[it].P_CHP[t] <= Pmax_CHP * 10 * comp_list[it].b_CHP[t],
                                   comp_list[it].Q_CHP[t] <= Pmax_CHP * 10 * comp_list[it].b_CHP[t],
                                   comp_list[it].P_CHP[t] >= Pmin_CHP * comp_list[it].b_CHP[t],
                                   comp_list[it].Q_CHP[t] >= Pmin_CHP * comp_list[it].b_CHP[t],
                                   comp_list[it].P_CHP[t] == (
                                           comp_list[it].w11_CHP[t] * P11_CHP + comp_list[it].w12_CHP[t] * P12_CHP +
                                           comp_list[it].w13_CHP[t] * P13_CHP + comp_list[it].w14_CHP[t] * P14_CHP +
                                           comp_list[it].w21_CHP[t] * P21_CHP + comp_list[it].w22_CHP[t] * P22_CHP +
                                           comp_list[it].w23_CHP[t] * P23_CHP + comp_list[it].w24_CHP[t] * P24_CHP),
                                   comp_list[it].Q_CHP[t] == (
                                           comp_list[it].w11_CHP[t] * Q11_CHP + comp_list[it].w12_CHP[t] * Q12_CHP +
                                           comp_list[it].w13_CHP[t] * Q13_CHP + comp_list[it].w14_CHP[t] * Q14_CHP +
                                           comp_list[it].w21_CHP[t] * Q21_CHP + comp_list[it].w22_CHP[t] * Q22_CHP +
                                           comp_list[it].w23_CHP[t] * Q23_CHP + comp_list[it].w24_CHP[t] * Q24_CHP),
                                   comp_list[it].b1_CHP[t] + comp_list[it].b2_CHP[t] == comp_list[it].b_CHP[t],
                                   comp_list[it].w11_CHP[t] + comp_list[it].w12_CHP[t] + comp_list[it].w13_CHP[t] +
                                   comp_list[it].w14_CHP[t] == comp_list[it].b1_CHP[t],
                                   comp_list[it].w21_CHP[t] + comp_list[it].w22_CHP[t] + comp_list[it].w23_CHP[t] +
                                   comp_list[it].w24_CHP[t] == comp_list[it].b2_CHP[t],
                                   comp_list[it].w11_CHP[t] >= 0, comp_list[it].w12_CHP[t] >= 0,
                                   comp_list[it].w13_CHP[t] >= 0, comp_list[it].w14_CHP[t] >= 0,
                                   comp_list[it].w21_CHP[t] >= 0, comp_list[it].w22_CHP[t] >= 0,
                                   comp_list[it].w23_CHP[t] >= 0, comp_list[it].w24_CHP[t] >= 0,
                                   comp_list[it].w11_CHP[t] <= 1, comp_list[it].w12_CHP[t] <= 1,
                                   comp_list[it].w13_CHP[t] <= 1, comp_list[it].w14_CHP[t] <= 1,
                                   comp_list[it].w21_CHP[t] <= 1, comp_list[it].w22_CHP[t] <= 1,
                                   comp_list[it].w23_CHP[t] <= 1, comp_list[it].w24_CHP[t] <= 1,
                                   comp_list[it].yon_CHP[t] + comp_list[it].zoff_CHP[t] <= 1,
                                   comp_list[it].C_CHP[t] == C_Fuel * comp_list[it].F_CHP[t],
                                   comp_list[it].F_CHP[t] == comp_list[it].P_CHP[t] / Eff_CHP]
                        if t >= 1:
                            constr += [(comp_list[it].P_CHP[t] <= comp_list[it].P_CHP[t - 1] + 0.5 * Pmax_CHP *
                                        (comp_list[it].b_CHP[t - 1] + comp_list[it].yon_CHP[t])),
                                       (comp_list[it].P_CHP[t] >= comp_list[it].P_CHP[t - 1] - 0.5 * Pmax_CHP *
                                        (comp_list[it].b_CHP[t] + comp_list[it].zoff_CHP[t])),
                                       (comp_list[it].Q_CHP[t] <= comp_list[it].Q_CHP[t - 1] + 0.5 * Pmax_CHP *
                                        (comp_list[it].b_CHP[t - 1] + comp_list[it].yon_CHP[t])),
                                       (comp_list[it].Q_CHP[t] >= comp_list[it].Q_CHP[t - 1] - 0.5 * Pmax_CHP *
                                        (comp_list[it].b_CHP[t] + comp_list[it].zoff_CHP[t])),
                                       (comp_list[it].yon_CHP[t] - comp_list[it].zoff_CHP[t] ==
                                        comp_list[it].b_CHP[t] - comp_list[it].b_CHP[t - 1])]

                        # min up time constraints
                        if UPmin_CHP > 0:
                            if t >= UPmin_CHP:
                                constr += [comp_list[it].b_CHP[t] >= comp_list[it].ysum_CHP[t],
                                           comp_list[it].ysum_CHP[t] == (comp_list[it].ysum_CHP[t - 1] -
                                                                         comp_list[it].yon_CHP[t - UPmin_CHP] +
                                                                         comp_list[it].yon_CHP[t])]

                            elif 1 <= t < UPmin_CHP:
                                constr += [comp_list[it].b_CHP[t] >= comp_list[it].ysum_CHP[t],
                                           comp_list[it].ysum_CHP[t] == (comp_list[it].ysum_CHP[t - 1] +
                                                                         comp_list[it].yon_CHP[t])]

                            if 0 < Rini_CHP < UPmin_CHP:
                                if t < (UPmin_CHP - Rini_CHP):
                                    constr += [comp_list[it].b_CHP[t] == 1,
                                               comp_list[it].yon_CHP[t] == 0, comp_list[it].zoff_CHP[t] == 0]

                            elif Rini_CHP >= UPmin_CHP:
                                if t == 0:
                                    constr += [comp_list[it].zoff_CHP[t] == 1 - comp_list[it].b_CHP[t],
                                               comp_list[it].yon_CHP[t] == 0]

                        if DNmin_CHP > 0:

                            if t >= DNmin_CHP:
                                constr += [(1 - comp_list[it].b_CHP[t]) >= comp_list[it].zsum_CHP[t],
                                           comp_list[it].zsum_CHP[t] == (comp_list[it].zsum_CHP[t - 1] -
                                                                         comp_list[it].zoff_CHP[t - DNmin_CHP] +
                                                                         comp_list[it].zoff_CHP[t])]

                            if 1 <= t < DNmin_CHP:
                                constr += [(1 - comp_list[it].b_CHP[t]) >= comp_list[it].zsum_CHP[t],
                                           comp_list[it].zsum_CHP[t] == (comp_list[it].zsum_CHP[t - 1] +
                                                                         comp_list[it].zoff_CHP[t])]

                            if 0 < Dini_CHP < DNmin_CHP:
                                if t < (DNmin_CHP - Dini_CHP):
                                    constr += [comp_list[it].b_CHP[t] == 0, comp_list[it].yon_CHP[t] == 0,
                                               comp_list[it].zoff_CHP[t] == 0]

                            elif Dini_CHP >= DNmin_CHP:
                                if t == 0:
                                    constr += [comp_list[it].zoff_CHP[t] == 0,
                                               comp_list[it].yon_CHP[t] == comp_list[it].b_CHP[t]]

                    it = it + 1

                elif item == 'GSHP_1' or item == 'GSHP_2':

                    Qmax_GSHP = math.ceil(capacities_conv.loc[((capacities_conv.hub == hub) &
                                                               (capacities_conv.tech == item)), 'value'].squeeze())
                    Qmin_GSHP = 0

                    comp_list.append(GSHP(num_opt_var))

                    power_list.append(-comp_list[it].P_GSHP)
                    heat_list.append(comp_list[it].Q_GSHP)

                    for t in range(num_opt_var):
                        constr += [comp_list[it].Q_GSHP[t] <= comp_list[it].b_GSHP[t] * Qmax_GSHP,
                                   comp_list[it].Q_GSHP[t] >= comp_list[it].b_GSHP[t] * Qmin_GSHP,
                                   comp_list[it].Q_GSHP[t] == comp_list[it].P_GSHP[t] * COP]

                    it = it + 1

                elif item == 'gas_boiler_1' or item == 'gas_boiler_2':

                    Qmax_GB = math.ceil(capacities_conv.loc[((capacities_conv.hub == hub) &
                                                             (capacities_conv.tech == item)), 'value'].squeeze())
                    Qmin_GB = 0

                    x0_GB = 0
                    x1_GB = 0.25 * Qmax_GB
                    x2_GB = 0.5 * Qmax_GB
                    x3_GB = 0.75 * Qmax_GB
                    x4_GB = Qmax_GB

                    Eff1_GB = 0.01 * (21.49 + (182.18 * (1 / 4)) + ((-120.67) * (1 / 4) ** 2))
                    Eff2_GB = 0.01 * (21.49 + (182.18 * (2 / 4)) + ((-120.67) * (2 / 4) ** 2))
                    Eff3_GB = 0.01 * (21.49 + (182.18 * (3 / 4)) + ((-120.67) * (3 / 4) ** 2))
                    Eff4_GB = 0.01 * (21.49 + (182.18 * (4 / 4)) + ((-120.67) * (4 / 4) ** 2))

                    comp_list.append(GB(num_opt_var))

                    heat_list.append(comp_list[it].Q_GB)

                    for t in range(num_opt_var):
                        cost += comp_list[it].C_GB[t]
                        constr += [comp_list[it].Q_GB[t] <= comp_list[it].b_GB[t] * Qmax_GB,
                                   comp_list[it].Q_GB[t] >= comp_list[it].b_GB[t] * Qmin_GB,
                                   comp_list[it].Q_GB[t] == (comp_list[it].w1_GB[t] * x1_GB +
                                                             comp_list[it].w2_GB[t] * x2_GB +
                                                             comp_list[it].w3_GB[t] * x3_GB +
                                                             comp_list[it].w4_GB[t] * x4_GB),
                                   (comp_list[it].b1_GB[t] + comp_list[it].b2_GB[t] +
                                    comp_list[it].b3_GB[t] + comp_list[it].b4_GB[t]) == comp_list[it].b_GB[t],
                                   (comp_list[it].w0_GB[t] + comp_list[it].w1_GB[t] + comp_list[it].w2_GB[t] +
                                    comp_list[it].w3_GB[t] + comp_list[it].w4_GB[t]) == comp_list[it].b_GB[t],
                                   comp_list[it].w0_GB[t] <= comp_list[it].b1_GB[t],
                                   comp_list[it].w1_GB[t] <= comp_list[it].b1_GB[t] + comp_list[it].b2_GB[t],
                                   comp_list[it].w2_GB[t] <= comp_list[it].b3_GB[t] + comp_list[it].b2_GB[t],
                                   comp_list[it].w3_GB[t] <= comp_list[it].b3_GB[t] + comp_list[it].b4_GB[t],
                                   comp_list[it].w4_GB[t] <= comp_list[it].b4_GB[t],
                                   comp_list[it].w0_GB[t] >= 0, comp_list[it].w1_GB[t] >= 0,
                                   comp_list[it].w2_GB[t] >= 0,
                                   comp_list[it].w3_GB[t] >= 0, comp_list[it].w4_GB[t] >= 0,
                                   comp_list[it].w0_GB[t] <= 1, comp_list[it].w1_GB[t] <= 1,
                                   comp_list[it].w2_GB[t] <= 1,
                                   comp_list[it].w3_GB[t] <= 1, comp_list[it].w4_GB[t] <= 1,
                                   comp_list[it].C_GB[t] == C_Fuel * comp_list[it].F_GB[t],
                                   comp_list[it].F_GB[t] == (comp_list[it].w1_GB[t] * (x1_GB / Eff1_GB) +
                                                             comp_list[it].w2_GB[t] * (x2_GB / Eff2_GB) +
                                                             comp_list[it].w3_GB[t] * (x3_GB / Eff3_GB) +
                                                             comp_list[it].w4_GB[t] * (x4_GB / Eff4_GB))]

                    it = it + 1

            for item in list_storage[hub - 1]:

                if item == 'heat_storage':

                    Qmax_Storage = capacities_stor.loc[((capacities_stor.hub == hub) &
                                                        (capacities_stor.tech == item)), 'value'].squeeze()
                    Eff_Storage = storage_details.loc[(storage_details.tech == item), 'stateff'].squeeze()
                    Eff_StorageCh = storage_details.loc[(storage_details.tech == item), 'cyceff'].squeeze()
                    Eff_StorageDc = Eff_StorageCh

                    comp_list.append(Heat_Storage(num_opt_var))

                    constr += [comp_list[it].Q_StorageTot[0] == (Eff_Storage * thermal_storage[hub - 1] +
                                                                 Eff_StorageCh * comp_list[it].Q_StorageCh[0] -
                                                                 Eff_StorageDc * comp_list[it].Q_StorageDc[0])]

                    heat_list.append(comp_list[it].Q_StorageDc)
                    heat_list.append(-comp_list[it].Q_StorageCh)

                    for t in range(num_opt_var):

                        constr += [comp_list[it].Q_StorageCh[t] >= 0,
                                   comp_list[it].Q_StorageCh[t] <= BigM * comp_list[it].b_StorageCh[t],
                                   comp_list[it].Q_StorageDc[t] >= 0,
                                   comp_list[it].Q_StorageDc[t] <= BigM * comp_list[it].b_StorageDc[t],
                                   comp_list[it].Q_StorageTot[t] >= 0.2 * Qmax_Storage,
                                   comp_list[it].Q_StorageTot[t] <= Qmax_Storage,
                                   comp_list[it].b_StorageCh[t] + comp_list[it].b_StorageDc[t] <= 1,
                                   comp_list[it].b_StorageCh[t] >= 0, comp_list[it].b_StorageDc[t] >= 0,
                                   comp_list[it].b_StorageCh[t] <= 1, comp_list[it].b_StorageDc[t] <= 1]
                        if t >= 1:
                            constr += [(comp_list[it].Q_StorageTot[t] ==
                                        Eff_Storage * comp_list[it].Q_StorageTot[t - 1] +
                                        Eff_StorageCh * comp_list[it].Q_StorageCh[t] -
                                        Eff_StorageDc * comp_list[it].Q_StorageDc[t])]

                    it = it + 1

                elif item == 'Battery':

                    Pmax_Battery = capacities_stor.loc[((capacities_stor.hub == hub) &
                                                        (capacities_stor.tech == item)), 'value'].squeeze()
                    Pmin_Battery = 0
                    Eff_Battery = storage_details.loc[(storage_details.tech == item), 'stateff'].squeeze()
                    Eff_BatteryCh = storage_details.loc[(storage_details.tech == item), 'cyceff'].squeeze()
                    Eff_BatteryDc = Eff_BatteryCh

                    c1_Battery = 0.11
                    c2_Battery = 0.32
                    c3_Battery = 0.55
                    c4_Battery = 0.76

                    comp_list.append(Elec_Storage(num_opt_var))

                    power_list.append(comp_list[it].P_BatteryDc)
                    power_list.append(-comp_list[it].P_BatteryCh)

                    constr += [comp_list[it].P_BatteryTot[0] == (Eff_Battery * elec_storage[hub - 1] +
                                                                 Eff_BatteryCh * comp_list[it].P_BatteryCh[0] -
                                                                 (1 / Eff_BatteryDc) * comp_list[it].P_BatteryDc[0]),
                               comp_list[it].w1_Battery[0] == (
                                       battery_depth[hub - 1][0] + comp_list[it].p1_BatteryCh[0] -
                                       comp_list[it].p1_BatteryDc[0]),
                               comp_list[it].w2_Battery[0] == (
                                       battery_depth[hub - 1][1] + comp_list[it].p2_BatteryCh[0] -
                                       comp_list[it].p2_BatteryDc[0]),
                               comp_list[it].w3_Battery[0] == (
                                       battery_depth[hub - 1][2] + comp_list[it].p3_BatteryCh[0] -
                                       comp_list[it].p3_BatteryDc[0]),
                               comp_list[it].w4_Battery[0] == (
                                       battery_depth[hub - 1][3] + comp_list[it].p4_BatteryCh[0] -
                                       comp_list[it].p4_BatteryDc[0])]

                    for t in range(num_opt_var):

                        # cost += comp_list[it].C_Battery[t]
                        constr += [comp_list[it].P_BatteryTot[t] >= 0.2 * Pmax_Battery,
                                   comp_list[it].P_BatteryTot[t] <= 0.8 * Pmax_Battery,
                                   comp_list[it].P_BatteryCh[t] >= 0,
                                   comp_list[it].P_BatteryCh[t] <= BigM * comp_list[it].b_BatteryCh[t],
                                   comp_list[it].P_BatteryDc[t] >= 0,
                                   comp_list[it].P_BatteryDc[t] <= BigM * comp_list[it].b_BatteryDc[t],
                                   comp_list[it].b_BatteryCh[t] + comp_list[it].b_BatteryDc[t] <= 1,
                                   comp_list[it].w1_Battery[t] <= 0.2, comp_list[it].w2_Battery[t] <= 0.2,
                                   comp_list[it].w3_Battery[t] <= 0.2, comp_list[it].w4_Battery[t] <= 0.2,
                                   comp_list[it].w1_Battery[t] >= 0, comp_list[it].w2_Battery[t] >= 0,
                                   comp_list[it].w3_Battery[t] >= 0, comp_list[it].w4_Battery[t] >= 0,
                                   comp_list[it].p1_BatteryCh[t] >= 0, comp_list[it].p2_BatteryCh[t] >= 0,
                                   comp_list[it].p3_BatteryCh[t] >= 0, comp_list[it].p4_BatteryCh[t] >= 0,
                                   comp_list[it].p1_BatteryDc[t] >= 0, comp_list[it].p2_BatteryDc[t] >= 0,
                                   comp_list[it].p3_BatteryDc[t] >= 0, comp_list[it].p4_BatteryDc[t] >= 0,
                                   comp_list[it].p1_BatteryCh[t] <= 0.2 - comp_list[it].w1_Battery[t],
                                   comp_list[it].p2_BatteryCh[t] <= 0.2 - comp_list[it].w2_Battery[t],
                                   comp_list[it].p3_BatteryCh[t] <= 0.2 - comp_list[it].w3_Battery[t],
                                   comp_list[it].p4_BatteryCh[t] <= 0.2 - comp_list[it].w4_Battery[t],
                                   comp_list[it].p1_BatteryDc[t] <= comp_list[it].w1_Battery[t],
                                   comp_list[it].p2_BatteryDc[t] <= comp_list[it].w2_Battery[t],
                                   comp_list[it].p3_BatteryDc[t] <= comp_list[it].w3_Battery[t],
                                   comp_list[it].p4_BatteryDc[t] <= comp_list[it].w4_Battery[t],
                                   ((1 / Eff_BatteryDc) * comp_list[it].P_BatteryDc[t] ==
                                    (comp_list[it].p1_BatteryDc[t] + comp_list[it].p2_BatteryDc[t] +
                                     comp_list[it].p3_BatteryDc[t] + comp_list[it].p4_BatteryDc[t]) * Pmax_Battery),
                                   (Eff_BatteryCh * comp_list[it].P_BatteryCh[t] ==
                                    (comp_list[it].p1_BatteryCh[t] + comp_list[it].p2_BatteryCh[t] +
                                     comp_list[it].p3_BatteryCh[t] + comp_list[it].p4_BatteryCh[
                                         t]) * Pmax_Battery)]  # ,
                        # comp_list[it].C_Battery[t] == ((c1_Battery * (comp_list[it].p1_BatteryCh[t] +
                        #                                              comp_list[it].p1_BatteryDc[t]) +
                        #                                c2_Battery * (comp_list[it].p2_BatteryCh[t] +
                        #                                              comp_list[it].p2_BatteryDc[t]) +
                        #                                c3_Battery * (comp_list[it].p3_BatteryCh[t] +
                        #                                              comp_list[it].p3_BatteryDc[t]) +
                        #                                c4_Battery * (comp_list[it].p4_BatteryCh[t] +
                        #                                              comp_list[it].p4_BatteryDc[t]))
                        # * Pmax_Battery)]
                        if t >= 1:
                            constr += [
                                comp_list[it].P_BatteryTot[t] == (Eff_Battery * comp_list[it].P_BatteryTot[t - 1] +
                                                                  Eff_BatteryCh * comp_list[it].P_BatteryCh[t] -
                                                                  (1 / Eff_BatteryDc) * comp_list[it].P_BatteryDc[t]),
                                comp_list[it].w1_Battery[t] == (comp_list[it].w1_Battery[t - 1] +
                                                                comp_list[it].p1_BatteryCh[t] -
                                                                comp_list[it].p1_BatteryDc[t]),
                                comp_list[it].w2_Battery[t] == (comp_list[it].w2_Battery[t - 1] +
                                                                comp_list[it].p2_BatteryCh[t] -
                                                                comp_list[it].p2_BatteryDc[t]),
                                comp_list[it].w3_Battery[t] == (comp_list[it].w3_Battery[t - 1] +
                                                                comp_list[it].p3_BatteryCh[t] -
                                                                comp_list[it].p3_BatteryDc[t]),
                                comp_list[it].w4_Battery[t] == (comp_list[it].w4_Battery[t - 1] +
                                                                comp_list[it].p4_BatteryCh[t] -
                                                                comp_list[it].p4_BatteryDc[t])]

                    it = it + 1

            R_GridOut = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), 'el_tariff'].values.tolist()
            R_GridIn = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), 'feed_in_tariff'].values.tolist()

            comp_list.append(Elec_Grid(num_opt_var))
            power_list.append(comp_list[it].P_GridOut)
            power_list.append(-comp_list[it].P_GridIn)

            for idx in range(len(tran_list)):
                if tran_list[idx].origin == hub:
                    power_list.append(-tran_list[idx].P_strt)
                    heat_list.append(-tran_list[idx].Q_strt)

                elif tran_list[idx].recpnt == hub:
                    power_list.append(tran_list[idx].P_strt)
                    heat_list.append(tran_list[idx].Q_strt)

            if len(power_list) < 24:
                t = len(power_list)
                while t <= 23:
                    power_list.append([0] * num_opt_var)
                    t = t + 1

            if len(heat_list) < 24:
                t = len(heat_list)
                while t <= 23:
                    heat_list.append([0] * num_opt_var)
                    t = t + 1

            for t in range(num_opt_var):
                # Demand
                cost += comp_list[it].C_Grid[t]  # + (cp.huber(cp.norm(comp_list[it].P_Slack[t]), P_delta) +
                #   cp.huber(cp.norm(comp_list[it].Q_Slack[t]), Q_delta))

                constr += [P_Demand[t] == (power_list[0][t] + power_list[1][t] + power_list[2][t] + power_list[3][t] +
                                           power_list[4][t] + power_list[5][t] + power_list[6][t] + power_list[7][t] +
                                           power_list[8][t] + power_list[9][t] + power_list[10][t] + power_list[11][t] +
                                           power_list[12][t] + power_list[13][t] + power_list[14][t] + power_list[15][
                                               t] +
                                           power_list[16][t] + power_list[17][t] + power_list[18][t] + power_list[19][
                                               t] +
                                           power_list[20][t] + power_list[21][t] + power_list[22][t] + power_list[23][
                                               t]),
                           Q_Demand[t] == (heat_list[0][t] + heat_list[1][t] + heat_list[2][t] + heat_list[3][t] +
                                           heat_list[4][t] + heat_list[5][t] + heat_list[6][t] + heat_list[7][t] +
                                           heat_list[8][t] + heat_list[9][t] + heat_list[10][t] + heat_list[11][t] +
                                           heat_list[12][t] + heat_list[13][t] + heat_list[14][t] + heat_list[15][t] +
                                           heat_list[16][t] + heat_list[17][t] + heat_list[18][t] + heat_list[19][t] +
                                           heat_list[20][t] + heat_list[21][t] + heat_list[22][t] + heat_list[23][t])]

                constr += [comp_list[it].b_GridIn[t] + comp_list[it].b_GridOut[t] <= 1,
                           comp_list[it].P_GridIn[t] >= 0,
                           comp_list[it].P_GridIn[t] <= BigM * comp_list[it].b_GridIn[t],
                           comp_list[it].P_GridOut[t] >= 0,
                           comp_list[it].P_GridOut[t] <= BigM * comp_list[it].b_GridOut[t],
                           comp_list[it].C_Grid[t] == (R_GridOut[t] * comp_list[it].P_GridOut[t] -
                                                       R_GridIn[t] * comp_list[it].P_GridIn[t]),
                           comp_list[it].P_Slack[t] >= 0, comp_list[it].Q_Slack[t] >= 0]

            it = it + 1

            demand_power.append(P_Demand[0])
            demand_heat.append(Q_Demand[0])


        # Solve with mosek or Gurobi
        problem = cp.Problem(cp.Minimize(cost), constr)
        problem.solve(solver=cp.MOSEK, verbose=True, save_file='opt_diagnosis.opf',
                      mosek_params={mosek.iparam.intpnt_solve_form: mosek.solveform.dual,
                                    mosek.dparam.optimizer_max_time: 500.0})

        opt_stat = problem.status
        opt_val = problem.value
        opt_time = problem.solver_stats
        print(f"Status:{opt_stat}, with Value:{opt_val:.2f}")

        power = []
        heat = []
        grid_in = []
        grid_out = []
        storage_heatin = []
        storage_heatout = []
        storage_elecin = []
        storage_elecout = []
        tech_cost = []
        storage_cost = []
        grid_cost = []
        final_cost = []
        storage_elec = []
        storage_heat = []
        batt_depth = []
        batt_in = []
        batt_out = []
        CHP_ontime = []
        CHP_offtime = []
        elec_net = []
        heat_net = []

        it = 0
        for hub in range(1, num_hubs + 1):

            g_cost = []
            s_cost = 0
            t_cost = 0
            f_cost = 0
            pwr = []
            ht = []
            st_heatin = []
            st_heatout = []
            st_elecin = []
            st_elecout = []
            st_heat = []
            st_elec = []
            batt_d = [0, 0, 0, 0]
            C_on = []
            C_off = []

            for item in list_techs[hub - 1]:

                if item == 'solar_PV':
                    pwr.append(comp_list[it].P_PV.value[0])
                    ht.append(0)
                    it = it + 1

                if item == 'solar_PVT':
                    pwr.append(comp_list[it].P_PVT.value[0])
                    ht.append(comp_list[it].Q_PVT.value[0])
                    it = it + 1

                if item == 'Gas_CHP_unit_1':
                    pwr.append(comp_list[it].P_mCHP.value[0])
                    ht.append(comp_list[it].Q_mCHP.value[0])
                    t_cost += comp_list[it].C_mCHP.value[0]
                    f_cost += comp_list[it].C_mCHP.value[0]
                    it = it + 1

                if item == 'Gas_CHP_unit_2':
                    pwr.append(comp_list[it].P_CHP.value[0])
                    ht.append(comp_list[it].Q_CHP.value[0])
                    t_cost += comp_list[it].C_CHP.value[0]

                    C_on.append(round(comp_list[it].R_CHP.value[0]))
                    C_off.append(round(comp_list[it].D_CHP.value[0]))
                    f_cost += comp_list[it].C_CHP.value[0]
                    it = it + 1

                if item == 'GSHP_1' or item == 'GSHP_2':
                    pwr.append(-comp_list[it].P_GSHP.value[0])
                    ht.append(comp_list[it].Q_GSHP.value[0])
                    it = it + 1

                if item == 'gas_boiler_1' or item == 'gas_boiler_2':
                    pwr.append(0)
                    ht.append(comp_list[it].Q_GB.value[0])
                    t_cost += comp_list[it].C_GB.value[0]
                    f_cost += comp_list[it].C_GB.value[0]
                    it = it + 1

            for item in list_storage[hub - 1]:

                if item == 'heat_storage':
                    st_heatin.append(-comp_list[it].Q_StorageCh.value[0])
                    st_heatout.append(comp_list[it].Q_StorageDc.value[0])
                    st_heat.append(comp_list[it].Q_StorageTot.value[0])
                    it = it + 1

                if item == 'Battery':
                    st_elecin.append(-comp_list[it].P_BatteryCh.value[0])
                    st_elecout.append(comp_list[it].P_BatteryDc.value[0])
                    st_elec.append(comp_list[it].P_BatteryTot.value[0])
                    # s_cost += comp_list[it].C_Battery.value[0]
                    batt_d = [comp_list[it].w1_Battery.value[0], comp_list[it].w2_Battery.value[0],
                              comp_list[it].w3_Battery.value[0], comp_list[it].w4_Battery.value[0]]
                    batt_in = [comp_list[it].p1_BatteryCh.value[0], comp_list[it].p2_BatteryCh.value[0],
                               comp_list[it].p3_BatteryCh.value[0], comp_list[it].p4_BatteryCh.value[0]]
                    batt_out = [comp_list[it].p1_BatteryDc.value[0], comp_list[it].p2_BatteryDc.value[0],
                                comp_list[it].p3_BatteryDc.value[0], comp_list[it].p4_BatteryDc.value[0]]
                    # f_cost += comp_list[it].C_Battery.value[0]
                    it = it + 1

            g_cost = comp_list[it].C_Grid.value[0]
            f_cost += comp_list[it].C_Grid.value[0]

            if not st_heatin:
                storage_heatin.append(0.0)
            else:
                storage_heatin.extend(st_heatin)

            if not st_heatout:
                storage_heatout.append(0.0)
            else:
                storage_heatout.extend(st_heatout)

            if not st_elecin:
                storage_elecin.append(0.0)
            else:
                storage_elecin.extend(st_elecin)

            if not st_elecout:
                storage_elecout.append(0.0)
            else:
                storage_elecout.extend(st_elecout)

            if not st_heat:
                storage_heat.append(0.0)
            else:
                storage_heat.extend(st_heat)

            if not st_elec:
                storage_elec.append(0.0)
            else:
                storage_elec.extend(st_elec)

            if not C_on:
                CHP_ontime.append(0)
            else:
                CHP_ontime.extend(C_on)

            if not C_off:
                CHP_offtime.append(0)
            else:
                CHP_offtime.extend(C_off)

            batt_depth.append(batt_d)

            power.append(pwr)
            heat.append(ht)
            grid_in.append(-comp_list[it].P_GridIn.value[0])
            grid_out.append(comp_list[it].P_GridOut.value[0])

            grid_cost.append(g_cost)
            final_cost.append(f_cost)
            tech_cost.append(t_cost)
            storage_cost.append(s_cost)

            it = it + 1
            nwk_pwr = []
            nwk_ht = []
            for idx in range(len(tran_list)):
                if tran_list[idx].origin == hub:
                    nwk_pwr.append(-tran_list[idx].P_strt.value[0])
                    nwk_ht.append(-tran_list[idx].Q_strt.value[0])

            for idx in range(len(tran_list)):
                if tran_list[idx].recpnt == hub:
                    nwk_pwr.append(tran_list[idx].P_strt.value[0])
                    nwk_ht.append(tran_list[idx].Q_strt.value[0])

            elec_net.append(nwk_pwr)
            heat_net.append(nwk_ht)

        print('run complete')
        return demand_power, demand_heat, power, heat, grid_in, grid_out, storage_heatin, storage_heatout, \
               storage_elecin, storage_elecout, tech_cost, storage_cost, grid_cost, final_cost, storage_heat, \
               storage_elec, batt_depth, CHP_ontime, CHP_offtime, elec_net, heat_net


    Battery_max = []
    elec_storage = []
    Thermal_max = []
    thermal_storage = []
    battery_depth = []

    for hub in range(1, num_hubs + 1):
        if 'Battery' in list_storage[hub - 1]:
            temp = capacities_stor.loc[((capacities_stor.hub == hub) &
                                        (capacities_stor.tech == 'Battery')), 'value'].squeeze()
            Battery_max.append(temp)
            elec_storage.append(temp * 0.25)

            b_depth = [0, 0, 0, 0]
            if temp > 0:
                for j in range(4):
                    bat_SOC = elec_storage[hub - 1] / temp
                    if bat_SOC >= ((j + 1) * 0.2):
                        b_depth[j] = 0.2

                    elif bat_SOC < ((j + 1) * 0.2) and (bat_SOC >= 0.2 * j):

                        b_depth[j] = bat_SOC - 0.2 * j

                    else:
                        b_depth[j] = 0.0

            battery_depth.append(b_depth)

        else:

            Battery_max.append(0)
            elec_storage.append(0)
            battery_depth.append([0, 0, 0, 0])

        if 'heat_storage' in list_storage[hub - 1]:
            temp = capacities_stor.loc[((capacities_stor.hub == hub) &
                                        (capacities_stor.tech == 'heat_storage')), 'value'].squeeze()
            Thermal_max.append(temp)
            thermal_storage.append(temp * 0.25)
        else:
            Thermal_max.append(0)
            thermal_storage.append(0)

    CHP_Runtime = [0, 0, 0]
    CHP_Downtime = [12, 0, 0]

    init = False
    i = 0

    while (i < 3) and (init == False):

        (thermal_storage_end, elec_storage_end, battery_depth_end, CHP_ontime,
         CHP_offtime) = main_optimize(elec_storage, battery_depth, thermal_storage, CHP_Runtime, CHP_Downtime,
                                      capacities_conv, capacities_stor, tech_details, storage_details, network_cap,
                                      list_techs, list_storage, time_now)[14:19]

        for hub in range(0, num_hubs):
            if (thermal_storage[hub] - 0.1 * Thermal_max[hub]) <= thermal_storage_end[hub] <= (
                    thermal_storage[hub] + 0.1 * Thermal_max[hub]):
                init = True
            else:
                init = False

        thermal_storage = thermal_storage_end
        elec_storage = elec_storage_end
        battery_depth = battery_depth_end
        i += 1

    demand_power_final = []
    demand_heat_final = []
    power_final = []
    heat_final = []
    grid_in_final = []
    grid_out_final = []
    storage_heatin_final = []
    storage_heatout_final = []
    storage_elecin_final = []
    storage_elecout_final = []
    elec_net_final = []
    heat_net_final = []
    tech_cost_final = []
    storage_cost_final = []
    final_cost_final = []
    grid_cost_final = []
    storage_elec_final = []
    battery_depth_final = []
    storage_heat_final = []
    CHP_ontime_final = []
    CHP_offtime_final = []
    SOC_elec = []
    SOC_therm = []
    date_info = []
    time_info = []

    while time_now <= time_end:
        time_now += dt.timedelta(hours=1)
        logger.info(time_now)
        # Optimization based on current state, model and forecast of boundary conditions
        (demand_power, demand_heat, power, heat, grid_in, grid_out, storage_heatin, storage_heatout, storage_elecin,
         storage_elecout, tech_cost, storage_cost, grid_cost, final_cost, storage_heat, storage_elec, batt_depth,
         CHP_ontime, CHP_offtime, elec_net, heat_net) = main_optimize(elec_storage, battery_depth, thermal_storage,
                                                                      CHP_Runtime, CHP_Downtime, capacities_conv,
                                                                      capacities_stor, tech_details, storage_details,
                                                                      network_cap, list_techs, list_storage, time_now)

        demand_power_final.append(demand_power)
        demand_heat_final.append(demand_heat)
        power_final.append(power)
        heat_final.append(heat)
        grid_in_final.append(grid_in)
        grid_out_final.append(grid_out)
        storage_heatin_final.append(storage_heatin)
        storage_heatout_final.append(storage_heatout)
        storage_elecin_final.append(storage_elecin)
        storage_elecout_final.append(storage_elecout)

        elec_net_final.append(elec_net)
        heat_net_final.append(heat_net)

        tech_cost_final.append(tech_cost)
        storage_cost_final.append(storage_cost)
        final_cost_final.append(final_cost)
        grid_cost_final.append(grid_cost)

        storage_heat_final.append(storage_heat)
        storage_elec_final.append(storage_elec)
        battery_depth_final.append(batt_depth)

        CHP_ontime_final.append(CHP_ontime)
        CHP_offtime_final.append(CHP_offtime)

        SOC_e = []
        SOC_th = []



        for hub in range(0, num_hubs):
            if Battery_max[hub] > 0:
                temp = storage_elec[hub] * 100 / Battery_max[hub]
                SOC_e.append(temp)
            else:
                SOC_e.append(0)

            if Thermal_max[hub] > 0:
                temp1 = storage_heat[hub] * 100 / Thermal_max[hub]
                SOC_th.append(temp1)
            else:
                SOC_th.append(0)

        SOC_elec.append(SOC_e)
        SOC_therm.append(SOC_th)

        str1 = str(time_now.day) + "." + str(time_now.month) + "." + str(time_now.year)
        str2 = str(time_now.hour) + ":" + str(time_now.minute) + ":" + str(time_now.second)
        date_info.append([str1])
        time_info.append([str2])
        print("wait")

        elec_storage = storage_elec
        battery_depth = batt_depth
        thermal_storage = storage_heat
        CHP_Runtime = CHP_ontime
        CHP_Downtime = CHP_offtime

    comp_end = time.perf_counter()

    with xlsxwriter.Workbook('results_trcost.xlsx') as workbook:

        savePower(workbook, demand_power_final, power_final, grid_in_final, grid_out_final, storage_elecin_final,
                  storage_elecout_final, elec_net_final, list_techs, list_storage, date_info, time_info, num_hubs)

        saveHeat(workbook, demand_heat_final, heat_final, storage_heatin_final, storage_heatout_final, heat_net_final,
                 list_techs, list_storage, date_info, time_info, num_hubs)

        saveCost(workbook, tech_cost_final, storage_cost_final, final_cost_final, grid_cost_final, date_info, time_info,
                 num_hubs)

        saveStorage(workbook, storage_heat_final, storage_elec_final, battery_depth_final, SOC_elec, SOC_therm,
                    storage_elecin_final, storage_elecout_final, storage_heatin_final, storage_heatout_final,
                    list_storage, date_info, time_info, num_hubs)

        saveChp(workbook, CHP_ontime_final, CHP_offtime_final, list_techs, date_info, time_info, num_hubs)

    print('complete and saved')
    print(comp_end - comp_start)

# if __name__ == "__main__":
#     try:
#         main()
#     except Exception as e:
#         logger.warning(f"An error has occured ({e})")
#     except (KeyboardInterrupt, SystemExit):
#         logger.warning("The main script has been manually interrupted.")
#     finally:
#         logger.info('Finish current run')
