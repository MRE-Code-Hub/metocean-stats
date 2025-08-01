import matplotlib.pyplot as plt
import numpy as np
import windrose
import sys
import matplotlib.ticker as mticker

def rose(data,
         var_dir,
         var,
         max_var,
         step_var,
         min_percent,
         max_percent,
         step_percent,
         nsector=16,
         cmap=plt.get_cmap("viridis")):

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="windrose")
    ax.bar(data[var_dir], data[var], bins=np.arange(0, max_var, step_var), cmap=cmap, normed=True, opening=0.9, edgecolor='white', nsector=nsector)
    ax.set_yticks(np.arange(min_percent, max_percent, step_percent))
    ax.set_yticklabels(np.arange(min_percent, max_percent,step_percent))
    ax.legend(bbox_to_anchor=(0.90,-0.05),framealpha=0.5)
    return fig


def var_rose(data, 
             var_dir,
             var, 
             method='overall',
             max_perc=40,
             decimal_places=1, 
             units='m/s',
             single_figure=True, 
             output_file='rose.png', 
             nsector=16, 
             cmap=plt.get_cmap("viridis")):
    
    direction = var_dir
    intensity = var

    direction2 = data[direction]
    intensity2 = data[intensity]
    size = 5
    bins_range = np.array([0, np.percentile(intensity2,40),
                   np.percentile(intensity2,60),
                   np.percentile(intensity2,80),
                   np.percentile(intensity2,99)])

    if method == 'overall':
        fig = plt.figure(figsize = (8,8))
        ax = fig.add_subplot(111, projection="windrose")
        ax.bar(direction2, intensity2, normed=True, bins=bins_range, opening=0.99,edgecolor="white",cmap=cmap, nsector=nsector)
        ax.set_yticks(np.arange(5, max_perc+10, step=10))
        ax.set_yticklabels(np.arange(5, max_perc+10, step=10))
        ax.set_legend(decimal_places=decimal_places,  title=units)
        ax.set_title('Overall')
        ax.figure.set_size_inches(size, size)
        plt.savefig(output_file,dpi=100,facecolor='white',bbox_inches='tight')

    elif method == 'monthly':
        fig = monthly_var_rose(data=data,var_dir=direction,var=intensity,bins=bins_range,max_perc=max_perc,
                               decimal_places=decimal_places,units=units,single_figure=single_figure,output_file=output_file)
    
    plt.close()
    return fig

def monthly_var_rose(data, 
                     var_dir,
                     var,
                     bins,
                     max_perc=40,
                     decimal_places=1, 
                     units='m/s',
                     single_figure=True,
                     output_file='rose.png', 
                     nsector=16, 
                     cmap=plt.get_cmap("viridis")):

    # this function make monthly wind/wave rose
    # direction, intensity: panda series 
    # get month from panda series 
    direction = data[var_dir]
    intensity = data[var]
    M = intensity.index.month.values
    
    # get month names 
    import calendar
    months = calendar.month_name[1:] # eliminate the first insane one 
    for i in range(len(months)) : 
        months[i] = months[i][:3] # get the three first letters 
    
    # sort them outh by months 
    dic_intensity = {} # dic_intensity
    dic_direction = {} # dic_direction
    for i in range(len(months)) : 
        dic_intensity[months[i]] = [] 
        dic_direction[months[i]] = [] 
        
    for i in range(len(intensity)) : 
        m_idx = int(M[i]-1)
        dic_intensity[months[m_idx]].append(intensity.iloc[i])
        dic_direction[months[m_idx]].append(direction.iloc[i])

    if single_figure is False:  
        for j in range(12):
            fig = plt.figure(figsize = (8,8))
            ax = fig.add_subplot(111, projection="windrose")
            ax.bar(dic_direction[months[j]], dic_intensity[months[j]], normed=True, bins=bins, opening=0.99,edgecolor="white",cmap=cmap, nsector=nsector)
            ax.set_yticks(np.arange(5, max_perc+10, step=10))
            ax.set_yticklabels(np.arange(5, max_perc+10, step=10))
            ax.set_legend(decimal_places=decimal_places,  title=units)
            ax.set_title(months[j])
            size = 5
            ax.figure.set_size_inches(size, size)
            plt.savefig(months[j]+'_'+output_file,dpi=100,facecolor='white',bbox_inches='tight')
            plt.close()
    else:
        fig, axs = plt.subplots(3, 4, figsize=(20, 15), subplot_kw=dict(projection="windrose"))

        for j, ax in enumerate(axs.flatten()):
            ax.bar(dic_direction[months[j]], dic_intensity[months[j]], normed=True, bins=bins, opening=0.99,edgecolor="white",cmap=cmap, nsector=nsector)
            ax.set_title(months[j],fontsize=16)
            ax.set_yticks(np.arange(5, max_perc+10, step=10))
            ax.set_yticklabels(np.arange(5, max_perc+10, step=10))

        # Place the legend in the last subplot
        axs.flatten()[-1].legend(decimal_places=decimal_places, title=units)

        # Adjust layout to prevent overlap
        plt.tight_layout()

        # Save the figure
        if output_file is not None:
            plt.savefig(output_file, dpi=100, facecolor='white', bbox_inches='tight')

    return fig


