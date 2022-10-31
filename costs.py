import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

pd.set_option('display.max_columns', 100)


costs = pd.read_csv(f"./data/costs.csv")
costs = costs.head(-2).copy() # remove unused inventory
usage = pd.read_csv(f"./data/usage.csv").set_index('Month').fillna(0)
costs['Month'] = pd.to_datetime(costs['Month'])
usage.index = pd.to_datetime(usage.index)
usage['refills'] = usage.astype(bool).sum(axis=1)
usage['num_months'] = np.arange(1, usage.shape[0]+1)
costs['Amount'] = costs['Amount'].apply(lambda x: x.replace('$', '')).astype(float) 
monthly_costs = costs.groupby(['Month', 'Type'])['Amount'].sum().reset_index()

oz_per_refill = 135
usage['cum_refills'] = usage['refills'].cumsum()
usage['cum_oz'] = usage['cum_refills'] * oz_per_refill
usage['startup_costs'] = usage.index.map(
    monthly_costs.query("Type == 'Start-up'").set_index('Month')['Amount']
).fillna(0)
usage['maintenance_costs'] = usage.index.map(
    monthly_costs.query("Type == 'Maintenance'").set_index('Month')['Amount']
).fillna(0)
usage['total_costs'] = usage['startup_costs'] + usage['maintenance_costs']
usage['cum_startup_costs'] = usage['startup_costs'].cumsum()
usage['cum_maintenance_costs'] = usage['maintenance_costs'].cumsum()
usage['cum_total_costs'] = usage['total_costs'].cumsum()

usage['cost_per_month'] = usage['cum_total_costs'] / usage['num_months']
usage['maintenance_costs_per_month'] = usage['cum_maintenance_costs'] / usage['num_months']
usage['cost_per_oz'] = usage['cum_total_costs'] / usage['cum_oz']
usage['Cost per 16oz'] = usage['cost_per_oz'] * 16

synergy_kombucha_48oz_cost = 8.79
usage['pretend_48oz_bottles'] = usage['cum_oz'] / 48
usage['pretend_48oz_synergy_cumcost'] = usage['pretend_48oz_bottles'] * synergy_kombucha_48oz_cost
usage.reset_index(inplace=True)
usage['Years'] = usage['num_months'] / 12

# Cost per 16oz
plt.close('all')
sns.set(style="whitegrid")
plt.figure(figsize=(9,6))
sns.lineplot(x='Years', y="Cost per 16oz", lw=1, 
    data=usage.query("Years >= 1"))
sns.despine()
plt.gca().grid(True, axis='y')
plt.title(f"")
plt.gca().set_yticks([.3, .4, .5, .6, .7, .8], minor=False)
plt.gca().set_yticklabels(["$0.30", "$0.40", "$0.50", "$0.60", "$0.70", "$0.80"], fontdict=None, minor=False)
plt.xticks([1,2,3,4])
plt.tight_layout()
plt.savefig(os.path.join(os.getcwd(), 'img', 'cost_per_16oz.png'))
plt.close()
# 4.75Y Cost per 16oz: 0.253614

avg_refills_per_month = usage['refills'].mean() # 7.964912280701754
maintenance_costs_per_month = usage['maintenance_costs_per_month'].values[-1] # 9.99824561403509
cum_total_costs = usage['cum_total_costs'].values[-1]
cum_refills = usage['cum_refills'].values[-1]
num_months = usage['num_months'].values[-1]
extended = usage[['cum_total_costs', 'num_months', 'cum_refills']].copy()
extended['Data'] = 'Real'
additional = []
for month in range(1, 64):
    cum_total_costs += maintenance_costs_per_month
    cum_refills += avg_refills_per_month
    num_months += 1
    additional.append({
        'cum_total_costs': cum_total_costs, 
        'cum_refills': cum_refills,
        'num_months': num_months,
        'Data': 'Projected',
    })
extended = pd.concat([extended, pd.DataFrame(additional)], sort=False, ignore_index=False)
extended['Years'] = extended['num_months'] / 12
extended['cum_oz'] = extended['cum_refills'] * oz_per_refill
extended['cost_per_oz'] = extended['cum_total_costs'] / extended['cum_oz']
extended['Cost per 16oz'] = extended['cost_per_oz'] * 16

# Cost per 16oz extended
plt.close('all')
sns.set(style="whitegrid")
plt.figure(figsize=(9,6))
sns.lineplot(x='Years', y="Cost per 16oz", hue='Data', lw=1, 
    data=extended.query("Years >= 1"))
