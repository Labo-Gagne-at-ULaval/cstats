#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Script to compute statistics for a chosen column in a file.
Usage : cstats.py filename column# [column label] [GRAPH flag] [SAVE_TRIMMED_DATA flag]

Usage 1 (with filename) :
    cstats.py filename # [label] [graph?] [save trimmed data?]
    
Usage 2 (with STDIN) :
    cstats.py stdin # [label] [graph?] [save trimmed data?] < filename
    cat filename | cstats.py stdin # [label]
    tail -n 100 filename | cstats.py stdin # [label]

# for first column is 0

Optional third argument : label for the number in column
    if label is more than one word, or contains special characters
    use single quotes :
        'protein concentration (mM)'

Optional fourth argument : 0 (no graph) or 1 (graph, default)

Optional fifth argument : 0 (do not save trimmed data, default) or 1 (save trimmed data)

The program identifies and highlights potential outliers:
  Outliers are selected using the rule "median +/- 3* MAD",
    where MAD= Median Absolute Deviation
  Statistics for the trimmed data (without outliers) is provided for four rounds of trimming

Output to terminal (6 columns):
    [1] All data    [2-6] Trimmed data, round 1-5
        Count
        Min
        Max
        Mean
        StD (standard deviation with ddof=1)
        MeanAD (mean absolute deviation)
        SEM (standard error of the mean)
        ci95 (95% confidence interval for mean based on SEM)
        Median
        MAD (median absolute deviation)
        Skewness
        Kurtosis (normal Gaussian has kurtosis=0)

Graphical output :
    Histogram with mean and median

Written by Stephane M. Gagne, Laval University, Canada
(Replacement for my old 2004 "stats1" awk script)

v. 0.1.1 (2019-09-19) :
    - rewrote some code (more compact)
    - improved comments
    - added # of outliers to console output
v. 0.1.0 (2019-09-15) :
    - Initial version
'''

########
# TODO #
########


#########
# FLAGS #
#########
'''
TESTING flag
    0 : normal, use file
    1 : use generated normal distribution
    2 : use generated normal distribution with outsiders on one side
    3 : use generated array with 60% same values
    4 : use generated array with 100% same values
    5 : use generated array with uniform distribution
    6 : use generated normal distribution with outsiders on both side
   10 : use misc array

GRAPH flag
    0 : no graphics presented
    1 : graphic with four plots presented
    
SAVE_TRIMMED_DATA flag
    0 : do not save trimmed data
    1 : prompt for saved data
