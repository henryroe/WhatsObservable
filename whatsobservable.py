import datetime
import ephem
import os.path
import os
import numpy as np
import pdb
from pandas import DataFrame


__version__ = '0.1.1'


class Error(Exception):
    pass


def _convert_datetime_to_pyephem_date_string(in_datetime):
    return in_datetime.strftime('%Y/%m/%d %H:%M:%S')


def _find_cached_file(filename):
    base = os.path.expanduser('~/')
    # Look in a few likely locations before doing a giant search
    filenames_to_test = [os.path.join(base, filename),
                         os.path.join(base, 'refdata', filename),
                         os.path.join(base, 'Dropbox', filename),
                         os.path.join(base, 'Dropbox', 'refdata', filename)]
    for cur_filename in filenames_to_test:
        if os.path.isfile(cur_filename):
            return cur_filename
    # didn't find it, so do a giant search
    for root, dirs, files in os.walk(base):
        if filename in files:
            return os.path.join(root, filename)
    return "File Not Found"


def get_latlon_from_observatory_code(code):
    if type(code) is int:
        code = '%03i' % code
    elif type(code) is str:
        code = code[:3]  # trim any remainder, like @399
    try:
        obscode_filename = _find_cached_file('ObsCodes.html')
        # TODO: add a verbose option to print path to ObsCodes.html
        obscodes = open(obscode_filename, 'r').read().splitlines()
    except:
        raise Error("Problem reading ObsCodes.html file from disk.  \n"
                    "Most likely you need to go download a copy from:  \n"
                    "    http://www.minorplanetcenter.net/iau/lists/ObsCodes.html")
    curobsline = [a for a in obscodes if a.startswith(code)][0]
    output = {'obscode':curobsline[0:3],
              'longitude':float(curobsline[4:13]),
              'cos':float(curobsline[13:21]),
              'sin':float(curobsline[21:30]),
              'name':curobsline[30:].strip()}
    # From the documentation:
    # "The following list gives the observatory code, longitude (in degrees east of Greenwich) and the parallax
    # constants (rho cos phi' and rho sin phi', where phi' is the geocentric latitude and rho is the geocentric
    # distance in earth radii) for each observatory. It is updated nightly."
    output['latitude'] = np.degrees(np.arctan2(output['sin'], output['cos']))
    # Unsure where the following comment came from:
    # geocentric distance in earth radii:
    #   output['sin']/np.sin(np.radians(output['latitude']))
    # NOTE: while ObsCodes.html is clear about being geocentric, it is unclear what pyephem wants, so blaze ahead
    # TODO: confirm whether pyephem wants geocentric
    return output


def pack_mpc_date(in_datetime):
    """
    Convert a datetime.date or datetime.datetime object into the MPC packed date format, as described at:
        http://www.minorplanetcenter.net/iau/info/PackedDates.html

    Copy of the packing definition from the above web page:
        Packed Dates
        Dates of the form YYYYMMDD may be packed into five characters to conserve space.
        The first two digits of the year are packed into a single character in column 1 (I = 18, J = 19, K = 20). Columns 2-3 contain the last two digits of the year. Column 4 contains the month and column 5 contains the day, coded as detailed below:
           Month     Day      Character         Day      Character
                             in Col 4 or 5              in Col 4 or 5
           Jan.       1           1             17           H
           Feb.       2           2             18           I
           Mar.       3           3             19           J
           Apr.       4           4             20           K
           May        5           5             21           L
           June       6           6             22           M
           July       7           7             23           N
           Aug.       8           8             24           O
           Sept.      9           9             25           P
           Oct.      10           A             26           Q
           Nov.      11           B             27           R
           Dec.      12           C             28           S
                     13           D             29           T
                     14           E             30           U
                     15           F             31           V
                     16           G

        Examples:

           1996 Jan. 1    = J9611
           1996 Jan. 10   = J961A
           1996 Sept.30   = J969U
           1996 Oct. 1    = J96A1
           2001 Oct. 22   = K01AM
        This system can be extended to dates with non-integral days. The decimal fraction of the day is simply appended to the five characters defined above.
        Examples:

           1998 Jan. 18.73     = J981I73
           2001 Oct. 22.138303 = K01AM138303
    """
    if in_datetime.year >= 1800 and in_datetime.year < 1900:
        century = 'I'
    elif in_datetime.year >= 1900 and in_datetime.year < 2000:
        century = 'J'
    elif in_datetime.year >= 2000 and in_datetime.year < 2100:
        century = 'K'
    else:
        raise Error("Year is not within 1800-2099: " + in_datetime.isoformat())
    year = in_datetime.strftime('%y')
    translate = {}
    for i in range(10):
        translate[i] = str(i)
    for i in range(10,32):
        translate[i] = chr(ord('A') + i - 10)
    month = translate[in_datetime.month]
    day = translate[in_datetime.day]
    try:
        decimaldays = ('%7.5f' % ((in_datetime.hour + (in_datetime.minute / 60.) + (in_datetime.second / 3600.)) / 24.))[2:]
    except:
        decimaldays = ''
    return century + year + month + day + decimaldays


