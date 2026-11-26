"""Site layers for the geography test. All from public files, downloaded with the honest UA
into data/raw/taxo_geo/ (SHA-1s recorded in the report):

  airports.csv          OurAirports (public domain)
      https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv
  nuclear_power_plants.csv  GeoNuclearData (WNA/IAEA PRIS-derived)
      https://raw.githubusercontent.com/cristianst85/GeoNuclearData/master/data/csv/denormalized/nuclear_power_plants.csv
  ne_10m_coastline.geojson  Natural Earth 10m coastline (public domain)
      https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_coastline.geojson
  These are moving 'main/master' files: the SHA-1s of the copies used are in
  evidence_vault/12_CRAFT_TAXONOMY/FETCH_MANIFEST.md.

Military airfields are a NAME-BASED PROXY over OurAirports (AFB, Army Air Field, NAS, MCAS,
Air Base, RAF, Base Aerienne...). It catches flying bases, not missile fields, depots, test
ranges or labs. That is an inferred layer and is labelled so.
"""
import csv, json, re, os, numpy as np
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
G = os.path.join(ROOT, 'data', 'raw', 'taxo_geo')
MIL = re.compile(r"\b(AFB|Air Force Base|Air Base|Naval Air Station|NAS|Army Air ?field|AAF|Marine Corps Air Station|"
                 r"MCAS|Air National Guard|ANGB|Air Reserve Base|ARB|Naval Air Facility|NAF|Joint Base|Naval Outlying|"
                 r"RAF|Base A[ée]rienne|BA \d+|Military|Air Station)\b", re.I)
R_EARTH = 6371.0


def xyz(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


class Nearest:
    def __init__(self, lat, lon):
        self.t = cKDTree(xyz(np.asarray(lat, float), np.asarray(lon, float)))
        self.n = len(lat)

    def km(self, lat, lon):
        d, _ = self.t.query(xyz(np.asarray(lat, float), np.asarray(lon, float)))
        return 2 * R_EARTH * np.arcsin(np.clip(d / 2, 0, 1))


def airports():
    civ, mil = [], []
    for r in csv.DictReader(open(os.path.join(G, 'airports.csv'), encoding='utf-8')):
        if r['type'] in ('closed', 'heliport', 'seaplane_base', 'balloonport'):
            continue
        if re.search(r'heli|seaplane', r['name'], re.I):
            continue
        p = (float(r['latitude_deg']), float(r['longitude_deg']), r['iso_country'], r['name'])
        if MIL.search(r['name']):
            mil.append(p)
        elif r['type'] in ('large_airport', 'medium_airport'):
            civ.append(p)
    return civ, mil


def nuclear(year_max=None):
    """Plants that had started operating by year_max (any later status). None = all with a start date."""
    out = []
    for r in csv.DictReader(open(os.path.join(G, 'nuclear_power_plants.csv'), encoding='utf-8')):
        if not r['Latitude'] or not r['OperationalFrom']:
            continue
        y0 = int(r['OperationalFrom'][:4])
        y1 = int(r['OperationalTo'][:4]) if r['OperationalTo'] else 9999
        if year_max is not None and y0 > year_max:
            continue
        out.append((float(r['Latitude']), float(r['Longitude']), r['CountryCode'], r['Name'], y0, y1))
    return out


def coast_points(step=1):
    gj = json.load(open(os.path.join(G, 'ne_10m_coastline.geojson'), encoding='utf-8'))
    pts = []
    for f in gj['features']:
        g = f['geometry']
        lines = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
        for ln in lines:
            pts.extend(ln[::step])
    a = np.array(pts)
    return a[:, 1], a[:, 0]


def layers():
    civ, mil = airports()
    nuc = nuclear()
    cla, clo = coast_points()
    return {
        'airport_civil': Nearest([p[0] for p in civ], [p[1] for p in civ]),
        'military_airfield': Nearest([p[0] for p in mil], [p[1] for p in mil]),
        'nuclear_plant': Nearest([p[0] for p in nuc], [p[1] for p in nuc]),
        'coast': Nearest(cla, clo),
    }, dict(airport_civil=len(civ), military_airfield=len(mil), nuclear_plant=len(nuc), coast=len(cla))