sns.despine()
plt.gca().grid(True, axis='y')
plt.title(f"")
plt.gca().set_yticks([.2, .3, .4, .5, .6, .7, .8], minor=False)
plt.gca().set_yticklabels(["$0.20", "$0.30", "$0.40", "$0.50", "$0.60", "$0.70", "$0.80"], fontdict=None, minor=False)
plt.legend(loc='best', title='', shadow=False, edgecolor='white')
plt.tight_layout()
plt.savefig(os.path.join(os.getcwd(), 'img', 'cost_per_16oz_extended.png'))
plt.close()
# 10yr Cost per 16oz.: $0.198573

# total costs compared to retail purchases
usage['desc_startup_cost'] = 'Start-up Costs'
usage['desc_mainenance_cost'] = 'Maintenance Costs'
usage['desc_total_cost'] = 'Total DIY Costs'
usage['desc_synergy_cost'] = 'Retail Costs'
cost_comparison = pd.concat([
        pd.DataFrame(usage[['Years', 'cum_startup_costs', 'desc_startup_cost']].values, 
            columns=['Years', 'Total Costs', 'Description']),
        pd.DataFrame(usage[['Years', 'cum_maintenance_costs', 'desc_mainenance_cost']].values, 
            columns=['Years', 'Total Costs', 'Description']),
        pd.DataFrame(usage[['Years', 'cum_total_costs', 'desc_total_cost']].values, 
            columns=['Years', 'Total Costs', 'Description']),
        pd.DataFrame(usage[['Years', 'pretend_48oz_synergy_cumcost', 'desc_synergy_cost']].values, 
            columns=['Years', 'Total Costs', 'Description']),
    ], sort=False, ignore_index=True)
cost_comparison['Years'] = cost_comparison['Years'].astype(float)
cost_comparison['Total Costs'] = cost_comparison['Total Costs'].astype(float)
plt.close('all')
sns.set(style="whitegrid")
plt.figure(figsize=(9,6))
sns.lineplot(x='Years', y="Total Costs", hue='Description', lw=1, 
    data=cost_comparison.query("Description != 'Retail Costs'"))
sns.despine()
plt.gca().grid(True, axis='y')
plt.title(f"")
plt.xticks([1,2,3,4])
plt.gca().set_yticks([0, 200, 400, 600, 800], minor=False)
plt.gca().set_yticklabels(["$0", "$200", "$400", "$600", "$800"], fontdict=None, minor=False)
plt.tight_layout()
plt.savefig(os.path.join(os.getcwd(), 'img', 'total_costs.png'))
plt.close()
# including retail
plt.close('all')
sns.set(style="whitegrid")
plt.figure(figsize=(9,6))
sns.lineplot(x='Years', y="Total Costs", hue='Description', lw=1, data=cost_comparison)
sns.despine()
plt.gca().grid(True, axis='y')
plt.title(f"")
plt.xticks([1,2,3,4])
plt.gca().set_yticks([0, 2000, 4000, 6000, 8000, 10000], minor=False)
plt.gca().set_yticklabels(["$0", "$2,000", "$4,000", "$6,000", "$8,000", "$10,000"], fontdict=None, minor=False)
plt.tight_layout()
plt.savefig(os.path.join(os.getcwd(), 'img', 'total_costs_including_retail.png'))
plt.close()

# new purchase of $200 barrel
new = usage.copy()
new['cum_total_costs'] = new['cum_total_costs'] - 200
new['cost_per_oz'] = new['cum_total_costs'] / new['cum_oz']
new['Cost per 16oz'] = new['cost_per_oz'] * 16
new[new['Years'].isin([1,2,3,4,5])].groupby("Years")['Cost per 16oz'].last()

cum_total_costs = new['cum_total_costs'].values[-1]
cum_refills = new['cum_refills'].values[-1]
num_months = new['num_months'].values[-1]
new_extended = new[['cum_total_costs', 'num_months', 'cum_refills']].copy()
new_extended['Data'] = 'Real'
additional = []
for month in range(1, 64):
    cum_total_costs += maintenance_costs_per_month
    cum_refills += avg_refills_per_month
    num_months += 1
    additional.append({
        'cum_total_costs': cum_total_costs, 
        'cum_refills': cum_refills,
        'num_months': num_months,
        'Data': 'Projected',
    })
new_extended = pd.concat([new_extended, pd.DataFrame(additional)], sort=False, ignore_index=False)
new_extended['Years'] = new_extended['num_months'] / 12
new_extended['cum_oz'] = new_extended['cum_refills'] * oz_per_refill
new_extended['cost_per_oz'] = new_extended['cum_total_costs'] / new_extended['cum_oz']
new_extended['Cost per 16oz'] = new_extended['cost_per_oz'] * 16