import sys, glob, os
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
files = sorted(glob.glob(here + "/out/*.raw"))
only = sys.argv[2:] 
if only: files = [f for f in files if any(o in f for o in only)]
cols = 7 if len(files) == 14 else 4 if len(files) > 3 else len(files); rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 392, rows * 392), "#202020")
for i, f in enumerate(files):
    im = Image.frombytes("RGBA", (128, 128), open(f, "rb").read()).convert("RGB")
    im.save(f[:-4] + ".png")
    sheet.paste(im.resize((384, 384), Image.NEAREST), ((i % cols) * 392 + 4, (i // cols) * 392 + 4))
sheet.save(sys.argv[1])