'''
TESTING=2
GRAPH=1
SAVE_TRIMMED_DATA=0


##############
# INITIALIZE #
##############
import sys
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import math
import scipy.stats as st
sys.path.append('/home/smg/bin')
import mean_abs_dev

mpl.rcParams['font.family'] = 'monospace'
mpl.rcParams['font.monospace'] = 'Cousine'
mpl.rcParams['figure.autolayout'] = False
mpl.style.use('fast')

#############
# FUNCTIONS #
#############
def thousands(x, pos):               # Divide tick labels by 1000
    return '%g' % (x/1000)

def make_test_data(testing):         # Generate test data
    rg=np.random.default_rng()
    size=1000000
    outliers=10000
    outliers_center=6
    if testing == 1 :
        d=rg.standard_normal(size)
    elif testing == 2 :
        d=rg.standard_normal(size)
        d[:outliers]=rg.normal(outliers_center,0.1,outliers)
    elif testing == 3 :
        d=rg.standard_normal(size)
        n=int(0.60*size+1)
        d[:n]=0.0
    elif testing == 4 :
        d=np.ones(size)
    elif testing == 5 :
        d=rg.uniform(-1,1,size)
    elif testing == 6 :
        outliers=int(outliers/2)
        d=rg.standard_normal(size)
        d[:outliers]=rg.normal(outliers_center,0.1,outliers)
        d[outliers:outliers*2]=rg.normal(-outliers_center,0.5,outliers)
    elif testing == 10 :
        d=np.array([1,2,3,4,5,6,7,8,9])
    return d

def doStats(array,i):                 # Compute statistics and generate trimmed data
    ddof=1
    mad_sf=1.4826
    mean_ad_sf=1/(np.sqrt(2/np.pi))
    count[i]=array.size
    mini[i]=np.amin(array)
    maxi[i]=np.amax(array)
    mean[i]=np.mean(array)
    std[i]=np.std(array,ddof=ddof)
    sem[i]=st.sem(array,ddof=ddof)
    ci95[i]=sem[i]*1.96
    median[i]=np.median(array)
    mad[i]=st.median_abs_deviation(array,scale=mad_sf)
    mean_ad[i]=mean_abs_dev.mean_absolute_deviation(array,center=np.mean,scale=mean_ad_sf)
    skew[i]=st.skew(array,bias=1)
    kurt[i]=st.kurtosis(array,fisher=True)
    if mad[i] != 0.0 :             # Use MAD if MAD != 0
        trd=np.extract((array>=median[i]-3*mad[i]) & (array<=median[i]+3*mad[i]),array)
    else :                      # Use MeanAD if MAD==0
        trd=np.extract((array>=median[i]-3*mean_ad[i]) & (array<=median[i]+3*mean_ad[i]),array)
    outliers[i]=d[i].size-trd.size
    return trd

def plValues(ax,array,mean,median,MAD):        # Plot Values vs Position
    ax.plot(array, color = '0.4', linewidth=0.5)
    ax.plot(np.sort(array), color = '0.0', linewidth=2.0)
    ax.set_ylabel(label, size=12)
    ax.axhline(y=mean,color='0.0', linewidth=2.0)
    ax.axhline(y=median,color='0.0', linewidth=2.0, linestyle='dashed')
    ax.axhspan(median-3*MAD,median+3*MAD,color='0.90',zorder=0.0)
    ax.autoscale(axis='x',tight=True)
    min_xlim, max_xlim = ax.get_xlim()
    ax.set_xlim(min_xlim-(max_xlim-min_xlim)*0.01,max_xlim+(max_xlim-min_xlim)*0.01)
    min_ylim, max_ylim = ax.get_ylim()
    if min_ylim > (median-3.5*MAD) : min_ylim=median-3.5*MAD
    if max_ylim < (median+3.5*MAD) : max_ylim=median+3.5*MAD
    ax.set_ylim(min_ylim,max_ylim)

def plHist(ax,array,mean,std,mean_ad,sem,median,mad,MAD):     # Plot Histogram
    rects=ax.hist(array, color = '0.0', rwidth=0.80, bins='doane',alpha=1.0)
    delta=(rects[1][1]-rects[1][0])*0.49
    maxbar=np.amax(rects[0])
    for i in range(rects[0].size):
        if rects[0][i]<1000*maxbar*0.01 and rects[0][i]>0 :
            ax.annotate(int(rects[0][i]),xy=(rects[1][i]+delta, rects[0][i]),size=6,ha='center',va='bottom')
    ax.set_xlabel(label, size=12)
    ax.set_ylabel('Frequency', size=12)
    ylim_mult=1.2
    min_ylim, max_ylim = ax.get_ylim()
    min_xlim, max_xlim = ax.get_xlim()
    if max_ylim > 8000/ylim_mult :
        ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(thousands))
        ax.set_ylabel('Frequency (x1000)', size=12)
    if mean <= median :
        mean_align='right'
        median_align='left'
        if (mean-min_xlim) < (max_xlim-median) :
            min_xlim = (mean - (max_xlim-median))
        else :
            max_xlim = (median + (mean-min_xlim))
    else :
        mean_align='left'
        median_align='right'
        if (median-min_xlim) < (max_xlim-mean) : min_xlim = (median - (max_xlim-mean))
        else : max_xlim = (mean + (median-min_xlim))
    if min_xlim > (median-3.5*MAD) : min_xlim=median-3.5*MAD
    if max_xlim < (median+3.5*MAD) : max_xlim=median+3.5*MAD
    ax.set_xlim(min_xlim, max_xlim)
    ax.set_ylim(min_ylim,max_ylim*ylim_mult)
    ax.axvline(x=mean,ymax=0.99/ylim_mult,color='0.7',linewidth=4,linestyle='solid')
    ax.axvline(x=median,ymax=0.99/ylim_mult,color='0.7',linewidth=4,linestyle='dashed')
    ax.axvspan(median-3*MAD,median+3*MAD,ymax=1/ylim_mult,color='0.90',zorder=0.0)
    ax.text(mean, max_ylim*ylim_mult*0.99, ' Mean:{1:{0}} \n   SD:{3:{0}} \n  SEM:{2:{0}} '.format(fmt,mean,sem,std), color='0.0', ha=mean_align, va='top', size=11)
    ax.text(median, max_ylim*ylim_mult*0.99, ' Median:{1:{0}} \n    MAD:{2:{0}} \n MeanAD:{3:{0}} '.format(fmt,median,mad,mean_ad), color='0.4', ha=median_align, va='top', size=11)
    if mad !=0.0 : ax.text(min_xlim, max_ylim*ylim_mult*0.99, ' Outliers :\n  med\u00B13*MAD',color='0.4',va='top', size=11)
    else : ax.text(min_xlim, max_ylim*ylim_mult*0.99, ' Outlier ID\n med\u00B13*MeanAD',color='0.4',va='top', size=11)


#########################################################
# Load file, with handling of errors and gracefull exit #
#########################################################
d=[]
if TESTING == 0:
    try:
        f=sys.argv[1]
        c=int(sys.argv[2])
        if len(sys.argv) > 3 : label=sys.argv[3]
        else : label="Column "+str(c)
        if len(sys.argv) > 4 : GRAPH=int(sys.argv[4])
        if len(sys.argv) > 5 : SAVE_TRIMMED_DATA=int(sys.argv[5])
        if f == 'stdin' : d.append(np.loadtxt(sys.stdin, usecols=c))
        else : d.append(np.loadtxt(f, usecols=c))
    except IndexError:
        print('''
