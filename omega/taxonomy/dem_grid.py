"""Terrain layer on the same 0.05 deg grid as pop_usa_005.npz, from Copernicus GLO-90 DEM
(public COGs, s3://copernicus-dem-90m). Per cell: mean elevation (m) and relief = SD of the
nine 1/60-deg sub-cell means (m). Only 1-deg tiles that hold population are read.
Ocean tiles do not exist upstream (404) and are left NaN.
"""
import os, numpy as np, rasterio
from rasterio.enums import Resampling
from concurrent.futures import ThreadPoolExecutor
os.environ.setdefault('CURL_CA_BUNDLE', '/root/.ccr/ca-bundle.crt')
os.environ.setdefault('GDAL_HTTP_USERAGENT', 'omega-research/1.0 (academic UAP data study; non-commercial)')
os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR')
P = np.load('data/processed/taxonomy/pop_usa_005.npz')
g, LAT0, LON0, RES = P['grid'], float(P['lat0']), float(P['lon0']), float(P['res'])
ny, nx = g.shape
elev = np.full((ny, nx), np.nan); relief = np.full((ny, nx), np.nan)
c = int(round(1 / RES))
tiles = set()
for iy, ix in zip(*np.nonzero(g > 0)):
    tiles.add((int(np.floor(LAT0 + iy * RES)), int(np.floor(LON0 + ix * RES))))
def name(la, lo):
    ns = 'N%02d' % la if la >= 0 else 'S%02d' % -la
    ew = 'E%03d' % lo if lo >= 0 else 'W%03d' % -lo
    n = f'Copernicus_DSM_COG_30_{ns}_00_{ew}_00_DEM'
    return f'/vsicurl/https://copernicus-dem-90m.s3.amazonaws.com/{n}/{n}.tif'
def work(t):
    la, lo = t
    try:
        with rasterio.open(name(la, lo)) as ds:
            a = ds.read(1, out_shape=(3 * c, 3 * c), resampling=Resampling.average).astype(float)
    except Exception:
        return t, None
    return t, a
ok = 0
with ThreadPoolExecutor(16) as ex:
    for (la, lo), a in ex.map(work, sorted(tiles)):
        if a is None: continue
        ok += 1
        a = a[::-1]  # north-up -> south-up rows
        b = a.reshape(c, 3, c, 3)
        e = b.mean((1, 3)); r = b.std((1, 3))
        y0 = int(round((la - LAT0) / RES)); x0 = int(round((lo - LON0) / RES))
        if 0 <= y0 and y0 + c <= ny and 0 <= x0 and x0 + c <= nx:
            elev[y0:y0 + c, x0:x0 + c] = e; relief[y0:y0 + c, x0:x0 + c] = r
np.savez_compressed('data/processed/taxonomy/dem_usa_005.npz', elev=elev, relief=relief, lat0=LAT0, lon0=LON0, res=RES)
print('tiles wanted', len(tiles), 'read', ok)
