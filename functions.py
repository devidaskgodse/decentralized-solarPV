# created on IST 202010291540
# author: Devidas Kachru Godse

import numpy as np
from sys import argv
#import networkx

script, no_of_panels, no_of_batteries, daily_demand = argv

# input variables (some could be inserted as arguments)
## solar PV parameters
# panel_market_rating = 250 # watts
# cost_per_panel =  0 # Rs. per panel (for the rated one)
panel_area = 0.25 # m^2
panel_efficiency = 0.17
# need to estimate no. of panels & price

## battery & inverter parameters
# inverter_cost = 0# based on ratings
inverter_input_efficiency = 0.9
inverter_output_efficiency = 0.85

battery_voltage_rating = 2# volts
battery_charge_rating = 100 # Ah
energy_per_battery = battery_charge_rating * battery_voltage_rating / 1000 # kWh
battery_DOD = 0.5 # (0.5 for Lead Acid 0.9 for Li-ion)
# battery_cost = 0 # Rs. per battery
# need to estimate no. of batteries & price


'''
#############################################
# functions for calculating solar radiation on titled surface
#############################################
# reference: Sukhatme S P
d = pi / 180
# Location Specification
phi = d * float(input("latitude in degrees: "))
# longitudes to be taken as +ve for east and -ve for west 
longitude = float(input("longitude in degrees: "))
lsm = float(input("standard time meridian in degrees: "))

gamma = 0 # Surface azimuthal angle in radians
beta = phi # Tilt of the surface ~ latitude

# Time Specification
n = # day of the year
LST = # local standard time

# Solar radiation incident on ground in W/m^2
Ig = # global radiation every hour
Id = # diffuse radiation every hour

# hourly radiation on a tilted panel
def IT(phi, longitude, lsm, Ig, Id, n, LST, gamma, beta):
    Ib = Ig - Id # beam radiation

    delta = d * (23.45 * sin(360 * (284.0 + n) * d / 365.0))
    B = d * (360.0 * (n - 1) / 365.0)
    ET = (9.87 * sin(2.0*B) - 7.53 * cos(B) - 1.5 * sin(B)) / 60.0
    ST = LST + ET + (lsm - longitude) / 15.0
    omega = d * (15 * (ST - 12.0))
    costheta = sin(phi) * sin(delta) * cos(beta) + \
               + sin(phi) * cos(delta) * cos(gamma) * cos(omega) * sin(beta) \
               + cos(phi) * cos(delta) * cos(omega) * cos(beta)\
           - cos(phi) * sin(delta) * cos(gamma) * sin(beta)\
           + cos(delta) * sin(gamma) * sin(omega) * sin(beta)
    costhetaz = sin(phi) * sin(delta) + cos(phi) * cos(delta) * cos(omega)

    ro = 0.2
    Rb = costheta / costhetaz
    Rd = cos(beta * d / 2.0)**2.0
    Rr = sin(beta * d / 2.0)**2.0
    It = Ib * Rb + Id * Rd + Ig * Rr * ro

    return It

# daily radiation on a tilted panel
def HT():
	pass
'''

## PV generation based on radiation and amount of panels available

def generate_PV(panel_area, radiation, efficiency):
	generatedPV = panel_area * radiation * efficiency * 0.75 # 0.75 is to account for all PV losses
	return generatedPV

def grid_loss(): 
	return 0.2

# simulate 
## keep the demand constant throughout the day for now

no_of_panels = float(no_of_panels)
no_of_batteries = float(no_of_batteries)
charge_capacity = energy_per_battery * no_of_batteries * battery_DOD

# system_cost = battery_cost * no_of_batteries + cost_per_panel * no_of_panels + inverter_cost

total_PVgeneration = 0
current_charge = 0 # track level of charge in battery (shouldnot exceed charge capacity)
grid_feed = 0 # kWh
grid_consumption = 0 # kWh
grid_energy_losses = 0 # track losses occuring from grid
# radiation = [4.53, 5.31, 6.12, 6.59, 6.66, 5.73, 4.48, 4.19, 4.96, 5.21, 4.72, 4.16]
i = 0
vector = np.zeros([12,6])
data = [[9.075,9.549,7.966,8.781,8.911,7.782,8.104,9.667,9.602,9.688,8.908,8.753,8.655,8.532], # jaipur
[8.063,5.3,8.053,10.172,9.96,9.262,9.232,6.817,6.675,8.144,8.082,8.001,7.837,7.896], # mumbai
[5.424,8.236,4.336,1.605,1.412,6.97,9.261,8.556,9.308,9.376,6.628,7.913,8.024,6.48]] # channai

# for radiation in [4.53*31, 5.31*28, 6.12*31, 6.59*30, 6.66*31, 5.73*30, 4.48*31, 4.19*31, 4.96*30, 5.21*31, 4.72*30, 4.16*31]: # radiation in kWh/m^2/day
for radiation in [4.53, 5.31, 6.12, 6.59, 6.66, 5.73, 4.48, 4.19, 4.96, 5.21, 4.72, 4.16]:
#for radiation in data[0]:
	current_demand = int(daily_demand) # kWh
	Radiation_per_day = 750 #kWh/day #IT()
	generatedPV = generate_PV(panel_area * no_of_panels, radiation, panel_efficiency)
	total_PVgeneration += generatedPV

	# feed generation to battery & grid
	if current_charge + generatedPV * inverter_input_efficiency < charge_capacity:
		current_charge  += generatedPV * inverter_input_efficiency
	else:
		ExcessPV = current_charge + generatedPV * inverter_input_efficiency - charge_capacity
		grid_feed += ExcessPV * (1 - grid_loss()) * inverter_input_efficiency
		grid_energy_losses = grid_energy_losses +  ExcessPV * grid_loss() * inverter_input_efficiency

		current_charge  += generatedPV * inverter_input_efficiency

	# consume based on demand
	if current_charge * inverter_output_efficiency < current_demand:
		ExcessDemand = current_demand - current_charge * inverter_output_efficiency
		grid_consumption += ExcessDemand / (1 - grid_loss())
		grid_energy_losses +=  ExcessDemand * grid_loss() / (1 - grid_loss())

		current_demand = 0
		current_charge = 0
	else:
		current_charge -= current_demand / inverter_output_efficiency
		current_demand = 0
	params = np.array([total_PVgeneration, grid_feed, grid_consumption, grid_energy_losses, current_charge, current_demand])
	vector[i,:] += params
	i += 1


print(vector[-1,:])


'''
electricity charges for consumption from grid

tariff_rate_from_grid = 
tariff_rate_to_grid = 
fixed_charge = 
FAC = # fuel adjustment charges
wheeling_charges = # depends on distance from grid
tax_rate = 
def tariff(grid_consumption, tariff_rate_from_grid, grid_feed, tariff_rate_to_grid, fixed_charge, FAC, wheeling_charges, tax_rate):
	return (1 + tax_rate) * (grid_consumption* tariff_rate_from_grid - grid_feed * tariff_rate_to_grid + fixed_charge + (FAC + wheeling_charges) * grid_consumption)

print(tariff(grid_consumption, tariff_rate_from_grid, grid_feed, tariff_rate_to_grid, fixed_charge, FAC, wheeling_charges, tax_rate))
'''