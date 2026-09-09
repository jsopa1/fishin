import csv, glob, os
from collections import defaultdict

rows = []
for fn in sorted(glob.glob("raw/ndbc_45007_*.txt")):
    year = os.path.basename(fn).split("_")[-1].split(".")[0]
    with open(fn) as f:
        lines = f.readlines()
    # find header
    header = lines[0].lstrip("#").split()
    data_lines = [l for l in lines[2:] if l.strip() and not l.startswith("#")]
    day_data = defaultdict(lambda: defaultdict(list))
    for l in data_lines:
        parts = l.split()
        if len(parts) < len(header):
            continue
        rec = dict(zip(header, parts))
        date = f"{rec['YY']}-{rec['MM']}-{rec['DD']}"
        for field in ["WDIR","WSPD","GST","WVHT","DPD","APD","MWD","PRES","ATMP","WTMP"]:
            val = rec.get(field)
            try:
                fval = float(val)
            except:
                continue
            # missing value sentinels
            if fval in (99.0, 999.0, 9999.0, 99.00, 999.0):
                continue
            day_data[date][field].append(fval)
    for date, fields in day_data.items():
        row = {"date": date}
        for field in ["WDIR","WSPD","GST","WVHT","DPD","APD","MWD","PRES","ATMP","WTMP"]:
            vals = fields.get(field, [])
            row[field+"_mean"] = round(sum(vals)/len(vals), 3) if vals else ""
            row[field+"_max"] = round(max(vals), 3) if vals else ""
        rows.append(row)

rows.sort(key=lambda r: r["date"])
fieldnames = ["date"] + [f"{fld}_{stat}" for fld in ["WDIR","WSPD","GST","WVHT","DPD","APD","MWD","PRES","ATMP","WTMP"] for stat in ["mean","max"]]
with open("lake_michigan_ndbc_45007_daily.csv","w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("rows:", len(rows))
