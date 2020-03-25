#! /usr/bin/env python
import sys
import string
import subprocess
import datetime as date
import numpy as np
import matplotlib.pyplot as plt
import netCDF4 as netcdf4
from scipy import interpolate

# load proper modules first, i.e.
# cheyenne
'''
module load python/2.7.16  
ncar_pylib
#module load numpy/1.12.0
#module load matplotlib/2.0.0
#module load scipy/0.18.1
#module load intel/16.0.3         
#module load ncarcompilers/0.3.5
#module load netcdf/4.4.1.1
#module load netcdf4-python/1.2.7
'''

# caldera / geyser

'''
module load python/2.7.7  
module load numpy/1.11.0
module load pyside/1.1.2
module load matplotlib/1.5.1
module load scipy/0.18.1
module load netcdf4python/1.2.4
'''

#-------------------------------------------------------
"""

This script creates CLM anomaly forcing data

"""
#-------------------------------------------------------

#--  end of function definitions  ---------------------------------
#0

sspnum = 3
smoothsize = 5

if sspnum == 1:
    # SSP1-26
    ssptag = 'SSP126'
    sspoutdir = 'forcingSSP126'
    hist_case = 'b.e21.BHIST.f09_g17.CMIP6-historical.010'
    fut_case = 'b.e21.BSSP126cmip6.f09_g17.CMIP6-SSP1-2.6.001'
if sspnum == 2:
    # SSP3-70
    ssptag = 'SSP370'
    sspoutdir = 'forcingSSP370'
    hist_case = 'b.e21.BHIST.f09_g17.CMIP6-historical.010'
    fut_case = 'b.e21.BSSP370cmip6.f09_g17.CMIP6-SSP3-7.0.001'
if sspnum == 3:
    # SSP5-85
    ssptag = 'SSP585'
    sspoutdir = 'forcingSSP585'
    hist_case = 'b.e21.BHIST.f09_g17.CMIP6-historical.010'
    fut_case = 'b.e21.BSSP585cmip6.f09_g17.CMIP6-SSP5-8.5.001'

spath                 = './'

hist_yrstart          = 2000
hist_yrend            = 2014
hist_nyrs             = hist_yrend - hist_yrstart + 1

fut1_yrstart          = 2015
fut1_yrend            = 2064
fut1_nyrs             = fut1_yrend - fut1_yrstart + 1

fut2_yrstart          = 2065
fut2_yrend            = 2100
fut2_nyrs             = fut2_yrend - fut2_yrstart + 1

fut_yrstart           = 2015
fut_yrend             = 2100
fut_nyrs              = fut_yrend - fut_yrstart + 1

tot_yrstart           = 2000
tot_yrend             = 2100
tot_nyrs              = tot_yrend - tot_yrstart + 1

nmo                   = 12
histnm                = nmo*hist_nyrs
futnm                 = nmo*fut_nyrs
totnm                 = nmo*tot_nyrs
outnm                 = nmo*fut_nyrs

dpath                 = './historyfiles/'
dfile                 = '/lnd/proc/tseries/month_1/'
hdir                  = dpath+hist_case+dfile
fdir                  = dpath+fut_case+dfile

# needed to use QBOT and U10, not using V and U(for sfcwind)
#field_in              = ['TREFHT','PRECT','FSDS','FLDS','QBOT','PS','U10','U10']
field_in              = [   'TBOT',        'RAIN',        'SNOW',        'FSDS',        'FLDS',   'QBOT',   'PBOT']
field_combine         = [        0,             1,             1,             0,             0,        0,        0]
field_out             = [    'tas',          'pr',          'pr',        'rsds',        'rlds',   'huss',     'ps']
units                 = [      'K',           ' ',           ' ',           ' ',           ' ',  'kg/kg',     'Pa']
units_disp            = [      'K',        'mm/s',        'mm/s',   'W m!U-2!N',   'W m!U-2!N',  'kg/kg',     'Pa']
anomsf                = ['anomaly','scale factor','scale factor','scale factor','scale factor','anomaly','anomaly']

nfields               = len(field_in)

#--  Read coordinates
landfile              = hdir+hist_case+'.clm2.h0.TBOT.'+str(hist_yrstart)+'01-'+str(hist_yrend)+'12.nc'
print 'Land File: ' + landfile
f1 = netcdf4.Dataset(landfile, 'r')
landfrac=np.asfarray(f1.variables['landfrac'][:,:],np.float64)
landmask=np.asfarray(f1.variables['landmask'][:,:],np.float64)
area=np.asfarray(f1.variables['area'][:,:],np.float64)
lon   = np.asfarray(f1.variables['lon'][:],np.float64)
lat   = np.asfarray(f1.variables['lat'][:],np.float64)
nlat  = lat.size
nlon  = lon.size
f1.close()
ind=np.where(landfrac > 1.e10)
landfrac[ind]=0

