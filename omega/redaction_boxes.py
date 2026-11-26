#!/usr/bin/env python3
"""Find visual redaction boxes on page images (session 6, HANDOFF §5 item 3).

The OCR text only shows a redaction when the box carries a printed exemption code.
A plain black box with no code leaves no trace in the text. This script renders each
page at low dpi and finds solid, near-black rectangles, which is what a blackout
redaction looks like. It also finds outlined white boxes carrying a code (the 2026
release style) only through the OCR, so the two counts are reported separately.

Usage: redaction_boxes.py OUT.json PDF [PDF ...]
Each PDF is rendered to a temp dir at DPI, scanned, and the images are deleted.
"""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage

DPI = 50
DARK = 60            # gray level counted as black
MIN_W_IN, MIN_H_IN = 0.30, 0.10   # smallest box: about one short word
MAX_H_IN = 3.0       # taller than this is a photo or figure, not a word/line redaction
FILL = 0.92          # share of the bounding box that must be black
EDGE_IN = 0.25       # ignore components touching the scan edge (scanner borders)


def boxes_on_page(png):
    g = np.asarray(Image.open(png).convert("L"))
    H, W = g.shape
    # opening removes text strokes (1-2 px at 50 dpi) that touch a box and
    # would otherwise merge with it and break the fill test
    mask = ndimage.binary_opening(g < DARK, structure=np.ones((3, 3)))
    lab, n = ndimage.label(mask)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is None:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        h, w = y1 - y0, x1 - x0
        if w < MIN_W_IN * DPI or h < MIN_H_IN * DPI or h > MAX_H_IN * DPI:
            continue
        e = EDGE_IN * DPI
        if x0 < e or y0 < e or x1 > W - e or y1 > H - e:
            continue
        fill = (lab[sl] == i).mean()
        if fill < FILL:
            continue
        # a solid box is uniformly dark; a dark photo patch has texture
        if g[sl][lab[sl] == i].std() > 25:
            continue
        out.append({"x": round(x0 / DPI, 2), "y": round(y0 / DPI, 2),
                    "w_in": round(w / DPI, 2), "h_in": round(h / DPI, 2),
                    "fill": round(float(fill), 3)})
    return out


def scan(pdf):
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", str(DPI), "-gray", "-png", pdf,
                        os.path.join(td, "p")], check=True)
        pages = sorted(os.listdir(td), key=lambda s: int(s.split("-")[-1].split(".")[0]))
        res = []
        for k, p in enumerate(pages, 1):
            b = boxes_on_page(os.path.join(td, p))
            if b and os.environ.get("BOX_CROPS"):
                im = Image.open(os.path.join(td, p))
                for m, x in enumerate(b):
                    pad = 0.4
                    box = [max(0, int((x["x"] - pad) * DPI)), max(0, int((x["y"] - pad) * DPI)),
                           int((x["x"] + x["w_in"] + pad) * DPI), int((x["y"] + x["h_in"] + pad) * DPI)]
                    im.crop(box).save(os.path.join(os.environ["BOX_CROPS"],
                                      f"{os.path.basename(pdf)[:12]}_p{k}_{m}.png"))
            if b:
                res.append({"page": k, "boxes": b})
        return len(pages), res


if __name__ == "__main__":
    out = sys.argv[1]
    data = json.load(open(out)) if os.path.exists(out) else {}
    for pdf in sys.argv[2:]:
        n, res = scan(pdf)
        key = os.path.basename(pdf)
        data[key] = {"pages": n, "pages_with_boxes": len(res),
                     "boxes": sum(len(r["boxes"]) for r in res), "detail": res}
        print(f"{key[:60]}: {n} pp, {data[key]['boxes']} boxes on "
              f"{len(res)} pages", flush=True)
        json.dump(data, open(out, "w"), indent=1)
