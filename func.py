from numpy import sin, cos, pi
import numpy as np
#import matplotlib.pyplot as plt
#import seaborn as sns
from scipy import stats
import datetime

# hourly radiation on a tilted panel
# reference: Sukhatme S P
def IT(Ib, Id, n, LST):
    d = pi / 180
    # Location Specification
    phi = d * 18.5 # latitude in degrees
    # longitudes to be taken as +ve for east and -ve for west 
    longitude = 73.85 # longitude in degrees
    lsm = 82.5 # standard time meridian in degrees
    gamma = 0 # Surface azimuthal angle in radians
    beta = phi # Tilt of the surface ~ latitude
    
    Ig = Ib + Id # global radiation

    delta = d * (23.45 * sin(360 * (284.0 + n) * d / 365.0))
    B = d * (360.0 * (n - 1) / 365.0)
    ET = (9.87 * sin(2*B) - 7.53 * cos(B) - 1.5 * sin(B)) / 60.0
    ST = LST + ET + (lsm - longitude) / 15.0
    omega = d * (15 * (ST - 12.0))
    #costheta = sin(phi) * sin(delta) * cos(beta) + sin(phi) * cos(delta) * cos(gamma) * cos(omega) * sin(beta) + cos(phi) * cos(delta) * cos(omega) * cos(beta) - cos(phi) * sin(delta) * cos(gamma) * sin(beta) + cos(delta) * sin(gamma) * sin(omega) * sin(beta)
    costheta = sin(delta) * sin(phi - beta) + cos(delta) * cos(omega) * cos(phi-beta)
    costhetaz = sin(phi) * sin(delta) + cos(phi) * cos(delta) * cos(omega)

    ro = 0.2
    Rb = costheta / costhetaz
    Rd = cos(beta / 2.0)**2
    Rr = sin(beta / 2.0)**2 * ro
    It = Ib * Rb + Id * Rd + Ig * Rr

    It[np.where(It>1.75)] = 1.75

    return It

# Annual costing
def calcAnnualCost(number_of_panels, number_of_batteries, gridConsume, gridFeed, dailyDem):
    # Annual electricity costs
    consumption_charges = 10 # Rs. per kWh consumption charges
    wheel_charges = 1.75 # wheeling charges to account for grid losses
    FAC = 0.5 # Rs. per kWh # fuel adjustment cost
    Tax = 0.18 * consumption_charges # tax rates on per unit consumption
    feed_in_payback = 2.5 # Rs. per kWh
    fixed_charge = 200 * 12 # base charge for electricity connection for whole year
    # annual electricity bill in Rs.
    annualBill = fixed_charge + gridConsume * (consumption_charges + wheel_charges + FAC + Tax) - gridFeed * feed_in_payback

    # Annualized lifecycle costing

    # PV+Battery system costs
    PVprice = 5200 # Rs. per panel for given rating
    Investment_PV = PVprice * number_of_panels # Rs.
    
    Investment_inv = 26000 # Rs. per unit
    batteryprice = 11600 # in Rs. per unit
    Investment_bat = batteryprice * number_of_batteries # Rs.
    # Lifetimes
    pv_life = 25 # in years
    inv_life = 10 # in years
    bat_life = 5 # in years
    #capital recovery factor
    discount = 0.3
    CRF_PV = discount * (1 + discount)**pv_life / ((1 + discount)**pv_life - 1)
    CRF_inv = discount * (1 + discount)**inv_life / ((1 + discount)**inv_life - 1)
    CRF_bat = discount * (1 + discount)**bat_life / ((1 + discount)**bat_life - 1)

    # Net present value
    NPV = ((dailyDem * 365 - gridConsume) * (consumption_charges + wheel_charges + FAC + Tax) /CRF_PV) - (Investment_PV + Investment_bat + Investment_inv)
    
    # Annual expenditure in Rs.
    ALCC = Investment_PV * CRF_PV + Investment_inv * CRF_inv + Investment_bat * CRF_bat

    #print(annualBill/AnnualCost)
    return ALCC, annualBill, NPV

def genPV(radiation, number_of_panels):
    # generate electricity from hourly PV radiation
    # ref: https://pvwatts.nrel.gov/
    PR = 0.76
    # PR is the performance ratio of panels that combines losses 
    # like temperature loss, cable losses, shading losses, etc.
    inv_efficiency = 0.96 # inverter efficiency
    DC_AC_conv = 1.2 # DC to AC conversion ratio
    efficiency = 0.18 # panel efficiency
    panel_rating = 0.1 # in kilo Watts

    # calculate generation from solar PV in kWh
    generatedPV = number_of_panels * panel_rating * radiation * efficiency * PR * inv_efficiency / DC_AC_conv
    return generatedPV

def simulateYear(number_of_batteries, LST, generatedPV, dailyDem):
	inv_efficiency = 0.96 # inverter efficiency
	# battery parameters
	battery_capacity = 1.2 # in kWh
	battery_DOD = 0.5 # for Lead-acid battery
	batteryMax = battery_capacity * number_of_batteries * battery_DOD # The capacity of storage system

	# initiate loop parameters
	batteryCharge = 0 # Represents current charge in storage system
	gridFeed = 0 # Amount of electricity fed into grid from excess generation
	gridConsume = 0 # Amount of electricity consumed from grid

	for i in range(np.shape(LST)[0]):
		Dem = dailyDem / 24 # a constant demand in kWh consumed within an hour
		# check storage availability of generation
		if batteryCharge + generatedPV[i] < batteryMax:
			batteryCharge += generatedPV[i]
		else:
			gridFeed += batteryCharge + generatedPV[i] - batteryMax
			batteryCharge = float(batteryMax)

		# Fulfil the demand
		if batteryCharge * inv_efficiency < Dem:
			gridConsume += Dem - batteryCharge * inv_efficiency
			Dem = 0
			batteryCharge = 0
		else:
			batteryCharge -= Dem/inv_efficiency
			Dem = 0
	return gridConsume, gridFeed

def simulate(PV, Bat, n, LST, Ib, Id, dailyDem):
    number_of_panels = int(PV)
    number_of_batteries = int(Bat)
    # calculate radiation on a tilted surface using above function
    radiation = IT(Ib,Id,n,LST)/1000 # kW
    radiation[radiation<=0] = 0
    generatedPV = genPV(radiation, number_of_panels)
    gridConsume, gridFeed = simulateYear(number_of_batteries, LST, generatedPV, dailyDem)
    ALCC, annualBill, NPV = calcAnnualCost(number_of_panels, number_of_batteries, gridConsume, gridFeed, dailyDem)

    return ALCC, annualBill, NPV

# update probabilities of a distribution
def updateDist(distribution,sample,state,distname,X):
	prob = np.array(list(map(distribution.pmf,X)))

	if state:
		temp = np.sum(prob[np.where(X != sample)])
		prob[np.where(X != sample)] = 0
		prob += temp/3
	else:
		temp = np.sum(prob[np.where(X == sample)])
		prob[np.where(X == sample)] = 0
		prob += temp/3

	newdist = stats.rv_discrete(name= distname, values=(X,prob))
	return newdist