ERROR: Need minimum two arguments : filename and column #

Optional third argument : label for the number in column
    if label is more than one word, or contains special characters
    use single quotes :
        'protein concentration (mM)'
Optional fourth argument : 0 (no graph) or 1 (graph, default)
Optional fifth argument : 0 (do not save trimmed data, default) or 1 (save trimmed data)

Usage 1 (with filename) :
    cstats.py filename # [label] [graph?] [save trimmed data?]
    
Usage 2 (with STDIN) :
    cstats.py stdin # [label] [graph?] [save trimmed data?] < filename
    cat filename | cstats.py stdin # [label]
    tail -n 100 filename | cstats.py stdin # [label]
    
Column # : # for first column is 0
''')
        sys.exit()
    except FileNotFoundError:
        print("ERROR: file not found :",f)
        sys.exit()
    except ValueError:
        print("ERROR: wrong column # :",c)
        print("Usage : cstats.py filename column# (# for first column is 0)")
        sys.exit()
    
    # Exit if only one value for statistics
    count=d[0].size
    if count < 2 :
        print("ERROR: Can't do statistics... file / column has only one value")
        sys.exit()
else :
    f='Testing Mode='+str(TESTING)
    label='Test data'
    d.append(make_test_data(TESTING))


#######################################################
# Statistics calculations and outliers identification #
#######################################################
'''
Statistics calculation
    use numpy functions for mean, std, min, max, median
    use scipy.stats for sem, mad, skew
    use ddof=1 for std, sem (default for np.std is 0, default for st.sem is 1)
Outliers identification
    use MAD from SciPy (median absolute deviation with default scale=1.4826)
    if MAD==0, use MAD from Pandas instead (mean absolute deviation, mean_mad in script)
    MAD scaling factor:
        for median absolute deviation, use 1.4826 (default constant in SciPy mad function)
        for mean absolute deviation, use 1.253314 (no constant in Pandas mad function)
            => so multiply Pandas mad by 1.253314
        the scaling factor "normalizes" the calculated MAD (MAD ~ SD for normal data)
    print/plot for median +/- 2*MAD and 3*MAD