#--  Loop over forcing fields  ------------------------------------
fieldskip = 0
for f in range(nfields):
    # read in last ten years of historical data  ------------------

    infieldname1 = field_in[f]
    infieldcombine1 = field_combine[f]
    if ((infieldcombine1 == 1 and fieldskip == 0) or (infieldcombine1 == 0 and fieldskip == 0)):
        hvarfile1 = hdir+hist_case+'.clm2.h0.'+infieldname1+'.'+str(hist_yrstart)+'01-'+str(hist_yrend)+'12.nc'
        fvarfile1 = fdir+fut_case+'.clm2.h0.'+infieldname1+'.'+str(fut1_yrstart)+'01-'+str(fut1_yrend)+'12.nc'
        fvarfile2 = fdir+fut_case+'.clm2.h0.'+infieldname1+'.'+str(fut2_yrstart)+'01-'+str(fut2_yrend)+'12.nc'
        hf1 = netcdf4.Dataset(hvarfile1, 'r')
        ff1 = netcdf4.Dataset(fvarfile1, 'r')
        ff2 = netcdf4.Dataset(fvarfile2, 'r')
        hvarvalues1 = np.asfarray(hf1.variables[infieldname1][:],np.float64)
        htime1 = np.asfarray(hf1.variables['time'][:],np.float64)
        print 'Reading: ' + hvarfile1
        fvarvalues1 = np.asfarray(ff1.variables[infieldname1][:],np.float64)
        ftime1 = np.asfarray(ff1.variables['time'][:],np.float64)
        long_name = ff1.variables[field_in[f]].long_name
        print 'Reading: ' + fvarfile1
        fvarvalues2 = np.asfarray(ff2.variables[infieldname1][:],np.float64)
        ftime2 = np.asfarray(ff2.variables['time'][:],np.float64)
        print 'Reading: ' + fvarfile2
        hf1.close()
	ff1.close()
        ff2.close()
	if (infieldcombine1 == 1):
	    infieldname2 = field_in[f+1]
            infieldcombine2 = field_combine[f+1]
            hvarfile2 = hdir+hist_case+'.clm2.h0.'+infieldname2+'.'+str(hist_yrstart)+'01-'+str(hist_yrend)+'12.nc'
            fvarfile3 = fdir+fut_case+'.clm2.h0.'+infieldname2+'.'+str(fut1_yrstart)+'01-'+str(fut1_yrend)+'12.nc'
            fvarfile4 = fdir+fut_case+'.clm2.h0.'+infieldname2+'.'+str(fut2_yrstart)+'01-'+str(fut2_yrend)+'12.nc'
            hf2 = netcdf4.Dataset(hvarfile2, 'r')
            ff3 = netcdf4.Dataset(fvarfile3, 'r')
            ff4 = netcdf4.Dataset(fvarfile4, 'r')
            hvarvalues1 = hvarvalues1 + np.asfarray(hf2.variables[infieldname2][:],np.float64)
            print 'Reading: ' + hvarfile2
            fvarvalues1 = fvarvalues1 + np.asfarray(ff3.variables[infieldname2][:],np.float64)
            print 'Reading: ' + fvarfile3
            fvarvalues2 = fvarvalues2 + np.asfarray(ff4.variables[infieldname2][:],np.float64)
            print 'Reading: ' + fvarfile4
            hf2.close()
	    ff3.close()
            ff4.close()
            fieldskip = 1

        allvarvalues = np.concatenate((hvarvalues1,fvarvalues1,fvarvalues2),axis=0)
        alltime = np.concatenate((htime1,ftime1,ftime2),axis=0)
        ftime = np.concatenate((ftime1,ftime2),axis=0)
	outtime = ftime - 16
        histavgvalues = np.zeros((nmo,nlat,nlon))
        histavgcount = np.zeros((nmo))
        runningavgvalues = np.zeros((nlat,nlon))
        runningavgcount = 0.0
        outputvarvalues = np.zeros((outnm,nlat,nlon))

        for hmonthindex in range(histnm):
            havgmonthnum = (hmonthindex) % 12 + 1
            havgmonthindex = havgmonthnum - 1
            histavgvalues[havgmonthindex,:,:] = histavgvalues[havgmonthindex,:,:] * histavgcount[havgmonthindex]
            histavgvalues[havgmonthindex,:,:] = histavgvalues[havgmonthindex,:,:] + allvarvalues[hmonthindex,:,:]
            histavgcount[havgmonthindex] = histavgcount[havgmonthindex] + 1.0
            histavgvalues[havgmonthindex,:,:] = histavgvalues[havgmonthindex,:,:] / histavgcount[havgmonthindex]
