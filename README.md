# cstats - Script to compute statistics for a chosen column in a file.

## Usage
Usage : cstats.py filename column# [column label] [GRAPH flag] [SAVE_TRIMMED_DATA flag]

Usage 1 (with filename) :
```
    cstats.py filename # [label] [graph?] [save trimmed data?]

    # : column number (0 = first column)
```
Usage 2 (with STDIN) :
```
    cstats.py stdin # [label] [graph?] [save trimmed data?] < filename
    cat filename | cstats.py stdin # [label]
    tail -n 100 filename | cstats.py stdin # [label]
    
    # : column number (0 = first column)
```

## Optional arguments
Optional third argument : label for the number in column
- if label is more than one word, or contains special characters, use single quotes : 'protein concentration (mM)'

Optional fourth argument : 0 (no graph) or 1 (graph, default)

Optional fifth argument : 0 (do not save trimmed data, default) or 1 (save trimmed data)

## Outliers
The program identifies and highlights potential outliers:
- Outliers are selected using the rule "median +/- 3* MAD", where MAD= Median Absolute Deviation
- Statistics for the trimmed data (without outliers) is provided for four rounds of trimming

## Output to terminal (6 columns):
```
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
```
## Graphical output :
- Histogram with mean and median

## Versions
Written by Stephane M. Gagne, Laval University, Canada  
(Replacement for my old 2004 "stats1" awk script)  

v. 0.1.1 (2019-09-19) :  
- rewrote some code (more compact)
- improved comments
- added # of outliers to console output

v. 0.1.0 (2019-09-15) :  
 - Initial version

