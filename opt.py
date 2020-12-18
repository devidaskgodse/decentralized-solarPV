from func import *
import numpy as np
import pandas as pd
from scipy import stats
from sys import argv
import matplotlib.pyplot as plt
import seaborn as sns

script, PV, Bat, dailyDem = argv

# Import radiation data for a location
# Incident radiation data obtained from
# https://pvwatts.nrel.gov/pvwatts.php  
data = pd.read_csv("mumbai_hourly.csv")
# trimming the dataframe to essential variables
data = data[:-1]
# New variables
data["year"] = 2019
data["day_count"] = 0

arr = data.to_numpy(dtype=float)
# finding day of the year
date_ar = (arr[:,5] - 1970).astype('M8[Y]') + (arr[:,0] - 1).astype('m8[M]') + (arr[:,1] - 1).astype('m8[D]')
arr[:,-1] = date_ar - (arr[:,5] - 1970).astype('M8[Y]') + 1  # days since first day of the year

# Time Specification
n = arr[:,-1] # day of the year from data
LST = arr[:,2] + 0.5 # local standard time (hour from data)

# Solar radiation incident on ground in W/m^2
Ib = arr[:,3] # global radiation every hour
Id = arr[:,4] # diffuse radiation every hour

oldPV = int(PV)
oldBat = int(Bat)
dailyDem = float(dailyDem)

# defining distribution for optimization
X = np.array([-1,0,1])

PVprob= np.array([1/3,1/3,1/3])
Batprob= np.array([1/3,1/3,1/3])

PVdist = stats.rv_discrete(name="PV",values=(X,PVprob))
Batdist = stats.rv_discrete(name="Bat",values=(X,Batprob))

#number_of_panels = int(PV)
#number_of_batteries = int(Bat)
## calculate radiation on a tilted surface using above function
#radiation = IT(Ib,Id,n,LST)/1000 # kW
#radiation[radiation<=0] = 0
#generatedPV = genPV(radiation, number_of_panels)
#gridConsume, gridFeed = simulateYear(number_of_batteries, LST, generatedPV, dailyDem)
#ALCC, annualBill, NPV = calcAnnualCost(number_of_panels, number_of_batteries, gridConsume, gridFeed, dailyDem)

oldAnnualCost,oldannualBill, oldNPV = simulate(oldPV, oldBat, n, LST, Ib, Id, dailyDem)

# optimization loop

while PVdist.pmf(0) < 0.8 and Batdist.pmf(0) < 0.8 and oldPV > 0 and oldBat > 0:
	samplePV = PVdist.rvs() # sample from PVdistribution
	sampleBat = Batdist.rvs() #Batdist.rvs() # sample from Batdistribution

	newPV = oldPV + samplePV
	newBat = oldBat + sampleBat

	newAnnualCost, newannualBill, newNPV = simulate(newPV, newBat, n, LST, Ib, Id, dailyDem)

	# add a penalty
	newObj = newAnnualCost*(1 + 1/(1+newPV)**2 + 1/(1+newBat)**2)

	if newAnnualCost <= oldAnnualCost and newannualBill <= oldannualBill: #newNPV >= oldNPV
		if samplePV != 0:
			PVdist = updateDist(PVdist,samplePV,True,"PV",X)
		if sampleBat != 0:
			Batdist = updateDist(Batdist,sampleBat,True,"Bat",X)
	else:
		if samplePV != 0:
			PVdist = updateDist(PVdist,samplePV,False,"PV",X)
		if sampleBat !=0:
			Batdist = updateDist(Batdist,sampleBat,False,"Bat",X)

	oldAnnualCost = float(newAnnualCost)
	oldPV = float(newPV)
	oldBat = float(newBat)
	oldObj = float(newObj)
	oldannualBill = float(newannualBill)
	oldNPV = float(newNPV)
	#oldShare = float(newShare)

print(oldPV,oldBat,oldAnnualCost,oldNPV,oldannualBill)


# Generating heatmap
#ALCC = np.zeros((50,50))
#Bill = np.zeros((50,50))
#NPV = np.zeros((50,50))
#for i in range(50):
#	for j in range(50):
#		ALCC[i,j], Bill[i,j], NPV[i,j] = simulate(i, j, n, LST, Ib, Id, dailyDem)
#		print(i,j)
#
##np.save("50vs50meshgrid-10",grid)
#f, ax = plt.subplots(figsize=(9, 6))
#sns.heatmap(NPV, ax=ax)
#plt.show()
