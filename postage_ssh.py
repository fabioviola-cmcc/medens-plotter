#!/usr/bin/python3


###############################################
#
# global reqs
#
###############################################

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from numpy import meshgrid
from numpy import linspace
import configparser
import numpy as np
import traceback
import datetime
import xarray
import numpy
import math
import pdb
import sys
import os


###############################################
#
# initial config
#
###############################################

appname = "PlotPostageSsh"


###############################################
#
# main
#
###############################################

if __name__ == "__main__":

    ###############################################
    #
    # read input parameters
    #
    ###############################################    
    
    # read config file name
    configFile = None
    try:
        configFile = sys.argv[1]
    except:
        print("[ERROR] -- Config file not provided!")
        sys.exit(1)

    # read date
    inputDate = None
    try:
        inputDate = sys.argv[2]
    except:
        inputDate = datetime.datetime.today().strftime("%Y%m%d")

        
    ###############################################
    #
    # parse config file
    #
    ###############################################
        
    configParser = configparser.ConfigParser()
    configParser.read(configFile)

    # paths
    baseEnsPathTemplate = configParser.get("default", "baseEnsPath")
    inputFileTemplate = configParser.get("postcardSsh", "inputFile")
    inputFiles = []
    print("[%s] -- Input files set to:" % (appname))
    for i in range(10):
        inputFile = os.path.join(baseEnsPathTemplate.format(INSTANCE=i, DATE=inputDate), inputFileTemplate.format(DATE=inputDate))
        inputFiles.append(inputFile)
        print(inputFile)

    # chart details
    resolution = configParser.get("postcardSsh", "resolution")
    colorMap = configParser.get("postcardSsh", "colorMap")
    minValue = configParser.getfloat("postcardSsh", "minValue")
    maxValue = configParser.getfloat("postcardSsh", "maxValue")
    levels = configParser.getint("postcardSsh", "levels")
    print("[%s] -- Resolution set to: %s" % (appname, resolution))
    print("[%s] -- Min Value set to: %s" % (appname, minValue))
    print("[%s] -- Max Value set to: %s" % (appname, maxValue))
    print("[%s] -- Color map set to: %s" % (appname, colorMap))
    print("[%s] -- Levels set to: %s" % (appname, levels))
                    
        
    ###############################################
    #
    # start processing
    #
    ###############################################

    # open files
    datasets = []
    for i in inputFiles:
        datasets.append(xarray.open_dataset(i))

    # grid indices
    x = datasets[0].nav_lon.transpose().values[0]
    y = datasets[0].nav_lat.values[0]

    # lats and lons
    lats = datasets[0].nav_lat.transpose().values[0]
    lons = datasets[0].nav_lon.values[0]

    # create the grid
    xxx, yyy = meshgrid(lons, lats)
    
    # iterate over timesteps
    timestep_index = 0
    for t in datasets[0].time_counter:

        d1 = str(t.values).split("T")[0]        
        hour = str(t).split("T")[1].split(":")[0]
        minu = 30
        d2 = "%s:%s" % (hour, minu)
        d3 = "%s, %s" % (d1, d2)
        d4 = "%s_%s%s" % (d1, hour, minu)

        # debug print
        print("[%s] -- Timestep: %s" % (appname, d3))
                
        fig, axes = plt.subplots(nrows=5, ncols=2)
        
        ax_index = 0
        for ax in axes.flat:

            # create basemap
            bmap = Basemap(resolution=resolution,
                           llcrnrlon=lons[0],llcrnrlat=lats[0],
                           urcrnrlon=lons[-1],urcrnrlat=lats[-1], ax=ax)                

            # contourf
            mean_data_0 = datasets[ax_index].sossheig[timestep_index,:,:]            
            mean_data = mean_data_0.where(mean_data_0 >= minValue, other=minValue).where(mean_data_0 <= maxValue, other=maxValue)
            contour_levels = linspace(minValue, maxValue, levels)
            im = ax.contourf(xxx, yyy, mean_data, cmap=colorMap, levels=contour_levels, vmin=minValue, vmax=maxValue)
            ax.set_title("Member %s" % ax_index, fontsize = 5, pad = 4)
            ax.axis('off')
            ax_index += 1

            # draw coastlines, country boundaries, fill continents.
            bmap.drawcoastlines(linewidth=0.25)
            bmap.fillcontinents(color='white')

        # colorbar
        ticks = range(int(minValue), int(maxValue)+1, 1)
        cb = fig.colorbar(im, ax=axes.ravel().tolist(), ticks=ticks, shrink=0.5)
        cb.set_label("Sea Level Height (m)", fontsize = 3)
        cb.ax.tick_params(labelsize=3)
        for t in cb.ax.get_xticklabels():
            t.set_fontsize(1)
        
        # title
        finalDate = "%s:30" % (d3.split(":")[0])
        plt.suptitle("Sea Surface Height.\nTimestep: %s" % (finalDate), fontsize = 5)
            
        # save file
        filename = "output/postcard_ssh_%s.png" % (d4)
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        print("File %s generated" % filename)
        plt.clf()
        
    # increment timestep
    timestep_index += 1