#            if (havgmonthindex == 0):
#            print 'Climo: ' + str(hmonthindex) + ' ' + str( havgmonthindex) +' ' + str(hmonthindex) + ' vars ' + str(histavgvalues[havgmonthindex,150,200]) + ' orig ' + str(allvarvalues[hmonthindex,150,200])

        for fmonthindex in range(futnm):
            allmonthindex = fmonthindex + histnm
            allyearindex = allmonthindex / nmo
            favgmonthnum = (allmonthindex) % 12 + 1
            favgmonthindex = favgmonthnum - 1

            firstmonthindex = allmonthindex - nmo * smoothsize
            if allyearindex <= (tot_nyrs - smoothsize):
                lastmonthindex = allmonthindex + nmo * smoothsize
            else:
                lastmonthindex = allmonthindex + nmo * (tot_nyrs - allyearindex)

            runningavgvalues = 0.0
            runningavgcount = 0.0
            for smonthindex in range(firstmonthindex,lastmonthindex,nmo):
                runningavgvalues = runningavgvalues * runningavgcount
                runningavgvalues = runningavgvalues + allvarvalues[smonthindex,:,:]
                runningavgcount = runningavgcount + 1.0
                runningavgvalues = runningavgvalues / runningavgcount
#                if (favgmonthindex == 0):
#                    print 'Search window ' + str(smonthindex) + ' for ' + str(allmonthindex) + ' year ' + str(allyearindex) + ' month ' + str(favgmonthindex) + ' values ' + str(allvarvalues[smonthindex,150,200]) + ' ' + str(runningavgvalues[150,200]) + ' compared to ' + str(histavgvalues[havgmonthindex,150,200])

            climoavgvalues = histavgvalues[favgmonthindex,:,:]
            if anomsf[f] == 'anomaly':
                anomvalues = runningavgvalues - climoavgvalues

            if anomsf[f] == 'scale factor':
                anomvalues = np.ones((nlat,nlon),dtype=np.float64)
                
                nonzeroindex = np.where(climoavgvalues != 0.0)
                anomvalues[nonzeroindex] = runningavgvalues[nonzeroindex]/climoavgvalues[nonzeroindex]

                max_scale_factor = 5.
                if field_in[f] == 'FSDS':
                    max_scale_factor = 2.
                overmaxindex=np.where(anomvalues > max_scale_factor)
                anomvalues[overmaxindex] = max_scale_factor
            
            outputvarvalues[fmonthindex,:,:] = anomvalues

        # create netcdf file  ---------------------------------

        outfilename = spath + sspoutdir + '/'+'af.'+field_out[f]+'.cesm2.'+ssptag+'.'+str(fut_yrstart)+'-'+str(fut_yrend)+'.nc'
        print 'Creating: ' + outfilename
        outfile = netcdf4.Dataset(outfilename, 'w')

#        timetag = date.today()
#        outfile.creation_date = timetag 
        outfile.source_file = spath
        outfile.title = 'anomaly forcing data'
        outfile.note1 = 'Anomaly/scale factors calculated relative to ' \
        +str(hist_yrstart)+'-'+str(hist_yrend) \
        +' climatology from CESM2 historical simulation (case name: '+hist_case+')'
        outfile.note2 = ssptag+' '+str(fut_yrstart)+'-'+str(fut_yrend) \
        +' from CESM simulations (case names: '+fut_case[0]+' and '+fut_case[1]+')'

        outfile.createDimension('lat',int(nlat))
        outfile.createDimension('lon',int(nlon))
        outfile.createDimension('time',int(outnm))
    
        wtime = outfile.createVariable('time',np.float64,('time',))
        wlat  = outfile.createVariable('lat',np.float64,('lat',))
        wlon  = outfile.createVariable('lon',np.float64,('lon',))
        wmask = outfile.createVariable('landmask',np.int32,('lat','lon'))
        warea = outfile.createVariable('area',np.float64,('lat','lon'))
        wfrac = outfile.createVariable('landfrac',np.float64,('lat','lon'))
        wvar  = outfile.createVariable(field_out[f],np.float64,('time','lat','lon'),fill_value=np.float64(1.e36))
    
        wtime.units = 'days since ' + str(fut_yrstart) + '-01-01 00:00:00'
        wlon.units  = 'degrees'
        wlat.units  = 'degrees'
        wvar.units = units[f]
        warea.units = 'km2'
        wfrac.units = 'unitless'
        wmask.units = 'unitless'

        #wtime.long_name = 'Months since January '+str(fut_yrstart)
        wtime.long_name = 'days since ' + str(fut_yrstart) + '-01-01 00:00:00'
        wlon.long_name  = 'Longitude'
        wlat.long_name  = 'Latitude'
        wvar.long_name  = str(long_name)+' '+anomsf[f]
        warea.long_name = 'Grid cell area'
        wfrac.long_name = 'Grid cell land fraction'
        wmask.long_name = 'Grid cell land mask'

        wtime.calendar = 'noleap'
	
        # write to file  --------------------------------------------
        #wtime[:]   = month
        wtime[:]   = outtime
        wlon[:]    = lon
        wlat[:]    = lat
        wmask[:,:] = landmask
        wfrac[:,:] = landfrac
        warea[:,:] = area
        wvar[:,:,:] = outputvarvalues



    else:
        fieldskip = 0
    
