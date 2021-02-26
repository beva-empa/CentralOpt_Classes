from scipy.io import loadmat
from matplotlib.cbook import boxplot_stats
import numpy as np
import datetime as dt
import pandas as pd
import math
import os
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from matplotlib import pylab

import matplotlib.pyplot as plt

# plt.subplots()
input_path = 'results_trcost.xlsx'
plot_info = pd.read_excel(input_path, sheet_name='final power')

sum_column = plot_info["To hub2"] + plot_info["To hub3"] + plot_info["From hub2"] + plot_info["From hub3"]
plot_info["net"] = sum_column
plot_info["net pos"] = plot_info["net"].clip(lower=0)
plot_info["net neg"] = plot_info["net"].clip(upper=0)

ax1 = plot_info['demand 1'].plot(color='black', label='demand', linewidth=1.5)
ax1.stackplot(plot_info.index.values, plot_info['solar_PV'].values, plot_info['solar_PVT'].values,
              plot_info['Gas_CHP_unit_1'].values, plot_info['Gas_CHP_unit_2'].values,
              plot_info['grid output'].values, plot_info['Battery output'].values,
              colors=['yellow', 'cyan', 'magenta', 'forestgreen',  'b', 'orangered'],
              labels= ['Solar PV', 'Solar PVT', 'mCHP', ' CHP', 'From Grid', 'From Battery'], alpha=0.3)

sum_line1 = plot_info['demand 1'] - plot_info["GSHP_1"]
plot_info["net1"] = sum_line1
sum_line2 = plot_info['demand 1'] - plot_info["GSHP_1"] - plot_info["Battery input"]
plot_info["net2"] = sum_line2
sum_line3 = plot_info['demand 1'] - plot_info["GSHP_1"] - plot_info["Battery input"] - plot_info["net neg"]
plot_info["net3"] = sum_line3
sum_line4 = plot_info['demand 1'] - plot_info["GSHP_1"] - plot_info["Battery input"] - plot_info["net neg"] - plot_info["grid input"]
plot_info["net4"] = sum_line4
ax1.plot(plot_info["net1"], color='navy', label='GSHP', linewidth=1.5, linestyle=':')
ax1.plot(plot_info["net2"], color='black', label='To Battery', linewidth=1.5, linestyle='--')
ax1.plot(plot_info["net3"], color='navy', label='To H2,H3', linewidth=1.5, linestyle='-.')
ax1.plot(plot_info["net4"], color='black', label='To H2,H3', linewidth=1.5, linestyle=':')
ax1.set_ylabel('Power [kW]')
ax1.set_xlabel('Time [Hrs]')
ax1.set_xlim(0,72)
handles, labels = ax1.get_legend_handles_labels()
plt.title('Different electricity supply versus demands (Hub 1)')
box1 = ax1.get_position()
ax1.set_position([box1.x0, box1.y0 + box1.height * 0.3, box1.width, box1.height * 0.8])
leg1 = ax1.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
# ax1.add_artist(leg1)
ax1.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=3)
plt.savefig('hub1_demand.png', dpi=2000)
plt.close()
# ----------------------------------------------------------------------------------------------------------------------
plt.subplots()

sum_column = plot_info["To hub1"] + plot_info["To hub3.1"] + plot_info["From hub1"] + plot_info["From hub3.1"]
plot_info["net"] = sum_column
plot_info["net pos"] = plot_info["net"].clip(lower=0)
plot_info["net neg"] = plot_info["net"].clip(upper=0)

ax1 = plot_info['demand 2'].plot(color='black', label='demand', linewidth=1.5)
ax1.stackplot(plot_info.index.values, plot_info['solar_PV.1'].values, plot_info['grid output.1'].values,
              plot_info['net pos'].values,
              colors=['yellow', 'b', 'cyan'], labels= ['Solar PV', 'From Grid', 'From H1,H3'], alpha=0.3)

