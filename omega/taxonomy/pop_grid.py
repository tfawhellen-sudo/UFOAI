"""Population null layers from Meta/CIESIN High Resolution Settlement Layer (HRSL, CC-BY 4.0),
public bucket https://dataforgood-fb-data.s3.amazonaws.com .

  usa  : csv/month=2019-06/country=USA/type=total_population/USA_total_population.csv.gz
         (30 m settled-pixel points, ~962 MB gz) binned to a 0.05 deg grid -> people per cell.
  admin: gadm_hrsl_pop/gadm_pop_2022-02-05.tsv (HRSL totals per GADM unit) -> for FR, GB, CA:
         centroid (vertex mean of the largest ring; approximate) + population.

Streams; nothing large is stored. Outputs in data/processed/taxonomy/.
Note: an earlier attempt read the COG overviews; those average only settled pixels, which
inflates sparse cells (~3000x on a western-US tile). Rejected; recorded here.
"""
import os, sys, io, json, subprocess, numpy as np
UA = 'omega-research/1.0 (academic UAP data study; non-commercial)'
B = 'https://dataforgood-fb-data.s3.amazonaws.com/'
OUT = 'data/processed/taxonomy'
os.makedirs(OUT, exist_ok=True)

def stream(key):
    p = subprocess.Popen(['curl', '-s', '-A', UA, B + key], stdout=subprocess.PIPE)
    return p

def usa():
    import pandas as pd
    RES = 0.05; LAT0, LAT1, LON0, LON1 = 15.0, 72.0, -180.0, -60.0
    ny, nx = int((LAT1 - LAT0) / RES), int((LON1 - LON0) / RES)
    g = np.zeros(ny * nx)
    p = stream('csv/month=2019-06/country=USA/type=total_population/USA_total_population.csv.gz')
    gz = subprocess.Popen(['gzip', '-dc'], stdin=p.stdout, stdout=subprocess.PIPE)
    n = 0
    for ch in pd.read_csv(gz.stdout, sep="\t", chunksize=5_000_000):
        cols = list(ch.columns)
        la, lo, po = ch.iloc[:, 0].values, ch.iloc[:, 1].values, ch.iloc[:, 2].values
        if n == 0: print('columns', cols, flush=True)
        iy = ((la - LAT0) / RES).astype(int); ix = ((lo - LON0) / RES).astype(int)
        m = (iy >= 0) & (iy < ny) & (ix >= 0) & (ix < nx) & np.isfinite(po)
        np.add.at(g, iy[m] * nx + ix[m], po[m])
        n += len(ch); print('rows', n, 'pop', round(g.sum()), flush=True)
    np.savez_compressed(f'{OUT}/pop_usa_005.npz', grid=g.reshape(ny, nx), lat0=LAT0, lon0=LON0, res=RES)
    print('USA done, total', g.sum())

def admin():
    p = stream('gadm_hrsl_pop/gadm_pop_2022-02-05.tsv')
    out = []
    hdr = None
    for line in io.TextIOWrapper(p.stdout, encoding='utf-8', errors='replace'):
        if hdr is None:
            hdr = line.rstrip('\n').split('\t'); continue
        f = line.rstrip('\n').split('\t')
        if len(f) < 5 or f[2] not in ('FR', 'GB', 'CA', 'US'): continue
        try:
            gj = json.loads(f[3]); pop = float(f[4])
        except Exception:
            continue
        polys = gj['coordinates'] if gj['type'] == 'MultiPolygon' else [gj['coordinates']]
        ring = max((pp[0] for pp in polys), key=len)
        a = np.array(ring)
        out.append(dict(id=f[0], name=f[1], iso2=f[2], lon=float(a[:, 0].mean()), lat=float(a[:, 1].mean()), pop=pop))
    json.dump(out, open(f'{OUT}/pop_admin.json', 'w'))
    import collections
    print('admin units', collections.Counter(o['iso2'] for o in out), flush=True)

if __name__ == '__main__':
    {'usa': usa, 'admin': admin}[sys.argv[1]]()
