import os
import math
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import calendar
import scipy.stats as st

from math import floor,ceil
from scipy.signal import find_peaks

from .aux_funcs import convert_latexTab_to_csv

def calculate_scatter(data,var1, step_var1, var2, step_var2, from_origin=False, labels_lower=False):
    '''
    data : pd.DataFrame
        The data containing the variables as columns.
    var1 : str
        The first variable.
    step_var1 : float
        Bin size of the first variable.
    var2 : str
        The second variable.
    step_var2 : float
        Bin size of the second variable.
    from_origin : bool, default False
        This will include the origin, even if there are no values near zero.
    labels_lower : bool, default False
        By default, upper edges of bins are used as labels. Switch this to use lower bin edges instead.
    '''

    data = data[[var1,var2]]
    if np.any(np.isnan(data)):
        print("Warning: Removing NaN rows.")
        data = data.dropna(how="any")

    # Initial min and max
    xmin = data[var2].values.min()
    ymin = data[var1].values.min()
    xmax = data[var2].values.max()
    ymax = data[var1].values.max()

    # Change min (max) to zero only if all values are above (below) and from_origin=True
    xmin = 0 if (from_origin and (xmin>0)) else (xmin//step_var2)*step_var2
    ymin = 0 if (from_origin and (ymin>0)) else (ymin//step_var1)*step_var1

    xmax = 0 if (from_origin and (xmax<0)) else xmax
    ymax = 0 if (from_origin and (ymax<0)) else ymax

    # Define bins and get histogram
    x = np.arange(xmin,xmax+step_var2,step_var2)
    y = np.arange(ymin,ymax+step_var1,step_var1)
    a, y, x = np.histogram2d(data.values[:,0],data.values[:,1],bins=(y,x))

    # Choose upper or lower edges as labels
    x = x[:-1] if labels_lower else x[1:]
    y = y[:-1] if labels_lower else y[1:]

    return pd.DataFrame(data = a.astype("int"),index = y,columns=x)

def scatter_diagram(data: pd.DataFrame, var1: str, step_var1: float, var2: str, step_var2: float, output_file):
    """
    The function is written by dung-manh-nguyen and KonstantinChri.
    Plot scatter diagram (heatmap) of two variables (e.g, var1='hs', var2='tp')
    step_var: size of bin e.g., 0.5m for hs and 1s for Tp
    cmap: colormap, default is 'Blues'
    outputfile: name of output file with extrensition e.g., png, eps or pdf 
     """

    sd = calculate_scatter(data, var1, step_var1, var2, step_var2)

    # Convert to percentage
    tbl = sd.values
    var1_data = data[var1]
    tbl = tbl/len(var1_data)*100

    # Then make new row and column labels with a summed percentage
    sumcols = np.sum(tbl, axis=0)
    sumrows = np.sum(tbl, axis=1)

    sumrows = np.around(sumrows, decimals=1)
    sumcols = np.around(sumcols, decimals=1)

    bins_var1 = sd.index
    bins_var2 = sd.columns
    lower_bin_1 = bins_var1[0] - step_var1
    lower_bin_2 = bins_var2[0] - step_var2

    rows = []
    rows.append(f'{lower_bin_1:04.1f}-{bins_var1[0]:04.1f} | {sumrows[0]:04.1f}%')
    for i in range(len(bins_var1)-1):
        rows.append(f'{bins_var1[i]:04.1f}-{bins_var1[i+1]:04.1f} | {sumrows[i+1]:04.1f}%')

    cols = []
    cols.append(f'{int(lower_bin_2)}-{int(bins_var2[0])} | {sumcols[0]:04.1f}%')
    for i in range(len(bins_var2)-1):
        cols.append(f'{int(bins_var2[i])}-{int(bins_var2[i+1])} | {sumcols[i+1]:04.1f}%')

    rows = rows[::-1]
    tbl = tbl[::-1,:]
    dfout = pd.DataFrame(data=tbl, index=rows, columns=cols)
    hi = sns.heatmap(data=dfout.where(dfout>0), cbar=True, cmap='Blues', fmt=".1f")
    plt.ylabel(var1)
    plt.xlabel(var2)
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

    return hi

def table_var_sorted_by_hs(data, var, var_hs='hs', output_file='var_sorted_by_Hs.txt'):
    """
    The function is written by dung-manh-nguyen and KonstantinChri.
    This will sort variable var e.g., 'tp' by 1 m interval og hs
    then calculate min, percentile 5, mean, percentile 95 and max
    data : panda series 
    var  : variable 
    output_file: extension .txt for latex table or .csv for csv table
    """
    Hs = data[var_hs]
    Var = data[var]
    binsHs = np.arange(0.,math.ceil(np.max(Hs))+0.1) # +0.1 to get the last one   
    temp_file = output_file.split('.')[0]

    Var_binsHs = {}
    for j in range(len(binsHs)-1) : 
        Var_binsHs[str(int(binsHs[j]))+'-'+str(int(binsHs[j+1]))] = [] 
    
    N = len(Hs)
    for i in range(N):
        for j in range(len(binsHs)-1) : 
            if binsHs[j] <= Hs.iloc[i] < binsHs[j+1] : 
                Var_binsHs[str(int(binsHs[j]))+'-'+str(int(binsHs[j+1]))].append(Var.iloc[i])
    
    with open(temp_file, 'w') as f:
        f.write('\\begin{tabular}{l p{1.5cm}|p{1.5cm} p{1.5cm} p{1.5cm} p{1.5cm} p{1.5cm}}' + '\n')
        f.write(r'& & \multicolumn{5}{c}{'+var+'} \\\\' + '\n')
        f.write(r'Hs & Entries & Min & 5\% & Mean & 95\% & Max \\\\' + '\n')
        f.write(r'\hline' + '\n')
    
        for j in range(len(binsHs)-1) : 
            Var_binsHs_temp = Var_binsHs[str(int(binsHs[j]))+'-'+str(int(binsHs[j+1]))]
            
            Var_min = round(np.min(Var_binsHs_temp), 1)
            Var_P5 = round(np.percentile(Var_binsHs_temp , 5), 1)
            Var_mean = round(np.mean(Var_binsHs_temp), 1)
            Var_P95 = round(np.percentile(Var_binsHs_temp, 95), 1)
            Var_max = round(np.max(Var_binsHs_temp), 1)
            
            hs_bin_temp = str(int(binsHs[j]))+'-'+str(int(binsHs[j+1]))
            f.write(hs_bin_temp + ' & '+str(len(Var_binsHs_temp))+' & '+str(Var_min)+' & '+str(Var_P5)+' & '+str(Var_mean)+' & '+str(Var_P95)+' & '+str(Var_max)+' \\\\' + '\n')
        hs_bin_temp = str(int(binsHs[-1]))+'-'+str(int(binsHs[-1]+1)) # +1 for one empty row 
        f.write(hs_bin_temp + ' & 0 & - & - & - & - & - \\\\' + '\n')
        
        # annual row 
        Var_min = round(np.min(Var), 1)
        Var_P5 = round(np.percentile(Var , 5), 1)
        Var_mean = round(np.mean(Var), 1)
        Var_P95 = round(np.percentile(Var, 95), 1)
        Var_max = round(np.max(Var), 1)
        
        hs_bin_temp = str(int(binsHs[0]))+'-'+str(int(binsHs[-1]+1)) # +1 for one empty row 
        f.write(hs_bin_temp + ' & '+str(len(Var))+' & '+str(Var_min)+' & '+str(Var_P5)+' & '+str(Var_mean)+' & '+str(Var_P95)+' & '+str(Var_max)+' \\\\' + '\n')
        f.write(r'\hline' + '\n')
        f.write(r'\end{tabular}' + '\n')
    
    if output_file.split('.')[1] == 'csv':
        convert_latexTab_to_csv(temp_file, output_file)
        os.remove(temp_file)
    else:
        os.rename(temp_file, output_file)
    

    return    

def table_monthly_percentile(data,var,output_file='var_monthly_percentile.txt'):  
    """
    The function is written by dung-manh-nguyen and KonstantinChri.
    this function will sort variable var e.g., hs by month and calculate percentiles 
    data : panda series 
    var  : variable 
    output_file: extension .txt for latex table or .csv for csv table
    """

    Var = data[var]
    varName = data[var].name
    Var_month = Var.index.month
    M = Var_month.values
    temp_file = output_file.split('.')[0]
    
    months = calendar.month_name[1:] # eliminate the first insane one 
    for i in range(len(months)) : 
        months[i] = months[i][:3] # get the three first letters 
    
    monthlyVar = {}
    for i in range(len(months)) : 
        monthlyVar[months[i]] = [] # create empty dictionaries to store data 
    
    
    for i in range(len(Var)) : 
        m_idx = int(M[i]-1) 
        monthlyVar[months[m_idx]].append(Var.iloc[i])  
        
        
    with open(temp_file, 'w') as f:
        f.write(r'\\begin{tabular}{l | p{1.5cm} p{1.5cm} p{1.5cm} p{1.5cm} p{1.5cm}}' + '\n')
        f.write(r'& \multicolumn{5}{c}{' + varName + '} \\\\' + '\n')
        f.write(r'Month & 5\% & 50\% & Mean & 95\% & 99\% \\\\' + '\n')
        f.write(r'\hline' + '\n')
    
        for j in range(len(months)) : 
            Var_P5 = round(np.percentile(monthlyVar[months[j]],5),1)
            Var_P50 = round(np.percentile(monthlyVar[months[j]],50),1)
            Var_mean = round(np.mean(monthlyVar[months[j]]),1)
            Var_P95 = round(np.percentile(monthlyVar[months[j]],95),1)
            Var_P99 = round(np.percentile(monthlyVar[months[j]],99),1)
            f.write(months[j] + ' & '+str(Var_P5)+' & '+str(Var_P50)+' & '+str(Var_mean)+' & '+str(Var_P95)+' & '+str(Var_P99)+' \\\\' + '\n')
        
        # annual row 
        f.write('Annual & '+str(Var_P5)+' & '+str(Var_P50)+' & '+str(Var_mean)+' & '+str(Var_P95)+' & '+str(Var_P99)+' \\\\' + '\n')
    
        f.write(r'\hline' + '\n')
        f.write(r'\end{tabular}' + '\n')
    
    if output_file.split('.')[1] == 'csv':
        convert_latexTab_to_csv(temp_file, output_file)
        os.remove(temp_file)
    else:
        os.rename(temp_file, output_file)
    
    return   


def table_monthly_min_mean_max(data, var,output_file='montly_min_mean_max.txt') :  
    """
    The function is written by dung-manh-nguyen and KonstantinChri.
    It calculates monthly min, mean, max based on monthly maxima. 
    data : panda series
    var  : variable 
    output_file: extension .txt for latex table or .csv for csv table
    """
        
    var = data[var]
    temp_file  = output_file.split('.')[0]
    months = calendar.month_name[1:] # eliminate the first insane one 
    for i in range(len(months)) : 
        months[i] = months[i][:3] # get the three first letters 
    
    monthly_max = var.resample('M').max() # max in every month, all months 
    minimum = monthly_max.groupby(monthly_max.index.month).min() # min, sort by month
    mean = monthly_max.groupby(monthly_max.index.month).mean() # mean, sort by month
    maximum = monthly_max.groupby(monthly_max.index.month).max() # max, sort by month
    
    with open(temp_file, 'w') as f :
        f.write(r'\\begin{tabular}{l | c c c }' + '\n')
        f.write(r'Month & Minimum & Mean & Maximum \\\\' + '\n')
        f.write(r'\hline' + '\n')
        for i in range(len(months)):
            f.write(months[i] + ' & ' + str(minimum.values[i]) + ' & ' + str(round(mean.values[i],1)) + ' & ' + str(maximum.values[i]) + ' \\\\' + '\n')
        
        ## annual row 
        annual_max = var.resample('Y').max()
        min_year = annual_max.min()
        mean_year = annual_max.mean()
        max_year = annual_max.max()
        f.write('Annual Max. & ' + str(min_year) + ' & ' + str(round(mean_year,1)) + ' & ' + str(max_year) + ' \\\\' + '\n')
            
        f.write(r'\hline' + '\n')
        f.write(r'\end{tabular}' + '\n')


    if output_file.split('.')[1] == 'csv':
        convert_latexTab_to_csv(temp_file, output_file)
        os.remove(temp_file)
    else:
        os.rename(temp_file, output_file)

    return


def Cmax(Hs,Tm,depth):
    
    # calculate k1
    g = 9.80665 # m/s2, gravity 
    Tm01 = Tm # second, period 
    d = depth # m, depth
    lamda1 = 1 # wave length from 8.5 to 212 
    lamda2 = 500 # wave length from 8.5 to 212 
    k1_temp=np.linspace(2*np.pi/lamda2,2*np.pi/lamda1,10000)
    F = (2*np.pi)**2/(g*Tm01**2*np.tanh(k1_temp*d)) - k1_temp
    #plt.plot(k1_temp,F)
    #plt.grid()
    
    
    epsilon = abs(F)
    try:
        param = find_peaks(1/epsilon)
        index = param[0][0]
    except:
        param = np.where(epsilon == epsilon.min())
        index = param[0][0]
        
    k1 = k1_temp[index]
    #lamda = 2*np.pi/k1
    #print ('wave length (m) =', round(lamda))
    
    #Hs=10
    Urs = Hs/(k1**2*d**3)
    S1 = 2*np.pi/g*Hs/Tm01**2
    
    sea_state='long-crested'
    #sea_state='short-crested'
    if sea_state == 'long-crested' :
        AlphaC = 0.3536 + 0.2892*S1 + 0.1060*Urs
        BetaC = 2 - 2.1597*S1 + 0.0968*Urs
    elif sea_state == 'short-crested' :
        AlphaC = 0.3536 + 0.2568*S1 + 0.08*Urs
        AlphaC = 2 - 1.7912*S1 - 0.5302*Urs + 0.2824*Urs
    else:
        print ('please check sea state')
        
        
    #x = np.linspace(0.1,10,1000)
    #Fc = 1-np.exp(-(x/(AlphaC*Hs))**BetaC)
    #
    #plt.plot(x,Fc)
    #plt.grid()
    #plt.title(sea_state)
    
    
    Tm02 = Tm
    #t=5
    #C_MPmax = AlphaC*Hs*(np.log(Tm02/t))**(1/BetaC) # This is wrong, anyway it is not important 
    
    t=10800 # 3 hours 
    p = 0.85
    C_Pmax = AlphaC*Hs*(-np.log(1-p**(Tm02/t)))**(1/BetaC)
    Cmax = C_Pmax*1.135 # this is between 1.13 and 1.14 
    
    return Cmax
    
    
    
def pdf_all(data, var, bins=70, output_file='pdf_all.png'): #pdf_all(data, bins=70)
    
    data = data[var].values
    
    x=np.linspace(min(data),max(data),100)
    
    param = st.weibull_min.fit(data) # shape, loc, scale
    pdf_weibull = st.weibull_min.pdf(x, param[0], loc=param[1], scale=param[2])
    
    # param = expon.fit(data) # loc, scale
    # pdf_expon = expon.pdf(x, loc=param[0], scale=param[1])
    
    param = st.genextreme.fit(data) # shape, loc, scale
    pdf_gev = st.genextreme.pdf(x, param[0], loc=param[1], scale=param[2])
    
    param = st.gumbel_r.fit(data) # loc, scale
    pdf_gumbel = st.gumbel_r.pdf(x, loc=param[0], scale=param[1])
    
    param = st.lognorm.fit(data) # shape, loc, scale
    pdf_lognorm = st.lognorm.pdf(x, param[0], loc=param[1], scale=param[2])
    
    fig, ax = plt.subplots(1, 1)
    #ax.plot(x, pdf_expon, label='pdf-expon')
    ax.plot(x, pdf_weibull,label='pdf-Weibull')
    ax.plot(x, pdf_gev, label='pdf-GEV')
    ax.plot(x, pdf_gumbel, label='pdf-GUM')
    ax.plot(x, pdf_lognorm, label='pdf-lognorm')
    ax.hist(data, density=True, bins=bins, color='tab:blue', label='histogram', alpha=0.5)
    #ax.hist(data, density=True, bins='auto', color='tab:blue', label='histogram', alpha=0.5)
    ax.legend()
    ax.grid()
    ax.set_xlabel('Wave height')
    ax.set_ylabel('Probability density')
    plt.savefig(output_file)
    
    return 


def scatter(df,var1,var2,location,regression_line,qqplot=True):
    x=df[var1].values
    y=df[var2].values
    fig, ax = plt.subplots()
    ax.scatter(x,y,marker='.',s=10,c='g')
    dmin, dmax = np.min([x,y])*0.9, np.max([x,y])*1.05
    diag = np.linspace(dmin, dmax, 1000)
    plt.plot(diag, diag, color='r', linestyle='--')
    plt.gca().set_aspect('equal')
    plt.xlim([0,dmax])
    plt.ylim([0,dmax])
    
    if qqplot :    
        percs = np.linspace(0,100,101)
        qn_x = np.nanpercentile(x, percs)
        qn_y = np.nanpercentile(y, percs)    
        ax.scatter(qn_x,qn_y,marker='.',s=80,c='b')

    if regression_line:  
        m,b,r,p,se1=st.linregress(x,y)
        cm0="$"+('y=%2.2fx+%2.2f'%(m,b))+"$"
        plt.plot(x, m*x + b, 'k--', label=cm0)
        plt.legend(loc='best')
        
    rmse = np.sqrt(((y - x) ** 2).mean())
    bias = np.mean(y-x)
    mae = np.mean(np.abs(y-x))
    corr = np.corrcoef(y,x)[0][1]
    std = np.std(x-y)/np.mean(x)
    plt.annotate('rmse = '+str(round(rmse,3))
                 +'\nbias = '+str(round(bias,3))
                 +'\nmean = '+str(round(mae,3))
                 +'\ncorr = '+str(round(corr,3))
                 +'\nstd = '+str(round(std,3)), xy=(dmin+1,0.6*(dmin+dmax)))
        
    plt.xlabel(var1, fontsize=15)
    plt.ylabel(var2, fontsize=15)

    plt.title("$"+(location +', N=%1.0f'%(np.count_nonzero(~np.isnan(x))))+"$",fontsize=15)
    plt.grid()
    plt.close()
    
    return fig


def calculate_weather_window(data: pd.DataFrame, var: str,threshold=5, window_size=12):
    """
    Calculate the mean and percentiles of consecutive periods where a variable
    stays below a certain threshold within a given window size.

    Parameters:
        data (pd.DataFrame): The DataFrame containing the time series data.
        var (str): The name of the variable in the DataFrame.
        threshold (float, optional): The threshold value for the variable.
            Defaults to 5.
        window_size (int, optional): The size of the window in hours.
            Defaults to 12.

    Returns:
        tuple: A tuple containing the mean and percentiles of consecutive periods
            where the variable stays below the threshold.
    """
    #data=data['1958-02-04' :'1958-02-23']
    df = (data[var]<threshold).astype(int)
    dt = (data.index[1]-data.index[0]).total_seconds()/3600 # in hours # 1 hour for NORA3
    #consecutive_periods = df.rolling(window=str(window_size+dt)+'H').sum()
    # Mark consecutive periods of window_size (hours) with 1
    #consecutive_periods[consecutive_periods < window_size] = 0
    #consecutive_periods = consecutive_periods > 0 
    #consecutive_periods = consecutive_periods.astype(int)*df  
    # Find consecutive sequences of ones
    consecutive_periods = (df == 1).astype(int).groupby((df != 1).cumsum()).cumsum()

    # Find indices of zeros between sequences of five or more consecutive ones
    #indices_zeros = df[df == 0].groupby(consecutive_periods).filter(lambda x: (x == 0).sum() >= window_size/dt).index
    
    
    plt.plot(data[var][:],'r')
    plt.axhline( y=threshold, color='k', linestyle='--')
    plt.plot(consecutive_periods,'go')
    #plt.plot(data[var].where(consecutive_periods==0)[:],'ro')
    #plt.plot(data[var].where(consecutive_periods==1)[:],'go')
    plt.grid()
    plt.show()    
    #breakpoint()
    # add all periods with zero waiting time (consecutive_periods==1)
    # counter_list_no_waiting = [window_size]*int((np.sum(consecutive_periods)*dt)//window_size)
    # add all periods with waiting time (consecutive_periods==0)
    counter = 0
    counter_list_with_waiting =   [[] for _ in range(12)]
    for i in range(len(consecutive_periods)-1):
        if consecutive_periods.iloc[i]==0 and consecutive_periods.iloc[i+1]==0:
            counter = counter + dt
        elif consecutive_periods.iloc[i]==0 and consecutive_periods.iloc[i+1]==1:
            counter = counter + dt
            counter_list_with_waiting[consecutive_periods.index[i].month-1].append(counter)
            counter = 0
    counter_list =  counter_list_with_waiting #+ counter_list_no_waiting 
    
    mean = np.zeros(12)
    p10 = np.zeros(12)
    p50 = np.zeros(12)
    p90 = np.zeros(12)

    for j in range(len(counter_list)): # 12 months
        counter_list_days = np.array(counter_list[j])/24 
        mean[j] = np.mean(counter_list_days)
        p10[j] = np.percentile(counter_list_days, 10)
        p50[j] = np.percentile(counter_list_days, 50)
        #p75 = np.percentile(counter_list_days, 75)
        p90[j] = np.percentile(counter_list_days, 90)
    #breakpoint()
    return mean, p10, p50,p90

def weather_window_length(time_series,threshold,op_duration,timestep,month=None):
    """
    This function calculates weather windows statistics for a condition on one variable

    Parameters
    ----------
    tim_series: pd.DataFrame
        Contains timeseries of the variable of interest
    threshold: float
        Threshold below which operation is possible (same unit as timeseries)
    op_duration: float
        Duration of operation in hours
    timestep: float
        Time resolution of time_series in hours
    month: integer
        From 1 for January to 12 for Decemer. Default is all year

    Returns
    -------
    Returns statistics of weather windows duration in hours

    Authors
    -------
    Written by clio-met
    """
    # time_series: input timeseries
    # threshold over which operation is possible (same unit as timeseries)
    # op_duration: duration of operation in hours
    # timestep: time resolution of time_series in hours
    # month: default is all year
    # returns an array with all weather windows duration in hours
    month_ts = time_series.index.month
    ts_mask=np.where(time_series<threshold,1,0)
    od=int(op_duration/timestep)
    ts=np.zeros((len(ts_mask)-od+1))
    for i in range(len(ts_mask)-od+1):
        ts[i]=np.sum(ts_mask[i:i+od])
    s0=np.where(ts==od)[0].tolist()
    mon_s0=month_ts[0:s0[-1]+1]
    wt=[]
    for s in range(len(s0)):
        if s0[s]==0:
            wt.append(0)
        elif s==0:
            diff=s0[s]
            a=0
            wt.append(diff)
            while (diff!=0):
                diff=s0[s]-a-1
                wt.append(diff*timestep)
                a=a+1
        else:
            diff=s
            a=0
            while (diff!=0):
                diff=s0[s]-s0[s-1]-a-1
                wt.append(diff*timestep)
                a=a+1
    wt1=(np.array(wt)+op_duration)/24
    # Note that in this subroutine, we stop the calculation of the waiting time
    # at the first timestep of the last operating period found in the timeseries
    if month is None:
        mean = np.mean(wt1)
        p10 = np.percentile(wt1,10)
        p50 = np.percentile(wt1,50)
        p90 = np.percentile(wt1,90)
    else:
        mean = np.mean(wt1[mon_s0==month])
        p10 = np.percentile(wt1[mon_s0==month],10)
        p50 = np.percentile(wt1[mon_s0==month],50)
        p90 = np.percentile(wt1[mon_s0==month],90)
    return mean, p10, p50, p90


def weather_window_length_MultipleVariables(df,vars,threshold,op_duration,timestep,month=None):
    """
    This function calculates weather windows statistics for up to 3 simultaneous conditions

    Parameters
    ----------
    df: pd.DataFrame
        Contains timeseries for different variables
    vars: list of strings
        Variables' names to consider (up to 3)
    threshold: list of floats
        Thresholds below which operation is possible
        for each variable (same unit as timeseries)
    op_duration: float
        Duration of operation in hours
    timestep: float
        Time resolution of time_series in hours
    month: integer
        From 1 for January to 12 for Decemer. Default is all year

    Returns
    -------
    Returns statistics of weather windows duration in hours

    Authors
    -------
    Generalization of weather_window_length to multiple conditions by clio-met
    """
    month_ts = df.index.month
    if (len(vars)!=len(threshold)):
        print('Error: vars must be the same length as threshold')
        print(sys.exit())
    if len(vars)==1:
        ts_mask=np.where(df[vars[0]]<threshold[0],1,0)
    elif len(vars)==2:
        ts_mask=np.where(((df[vars[0]]<threshold[0]) & (df[vars[1]]<threshold[1])),1,0)
    elif len(vars)==3:
        ts_mask=np.where(((df[vars[0]]<threshold[0]) & (df[vars[1]]<threshold[1]) & (df[vars[2]]<threshold[2])),1,0)
    else:
        print('Error: only 3 variables can be given')
        sys.exit()
    od=int(op_duration/timestep)
    ts=np.zeros((len(ts_mask)-od+1))
    for i in range(len(ts_mask)-od+1):
        ts[i]=np.sum(ts_mask[i:i+od])
    s0=np.where(ts==od)[0].tolist()
    mon_s0=month_ts[0:s0[-1]+1]
    wt=[]
    for s in range(len(s0)):
        if s0[s]==0:
            wt.append(0)
        elif s==0:
            diff=s0[s]
            a=0
            wt.append(diff)
            while (diff!=0):
                diff=s0[s]-a-1
                wt.append(diff*timestep)
                a=a+1
        else:
            diff=s
            a=0
            while (diff!=0):
                diff=s0[s]-s0[s-1]-a-1
                wt.append(diff*timestep)
                a=a+1
    wt1=(np.array(wt)+op_duration)/24
    # Note that in this subroutine, we stop the calculation of the waiting time
    # at the first timestep of the last operating period found in the timeseries
    if month is None:
        mean = np.mean(wt1)
        p10 = np.percentile(wt1,10)
        p50 = np.percentile(wt1,50)
        p90 = np.percentile(wt1,90)
        p95 = np.percentile(wt1,95)
        max = np.max(wt1)
    else:
        mean = np.mean(wt1[mon_s0==month])
        p10 = np.percentile(wt1[mon_s0==month],10)
        p50 = np.percentile(wt1[mon_s0==month],50)
        p90 = np.percentile(wt1[mon_s0==month],90)
        p95 = np.percentile(wt1[mon_s0==month],95)
        max = np.max(wt1[mon_s0==month])
    return mean, p10, p50, p90, p95, max


def pressure_surge(df,var='MSLP'):
    surge_max = (min(df.MSLP)-np.mean(df.MSLP))*(-0.01)
    surge_min = (max(df.MSLP)-np.mean(df.MSLP))*(-0.01)
    return  surge_min, surge_max


def nb_hours_below_threshold(df,var,thr_arr):
    thr_arr=np.array(thr_arr)
    delta_t=(df.index.to_series().diff().dropna().dt.total_seconds()/3600).mean()
    years=df.index.year.to_numpy()
    years_unique=np.unique(years)
    # Calculate the number of hours with hs below a threshold
    nbhr_arr=np.zeros((len(thr_arr),len(years_unique)))
    j=0
    for yr in years_unique:
        df1=df[df.index.year == yr]
        df1=df1[var]
        i=0
        for t in thr_arr:
            nbhr_arr[i,j]=len(df1[(df1 < t)])*delta_t
            i=i+1
        j=j+1
        del df1
    del i,j
    del years,years_unique,delta_t
    return nbhr_arr

def linfitef(x, y, stdx: float=1.0, stdy: float=1.0) -> tuple[float, float]:
    """
    Perform a linear fit considering uncertainties in both variables.
    Parameters:
    x (array-like): Independent variable data points.
    y (array-like): Dependent variable data points.
    
    stdx (float): Standard deviation of the error of x. 
    stdy (float): Standard deviation of the error of y.

    Default: stdx=stdy=1.0

    NB! Only relative values matter, i.e. stdx=1, stdy=2 gives same results as stdx=2, stdy=4.

    NB! For stdx=0, the method is identical to a normal least squares fit.
    
    Returns:
    tuple: Coefficients of the linear fit (slope, intercept).
    
    References:
    - Orear, J (1982). Least squares when both variables have uncertainties, J. Am Phys 50(10).
    """
    # Convert inputs to numpy arrays
    x = np.asarray(x)
    y = np.asarray(y)
    
    # Validate input lengths
    if x.shape != y.shape:
        raise ValueError("Input arrays must have the same shape.")
   
    # Calculate means of x and y
    x0 = np.mean(x)
    y0 = np.mean(y)
    
    # Calculate variances
    sx2 = stdx**2
    sy2 = stdy**2
    
    # Calculate sum of squares
    Sx2 = np.sum((x - x0)**2)
    Sy2 = np.sum((y - y0)**2)
    Sxy = np.sum((x - x0) * (y - y0))
    
    # Check for special cases where uncertainties or covariance might be zero
    if sx2 == 0 or Sxy == 0:
        slope = Sxy / Sx2
    else:
        term = (sy2 * Sx2)**2 - 2 * Sx2 * sy2 * sx2 * Sy2 + (sx2 * Sy2)**2 + 4 * Sxy**2 * sx2 * sy2
        slope = (sx2 * Sy2 - sy2 * Sx2 + np.sqrt(term)) / (2 * Sxy * sx2)
    
    # Calculate intercept
    intercept = y0 - slope * x0
    
    return slope, intercept



def tidal_type(df,var='tide'):
    """
    This function calculates the tidal type from sea level

    Parameters
    ----------
    df: pd.DataFrame
        Contains the timeseries with index as hourly datetime
    var: string
        Variable name, column name

    Returns
    -------
    output: string
        Tidal type
    
    Authors
    -------
    Written by Dung M. Nguyen
    """
    def find_h_g(Xk,Tm):
        dt = 1
        K = 0
        for i in range(len(Xk)):
            c = i/Tm
            if c.is_integer():
                K = i
            
        if K == 0 : 
            Hm = 0
            gm = 0
        else:
            Am = 0
            Bm = 0
            for k in range(K+1):
                Am = Am + 2/K*Xk[k]*np.cos(2*np.pi/Tm*k*dt)
                Bm = Bm + 2/K*Xk[k]*np.sin(2*np.pi/Tm*k*dt)
                
            Hm = np.sqrt(Am**2 + Bm**2)
            if Bm > 0 and Am > 0:
                gm = np.arctan(Bm/Am)
            elif Bm > 0 and Am < 0:
                gm = np.arctan(Bm/Am) + np.pi
            elif Bm < 0 and Am < 0:
                gm = np.arctan(Bm/Am) + np.pi
            elif Bm < 0 and Am > 0:
                gm = np.arctan(Bm/Am) + 2*np.pi
    
        return Hm, gm
    
    mean = np.mean(df[var].values)
    series = df.tide.values - mean
    
    ## M2
    Tm = 12.42 # hours 
    Hm, gm = find_h_g(series,Tm) 
    Hm2=Hm
    
    ## S2
    Tm = 12.00 # hours 
    Hm, gm = find_h_g(series,Tm) 
    Hs2=Hm
    
    ### K1
    Tm = 23.934 # hours 
    Hm,gm = find_h_g(series,Tm)
    Hk1=Hm
    
    #### O1
    Tm = 25.82 # hours 
    Hm, gm = find_h_g(series,Tm) 
    Ho1=Hm
    
    F = (Hk1+Ho1)/(Hm2+Hs2)
    if F < 0.25 :
        tidal_type = 'Tidal type = semi-diurnal'
    elif F < 1.5 :
        tidal_type = 'Tidal type = mixed, mainly semi-diurnal'
    elif F < 3 :
        tidal_type = 'Tidal type = mixed, mainly diurnal'
    else:
        tidal_type = 'Tidal type = diurnal'

    return tidal_type