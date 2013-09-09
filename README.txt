
===============
WhatsObservable
===============

WhatsObservable is used for determining which minor planets (and comets) 
are observable at a given time from a given location on Earth.  

WhatsObservable determines the locations of objects using the routines
of [PyEphem](http://rhodesmill.org/pyephem/) and the
[Minor Planet Center's Orbit Database](http://www.minorplanetcenter.net/iau/MPCORB/MPCORB.DAT).
*Note that at least for the time being the user must download this file 
separately and WhatsObservable will find it on disk.*

The intent is to replicate the functionality available at the [JPL Solar System
Dynamics Small Body Whats Observable web page](http://ssd.jpl.nasa.gov/sbwobs.cgi).
The motivation for writing WhatsObservable was to provide this capability when
offline and in an easily scriptable manner.  

NOTE: The precision of PyEphem with the MPC Orbit Database is good, especially for
dates near the orbital epoch, but is not nearly as good as what is available 
directly from the [JPL Horizons System](http://ssd.jpl.nasa.gov/?horizons).  Even
near the orbital epoch errors of a few arcseconds are not uncommon.  Use this
tool at your own risk and if precision matters, refer back directly to the
[JPL Horizons System](http://ssd.jpl.nasa.gov/?horizons).

A typical usage is:

    import datetime
    from whatsobservable import minorplanets

    objects = minorplanets(datetime.datetime(2013, 9, 1, 10, 0), 
                           568,   # 568 is the observatory code for Mauna Kea
                           max_objects=5, max_magnitude=12., max_zenithdistance_deg=60.0)
    print objects

Note that the return is a pandas.DataFrame

===============

Originally written 2013-09-07 by Henry Roe (hroe@hroe.me)