'''
trim_rounds=5

count,outliers,mini,maxi,mean,std,mean_ad,sem,ci95,median,mad,skew,kurt=np.array([np.ones(trim_rounds+1)]*13)

for i in range(trim_rounds+1):
    d.append(doStats(d[i],i))

MAD=[0.,0.]
if mad[0] != 0.0 : MAD[0]=mad[0]
else : MAD[0]=mean_ad[0]
if mad[1] != 0.0 : MAD[1]=mad[1]
else : MAD[1]=mean_ad[1]


################################
# Print statistics to terminal #
################################
statsList={'Count':count,'Outliers':outliers,'Min':mini,'Max':maxi,'Mean':mean,'StD':std,'MeanAD':mean_ad,'SEM':sem,'ci95 \u00B1':ci95,'Median':median,'MAD':mad,'Skewness':skew,'Kurtosis':kurt}
print()
print('                                                    Trim \u00B13*MAD ')
print('                            -----------------------------------------------------------')
print('                   All      Round 1      Round 2      Round 3      Round 4      Round 5')
print('=======================================================================================')
for i,j in statsList.items() :
    if i == 'Count' or i == 'Outliers' : fmt='9.0f'
    elif i == 'Skewness' or i=='Kurtosis' : fmt='9.2f'
    elif abs(mean[0]) > 1E06 : fmt='9.3e'
    elif sem[1] > 0 : fmt=f"9.{max(0,math.ceil(-math.log10(sem[1]))):}f"
    elif sem[0] == 0 : fmt='9g'
    else : fmt='9.5f'
    if i == 'Mean' or i == 'Median' or i == 'Skewness' :
        print('---------------------------------------------------------------------------------------')

    print(f'{i:>10}:  {j[0]:{fmt}}    {j[1]:{fmt}}    {j[2]:{fmt}}    {j[3]:{fmt}}    {j[4]:{fmt}}    {j[5]:{fmt}}')
print('---------------------------------------------------------------------------------------')
print()


#####################
# Save trimmed data #
#####################
if SAVE_TRIMMED_DATA==1 :
    np.savetxt("trim_1.dat",d[1],fmt="%9g")
    np.savetxt("trim_2.dat",d[2],fmt="%9g")
    np.savetxt("trim_3.dat",d[3],fmt="%9g")
    np.savetxt("trim_4.dat",d[4],fmt="%9g")
    np.savetxt("trim_5.dat",d[5],fmt="%9g")
    print('Trimmed data saved as "trim_[1-5].dat"')
    print()


##################
# Graphic output #
##################
if GRAPH == 1 :
    # Original data : ax1 (values) and ax3 (histogram)
    # Without outliers : ax2 (values) and ax4 (histogram)
    fig, ((ax1,ax2),(ax3,ax4)) = plt.subplots(nrows=2, ncols=2, figsize=[15.8,7.6], dpi=120)
    fig.dpi=120
    fig.suptitle(f+" : "+label, size=16, y=0.99, weight='bold', va='top', bbox={'facecolor': '0.9', 'edgecolor':'0.0', 'pad': 3})
    ax1.tick_params(axis='both', labelsize=10)
    ax2.tick_params(axis='both', labelsize=10)
    ax3.tick_params(axis='both', labelsize=10)
    ax4.tick_params(axis='both', labelsize=10)
    ax1.xaxis.tick_top()
    ax2.xaxis.tick_top()
    ax2.yaxis.tick_right()
    ax4.yaxis.tick_right()
    ax1.ticklabel_format(axis='x', style='plain')
    
    plValues(ax1,d[0],mean[0],median[0],MAD[0])
    plValues(ax2,d[1],mean[1],median[1],MAD[1])
    plHist(ax3,d[0],mean[0],std[0],mean_ad[0],sem[0],median[0],mad[0],MAD[0])
    plHist(ax4,d[1],mean[1],std[1],mean_ad[1],sem[1],median[1],mad[1],MAD[1])
    
    ax1.set_title('Original data', size=14, weight='bold', pad=15, ha='right', bbox={'facecolor': '1.0', 'pad':3})
    ax2.set_title('Outliers removed (\u00B1 3*MAD)', size=14, weight='bold', pad=15, ha='left', bbox={'facecolor': '1.0', 'pad':3})
    ax2.yaxis.set_label_position('right')
    ax4.yaxis.set_label_position('right')
    
    plt.figtext(0.5,0.005,"NOTE for outliers: if MAD==0 (median absolute deviation),\nuse MeanAD instead (mean absolute deviation)", ha='center', va='bottom', fontsize=8, bbox={'facecolor': '0.95', 'pad': 2})
    
    # Publicity...
    plt.figtext(0.995, 0.005, "cstats.py: Stephane M. Gagne\nLaval University (2019)", ha='right', va='bottom', fontsize=7)
    
    # Plot to screen
    plt.subplots_adjust(top=0.915,bottom=0.07,left=0.045,right=0.955,hspace=0.015,wspace=0.02)
    plt.show()
