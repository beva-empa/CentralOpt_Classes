import cvxpy as cp
from test import *
import mosek
import datetime as dt
import time


class PV:
    def __init__(self, num_opt_var):
        self.P_PV = cp.Variable(num_opt_var)
        self.b_PV = cp.Variable(num_opt_var, boolean=True)
        self.I_PV = [0] * num_opt_var
        self.TempEff_PV = [0] * num_opt_var


class PVT:
    def __init__(self, num_opt_var):
        self.P_PVT = cp.Variable(num_opt_var)
        self.Q_PVT = cp.Variable(num_opt_var)
        self.Out_PVT = cp.Variable(num_opt_var)
        self.b_PVT = cp.Variable(num_opt_var, boolean=True)
        self.I_PVT = [0] * num_opt_var
        self.TempEff_PVT = [0] * num_opt_var


class mCHP:
    def __init__(self, num_opt_var):
        self.Out_mCHP = cp.Variable(num_opt_var)
        self.P_mCHP = cp.Variable(num_opt_var)
        self.Q_mCHP = cp.Variable(num_opt_var)
        self.C_mCHP = cp.Variable(num_opt_var)
        self.F_mCHP = cp.Variable(num_opt_var)
        self.b_mCHP = cp.Variable(num_opt_var, boolean=True)


class CHP:
    def __init__(self, num_opt_var):
        self.C_CHP = cp.Variable(num_opt_var)
        self.F_CHP = cp.Variable(num_opt_var)
        self.P_CHP = cp.Variable(num_opt_var)
        self.Q_CHP = cp.Variable(num_opt_var)

        self.w11_CHP = cp.Variable(num_opt_var)
        self.w12_CHP = cp.Variable(num_opt_var)
        self.w13_CHP = cp.Variable(num_opt_var)
        self.w14_CHP = cp.Variable(num_opt_var)
        self.w21_CHP = cp.Variable(num_opt_var)
        self.w22_CHP = cp.Variable(num_opt_var)
        self.w23_CHP = cp.Variable(num_opt_var)
        self.w24_CHP = cp.Variable(num_opt_var)
        self.R_CHP = cp.Variable(1)
        self.D_CHP = cp.Variable(1)
        self.b_CHP = cp.Variable(num_opt_var, boolean=True)
        self.b1_CHP = cp.Variable(num_opt_var, boolean=True)
        self.b2_CHP = cp.Variable(num_opt_var, boolean=True)

        self.yon_CHP = cp.Variable(num_opt_var, boolean=True)
        self.zoff_CHP = cp.Variable(num_opt_var, boolean=True)
        self.ysum_CHP = cp.Variable(num_opt_var)
        self.zsum_CHP = cp.Variable(num_opt_var)


class GSHP:
    def __init__(self, num_opt_var):
        self.b_GSHP = cp.Variable(num_opt_var, boolean=True)
        self.P_GSHP = cp.Variable(num_opt_var)
        self.Q_GSHP = cp.Variable(num_opt_var)


class GB:
    def __init__(self, num_opt_var):
        self.F_GB = cp.Variable(num_opt_var)
        self.C_GB = cp.Variable(num_opt_var)
        self.Q_GB = cp.Variable(num_opt_var)

        self.w0_GB = cp.Variable(num_opt_var)
        self.w1_GB = cp.Variable(num_opt_var)
        self.w2_GB = cp.Variable(num_opt_var)
        self.w3_GB = cp.Variable(num_opt_var)
        self.w4_GB = cp.Variable(num_opt_var)

        self.b_GB = cp.Variable(num_opt_var, boolean=True)
        self.b1_GB = cp.Variable(num_opt_var, boolean=True)
        self.b2_GB = cp.Variable(num_opt_var, boolean=True)
        self.b3_GB = cp.Variable(num_opt_var, boolean=True)
        self.b4_GB = cp.Variable(num_opt_var, boolean=True)


class Heat_Storage:
    def __init__(self, num_opt_var):
        self.Q_StorageCh = cp.Variable(num_opt_var)
        self.Q_StorageDc = cp.Variable(num_opt_var)
        self.Q_StorageTot = cp.Variable(num_opt_var)
        self.b_StorageCh = cp.Variable(num_opt_var, boolean=True)
        self.b_StorageDc = cp.Variable(num_opt_var, boolean=True)