def unpack_mpc_date(in_packed):
    """
    Convert a MPC packed date format (as described below) to a datetime.date or datetime.datetime object
        http://www.minorplanetcenter.net/iau/info/PackedDates.html

    Copy of the packing definition from the above web page:
        Packed Dates
        Dates of the form YYYYMMDD may be packed into five characters to conserve space.
        The first two digits of the year are packed into a single character in column 1 (I = 18, J = 19, K = 20). Columns 2-3 contain the last two digits of the year. Column 4 contains the month and column 5 contains the day, coded as detailed below:
           Month     Day      Character         Day      Character
                             in Col 4 or 5              in Col 4 or 5
           Jan.       1           1             17           H
           Feb.       2           2             18           I
           Mar.       3           3             19           J
           Apr.       4           4             20           K
           May        5           5             21           L
           June       6           6             22           M
           July       7           7             23           N
           Aug.       8           8             24           O
           Sept.      9           9             25           P
           Oct.      10           A             26           Q
           Nov.      11           B             27           R
           Dec.      12           C             28           S
                     13           D             29           T
                     14           E             30           U
                     15           F             31           V
                     16           G

        Examples:

           1996 Jan. 1    = J9611
           1996 Jan. 10   = J961A
           1996 Sept.30   = J969U
           1996 Oct. 1    = J96A1
           2001 Oct. 22   = K01AM
        This system can be extended to dates with non-integral days. The decimal fraction of the day is simply appended to the five characters defined above.
        Examples:

           1998 Jan. 18.73     = J981I73
           2001 Oct. 22.138303 = K01AM138303
    """
    translate = {}
    for i in range(10):
        translate[str(i)] = i
    for i in range(10,32):
        translate[chr(ord('A') + i - 10)] = i
    if in_packed[0] == 'I':
        year = 1800
    elif in_packed[0] == 'J':
        year = 1900
    elif in_packed[0] == 'K':
        year = 2000
    else:
        raise Error('Unrecognized century code at start of: ' + in_packed)
    year += int(in_packed[1:3])
    month = translate[in_packed[3]]
    day = translate[in_packed[4]]
    if len(in_packed) == 5:
        return datetime.date(year, month, day)
    else:
        decimaldays = float('0.' + in_packed[5:])
        hour = int(decimaldays * 24.)
        minute = int((decimaldays * 24. - hour) * 60.)
        second = int(round(decimaldays * 24. * 60. * 60. - (hour * 3600.) - (minute * 60.)))
        return datetime.datetime(year, month, day, hour, minute, second)


#TODO: clean up the following comments and incorporate into the code
# can get all numbered asteroids (and other junk) from minor planet center in MPCORB.DAT file:
# [MPCORB.DAT](http://www.minorplanetcenter.net/iau/MPCORB/MPCORB.DAT)
# [Format is described in more detail](http://www.minorplanetcenter.org/iau/info/MPOrbitFormat.html)
# 944 Hidalgo line as of 2013-07-26 is:
#Des'n     H     G   Epoch     M        Peri.      Node       Incl.       e            n           a        Reference #Obs #Opp    Arc    rms  Perts   Computer
#00944   10.77  0.15 K134I 215.40344   56.65077   21.56494   42.54312  0.6617811  0.07172582   5.7370114  0 MPO263352   582  21 1920-2010 0.77 M-v 38h MPCLINUX   0000    (944) Hidalgo            20100222