sum_line1 = plot_info['demand 2'] - plot_info["GSHP_2"]
plot_info["net1"] = sum_line1
sum_line2 = plot_info['demand 2'] - plot_info["GSHP_2"] - plot_info["net neg"]
plot_info["net2"] = sum_line2
ax1.plot(plot_info["net1"], color='navy', label='GSHP', linewidth=1.5, linestyle=':')
# ax1.plot(plot_info["net2"], color='black', label='To H1,H3', linewidth=1.5, linestyle='--')
ax1.set_ylabel('Power [kW]')
ax1.set_xlabel('Time [Hrs]')
ax1.set_xlim(0,72)
handles, labels = ax1.get_legend_handles_labels()
plt.title('Different electricity supply versus demands (Hub 2)')
box1 = ax1.get_position()
ax1.set_position([box1.x0, box1.y0 + box1.height * 0.3, box1.width, box1.height * 0.8])
leg1 = ax1.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
# ax1.add_artist(leg1)
ax1.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=3)
plt.savefig('hub2_demand.png', dpi=2000)
plt.close()
# ----------------------------------------------------------------------------------------------------------------------
sum_column = plot_info["To hub1.1"] + plot_info["To hub2.1"] + plot_info["From hub1.1"] + plot_info["From hub2.1"]
plot_info["net"] = sum_column
plot_info["net pos"] = plot_info["net"].clip(lower=0)
plot_info["net neg"] = plot_info["net"].clip(upper=0)

ax1 = plot_info['demand 3'].plot(color='black', label='demand', linewidth=1.5)
ax1.stackplot(plot_info.index.values, plot_info['solar_PV.2'].values, plot_info['grid output.2'].values,
              plot_info['net pos'].values, labels= ['Solar PV', 'From Grid', 'From H1,H2'],
              colors=['yellow', 'b', 'cyan'], alpha=0.3)

sum_line1 = plot_info['demand 3'] - plot_info["GSHP_1.1"]
plot_info["net1"] = sum_line1
sum_line2 = plot_info['demand 3'] - plot_info["GSHP_1.1"] - plot_info["net neg"]
plot_info["net2"] = sum_line2
ax1.plot(plot_info["net1"], color='navy', label='GSHP', linewidth=1.5, linestyle=':')
# ax1.plot(plot_info["net2"], color='black', label='To H1,H2', linewidth=1.5, linestyle='--')
ax1.set_ylabel('Power [kW]')
ax1.set_xlabel('Time [Hrs]')
ax1.set_xlim(0,72)
handles, labels = ax1.get_legend_handles_labels()
plt.title('Different electricity supply versus demands (Hub 3)')
box1 = ax1.get_position()
ax1.set_position([box1.x0, box1.y0 + box1.height * 0.3, box1.width, box1.height * 0.8])
leg1 = ax1.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
# ax1.add_artist(leg1)
ax1.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=3)
plt.savefig('hub3_demand.png', dpi=2000)
plt.close()
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------------


input_path = 'results_trcost.xlsx'
plot_info = pd.read_excel(input_path, sheet_name='final heat')

sum_column = plot_info["To hub2"] + plot_info["To hub3"] + plot_info["From hub2"] + plot_info["From hub3"]
plot_info["net"] = sum_column
plot_info["net pos"] = plot_info["net"].clip(lower=0)
plot_info["net neg"] = plot_info["net"].clip(upper=0)

ax1 = plot_info['demand 1'].plot(color='black', label='demand', linewidth=1.5)
ax1.stackplot(plot_info.index.values,  plot_info["GSHP_1"], plot_info['solar_PVT'].values,
              plot_info['Gas_CHP_unit_1'].values, plot_info['Gas_CHP_unit_2'].values,
              plot_info['Storage output'].values, plot_info['net pos'].values,
              colors=['forestgreen', 'cyan', 'magenta', 'yellow',  'b', 'peru'],
              labels= ['GSHP', 'Solar PVT', 'mCHP', ' CHP', 'From storage', 'From H2, H3'], alpha=0.3)


