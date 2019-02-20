"""
Read athena zprof file using pandas and xarray
"""

from __future__ import print_function

import os
import os.path as osp
import glob
import numpy as np
import pandas as pd
import xarray as xr

def read_zprof_all(dirname, problem_id, phase='whole', force_override=False):
    """Read all zprof files in directory and make a Dataset object and
    write to a NetCDF file.

    Note that DataArray holds a single multi-dimensional variable and
    its coordinates, while a Dataset holds multiple variables that 
    potentially share the same coordinates.

    Parameters
    ----------
    dirname : str
        Name of the directory where zprof files are located
    problem_id : str
        Prefix of zprof files
    phase : str
        Name of thermal phase
        ex) whole, phase1, ..., phase5 (cold, intermediate, warm, hot1, hot2)
    force_override : bool
        Flag to force read of hst file even when pickle exists

    Returns
    -------
       da: xarray dataarray
    """

    # Find all files with "/dirname/problem_id.xxxx.phase.zprof"    
    fname_base = '{0:s}.????.{1:s}.zprof'.format(problem_id, phase)
    fnames = sorted(glob.glob(osp.join(dirname, fname_base)))
    
    fnetcdf = '{0:s}.{1:s}.zprof.nc'.format(problem_id, phase)
    fnetcdf = osp.join(dirname, fnetcdf)

    # Check if netcdf file exists and compare last modified times
    mtime_max = np.array([osp.getmtime(fname) for fname in fnames]).max()
    if not force_override and osp.exists(fnetcdf) and \
        osp.getmtime(fnetcdf) > mtime_max:
        da = xr.open_dataset(fnetcdf)
        return da
    
    # If here, need to create a new dataarray
    time = []
    df_all = []
    for i, fname in enumerate(fnames):
        # Read time
        with open(fname, 'r') as f:
            h = f.readline()
            time.append(float(h[h.rfind('t=') + 2:]))

        # read pickle if exists
        df = read_zprof(fname, force_override=False)
        if i == 0: # save z coordinates
            z = (np.array(df['z'])).astype(float)
        df.drop(columns='z', inplace=True)
        df_all.append(df)

        # For test
        # if i > 10:
        #     break
        
    fields = np.array(df.columns)

    # Combine all data
    # Coordinates: time and z
    time = (np.array(time)).astype(float)
    fields = np.array(df.columns)
    df_all = np.stack(df_all, axis=0)
    data_vars = dict()
    for i, f in enumerate(fields):
        data_vars[f] = (('z', 'time'), df_all[...,i].T)

    ds = xr.Dataset(data_vars, coords=dict(z=z, time=time))
    
    # Somehow overwriting using mode='w' doesn't work..
    if osp.exists(fnetcdf):
        os.remove(fnetcdf)

    try:
        ds.to_netcdf(fnetcdf, mode='w')
    except IOError:
        pass
    
    return ds

def read_zprof(filename, force_override=False, verbose=False):
    """
    Function to read one zprof file and pickle
    
    Parameters
    ----------
    filename : string
        Name of the file to open, including extension
    force_override: bool
        Flag to force read of zprof file even when pickle exists

    Returns
    -------
    df : pandas dataframe
    """

    skiprows = 2

    fpkl = filename + '.p'
    if not force_override and osp.exists(fpkl) and \
       osp.getmtime(fpkl) > osp.getmtime(filename):
        df = pd.read_pickle(fpkl)
        if verbose:
            print('[read_zprof]: reading from existing pickle.')
    else:
        if verbose:
            print('[read_zprof]: pickle does not exist or zprof file updated.' + \
                      ' Reading {0:s}'.format(filename))

        with open(filename, 'r') as f:
            # For the moment, skip the first line which contains information about
            # the time at which the file is written
            # "# Athena vertical profile at t=xxx.xx"
            h = f.readline()
            time = float(h[h.rfind('t=') + 2:])
            h = f.readline()
            vlist = h.split(',')
            if vlist[-1].endswith('\n'):
                vlist[-1] = vlist[-1][:-1]    # strip \n

        # c engine does not support regex separators
        df = pd.read_table(filename, names=vlist, skiprows=skiprows,
                           comment='#', sep=',', engine='python')
        try:
            df.to_pickle(fpkl)
        except IOError:
            pass
        
    return df