# But, I want in xephem format, [described here](http://www.clearskyinstitute.com/xephem/help/xephem.html#mozTocId468501)
# and minor planet provides a subset in xephem format [here](http://www.minorplanetcenter.net/iau/Ephemerides/Bright/2013/Soft03Bright.txt):
# though to ensure I was comparing same exact orbit solutions, used 944 Hidalgo from
#     http://www.minorplanetcenter.net/iau/Ephemerides/Distant/Soft03Distant.txt
# From MPO263352
#944 Hidalgo,e,42.5431,21.5649,56.6508,5.737011,0.0717258,0.66178105,215.4034,04/18.0/2013,2000,H10.77,0.15
# So, for my purposes, the xephem format, separated by commas is:
#   NUMBER NAME  - easy enough....
#   e - for ecliptic elliptical orbit
#   i = inclination, degrees                           (directly from MPCORB.DAT)
#   O = longitude of ascending node, degrees           (directly from MPCORB.DAT)
#   o = argument of perihelion, degrees                (directly from MPCORB.DAT)
#   a = mean distance (aka semi-major axis), AU        (directly from MPCORB.DAT)
#   n = mean daily motion, degrees per day (computed from a**3/2 if omitted)          (directly from MPCORB.DAT)
#   e = eccentricity, must be < 1                      (directly from MPCORB.DAT)
#   M = mean anomaly, i.e., degrees from perihelion    (directly from MPCORB.DAT)
#   E = epoch date, i.e., time of M                    MM/DD.D/YYYY
#                                    in MPCORB.DAT epoch date is packed according to rules:
#                                    http://www.minorplanetcenter.net/iau/info/PackedDates.html
#   Subfield 10A    First date these elements are valid, optional
#   SubField 10B	Last date these elements are valid, optional
#   D = the equinox year, i.e., time of i, O and o  (always J2000.0 in MPCORB.DAT, so 2000
#   First component of magnitude model, either g from (g,k) or H from (H,G). Specify which by preceding the number with a "g" or an "H". In absence of either specifier the default is (H,G) model. See Magnitude models.
#         corresponds to H in MPCORB.DAT, just need to preface with an 'H'
#    Second component of magnitude model, either k or G  (directly from MPCORB.DAT)
#    s = angular size at 1 AU, arc seconds, optional - I don't care, so skip....

def convert_mpcorb_to_xephem(input):
    """
    convert from, e.g.:
    [MPCORB.DAT](http://www.minorplanetcenter.net/iau/MPCORB/MPCORB.DAT)
    [Format is described in more detail](http://www.minorplanetcenter.org/iau/info/MPOrbitFormat.html)
    Des'n     H     G   Epoch     M        Peri.      Node       Incl.       e            n           a        Reference #Obs #Opp    Arc    rms  Perts   Computer
    # 944 Hidalgo line as of 2013-07-26 is:
    00944   10.77  0.15 K134I 215.40344   56.65077   21.56494   42.54312  0.6617811  0.07172582   5.7370114  0 MPO263352   582  21 1920-2010 0.77 M-v 38h MPCLINUX   0000    (944) Hidalgo            20100222

    to
    # From MPO263352
    944 Hidalgo,e,42.5431,21.5649,56.6508,5.737011,0.0717258,0.66178105,215.4034,04/18.0/2013,2000,H10.77,0.15

    input is a single line of text, output will include a newline character within it (but no newline at end)
    """
    output = '# From ' + input[107:116] + '\n'
    output += input[166:194].strip().replace('(','').replace(')','') + ','
    output += 'e,'
    output += input[59:68].strip() + ','    # i = inclination, degrees
    output += input[48:57].strip() + ','    # O = longitude of ascending node, degrees
    output += input[37:46].strip() + ','    # o = argument of perihelion, degrees
    output += input[92:103].strip() + ','   # a = mean distance (aka semi-major axis), AU
    output += input[80:91].strip() + ','    # n = mean daily motion, degrees per day (computed from a**3/2 if omitted)
    output += input[70:79].strip() + ','    # e = eccentricity, must be < 1
    output += input[26:35].strip() + ','    # M = mean anomaly, i.e., degrees from perihelion
    output += unpack_mpc_date(input[20:25].strip()).strftime('%m/%d/%Y') + ','    # E = epoch date, i.e., time of M
    output += '2000,'   # D = the equinox year, i.e., time of i, O and o  (always J2000.0 in MPCORB.DAT
    output += 'H' + input[8:13].strip() + ','   # First component of magnitude model
    output += input[14:19].strip()   # Second component of magnitude model
    return output


