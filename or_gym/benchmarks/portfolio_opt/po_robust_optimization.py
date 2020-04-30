import numpy as np 
from pyomo.environ import *
from pyomo.opt import SolverFactory 

po = ConcreteModel()

investment_horizon = 10

assets = [a for a in range(3)]
periods = [p for p in range(investment_horizon+1)]

#Parameters 
initial_cash = 150
initial_assets = [0, 0, 0]
buy_cost = [0.045, 0.025, 0.035]
sell_cost = [0.040, 0.020, 0.030]
asset_prices_means = np.random.rand(len(assets), investment_horizon+1)+0.5
print(asset_prices_means)
asset_prices_variance = np.ones(3)*0.25 #could use covariance matrix here instead 

#Variables 
po.Cash_Quantity = Var(periods, domain=NonNegativeReals)
po.Cash_Quantity[0].fix(initial_cash)
po.Asset_Quantities = Var(assets, periods, domain=NonNegativeReals)
for a in assets: 
	po.Asset_Quantities[a,0].fix(initial_assets[0])
po.Asset_Sell = Var(assets, periods[1:], domain=NonNegativeReals)
po.Asset_Buy = Var(assets, periods[1:], domain=NonNegativeReals)
po.T = Var()

#Constraints 
def PortfolioValueConstraint(po): 
	return po.T <= po.Cash_Quantity[investment_horizon] + \
	sum(asset_prices_means[a][-1]*po.Asset_Quantities[a,investment_horizon] for a in assets) \
	- 3*(sum(po.Asset_Quantities[a,investment_horizon]*asset_prices_variance[a]*\
	po.Asset_Quantities[a,investment_horizon] for a in assets))**0.5

def CashAccounting(po, p): 
	return po.Cash_Quantity[p] - po.Cash_Quantity[p-1] <= \
	sum(asset_prices_means[a][p]*((1-sell_cost[a])*po.Asset_Sell[a,p] - (1+buy_cost[a])*po.Asset_Buy[a,p]) \
		for a in assets) \
	- 3*(sum((1-sell_cost[a])*po.Asset_Sell[a,p] - (1+buy_cost[a])*po.Asset_Buy[a,p] for a in assets)**2 \
		)**0.5

def AssetBalance(po, a, p): 
	return po.Asset_Quantities[a,p] == po.Asset_Quantities[a,p-1] \
	- po.Asset_Sell[a,p] + po.Asset_Buy[a,p]

po.PortfolioValueConstraint = Constraint(rule=PortfolioValueConstraint)
po.CashAccounting = Constraint(periods[1:], rule=CashAccounting)
po.AssetBalance = Constraint(assets, periods[1:], rule=AssetBalance)

#Objective
def PortfolioValue(po): 
	return po.T
	
po.PortfolioValue = Objective(rule=PortfolioValue, sense=maximize)

opt = SolverFactory('baron')
results = opt.solve(po, tee=False, keepfiles=False)

print(results)
po.Asset_Quantities.pprint()
po.Cash_Quantity.pprint()