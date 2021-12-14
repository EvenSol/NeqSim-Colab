#This script implements calculation of dew point temperature of a hydrocarbon gas mixture
#Input to calculation is composition of the gas
#The dew point temperature is calculated using the srk-eos with classic mixing rule
"""
Created on Mon Feb  8 14:44:35 2021

@author: ESOL
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from fastapi import Body, FastAPI
from scipy.optimize import fsolve
from neqsim.thermo import *

class dewpointCalc(BaseModel):
    N2: float=0.01
    CO2: float=0.01
    methane: float=0.9
    ethane: float=0.1
    propane: float=0.03
    ibutane: float=.01
    nbutane: float=0.01
    npentane: float=0.001
    nhexane: float=0.001
   
    pressure_sep: float = 35.0
    
    def dewpointTemperature(self):
        fluid1 = fluid('srk')
        fluid1.addComponent("CO2", self.CO2)
        fluid1.addComponent("nitrogen", self.N2)
        fluid1.addComponent("methane", self.methane)
        fluid1.addComponent("ethane", self.ethane)
        fluid1.addComponent("propane", self.propane)
        fluid1.addComponent("i-butane", self.ibutane)
        fluid1.addComponent("n-butane", self.nbutane)
        fluid1.addComponent("n-pentane", self.npentane)
        fluid1.addComponent("n-hexane", self.nhexane)
        fluid1.setMixingRule(2)
        fluid1.setPressure(self.pressure_sep, "bara")
        fluid1.setTemperature(10.0, "C")
        return dewt(fluid1)-273.15

class dewpointResults(BaseModel):
    dewpointtemperature: float