sum_line2 = plot_info['demand 1'] - plot_info["Storage input"]
plot_info["net2"] = sum_line2
# sum_line3 = plot_info['demand 1'] - plot_info["Storage input"] - plot_info["net neg"]
# plot_info["net3"] = sum_line3
ax1.plot(plot_info["net2"], color='black', label='To storage', linewidth=1.5, linestyle='--')
# ax1.plot(plot_info["net3"], color='navy', label='To H2,H3', linewidth=1.5, linestyle=':')
ax1.set_ylabel('Heat [kW]')
ax1.set_xlabel('Time [Hrs]')
ax1.set_xlim(0,72)
handles, labels = ax1.get_legend_handles_labels()
plt.title('Different heat supply versus demands (Hub 1)')
box1 = ax1.get_position()
ax1.set_position([box1.x0, box1.y0 + box1.height * 0.3, box1.width, box1.height * 0.8])
leg1 = ax1.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
# ax1.add_artist(leg1)
ax1.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=3)
plt.savefig('hub1_h_demand.png', dpi=2000)
plt.close()
# ----------------------------------------------------------------------------------------------------------------------


sum_column = plot_info["To hub1"] + plot_info["To hub3.1"] + plot_info["From hub1"] + plot_info["From hub3.1"]
plot_info["net"] = sum_column
plot_info["net pos"] = plot_info["net"].clip(lower=0)
plot_info["net neg"] = plot_info["net"].clip(upper=0)

ax1 = plot_info['demand 2'].plot(color='black', label='demand', linewidth=1.5)
ax1.stackplot(plot_info.index.values, plot_info["GSHP_2"],
              plot_info['Storage output.1'].values, plot_info['net pos'].values,
              colors=['forestgreen', 'b', 'peru'], labels= ['GSHP', 'From storage', 'From H1,H3'], alpha=0.3)

sum_line1 = plot_info['demand 2'] - plot_info["Storage input.1"]
plot_info["net1"] = sum_line1
sum_line2 = plot_info['demand 2'] - plot_info["Storage input.1"] - plot_info["net neg"]
plot_info["net2"] = sum_line2
ax1.plot(plot_info["net1"], color='black', label='To Storage', linewidth=1.5, linestyle=':')
ax1.plot(plot_info["net2"], color='black', label='To H1,H3', linewidth=1.5, linestyle='--')

ax1.set_ylabel('Heat [kW]')
ax1.set_xlabel('Time [Hrs]')
ax1.set_xlim(0,72)
handles, labels = ax1.get_legend_handles_labels()
plt.title('Different heat supply versus demands (Hub 2)')
box1 = ax1.get_position()
ax1.set_position([box1.x0, box1.y0 + box1.height * 0.3, box1.width, box1.height * 0.8])
leg1 = ax1.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
# ax1.add_artist(leg1)
ax1.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=3)
plt.savefig('hub2_h_demand.png', dpi=2000)
plt.close()
# ----------------------------------------------------------------------------------------------------------------------

sum_column = plot_info["To hub1.1"] + plot_info["To hub2.1"] + plot_info["From hub1.1"] + plot_info["From hub2.1"]
plot_info["net"] = sum_column
plot_info["net pos"] = plot_info["net"].clip(lower=0)
plot_info["net neg"] = plot_info["net"].clip(upper=0)

ax1 = plot_info['demand 3'].plot(color='black', label='demand', linewidth=1.5)
ax1.stackplot(plot_info.index.values, plot_info['GSHP_1.1'].values, plot_info['net pos'].values,
              colors=['forestgreen', 'peru'], labels= ['GSHP PV', 'From H1,H2'], alpha=0.3)


sum_line2 = plot_info['demand 3'] - plot_info["net neg"]
plot_info["net2"] = sum_line2
ax1.plot(plot_info["net2"], color='black', label='To H1,H2', linewidth=1.5, linestyle='--')

ax1.set_ylabel('Heat [kW]')
ax1.set_xlabel('Time [Hrs]')
ax1.set_xlim(0,72)
handles, labels = ax1.get_legend_handles_labels()
plt.title('Different heat supply versus demands (Hub 3)')
box1 = ax1.get_position()
ax1.set_position([box1.x0, box1.y0 + box1.height * 0.3, box1.width, box1.height * 0.8])
leg1 = ax1.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
# ax1.add_artist(leg1)
ax1.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=3)
plt.savefig('hub3_h_demand.png', dpi=2000)
plt.close()


