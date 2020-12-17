from func import *
import numpy as np
import pandas as pd
from scipy import stats
from sys import argv
import matplotlib.pyplot as plt
import seaborn as sns

script, PV, Bat, dailyDem = argv

# Import radiation data for a location
#data = pd.read_csv("mumbai_hourly.csv")
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

oldAnnualCost = simulate(oldPV, oldBat, n, LST, Ib, Id, dailyDem)

# optimization loop
while PVdist.pmf(0) < 0.8 and Batdist.pmf(0) < 0.8 and oldPV > 1 and oldBat > 1:
	samplePV = PVdist.rvs() # sample from PVdistribution
	sampleBat = Batdist.rvs() #Batdist.rvs() # sample from Batdistribution

	newPV = oldPV + samplePV
	newBat = oldBat + sampleBat

	newAnnualCost = simulate(newPV, newBat, n, LST, Ib, Id, dailyDem)

	# add a penalty
	#objective = newAnnualCost*(1 + 1/(1+newPV)**2 + 1/(1+newBat)**2)

	if newAnnualCost <= oldAnnualCost:
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
	print(oldPV,oldBat,oldAnnualCost,(samplePV,sampleBat),(PVdist.pmf(0),Batdist.pmf(0)))

#while PVdist.pmf(0) < 0.7 and Batdist.pmf(0) < 0.7 and oldPV > 1 and oldBat > 1:
#	samplePV = PVdist.rvs() # sample from PVdistribution
#
#	newPV = oldPV + samplePV
#
#	newAnnualCost = simulate(newPV, oldBat, n, LST, Ib, Id, dailyDem)
#
#	# add a penalty
#	#objective = newAnnualCost*(1 + 1/(1+newPV)**2 + 1/(1+newBat)**2)
#
#	if newAnnualCost <= oldAnnualCost:
#		if samplePV != 0:
#			PVdist = updateDist(PVdist,samplePV,True,"PV",X)
#	else:
#		if samplePV != 0:
#			PVdist = updateDist(PVdist,samplePV,False,"PV",X)
#
#	oldAnnualCost = float(newAnnualCost)
#	oldPV = float(newPV)
#	oldBat = float(oldBat)
#
#	sampleBat = Batdist.rvs() #Batdist.rvs() # sample from Batdistribution
#	newBat = oldBat + sampleBat
#
#	newAnnualCost = simulate(oldPV, newBat, n, LST, Ib, Id, dailyDem)
#
#	if newAnnualCost <= oldAnnualCost:
#		if sampleBat != 0:
#			Batdist = updateDist(Batdist,sampleBat,True,"Bat",X)
#	else:
#		if sampleBat !=0:
#			Batdist = updateDist(Batdist,sampleBat,False,"Bat",X)
#
#	oldAnnualCost = float(newAnnualCost)
#	oldPV = float(oldPV)
#	oldBat = float(newBat)
#
#	print(oldPV,oldBat,oldAnnualCost,(samplePV,sampleBat),(PVdist.pmf(0),Batdist.pmf(0)))


#grid = np.zeros((50,50))
#for i in range(50):
#	for j in range(50):
#		grid[i,j] = simulate(i, j, n, LST, Ib, Id, dailyDem)
#		#print(i,j)
#
#np.save("50vs50meshgrid-10",grid)
#f, ax = plt.subplots(figsize=(9, 6))
#sns.heatmap(grid, ax=ax)
#plt.show()