class Elec_Storage:
    def __init__(self, num_opt_var):
        self.C_Battery = cp.Variable(num_opt_var)
        self.P_BatteryCh = cp.Variable(num_opt_var)
        self.P_BatteryDc = cp.Variable(num_opt_var)
        self.P_BatteryTot = cp.Variable(num_opt_var)
        self.w1_Battery = cp.Variable(num_opt_var)
        self.w2_Battery = cp.Variable(num_opt_var)
        self.w3_Battery = cp.Variable(num_opt_var)
        self.w4_Battery = cp.Variable(num_opt_var)
        self.p1_BatteryCh = cp.Variable(num_opt_var)
        self.p2_BatteryCh = cp.Variable(num_opt_var)
        self.p3_BatteryCh = cp.Variable(num_opt_var)
        self.p4_BatteryCh = cp.Variable(num_opt_var)
        self.p1_BatteryDc = cp.Variable(num_opt_var)
        self.p2_BatteryDc = cp.Variable(num_opt_var)
        self.p3_BatteryDc = cp.Variable(num_opt_var)
        self.p4_BatteryDc = cp.Variable(num_opt_var)
        self.b_BatteryCh = cp.Variable(num_opt_var, boolean=True)
        self.b_BatteryDc = cp.Variable(num_opt_var, boolean=True)


class Elec_Grid:
    def __init__(self, num_opt_var):
        self.C_Grid = cp.Variable(num_opt_var)
        self.P_GridIn = cp.Variable(num_opt_var)
        self.P_GridOut = cp.Variable(num_opt_var)

        self.P_Slack = cp.Variable(num_opt_var)
        self.Q_Slack = cp.Variable(num_opt_var)

        self.b_GridIn = cp.Variable(num_opt_var, boolean=True)
        self.b_GridOut = cp.Variable(num_opt_var, boolean=True)

# num_opt_var = 24
# cost = 0
# constr = []
# I_Solar = cp.Variable(num_opt_var)
# Pmax_PV = 0
# d_PV = 1
# P_Comp = cp.Variable(num_opt_var)
# Eff_PV = 1
# TempEff_PV = 1
# d = PV(I_Solar, num_opt_var, Pmax_PV, d_PV)
# print(d.I_PV)
#
# beta = 0.003
# d_PV = 0.15
# d_PVT = 0.18
# COP = 4.5
# C_Fuel = 0.115
# Tstc = 25
# Tnoct = 48.3
# Tstd = 20
# time_start = dt.datetime(2018, 1, 1, 0, 0, 0)
# time_end = dt.datetime(2018, 1, 1, 3, 0, 0)
# time_now = time_start
# start_time = dt.datetime(2018, 1, 1)
# num_opt_var = 24
# constr = []
# Pmax_PV = 2540
# Eff_PV = 0.3
# Pmin_PV = 0
# demand_data = get_data(start_time)
# Ta = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), 'temp'].values.tolist()
# I_Solar = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), 'solar_roof'].values.tolist()
# P_Demand = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), 'elec_1'].values.tolist()
# li = []
# li.append(PV(num_opt_var))
#
#
# print(li[0].P_PV)
#
# for t in range(num_opt_var):
#     li[0].I_PV[t] = I_Solar[t] * (Pmax_PV / d_PV)
#     li[0].TempEff_PV[t] = 1 + ((-beta) * ((Ta[t] - Tstc) + (Tnoct - Ta[t]) * (I_Solar[t] / 0.8)))
#
# for t in range(num_opt_var):
#
#     constr += [li[0].P_PV[t] >= 0,
#                li[0].P_PV[t] <= li[0].b_PV[t] * Eff_PV * li[0].TempEff_PV[t] * li[0].I_PV[t]]
#
# print('ghb')
#
# C_Grid = cp.Variable(num_opt_var)
# P_GridIn = cp.Variable(num_opt_var)
# P_GridOut = cp.Variable(num_opt_var)
#
# R_GridOut = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), 'el_tariff'].values.tolist()
# R_GridIn = demand_data.loc[time_now: time_now + dt.timedelta(hours=23), 'feed_in_tariff'].values.tolist()
#
# b_GridIn = cp.Variable(num_opt_var, boolean=True)
# b_GridOut = cp.Variable(num_opt_var, boolean=True)
#
# cost = 0
# for t in range(num_opt_var):
#     # Demand
#     cost += C_Grid[t]
#     constr += [P_Demand[t] == (li[0].P_PV[t] + P_GridOut[t] - P_GridIn[t]),
#                b_GridIn[t] + b_GridOut[t] <= 1,
#                P_GridIn[t] >= 0, P_GridIn[t] <= 10000000000000 * b_GridIn[t],
#                P_GridOut[t] >= 0, P_GridOut[t] <= 10000000000000 * b_GridOut[t],
#                C_Grid[t] == R_GridOut[t] * P_GridOut[t] - R_GridIn[t] * P_GridIn[t]]
#
#     # Solve with mosek or Gurobi
# problem = cp.Problem(cp.Minimize(cost), constr)
# problem.solve(solver=cp.MOSEK, verbose=True, save_file='opt_diagnosis.opf',
#               mosek_params={mosek.iparam.intpnt_solve_form: mosek.solveform.dual,
#                             mosek.dparam.optimizer_max_time: 100.0})
# print('test')
# class test1:
#     def __init__(self, cost1):
#         self.cost1 = cost1 + 5
#
# cost = 5
# d = test1(cost)
# cost = d.cost1
# print(cost)