def minorplanets(in_datetime, observatory_code,
                 max_objects=None,
                 max_magnitude=None, require_magnitude=True,
                 max_zenithdistance_deg=90.0,
                 min_heliocentric_distance_AU=None, max_heliocentric_distance_AU=None,
                 min_topocentric_distance_AU=None, max_topocentric_distance_AU=None):
    """
    in_datetime - datetime.datetime(), e.g. datetime.datetime.utcnow()
    observatory_code - the Code of the observatory in
                       http://www.minorplanetcenter.net/iau/lists/ObsCodes.html
                       can be either string or integer.
    max_objects - default is None, otherwise limits the return to this number
                  of observable objects
    max_magnitude - default is None, otherwise limits return to objects
                    brighter than or equal to this magnitude
                    (as calculated by PyEphem from the MPC data)
                    (TODO: confirm whether this is V-band, R-band,
                    or other...)
    require_magnitude - default is True.  If False and max_magnitude is None,
                        then return all objects, whether PyEphem can calculate
                        a magnitude or not.
    max_zenithdistance_deg - default is 90 degrees (horizon)
    min/max_heliocentric_distance_AU - defaults are None
    min/max_topocentric_distance_AU - defaults are None
    """
    obs_info = get_latlon_from_observatory_code(observatory_code)
    obs = ephem.Observer()
    obs.lat = np.radians(obs_info['latitude'])
    obs.lon = np.radians(obs_info['longitude'])
    obs.date = _convert_datetime_to_pyephem_date_string(in_datetime)
    mpc_filename = _find_cached_file('MPCORB.DAT')
    if mpc_filename == 'File Not Found':
        raise Error("Problem reading MPCORB.DAT file from disk.  \n"
                    "Most likely you need to go download a copy from:  \n"
                    "    http://www.minorplanetcenter.net/iau/MPCORB/MPCORB.DAT")
    if max_magnitude is not None:
        require_magnitude = True
    matching_objects = []
    with open(mpc_filename) as f:
        in_header = True
        for line in f:
            if in_header is False and len(line) > 1:
                if (not require_magnitude) or (require_magnitude and (line[8:13] != '     ')):
                    eph = ephem.readdb(convert_mpcorb_to_xephem(line).splitlines()[1])
                    eph.compute(obs)
                    if (max_magnitude is None) or (eph.mag <= max_magnitude):
                        if ((max_zenithdistance_deg is None) or
                            (np.degrees(np.pi/2. - eph.alt) <= max_zenithdistance_deg)):
                            if ((min_heliocentric_distance_AU is None) or
                                (eph.sun_distance >= min_heliocentric_distance_AU)):
                                if ((max_heliocentric_distance_AU is None) or
                                    (eph.sun_distance <= max_heliocentric_distance_AU)):
                                    if ((min_topocentric_distance_AU is None) or
                                        (eph.earth_distance >= min_topocentric_distance_AU)):
                                        if ((max_topocentric_distance_AU is None) or
                                            (eph.earth_distance <= max_topocentric_distance_AU)):
                                            matching_objects.append(eph)
            else:
                if line.startswith('-------------------'):
                    in_header = False
            if max_objects is not None:
                if len(matching_objects) >= max_objects:
                    break
    name = [a.name for a in matching_objects]
    d = {}
    d['rise_time'] = [a.rise_time.datetime() if a.rise_time is not None else np.nan for a in matching_objects]
    d['transit_time'] = [a.transit_time.datetime() if a.transit_time is not None else np.nan for a in matching_objects]
    d['set_time'] = [a.set_time.datetime() if a.set_time is not None else np.nan for a in matching_objects]
    d['raJ2000_deg'] = [np.degrees(a.a_ra) for a in matching_objects]
    d['decJ2000_deg'] = [np.degrees(a.a_dec) for a in matching_objects]
    d['mag'] = [a.mag for a in matching_objects]
    d['R_AU'] = [a.sun_distance for a in matching_objects]
    d['delta_AU'] = [a.earth_distance for a in matching_objects]
    moon = ephem.Moon()
    moon.compute(obs.date)
    d['O-E-M_deg'] = [np.degrees(ephem.separation(moon, a)) for a in matching_objects]
    output = DataFrame(d, index=name)
    output = output[['rise_time', 'transit_time', 'set_time', 'raJ2000_deg', 'decJ2000_deg',
                     'mag', 'R_AU', 'delta_AU', 'O-E-M_deg']] # re-order columns to something sensible
    return output