def plot_spectrum_2d(ds, var='SPEC', radius='frequency', log_radius=False, plot_type='contourf', dir_letters=False, output_file='Spectrum_plot.png'):
    '''
    This function plots a directional wave spectrum
    
    Parameters
    ----------
    ds : xarray dataset
        Should contain variable var with two (frequencies, directions).
    var : string
        Name of the spectrum variable
    radius : string
        Should be 'period'/'frequency' to plot the periods/frequencies in the radial direction
    log_radius : Boolean
        True to get the radial axis on a logarithmic scale
    plot_type : string
        Can be 'pcolormesh' or 'contourf'
    dir_letters : Boolean
        Displays the directions as letters instead of degrees if True'
    output_file : string
        Name of the figure file (xxx.pdf or xxx.png)

    Returns
    -------
    Figure matplotlib

    Authors
    -------
    Function written by clio-met
    '''
    spectrum=ds[var]
    dims=list(spectrum.dims)
    # Get the coordinates
    frequencies=spectrum.coords[dims[0]].to_numpy()
    directions=spectrum.coords[dims[1]].to_numpy()
    # The last direction should be the same as the first
    if directions[0]!=directions[-1]:
        if directions[0]<360:
            dirc=np.concatenate([directions,directions[0:1]+360])
        else:
            dirc=np.concatenate([directions,directions[0:1]])
        spec=np.concatenate([spectrum[:,:],spectrum[:,0:1]],axis=1)

    # Color map with 10 colors
    cmap = mpl.cm.hot_r(np.linspace(0,1,10))
    cmap = mpl.colors.ListedColormap(cmap)

    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    if radius=='period':
        rad_data=1/frequencies
    elif radius=='frequency':
        rad_data=frequencies

    if plot_type=='pcolormesh':
        c=ax.pcolormesh(np.radians(dirc), rad_data, spec, cmap='hot_r', shading='auto')
    elif plot_type=='contourf':
        c=ax.contourf(np.radians(dirc), rad_data, spec, cmap=cmap)
    else:
        print('plot_type should pcolormesh or contourf')
        sys.exit()

    ax.grid(True)
    if log_radius==True:
        ax.set_rscale('log')
    #ax.set_rlim(0,10)
    if dir_letters==True:
        ticks_loc = ax.get_xticks().tolist()
        ax.xaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
    plt.colorbar(c, label='['+spectrum.units+']', pad=0.1)
    plt.tight_layout()
    if output_file is not None:
        plt.savefig(output_file, dpi=200, bbox_inches='tight')
    plt.close()
         
    return fig