# def model_visualize(df_elec_demand, df_elec_prod, df_thermal_demand, df_thermal_prod, df_storage, df_storage_SOC,
#                     df_Grid, df_CHP2_operation, df_CHP2, df_network_exp, df_network_imp):
#     # print(len(df_elec_demand))
#     if len(df_elec_demand) > 0:
#         plt.subplots()
#         ax1 = df_elec_demand['elec supply (H' + str(i + 1) + ')'].plot(color='gold',
#                                                                        label='electricity supply (H' + str(i + 1) + ')')
#
#         ax1.set_ylabel('Power [kW]')
#         ax1.set_xlabel('hours')
#         df_elec_demand['grid tariff'].plot(ax=ax1, color='darkgoldenrod', linestyle='--', label='grid tariff',
#                                            secondary_y=True, legend=True)
#         plt.ylabel('Grid tariff [CHF]')
#         ax1.right_ax.set_ylim(0, 2)
#         plt.xlim(0, len(df_elec_demand['GSHP_elec']))
#         handles, labels = ax1.right_ax.get_legend_handles_labels()
#         plt.title('Different electricity demands versus total supply (H' + str(i + 1) + ')')
#         box1 = ax1.get_position()
#         ax1.set_position([box1.x0, box1.y0 + box1.height * 0.2, box1.width, box1.height * 0.8])
#         leg1 = ax1.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
#         ax1.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=2)
#         ax1.add_artist(leg1)
#         plt.savefig('(H' + str(i + 1) + ')' + 'Different electricity demands versus total supply_beaudm.png', dpi=2000)
# def model_visualize(df_elec_demand, df_elec_prod, df_thermal_demand, df_thermal_prod, df_storage, df_storage_SOC, df_Grid, df_CHP2_operation, df_CHP2, df_network_exp, df_network_imp):
#
#     #print(len(df_elec_demand))
#     if len(df_elec_demand) > 0 :
#         plt.subplots()
#         ax1 = df_elec_demand['elec supply (H' + str(i+1) + ')'].plot(color='gold', label= 'electricity supply (H' + str(i+1) + ')')
#         ax1.stackplot(df_elec_demand.index.values,df_elec_demand['hub elec demands (H' + str(i+1) + ')'].values, df_elec_demand['GSHP_elec'], df_elec_demand['battery input'].values, df_elec_demand['grid injection'].values, colors=['yellow', 'forestgreen', 'magenta', 'saddlebrown'], labels= ['hub' + str(i+1) + ' electricity demands', 'GSHP electricity demands', 'battery input', 'grid injection'], alpha=0.5)
#         ax1.set_ylabel('Power [kW]')
#         ax1.set_xlabel('hours')
#         df_elec_demand['grid tariff'].plot(ax=ax1,color='darkgoldenrod',  linestyle='--', label= 'grid tariff', secondary_y=True, legend=True)
#         plt.ylabel('Grid tariff [CHF]')
#         ax1.right_ax.set_ylim(0,2)
#         plt.xlim(0, len(df_elec_demand['GSHP_elec']))
#         handles, labels = ax1.right_ax.get_legend_handles_labels()
#         plt.title('Different electricity demands versus total supply (H' + str(i+1) + ')')
#         box1 = ax1.get_position()
#         ax1.set_position([box1.x0, box1.y0 + box1.height * 0.2, box1.width, box1.height * 0.8])
#         leg1 = ax1.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
#         ax1.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=2)
#         ax1.add_artist(leg1)
#         plt.savefig('(H' + str(i+1) + ')' + 'Different electricity demands versus total supply_beaudm.png', dpi=2000)
#
# #print(len(df_elec_prod))
# if len(df_elec_prod) > 0 :
#     plt.subplots()
#     ax2 = df_elec_prod['electricity demand (H' + str(i+1) + ')'].plot(color='gold', label='electricity demand')
#     ax2.stackplot(df_elec_prod.index.values, df_elec_prod['PV production'].values,  df_elec_prod['PVT elec production'].values, df_elec_prod['CHP 1 elec production'].values, df_elec_prod['CHP 2 elec production'].values, df_elec_prod['battery output'].values, df_elec_prod['grid supply'].values, colors = ['yellow', 'darkorange', 'deepskyblue', 'blue','magenta', 'saddlebrown'], labels = ['PV production', 'PVT production', 'CHP1 production', 'CHP2 production', 'battery extraction', 'grid supply'], alpha=0.5)
#     ax2.set_ylabel('Power [kW]')
#     ax2.set_xlabel('hours')
#     #ax22 = ax2.twinx()
#     #df_elec_prod['grid tariff'].plot(ax=ax22, color='darkgoldenrod',  linestyle='--', label='grid tariff', secondary_y=True, legend=True)
#     df_elec_prod['grid tariff'].plot(ax=ax2, color='darkgoldenrod',  linestyle='--', label='grid tariff', secondary_y=True, legend=True)
#     plt.ylabel('Grid tariff [CHF]')
#     ax2.right_ax.set_ylim(0,2)
#     plt.xlim(0, len(df_elec_prod['PV production']))
#     handles, labels = ax2.right_ax.get_legend_handles_labels()
#     plt.title('Electricity production (H' + str(i+1) + ')')
#     box2 = ax2.get_position()
#     ax2.set_position([box2.x0, box2.y0 + box2.height * 0.2, box2.width, box2.height * 0.8])
#     leg1 = ax2.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
#     # leg2 = mlines.Line2D([], [], color='darkgoldenrod', label='grid tariff', linestyle='--')
#     ax2.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=2)
#     ax2.add_artist(leg1)
#     # ax2.add_artist(leg2)
#     #plt.legend(handles=[leg2])
#     plt.savefig(own_results_path + '(H' + str(i+1) + ')' + 'Electricity production_beaudm.png', dpi=2000)
#
# #print(len(df_thermal_demand))
# if len(df_thermal_demand) > 0 :
#     plt.subplots()
#     ax3 = df_thermal_demand['heat supply (H' + str(i+1) + ')'].plot(color='maroon', label= 'heat supply (H' + str(i+1) + ')')
#     ax3.stackplot(df_thermal_demand.index.values,df_thermal_demand['hub heat demands (H' + str(i+1) + ')'].values, df_thermal_demand['thermal storage input'].values, colors=['maroon', 'orange'], labels= ['hub'+ str(i+1) + ' heat demands', 'storage input'], alpha=0.5)
#     ax3.set_ylabel('Power [kW]')
#     ax3.set_xlabel('hours')
#     df_thermal_demand['grid tariff'].plot(ax=ax3,color='darkgoldenrod',  linestyle='--', label= 'grid tariff', secondary_y=True, legend=True)
#     plt.ylabel('Grid tariff [CHF]')
#     ax3.right_ax.set_ylim(0,2)
#     plt.xlim(0, len(df_thermal_demand['thermal storage input']))
#     handles, labels = ax3.right_ax.get_legend_handles_labels()
#     plt.title('Different heat demands versus total supply (H' + str(i+1) + ')')
#     box1 = ax3.get_position()
#     ax3.set_position([box1.x0, box1.y0 + box1.height * 0.2, box1.width, box1.height * 0.8])
#     leg1 = ax3.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
#     ax3.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=2)
#     ax3.add_artist(leg1)
#     plt.savefig(own_results_path + '(H' + str(i+1) + ')' + 'Different heat demands versus total supply_beaudm.png', dpi=2000)
#
# #print(len(df_thermal_prod))
# if len(df_thermal_prod) > 0 :
#     plt.subplots()
#     ax4 = df_thermal_prod['hub heat demand (H' + str(i+1) + ')'].plot(color='maroon', label='hub' + str(i+1) + ' heat demand')
#     ax4.stackplot(df_thermal_prod.index.values, df_thermal_prod['GSHP'], df_thermal_prod['gas boiler 1'], df_thermal_prod['gas boiler 2'], df_thermal_prod['thermal storage output'], df_thermal_prod['PVT heat production'], df_thermal_prod['CHP 1 heat production'].values, df_thermal_prod['CHP 2 heat production'].values,colors=['forestgreen', 'coral','lightcoral','magenta','darkorange', 'deepskyblue', 'blue'],labels=['GSHP','gas boiler 1','gas boiler 2', 'thermal storage output','PVT heat production', 'CHP1 production', 'CHP2 production'], alpha=0.5)
#     ax4.set_ylabel('Power [kW]')
#     ax4.set_xlabel('hours')
#     df_thermal_prod['grid tariff'].plot(color='darkgoldenrod',  linestyle='--', label='grid tariff', secondary_y=True, legend=True)
#     plt.ylabel('Grid tariff [CHF]')
#     ax4.right_ax.set_ylim(0,2)
#     plt.xlim(0, len(df_thermal_prod['GSHP']))
#     handles, labels = ax4.right_ax.get_legend_handles_labels()
#     leg1 = ax4.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.1), shadow=False)
#     plt.title('Heat demand and supply (H' + str(i+1) + ')')
#     box3 = ax4.get_position()
#     ax4.set_position([box3.x0, box3.y0 + box3.height * 0.25, box3.width, box3.height * 0.75])
#     ax4.legend(loc='upper center',frameon=False, bbox_to_anchor=(0.35, -0.1), fancybox=True, shadow=False, ncol=2)
#     ax4.add_artist(leg1)
#     plt.savefig(own_results_path + '(H' + str(i+1) + ')' + 'Heat demand and supply_beaudm.png', dpi=2000)
#
# #print(len(df_storage))
# if len(df_storage) > 0 :
#     plt.subplots()
#     ax5 = df_storage['electrical storage'].plot(color=['gold'], label='electrical storage')
#     df_storage['thermal storage'].plot(ax=ax5, color=['maroon'])
#     plt.ylabel('Energy [kWh]')
#     ax5.set_xlabel('hours')
#     df_storage['grid tariff'].plot(ax=ax5, color=['darkgoldenrod'],  linestyle='--', legend=True, secondary_y=True)
#     plt.ylabel('Grid tariff [CHF]')
#     ax5.right_ax.set_ylim(0,2)
#     plt.xlim(0, len(df_storage['thermal storage']))
#     handles, labels = ax5.right_ax.get_legend_handles_labels()
#     leg1 = ax5.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
#     plt.xlabel('hours')
#     plt.title('Storage (H' + str(i+1) + ')')
#     box4 = ax5.get_position()
#     ax5.set_position([box4.x0, box4.y0 + box4.height * 0.2, box4.width, box4.height * 0.8])
#     ax5.legend(loc='upper center',frameon=False, bbox_to_anchor=(0.35, -0.15), fancybox=True, shadow=False, ncol=2)
#     ax5.add_artist(leg1)
#     plt.savefig(own_results_path + '(H' + str(i+1) + ')' + 'Storage_beaudm.png', dpi=2000)
#
# #print(len(df_storage_SOC))
# if len(df_storage_SOC) > 0 :
#     plt.subplots()
#     ax6 = df_storage_SOC['electrical storage'].plot(color=['gold'])
#     df_storage_SOC['thermal storage'].plot(ax=ax6, color=['maroon'])
#     plt.ylabel('State of charge [%]')
#     ax6.set_ylim(0,100)
#     ax6.set_xlabel('hours')
#     df_storage_SOC['grid tariff'].plot(ax=ax6,color='darkgoldenrod',  linestyle='--', label='grid tariff', legend=True, secondary_y=True)
#     plt.ylabel('Grid tariff [CHF]')
#     ax6.right_ax.set_ylim(0,2)
#     plt.xlim(0, len(df_storage_SOC['electrical storage']))
#     handles, labels = ax6.right_ax.get_legend_handles_labels()
#     leg1 = ax6.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
#     plt.xlabel('hours')
#     plt.title('Storage SOC (H' + str(i+1) + ')')
#     box5 = ax6.get_position()
#     ax6.set_position([box5.x0, box5.y0 + box5.height * 0.1, box5.width, box5.height * 0.9])
#     ax6.legend(loc='upper center',frameon=False, bbox_to_anchor=(0.35, -0.15), fancybox=True, shadow=False, ncol=2)
#     ax6.add_artist(leg1)
#     plt.savefig(own_results_path + '(H' + str(i+1) + ')' + 'Storage_SOC_beaudm.png', dpi=2000)
#
# #print(len(df_Grid))
# if len(df_Grid) > 0 :
#     plt.subplots()
#     ax7 = df_Grid['electricity sold'].plot(color=['gold'])
#     df_Grid['electricity purchased'].plot(ax=ax7, color='yellow')
#     df_Grid['grid tariff'].plot(ax=ax7, color='darkgoldenrod', secondary_y=True, legend=True,  linestyle='--')
#     plt.ylabel('Power [kW]')
#     plt.ylabel('Grid tariff [CHF]')
#     ax7.set_xlabel('hours')
#     ax7.right_ax.set_ylim(0,2)
#     plt.xlim(0, len(df_Grid['grid tariff']))
#     handles, labels = ax7.right_ax.get_legend_handles_labels()
#     leg1 = ax7.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
#     plt.xlabel('hours')
#     plt.title('Grid interaction (H' + str(i+1) + ')')
#     box6 = ax7.get_position()
#     ax7.set_position([box6.x0, box6.y0 + box6.height * 0.1, box6.width, box6.height * 0.9])
#     ax7.legend(loc='upper center',frameon=False, bbox_to_anchor=(0.35, -0.15), fancybox=True, shadow=False, ncol=2)
#     ax7.add_artist(leg1)
#     plt.savefig(own_results_path + '(H' + str(i+1) + ')' + 'Grid_interaction_beaudm.png', dpi=2000)
#
# #print(len(df_CHP2_operation))
# if len(df_CHP2_operation) > 0 :
#     plt.subplots()
#     ax8 = plt.scatter(df_CHP2_operation.oa1, df_CHP2_operation.oa2)
#     plt.plot(df_CHP2_operation.oa1, df_CHP2_operation.oa2, label = 'operational area CHP2')
#     plt.scatter(df_CHP2.CHP2heat, df_CHP2.CHP2electricity, color='black')
#     plt.xlabel('CHP heat output[kW]')
#     plt.ylabel('CHP electricity output [kW]')
#     plt.legend()
#     plt.savefig(own_results_path + '(H' + str(i+1) + ')' + 'CHP2_operation.png', dpi=2000)
#
# #print(len(df_storage_SOC))
# #if len(df_storage_SOC) > 0 :
#     # ax9 = plt.subplots()
#     # plt.bar(df_elec_prod.index.values, df_storage_SOC.batterydepth20, label = 'First 20%')
#     # plt.bar(df_elec_prod.index.values, df_storage_SOC.batterydepth40, label = '20%-40%', bottom = df_storage_SOC.batterydepth20)
#     # plt.bar(df_elec_prod.index.values, df_storage_SOC.batterydepth60, label = '40%-60%', bottom = df_storage_SOC.batterydepth20 + df_storage_SOC.batterydepth40)
#     # plt.bar(df_elec_prod.index.values, df_storage_SOC.batterydepth80, label = '60%-80%', bottom = df_storage_SOC.batterydepth20 + df_storage_SOC.batterydepth40 + df_storage_SOC.batterydepth60)
#     # plt.xlabel('hours')
#     # plt.xlim(0, len(df_elec_prod.index))
#     # plt.ylabel('Battery levels (H' + str(i+1) + ')')
#     # plt.ylim(0,1)
#     # plt.legend()
#     # plt.savefig(own_results_path + '(H' + str(i+1) + ')' + 'Battery_levels.png', dpi=2000)
#
# # print((len(df_network_exp) > 0), (len(df_network_imp) > 0))
# # if (len(df_network_exp) > 0) or (len(df_network_imp) > 0):
# if (i>2):
#     fig10, ax10 = plt.subplots()
#     # ax10 = df_elec_demand['elec supply (H' + str(i+1) + ')'].plot(color='gold', label= 'electricity supply (H' + str(i+1) + ')')
#     ax10.stackplot(df_elec_demand.index.values, df_network_exp['elec export hub A'].values, df_network_exp['elec export hub B'].values, df_network_exp['elec export hub C'].values, colors=['yellow', 'forestgreen', 'greenyellow'], labels= ['elec export hub A', 'elec export hub B', 'elec export hub C'], alpha=0.3)
#     plt.ylabel('Power [kW]')
#     ax10.stackplot(df_elec_demand.index.values, df_network_imp['elec import hub A'].values, df_network_imp['elec import hub B'].values, df_network_imp['elec import hub C'].values, colors=['yellow', 'forestgreen', 'greenyellow'], labels= ['elec import hub A', 'elec import hub B', 'elec import hub C'], alpha=0.6)
#     # ax10.set_ylabel('Power [kW]')
#     ax10.set_xlabel('hours')
#     df_elec_demand['grid tariff'].plot(ax=ax10,color='darkgoldenrod',  linestyle='--', label= 'grid tariff', secondary_y=True, legend=True)
#     plt.ylabel('Grid tariff [CHF]')
#     ax10.right_ax.set_ylim(0,2)
#     plt.xlim(0, len(df_elec_demand['GSHP_elec']))
#     handles, labels = ax10.right_ax.get_legend_handles_labels()
#     plt.title('Different electricity demands versus total supply (H' + str(i+1) + ')')
#     box10 = ax10.get_position()
#     ax10.set_position([box10.x0, box10.y0 + box10.height * 0.2, box10.width, box10.height * 0.8])
#     leg10 = ax10.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
#     ax10.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=2)
#     ax10.add_artist(leg10)
#     plt.savefig(own_results_path + '(H' + str(i+1) + ')' + 'Network_elec_beaudm.png', dpi=2000)
#
# # print((len(df_network_exp) > 0), (len(df_network_imp) > 0))
# if (i>2):
# # if (len(df_network_exp) > 0) or (len(df_network_imp) > 0):
#     fig11, ax11 = plt.subplots()
#     # ax11 = df_elec_demand['elec supply (H' + str(i+1) + ')'].plot(color='gold', label= 'electricity supply (H' + str(i+1) + ')')
#     ax11.stackplot(df_elec_demand.index.values, df_network_exp['heat export hub A'].values, df_network_exp['heat export hub B'].values, df_network_exp['heat export hub C'].values, colors=['yellow', 'forestgreen', 'greenyellow'], labels= ['heat export hub A', 'heat export hub B', 'heat export hub C'], alpha=0.3)
#     # ax11.set_ylabel('Power [kW]')
#     ax11.stackplot(df_elec_demand.index.values, df_network_imp['heat import hub A'].values, df_network_imp['heat import hub B'].values, df_network_imp['heat import hub C'].values, colors=['yellow', 'forestgreen', 'greenyellow'], labels= ['heat import hub A', 'heat import hub B', 'heat import hub C'], alpha=0.6)
#     plt.ylabel('Power [kW]')
#     ax11.set_xlabel('hours')
#     df_elec_demand['grid tariff'].plot(ax=ax11,color='darkgoldenrod',  linestyle='--', label= 'grid tariff', secondary_y=True, legend=True)
#     plt.ylabel('Grid tariff [CHF]')
#     ax11.right_ax.set_ylim(0,2)
#     plt.xlim(0, len(df_elec_demand['GSHP_elec']))
#     handles, labels = ax11.right_ax.get_legend_handles_labels()
#     plt.title('Different electricity demands versus total supply (H' + str(i+1) + ')')
#     box11 = ax11.get_position()
#     ax11.set_position([box11.x0, box11.y0 + box11.height * 0.2, box11.width, box11.height * 0.8])
#     leg11 = ax11.legend(handles, labels, loc='upper center', frameon=False, bbox_to_anchor=(0.9, -0.15), shadow=False)
#     ax11.legend(loc='upper center', frameon=False, bbox_to_anchor=(0.35, -0.15), shadow=False, ncol=2)
#     ax11.add_artist(leg11)
#     plt.savefig(own_results_path + '(H' + str(i+1) + ')' + 'Network_heat_beaudm.png', dpi=2000)
#
#
# if i < 3 :
#     [plt.close(f) for f in plt.get_fignums()]
