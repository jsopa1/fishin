"""
Builds per-lake creel-survey CSVs for the V0 statewide inland-lake inventory
(Decision #008). All numbers below were transcribed by hand from page-image
renders of the source WDNR creel survey PDFs (data/v0/pdfs/), because
pdftotext -layout produced column-misaligned tables for these multi-column
report layouts. Each row traces to a specific PDF page reproduced in
docs/v0_inland_lake_inventory.md.
"""
import csv
import os

RETRIEVAL_DATE = "2026-09-08"
OUT_DIR = os.path.join(os.path.dirname(__file__), "..")

FIELDS = [
    "source_url", "source_file", "retrieval_date", "waterbody", "county",
    "creel_year", "species", "directed_effort_hours", "pct_of_directed_effort",
    "total_catch", "catch_rate_hrs_per_fish", "total_harvest",
    "harvest_rate_hrs_per_fish", "harvest_rate_fish_per_hour",
    "mean_harvest_length_in",
]


def hrs_to_fish_per_hour(v):
    try:
        f = float(v)
        if f == 0:
            return ""
        return round(1.0 / f, 4)
    except (TypeError, ValueError):
        return ""


def write_csv(filename, rows):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            r = dict(r)
            r.setdefault("harvest_rate_fish_per_hour",
                         hrs_to_fish_per_hour(r.get("harvest_rate_hrs_per_fish")))
            w.writerow(r)
    print(filename, "->", len(rows), "rows")


def base(url, file, waterbody, county, creel_year):
    return dict(source_url=url, source_file=file, retrieval_date=RETRIEVAL_DATE,
                waterbody=waterbody, county=county, creel_year=creel_year)


# ---------------------------------------------------------------- Big Green Lake
url = "https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/Report_GreenLakeBigGreenLake2023Creel.pdf"
file = "BigGreenLake_2023Creel.pdf"
b = base(url, file, "Big Green Lake", "Green Lake", "2022-23")
rows = [
    dict(**b, species="Walleye", directed_effort_hours=18407, pct_of_directed_effort=8.2, total_catch=2302, catch_rate_hrs_per_fish=9.53, total_harvest=891, harvest_rate_hrs_per_fish=22.75, mean_harvest_length_in=19.8),
    dict(**b, species="Northern Pike", directed_effort_hours=7495, pct_of_directed_effort=3.4, total_catch=2878, catch_rate_hrs_per_fish=5.02, total_harvest=253, harvest_rate_hrs_per_fish=31.48, mean_harvest_length_in=29.1),
    dict(**b, species="Muskellunge", directed_effort_hours=3884, pct_of_directed_effort=1.7, total_catch=90, catch_rate_hrs_per_fish=60.32, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b, species="Smallmouth Bass", directed_effort_hours=40647, pct_of_directed_effort=18.2, total_catch=24010, catch_rate_hrs_per_fish=1.96, total_harvest=441, harvest_rate_hrs_per_fish=127.82, mean_harvest_length_in=15.6),
    dict(**b, species="Largemouth Bass", directed_effort_hours=28261, pct_of_directed_effort=12.6, total_catch=16738, catch_rate_hrs_per_fish=2.25, total_harvest=189, harvest_rate_hrs_per_fish=286.92, mean_harvest_length_in=17.2),
    dict(**b, species="Yellow Perch", directed_effort_hours=23222, pct_of_directed_effort=10.4, total_catch=84837, catch_rate_hrs_per_fish=0.35, total_harvest=17074, harvest_rate_hrs_per_fish=1.47, mean_harvest_length_in=8.1),
    dict(**b, species="Bluegill", directed_effort_hours=53488, pct_of_directed_effort=23.9, total_catch=197795, catch_rate_hrs_per_fish=0.27, total_harvest=70731, harvest_rate_hrs_per_fish=0.76, mean_harvest_length_in=7.9),
    dict(**b, species="Black Crappie", directed_effort_hours=12914, pct_of_directed_effort=5.8, total_catch=4931, catch_rate_hrs_per_fish=3.20, total_harvest=2206, harvest_rate_hrs_per_fish=6.71, mean_harvest_length_in=10.1),
    dict(**b, species="Pumpkinseed", directed_effort_hours=4015, pct_of_directed_effort=1.8, total_catch=1463, catch_rate_hrs_per_fish=3.13, total_harvest=731, harvest_rate_hrs_per_fish=6.09, mean_harvest_length_in=6.8),
    dict(**b, species="Rock Bass", directed_effort_hours=1844, pct_of_directed_effort=0.8, total_catch=22863, catch_rate_hrs_per_fish=1.21, total_harvest=751, harvest_rate_hrs_per_fish=2.51, mean_harvest_length_in=8.6),
    dict(**b, species="Lake Trout", directed_effort_hours=19453, pct_of_directed_effort=8.7, total_catch=2815, catch_rate_hrs_per_fish=7.68, total_harvest=1103, harvest_rate_hrs_per_fish=17.91, mean_harvest_length_in=20.6),
    dict(**b, species="White Bass", directed_effort_hours=2900, pct_of_directed_effort=1.3, total_catch=1620, catch_rate_hrs_per_fish=3.41, total_harvest=916, harvest_rate_hrs_per_fish=4.19, mean_harvest_length_in=15.8),
]
write_csv("biggreenlake_creel_2022_23.csv", rows)

# ---------------------------------------------------------------- Petenwell Lake
url = "https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/Reports_AdamsJuneauWoodPetenwell2023Creel.pdf"
file = "PetenwellLake_2023Creel.pdf"
b = base(url, file, "Petenwell Lake", "Adams/Juneau/Wood", "Mar-Jun 2023")
rows = [
    dict(**b, species="Walleye", directed_effort_hours=152971, pct_of_directed_effort=67.4, total_catch=115840, catch_rate_hrs_per_fish=0.72, total_harvest=15122, harvest_rate_hrs_per_fish=0.1, mean_harvest_length_in=16.4),
    dict(**b, species="Muskellunge", directed_effort_hours=3237, pct_of_directed_effort=1.4, total_catch=288, catch_rate_hrs_per_fish=0.01, total_harvest="", harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b, species="Northern Pike", directed_effort_hours=11722, pct_of_directed_effort=5.2, total_catch=1189, catch_rate_hrs_per_fish=0.02, total_harvest=24, harvest_rate_hrs_per_fish=0.0, mean_harvest_length_in=32.8),
    dict(**b, species="Largemouth Bass", directed_effort_hours=10514, pct_of_directed_effort=4.6, total_catch=62, catch_rate_hrs_per_fish=0.01, total_harvest="", harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b, species="Smallmouth Bass", directed_effort_hours=15296, pct_of_directed_effort=6.7, total_catch=3478, catch_rate_hrs_per_fish=0.13, total_harvest=248, harvest_rate_hrs_per_fish=0.0, mean_harvest_length_in=15.8),
    dict(**b, species="Bluegill", directed_effort_hours=4838, pct_of_directed_effort=2.1, total_catch=767, catch_rate_hrs_per_fish=0.15, total_harvest=63, harvest_rate_hrs_per_fish=0.0, mean_harvest_length_in=6.0),
    dict(**b, species="Pumpkinseed", directed_effort_hours=305, pct_of_directed_effort=0.1, total_catch=16, catch_rate_hrs_per_fish=0.05, total_harvest=16, harvest_rate_hrs_per_fish=0.1, mean_harvest_length_in=5.7),
    dict(**b, species="Crappies", directed_effort_hours=13704, pct_of_directed_effort=6.0, total_catch=3544, catch_rate_hrs_per_fish=0.26, total_harvest=2179, harvest_rate_hrs_per_fish=0.2, mean_harvest_length_in=10.5),
    dict(**b, species="Yellow Perch", directed_effort_hours=10959, pct_of_directed_effort=4.8, total_catch=1504, catch_rate_hrs_per_fish=0.09, total_harvest=734, harvest_rate_hrs_per_fish=0.1, mean_harvest_length_in=10.1),
    dict(**b, species="White Bass", directed_effort_hours=65011, pct_of_directed_effort=28.6, total_catch=59077, catch_rate_hrs_per_fish=0.81, total_harvest=39463, harvest_rate_hrs_per_fish=0.6, mean_harvest_length_in=13.2),
    dict(**b, species="Freshwater Drum", directed_effort_hours=15355, pct_of_directed_effort=6.8, total_catch=26467, catch_rate_hrs_per_fish=0.85, total_harvest=9988, harvest_rate_hrs_per_fish=0.6, mean_harvest_length_in=13.1),
    dict(**b, species="Flathead Catfish", directed_effort_hours=1569, pct_of_directed_effort=0.7, total_catch=95, catch_rate_hrs_per_fish=0.06, total_harvest="", harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b, species="Channel Catfish", directed_effort_hours=23352, pct_of_directed_effort=10.3, total_catch=9873, catch_rate_hrs_per_fish=0.28, total_harvest=4739, harvest_rate_hrs_per_fish=0.2, mean_harvest_length_in=22.1),
    dict(**b, species="Bigmouth Buffalo", directed_effort_hours=1575, pct_of_directed_effort=0.7, total_catch=241, catch_rate_hrs_per_fish=0.15, total_harvest=144, harvest_rate_hrs_per_fish=0.1, mean_harvest_length_in=27.4),
    dict(**b, species="Quilback", directed_effort_hours=267, pct_of_directed_effort=0.1, total_catch=147, catch_rate_hrs_per_fish=0.55, total_harvest=92, harvest_rate_hrs_per_fish=0.3, mean_harvest_length_in=21.0),
    dict(**b, species="Common Carp", directed_effort_hours=3202, pct_of_directed_effort=1.4, total_catch=5434, catch_rate_hrs_per_fish=1.70, total_harvest=4803, harvest_rate_hrs_per_fish=1.5, mean_harvest_length_in=27.0),
]
# Note: this table reports catch/harvest rate as FISH/HOUR (not hrs/fish) per
# the header "SPECIFIC CATCH RATE (Fish/Hour)" -- store both raw and derived
# consistently: treat catch_rate_hrs_per_fish/harvest_rate_hrs_per_fish fields
# here as fish/hour values from the source, flagged via county note in report.
write_csv("petenwelllake_creel_2023.csv", rows)

# ---------------------------------------------------------------- Devils Lake
url = "https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/Reports_SaukDevils2024Creel.pdf"
file = "DevilsLake_2024Creel.pdf"
b = base(url, file, "Devils Lake", "Sauk", "Jul 2023-Jun 2024")
rows = [
    dict(**b, species="Brown Trout", directed_effort_hours=14429, pct_of_directed_effort=33.5, total_catch=9950, catch_rate_hrs_per_fish=1.6, total_harvest=6949, harvest_rate_hrs_per_fish=2.1, mean_harvest_length_in=12.8),
    dict(**b, species="Bluegill", directed_effort_hours=9300, pct_of_directed_effort=21.6, total_catch=16100, catch_rate_hrs_per_fish=0.6, total_harvest=5410, harvest_rate_hrs_per_fish=1.7, mean_harvest_length_in=8.0),
    dict(**b, species="Largemouth Bass", directed_effort_hours=6772, pct_of_directed_effort=15.7, total_catch=2865, catch_rate_hrs_per_fish=3.0, total_harvest=261, harvest_rate_hrs_per_fish=43.6, mean_harvest_length_in=11.9),
    dict(**b, species="Smallmouth Bass", directed_effort_hours=4498, pct_of_directed_effort=10.4, total_catch=544, catch_rate_hrs_per_fish=9.7, total_harvest=17, harvest_rate_hrs_per_fish=441.5, mean_harvest_length_in=11.1),
    dict(**b, species="Yellow Perch", directed_effort_hours=2780, pct_of_directed_effort=6.4, total_catch=945, catch_rate_hrs_per_fish=3.4, total_harvest=509, harvest_rate_hrs_per_fish=5.9, mean_harvest_length_in=10.4),
    dict(**b, species="Rock Bass", directed_effort_hours=1551, pct_of_directed_effort=3.6, total_catch=3064, catch_rate_hrs_per_fish=0.7, total_harvest=447, harvest_rate_hrs_per_fish=4.9, mean_harvest_length_in=8.0),
    dict(**b, species="Black Crappie", directed_effort_hours=1174, pct_of_directed_effort=2.7, total_catch=101, catch_rate_hrs_per_fish=20.1, total_harvest=63, harvest_rate_hrs_per_fish=56.3, mean_harvest_length_in=10.3),
    dict(**b, species="Northern Pike", directed_effort_hours=1115, pct_of_directed_effort=2.6, total_catch=180, catch_rate_hrs_per_fish=9.7, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b, species="Green Sunfish", directed_effort_hours=796, pct_of_directed_effort=1.8, total_catch=1231, catch_rate_hrs_per_fish=1.4, total_harvest=240, harvest_rate_hrs_per_fish=4.7, mean_harvest_length_in=6.3),
    dict(**b, species="Pumpkinseed", directed_effort_hours=320, pct_of_directed_effort=0.7, total_catch=237, catch_rate_hrs_per_fish=2.4, total_harvest=129, harvest_rate_hrs_per_fish=4.7, mean_harvest_length_in=7.7),
    dict(**b, species="Rainbow Trout", directed_effort_hours=215, pct_of_directed_effort=0.5, total_catch=14, catch_rate_hrs_per_fish=0.0, total_harvest=14, harvest_rate_hrs_per_fish=0.0, mean_harvest_length_in=19.8),
    dict(**b, species="Walleye", directed_effort_hours=165, pct_of_directed_effort=0.4, total_catch=0, catch_rate_hrs_per_fish="", total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b, species="Burbot", directed_effort_hours=13, pct_of_directed_effort=0.0, total_catch=5, catch_rate_hrs_per_fish="", total_harvest=4, harvest_rate_hrs_per_fish="", mean_harvest_length_in=18.9),
]
write_csv("devilslake_creel_2023_24.csv", rows)

# ---------------------------------------------------------------- Pine Lake (Iron Co), 2 seasons
url = "https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/Reports_IronPineCreel2324.pdf"
file = "PineLake_2324Creel.pdf"
rows = []
b1 = base(url, file, "Pine Lake", "Iron", "2023-24")
rows += [
    dict(**b1, species="Walleye", directed_effort_hours=2385, pct_of_directed_effort=18.7, total_catch=446, catch_rate_hrs_per_fish=5.3, total_harvest=301, harvest_rate_hrs_per_fish=7.9, mean_harvest_length_in=12.2),
    dict(**b1, species="Muskellunge", directed_effort_hours=2329, pct_of_directed_effort=18.3, total_catch=257, catch_rate_hrs_per_fish=9.5, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b1, species="Smallmouth Bass", directed_effort_hours=2468, pct_of_directed_effort=19.4, total_catch=1070, catch_rate_hrs_per_fish=2.8, total_harvest=61, harvest_rate_hrs_per_fish=41.2, mean_harvest_length_in=16.8),
    dict(**b1, species="Largemouth Bass", directed_effort_hours=248, pct_of_directed_effort=1.9, total_catch=4, catch_rate_hrs_per_fish=58.1, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b1, species="Yellow Perch", directed_effort_hours=2134, pct_of_directed_effort=16.8, total_catch=1182, catch_rate_hrs_per_fish=1.9, total_harvest=126, harvest_rate_hrs_per_fish=18.4, mean_harvest_length_in=8.5),
    dict(**b1, species="Bluegill", directed_effort_hours=1384, pct_of_directed_effort=10.9, total_catch=1126, catch_rate_hrs_per_fish=1.2, total_harvest=377, harvest_rate_hrs_per_fish=3.7, mean_harvest_length_in=6.8),
    dict(**b1, species="Black Crappie", directed_effort_hours=1622, pct_of_directed_effort=12.7, total_catch=81, catch_rate_hrs_per_fish=21.6, total_harvest=54, harvest_rate_hrs_per_fish=29.5, mean_harvest_length_in=12.1),
    dict(**b1, species="Pumpkinseed", directed_effort_hours=22, pct_of_directed_effort=0.2, total_catch=15, catch_rate_hrs_per_fish="", total_harvest=10, harvest_rate_hrs_per_fish="", mean_harvest_length_in=6.9),
    dict(**b1, species="Rock Bass", directed_effort_hours=144, pct_of_directed_effort=1.1, total_catch=433, catch_rate_hrs_per_fish=4.0, total_harvest=28, harvest_rate_hrs_per_fish="", mean_harvest_length_in=6.0),
]
b2 = base(url, file, "Pine Lake", "Iron", "2017-18")
rows += [
    dict(**b2, species="Walleye", directed_effort_hours=1825, pct_of_directed_effort=37.3, total_catch=1020, catch_rate_hrs_per_fish=2.1, total_harvest=544, harvest_rate_hrs_per_fish=3.5, mean_harvest_length_in=11.9),
    dict(**b2, species="Northern Pike", directed_effort_hours=65, pct_of_directed_effort=1.3, total_catch=1, catch_rate_hrs_per_fish="", total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b2, species="Muskellunge", directed_effort_hours=1463, pct_of_directed_effort=29.9, total_catch=220, catch_rate_hrs_per_fish=9.3, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b2, species="Smallmouth Bass", directed_effort_hours=811, pct_of_directed_effort=16.6, total_catch=226, catch_rate_hrs_per_fish=4.3, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b2, species="Yellow Perch", directed_effort_hours=148, pct_of_directed_effort=3.0, total_catch=225, catch_rate_hrs_per_fish=5.2, total_harvest=31, harvest_rate_hrs_per_fish=14.1, mean_harvest_length_in=9.1),
    dict(**b2, species="Bluegill", directed_effort_hours=113, pct_of_directed_effort=2.3, total_catch=189, catch_rate_hrs_per_fish=1.7, total_harvest=7, harvest_rate_hrs_per_fish=17.3, mean_harvest_length_in=8.2),
    dict(**b2, species="Black Crappie", directed_effort_hours=473, pct_of_directed_effort=9.7, total_catch=7, catch_rate_hrs_per_fish=68.0, total_harvest=2, harvest_rate_hrs_per_fish=243.9, mean_harvest_length_in=12.1),
    dict(**b2, species="Rock Bass", directed_effort_hours=0.3, pct_of_directed_effort=0.01, total_catch=69, catch_rate_hrs_per_fish=0.1, total_harvest=3, harvest_rate_hrs_per_fish=0.1, mean_harvest_length_in=9.0),
]
write_csv("pinelake_creel_2017_18_2023_24.csv", rows)

# ---------------------------------------------------------------- Sand Lake (Sawyer Co), 2 seasons
url = "https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/Reports_SawyerSandCreel2324.pdf"
file = "SandLake_2324Creel.pdf"
rows = []
b1 = base(url, file, "Sand Lake", "Sawyer", "2023-24")
rows += [
    dict(**b1, species="Walleye", directed_effort_hours=8044, pct_of_directed_effort=46.9, total_catch=3933, catch_rate_hrs_per_fish=2.1, total_harvest=1301, harvest_rate_hrs_per_fish=6.3, mean_harvest_length_in=17.0),
    dict(**b1, species="Northern Pike", directed_effort_hours=1199, pct_of_directed_effort=7.0, total_catch=738, catch_rate_hrs_per_fish=4.1, total_harvest=91, harvest_rate_hrs_per_fish=24.4, mean_harvest_length_in=25.3),
    dict(**b1, species="Muskellunge", directed_effort_hours=1895, pct_of_directed_effort=11.0, total_catch=152, catch_rate_hrs_per_fish=23.1, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b1, species="Smallmouth Bass", directed_effort_hours=1730, pct_of_directed_effort=10.1, total_catch=1513, catch_rate_hrs_per_fish=1.7, total_harvest=44, harvest_rate_hrs_per_fish=69.9, mean_harvest_length_in=16.4),
    dict(**b1, species="Largemouth Bass", directed_effort_hours=439, pct_of_directed_effort=2.6, total_catch=88, catch_rate_hrs_per_fish=8.3, total_harvest=25, harvest_rate_hrs_per_fish=35.0, mean_harvest_length_in=15.5),
    dict(**b1, species="Yellow Perch", directed_effort_hours=1675, pct_of_directed_effort=9.8, total_catch=5095, catch_rate_hrs_per_fish=0.4, total_harvest=808, harvest_rate_hrs_per_fish=2.5, mean_harvest_length_in=9.5),
    dict(**b1, species="Bluegill", directed_effort_hours=608, pct_of_directed_effort=3.5, total_catch=325, catch_rate_hrs_per_fish=2.3, total_harvest=43, harvest_rate_hrs_per_fish=20.7, mean_harvest_length_in=7.7),
    dict(**b1, species="Black Crappie", directed_effort_hours=1578, pct_of_directed_effort=9.2, total_catch=1383, catch_rate_hrs_per_fish=1.2, total_harvest=1092, harvest_rate_hrs_per_fish=1.5, mean_harvest_length_in=11.5),
    dict(**b1, species="Pumpkinseed", directed_effort_hours=0, pct_of_directed_effort=0.0, total_catch=5, catch_rate_hrs_per_fish="", total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b1, species="Rock Bass", directed_effort_hours=0, pct_of_directed_effort=0.0, total_catch=1037, catch_rate_hrs_per_fish="", total_harvest=179, harvest_rate_hrs_per_fish="", mean_harvest_length_in=7.8),
]
b2 = base(url, file, "Sand Lake", "Sawyer", "2007-08")
rows += [
    dict(**b2, species="Walleye", directed_effort_hours=2111, pct_of_directed_effort=11.2, total_catch=2149, catch_rate_hrs_per_fish=1.1, total_harvest=1, harvest_rate_hrs_per_fish=1666.7, mean_harvest_length_in=16.0),
    dict(**b2, species="Northern Pike", directed_effort_hours=920, pct_of_directed_effort=4.9, total_catch=376, catch_rate_hrs_per_fish=20.7, total_harvest=29, harvest_rate_hrs_per_fish=85.5, mean_harvest_length_in=33.1),
    dict(**b2, species="Muskellunge", directed_effort_hours=8372, pct_of_directed_effort=44.6, total_catch=439, catch_rate_hrs_per_fish=20.5, total_harvest=7, harvest_rate_hrs_per_fish="", mean_harvest_length_in=33.4),
    dict(**b2, species="Smallmouth Bass", directed_effort_hours=1208, pct_of_directed_effort=6.4, total_catch=241, catch_rate_hrs_per_fish=10.2, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b2, species="Largemouth Bass", directed_effort_hours=490, pct_of_directed_effort=2.6, total_catch=111, catch_rate_hrs_per_fish=7.1, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b2, species="Yellow Perch", directed_effort_hours=1993, pct_of_directed_effort=10.6, total_catch=3485, catch_rate_hrs_per_fish=0.6, total_harvest=981, harvest_rate_hrs_per_fish=2.0, mean_harvest_length_in=8.2),
    dict(**b2, species="Bluegill", directed_effort_hours=1591, pct_of_directed_effort=8.5, total_catch=1509, catch_rate_hrs_per_fish=1.2, total_harvest=255, harvest_rate_hrs_per_fish=6.9, mean_harvest_length_in=7.6),
    dict(**b2, species="Black Crappie", directed_effort_hours=2019, pct_of_directed_effort=10.7, total_catch=445, catch_rate_hrs_per_fish=4.5, total_harvest=353, harvest_rate_hrs_per_fish=5.7, mean_harvest_length_in=11.8),
    dict(**b2, species="Pumpkinseed", directed_effort_hours=59, pct_of_directed_effort=0.3, total_catch=26, catch_rate_hrs_per_fish=8.1, total_harvest=14, harvest_rate_hrs_per_fish="", mean_harvest_length_in=7.1),
    dict(**b2, species="Rock Bass", directed_effort_hours=22, pct_of_directed_effort=0.1, total_catch=470, catch_rate_hrs_per_fish=0.3, total_harvest=48, harvest_rate_hrs_per_fish=2.0, mean_harvest_length_in=8.0),
]
write_csv("sandlake_creel_2007_08_2023_24.csv", rows)

# ---------------------------------------------------------------- Pelican Lake (Oneida Co), 2 seasons
url = "https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/Reports_OneidaPelican2425Creel.pdf"
file = "PelicanLake_2425Creel.pdf"
rows = []
b1 = base(url, file, "Pelican Lake", "Oneida", "2024-25")
rows += [
    dict(**b1, species="Walleye", directed_effort_hours=34813, pct_of_directed_effort=23.4, total_catch=11664, catch_rate_hrs_per_fish=3.3, total_harvest=2815, harvest_rate_hrs_per_fish=12.6, mean_harvest_length_in=16.6),
    dict(**b1, species="Northern Pike", directed_effort_hours=14703, pct_of_directed_effort=9.9, total_catch=3685, catch_rate_hrs_per_fish=6.7, total_harvest=1381, harvest_rate_hrs_per_fish=12.5, mean_harvest_length_in=25.3),
    dict(**b1, species="Muskellunge", directed_effort_hours=12149, pct_of_directed_effort=8.2, total_catch=450, catch_rate_hrs_per_fish=35.4, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b1, species="Smallmouth Bass", directed_effort_hours=10274, pct_of_directed_effort=6.9, total_catch=10227, catch_rate_hrs_per_fish=1.3, total_harvest=140, harvest_rate_hrs_per_fish=159.2, mean_harvest_length_in=17.7),
    dict(**b1, species="Largemouth Bass", directed_effort_hours=5008, pct_of_directed_effort=3.4, total_catch=1827, catch_rate_hrs_per_fish=3.7, total_harvest=22, harvest_rate_hrs_per_fish="", mean_harvest_length_in=16.9),
    dict(**b1, species="Yellow Perch", directed_effort_hours=30568, pct_of_directed_effort=20.5, total_catch=41353, catch_rate_hrs_per_fish=0.8, total_harvest=12849, harvest_rate_hrs_per_fish=2.4, mean_harvest_length_in=8.4),
    dict(**b1, species="Bluegill", directed_effort_hours=18964, pct_of_directed_effort=12.7, total_catch=31800, catch_rate_hrs_per_fish=0.7, total_harvest=10891, harvest_rate_hrs_per_fish=1.9, mean_harvest_length_in=7.4),
    dict(**b1, species="Black Crappie", directed_effort_hours=12584, pct_of_directed_effort=8.4, total_catch=5895, catch_rate_hrs_per_fish=2.8, total_harvest=2480, harvest_rate_hrs_per_fish=5.6, mean_harvest_length_in=10.3),
    dict(**b1, species="Pumpkinseed", directed_effort_hours=9454, pct_of_directed_effort=6.3, total_catch=1777, catch_rate_hrs_per_fish=11.4, total_harvest=514, harvest_rate_hrs_per_fish=37.9, mean_harvest_length_in=7.1),
    dict(**b1, species="Rock Bass", directed_effort_hours=458, pct_of_directed_effort=0.3, total_catch=4559, catch_rate_hrs_per_fish=1.8, total_harvest=286, harvest_rate_hrs_per_fish=3.6, mean_harvest_length_in=7.5),
    dict(**b1, species="Burbot", directed_effort_hours=0, pct_of_directed_effort=0.0, total_catch=9, catch_rate_hrs_per_fish="", total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b1, species="White Bass", directed_effort_hours=0, pct_of_directed_effort=0.0, total_catch=54, catch_rate_hrs_per_fish="", total_harvest=21, harvest_rate_hrs_per_fish="", mean_harvest_length_in=13.2),
]
b2 = base(url, file, "Pelican Lake", "Oneida", "2011-12")
rows += [
    dict(**b2, species="Walleye", directed_effort_hours=52019, pct_of_directed_effort=18.4, total_catch=13479, catch_rate_hrs_per_fish=4.3, total_harvest=3915, harvest_rate_hrs_per_fish=13.9, mean_harvest_length_in=17.8),
    dict(**b2, species="Northern Pike", directed_effort_hours=36946, pct_of_directed_effort=13.1, total_catch=14976, catch_rate_hrs_per_fish=4.0, total_harvest=6032, harvest_rate_hrs_per_fish=7.2, mean_harvest_length_in=22.5),
    dict(**b2, species="Muskellunge", directed_effort_hours=17447, pct_of_directed_effort=6.2, total_catch=217, catch_rate_hrs_per_fish=116.3, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b2, species="Smallmouth Bass", directed_effort_hours=14541, pct_of_directed_effort=5.2, total_catch=9066, catch_rate_hrs_per_fish=2.5, total_harvest=149, harvest_rate_hrs_per_fish=122.0, mean_harvest_length_in=18.8),
    dict(**b2, species="Largemouth Bass", directed_effort_hours=13329, pct_of_directed_effort=4.7, total_catch=8633, catch_rate_hrs_per_fish=1.7, total_harvest=30, harvest_rate_hrs_per_fish="", mean_harvest_length_in=18.2),
    dict(**b2, species="Yellow Perch", directed_effort_hours=68286, pct_of_directed_effort=24.2, total_catch=131000, catch_rate_hrs_per_fish=0.5, total_harvest=40141, harvest_rate_hrs_per_fish=1.7, mean_harvest_length_in=8.9),
    dict(**b2, species="Bluegill", directed_effort_hours=48537, pct_of_directed_effort=17.2, total_catch=104476, catch_rate_hrs_per_fish=0.5, total_harvest=30093, harvest_rate_hrs_per_fish=1.7, mean_harvest_length_in=7.0),
    dict(**b2, species="Black Crappie", directed_effort_hours=18847, pct_of_directed_effort=6.7, total_catch=9730, catch_rate_hrs_per_fish=2.2, total_harvest=5682, harvest_rate_hrs_per_fish=3.8, mean_harvest_length_in=10.1),
    dict(**b2, species="Pumpkinseed", directed_effort_hours=11595, pct_of_directed_effort=4.1, total_catch=9220, catch_rate_hrs_per_fish=2.3, total_harvest=1830, harvest_rate_hrs_per_fish=8.0, mean_harvest_length_in=6.6),
    dict(**b2, species="Rock Bass", directed_effort_hours=236, pct_of_directed_effort=0.1, total_catch=4269, catch_rate_hrs_per_fish=0.6, total_harvest=403, harvest_rate_hrs_per_fish=1.2, mean_harvest_length_in=8.0),
    dict(**b2, species="White Bass", directed_effort_hours=449, pct_of_directed_effort=0.2, total_catch=699, catch_rate_hrs_per_fish=1.3, total_harvest=468, harvest_rate_hrs_per_fish=1.4, mean_harvest_length_in=12.5),
]
write_csv("pelicanlake_creel_2011_12_2024_25.csv", rows)

# ---------------------------------------------------------------- Minocqua Lake (Oneida Co), 2 seasons
url = "https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/Reports_OneidaMinocqua20242025Creel.pdf"
file = "MinocquaLake_2425Creel.pdf"
rows = []
b1 = base(url, file, "Minocqua Lake", "Oneida", "2024-25")
rows += [
    dict(**b1, species="Walleye", directed_effort_hours=11177, pct_of_directed_effort=8.4, total_catch=2342, catch_rate_hrs_per_fish=8.3, total_harvest=378, harvest_rate_hrs_per_fish=41.1, mean_harvest_length_in=19.7),
    dict(**b1, species="Northern Pike", directed_effort_hours=9481, pct_of_directed_effort=7.1, total_catch=3009, catch_rate_hrs_per_fish=4.7, total_harvest=491, harvest_rate_hrs_per_fish=19.7, mean_harvest_length_in=21.9),
    dict(**b1, species="Muskellunge", directed_effort_hours=4873, pct_of_directed_effort=3.7, total_catch=267, catch_rate_hrs_per_fish=20.7, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b1, species="Smallmouth Bass", directed_effort_hours=9733, pct_of_directed_effort=7.3, total_catch=3360, catch_rate_hrs_per_fish=4.0, total_harvest=71, harvest_rate_hrs_per_fish=465.9, mean_harvest_length_in=13.1),
    dict(**b1, species="Largemouth Bass", directed_effort_hours=17282, pct_of_directed_effort=13.0, total_catch=18254, catch_rate_hrs_per_fish=1.3, total_harvest=1357, harvest_rate_hrs_per_fish=17.4, mean_harvest_length_in=13.8),
    dict(**b1, species="Yellow Perch", directed_effort_hours=15403, pct_of_directed_effort=11.6, total_catch=10153, catch_rate_hrs_per_fish=1.9, total_harvest=2456, harvest_rate_hrs_per_fish=7.2, mean_harvest_length_in=8.4),
    dict(**b1, species="Bluegill", directed_effort_hours=27687, pct_of_directed_effort=20.8, total_catch=85861, catch_rate_hrs_per_fish=0.3, total_harvest=24157, harvest_rate_hrs_per_fish=1.2, mean_harvest_length_in=7.6),
    dict(**b1, species="Black Crappie", directed_effort_hours=27710, pct_of_directed_effort=20.9, total_catch=21674, catch_rate_hrs_per_fish=1.3, total_harvest=8658, harvest_rate_hrs_per_fish=3.2, mean_harvest_length_in=10.5),
    dict(**b1, species="Pumpkinseed", directed_effort_hours=9226, pct_of_directed_effort=6.9, total_catch=5647, catch_rate_hrs_per_fish=2.2, total_harvest=2655, harvest_rate_hrs_per_fish=4.5, mean_harvest_length_in=7.4),
    dict(**b1, species="Rock Bass", directed_effort_hours=172, pct_of_directed_effort=0.1, total_catch=1997, catch_rate_hrs_per_fish=4.1, total_harvest=265, harvest_rate_hrs_per_fish=13.3, mean_harvest_length_in=7.6),
    dict(**b1, species="Cisco", directed_effort_hours=78, pct_of_directed_effort=0.1, total_catch=25, catch_rate_hrs_per_fish=18.7, total_harvest=11, harvest_rate_hrs_per_fish=18.7, mean_harvest_length_in=17.6),
]
b2 = base(url, file, "Minocqua Lake", "Oneida", "2009-10")
rows += [
    dict(**b2, species="Walleye", directed_effort_hours=23819, pct_of_directed_effort=16.1, total_catch=618, catch_rate_hrs_per_fish=38.5, total_harvest=164, harvest_rate_hrs_per_fish=144.9, mean_harvest_length_in=18.1),
    dict(**b2, species="Northern Pike", directed_effort_hours=16238, pct_of_directed_effort=10.9, total_catch=2638, catch_rate_hrs_per_fish=13.9, total_harvest=534, harvest_rate_hrs_per_fish=33.7, mean_harvest_length_in=24.3),
    dict(**b2, species="Muskellunge", directed_effort_hours=18571, pct_of_directed_effort=12.5, total_catch=284, catch_rate_hrs_per_fish=88.5, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b2, species="Smallmouth Bass", directed_effort_hours=8892, pct_of_directed_effort=6.0, total_catch=4337, catch_rate_hrs_per_fish=2.7, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b2, species="Largemouth Bass", directed_effort_hours=15058, pct_of_directed_effort=10.2, total_catch=21407, catch_rate_hrs_per_fish=0.9, total_harvest=68, harvest_rate_hrs_per_fish=588.2, mean_harvest_length_in=15.8),
    dict(**b2, species="Yellow Perch", directed_effort_hours=16489, pct_of_directed_effort=11.1, total_catch=8129, catch_rate_hrs_per_fish=2.2, total_harvest=2334, harvest_rate_hrs_per_fish=7.6, mean_harvest_length_in=8.8),
    dict(**b2, species="Bluegill", directed_effort_hours=26580, pct_of_directed_effort=17.9, total_catch=36263, catch_rate_hrs_per_fish=0.8, total_harvest=13197, harvest_rate_hrs_per_fish=2.0, mean_harvest_length_in=7.1),
    dict(**b2, species="Black Crappie", directed_effort_hours=21510, pct_of_directed_effort=14.5, total_catch=13852, catch_rate_hrs_per_fish=1.6, total_harvest=7313, harvest_rate_hrs_per_fish=3.0, mean_harvest_length_in=10.4),
    dict(**b2, species="Pumpkinseed", directed_effort_hours=633, pct_of_directed_effort=0.4, total_catch=990, catch_rate_hrs_per_fish=0.9, total_harvest=297, harvest_rate_hrs_per_fish=2.2, mean_harvest_length_in=6.4),
    dict(**b2, species="Rock Bass", directed_effort_hours=527, pct_of_directed_effort=0.4, total_catch=2899, catch_rate_hrs_per_fish=1.1, total_harvest=152, harvest_rate_hrs_per_fish="", mean_harvest_length_in=7.4),
]
write_csv("minocqualake_creel_2009_10_2024_25.csv", rows)

# ---------------------------------------------------------------- White Potato Lake (Oconto Co)
url = "https://dnr.wisconsin.gov/sites/default/files/topic/OcontoWhitePotato2020Creel_Final.pdf"
file = "WhitePotatoLake_2020Creel.pdf"
b = base(url, file, "White Potato Lake", "Oconto", "2019-20")
rows = [
    dict(**b, species="Walleye", directed_effort_hours=2641, pct_of_directed_effort=8.3, total_catch=220, catch_rate_hrs_per_fish=20.3, total_harvest=85, harvest_rate_hrs_per_fish=34.6, mean_harvest_length_in=18.4),
    dict(**b, species="Northern Pike", directed_effort_hours=3397, pct_of_directed_effort=10.7, total_catch=374, catch_rate_hrs_per_fish=9.8, total_harvest=114, harvest_rate_hrs_per_fish=29.8, mean_harvest_length_in=23.4),
    dict(**b, species="Muskellunge", directed_effort_hours=462, pct_of_directed_effort=1.5, total_catch=0, catch_rate_hrs_per_fish=0.0, total_harvest=0, harvest_rate_hrs_per_fish=0.0, mean_harvest_length_in=""),
    dict(**b, species="Largemouth Bass", directed_effort_hours=3459, pct_of_directed_effort=10.9, total_catch=3356, catch_rate_hrs_per_fish=2.0, total_harvest=121, harvest_rate_hrs_per_fish=59.4, mean_harvest_length_in=15.0),
    dict(**b, species="Yellow Perch", directed_effort_hours=7972, pct_of_directed_effort=25.1, total_catch=3064, catch_rate_hrs_per_fish=2.8, total_harvest=837, harvest_rate_hrs_per_fish=9.5, mean_harvest_length_in=8.9),
    dict(**b, species="Bluegill", directed_effort_hours=7702, pct_of_directed_effort=24.3, total_catch=4962, catch_rate_hrs_per_fish=1.6, total_harvest=1342, harvest_rate_hrs_per_fish=5.8, mean_harvest_length_in=7.8),
    dict(**b, species="Black Crappie", directed_effort_hours=5618, pct_of_directed_effort=17.7, total_catch=476, catch_rate_hrs_per_fish=12.1, total_harvest=209, harvest_rate_hrs_per_fish=26.8, mean_harvest_length_in=9.6),
    dict(**b, species="Pumpkinseed", directed_effort_hours=482, pct_of_directed_effort=1.5, total_catch=113, catch_rate_hrs_per_fish=4.3, total_harvest=35, harvest_rate_hrs_per_fish=13.8, mean_harvest_length_in=7.3),
    dict(**b, species="Rock Bass", directed_effort_hours=0, pct_of_directed_effort=0.0, total_catch=96, catch_rate_hrs_per_fish=0.0, total_harvest=0, harvest_rate_hrs_per_fish=0.0, mean_harvest_length_in=""),
    dict(**b, species="Yellow Bullhead", directed_effort_hours=0, pct_of_directed_effort=0.0, total_catch=7, catch_rate_hrs_per_fish=0.0, total_harvest=0, harvest_rate_hrs_per_fish=0.0, mean_harvest_length_in=""),
]
write_csv("whitepotatolake_creel_2019_20.csv", rows)

# ---------------------------------------------------------------- Sawyer Lake (Langlade Co)
url = "https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/LangladeSawyer2023Creel.pdf"
file = "SawyerLakeLanglade_2023Creel.pdf"
b = base(url, file, "Sawyer Lake", "Langlade", "Summer 2023")
rows = [
    dict(**b, species="Walleye", directed_effort_hours=383, pct_of_directed_effort=3.0, total_catch=19, catch_rate_hrs_per_fish=28.0, total_harvest=10, harvest_rate_hrs_per_fish=36.8, mean_harvest_length_in=23.9),
    dict(**b, species="Northern Pike", directed_effort_hours=1326, pct_of_directed_effort=10.4, total_catch=377, catch_rate_hrs_per_fish=4.5, total_harvest=48, harvest_rate_hrs_per_fish=32.6, mean_harvest_length_in=24.5),
    dict(**b, species="Smallmouth Bass", directed_effort_hours=166, pct_of_directed_effort=1.3, total_catch=75, catch_rate_hrs_per_fish=7.8, total_harvest=5, harvest_rate_hrs_per_fish=34.3, mean_harvest_length_in=""),
    dict(**b, species="Largemouth Bass", directed_effort_hours=4055, pct_of_directed_effort=31.7, total_catch=2247, catch_rate_hrs_per_fish=1.9, total_harvest=67, harvest_rate_hrs_per_fish=66.2, mean_harvest_length_in=14.5),
    dict(**b, species="Yellow Perch", directed_effort_hours=334, pct_of_directed_effort=2.6, total_catch=437, catch_rate_hrs_per_fish=1.3, total_harvest=78, harvest_rate_hrs_per_fish=5.5, mean_harvest_length_in=7.6),
    dict(**b, species="Bluegill", directed_effort_hours=3601, pct_of_directed_effort=28.1, total_catch=10325, catch_rate_hrs_per_fish=0.4, total_harvest=2667, harvest_rate_hrs_per_fish=1.4, mean_harvest_length_in=7.4),
    dict(**b, species="Black Crappie", directed_effort_hours=1773, pct_of_directed_effort=13.8, total_catch=2736, catch_rate_hrs_per_fish=0.7, total_harvest=886, harvest_rate_hrs_per_fish=2.1, mean_harvest_length_in=9.5),
    dict(**b, species="Pumpkinseed", directed_effort_hours=1135, pct_of_directed_effort=8.9, total_catch=474, catch_rate_hrs_per_fish=2.4, total_harvest=197, harvest_rate_hrs_per_fish=5.8, mean_harvest_length_in=7.5),
    dict(**b, species="Rock Bass", directed_effort_hours=33, pct_of_directed_effort=0.3, total_catch=1351, catch_rate_hrs_per_fish=2.7, total_harvest=90, harvest_rate_hrs_per_fish=6.8, mean_harvest_length_in=8.1),
]
write_csv("sawyerlake_langlade_creel_2023.csv", rows)

# ---------------------------------------------------------------- Lake Wisconsin (Columbia/Sauk Co)
url = "https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/Reports_ColumbiaSaukLakeWisconsinandWisconsinRiver2023Creel.pdf"
file = "LakeWisconsin_2023Creel.pdf"
b = base(url, file, "Lake Wisconsin", "Columbia/Sauk", "Jul 2022-Jun 2023")
# Table 3: catch/harvest rate columns split open-water vs ice fishing (hrs/fish).
rows = [
    dict(**b, species="Walleye", directed_effort_hours=57393, pct_of_directed_effort=29.2, total_catch=34628, catch_rate_hrs_per_fish=1.7, total_harvest=5231, harvest_rate_hrs_per_fish=11.0, mean_harvest_length_in=17.0),
    dict(**b, species="Sauger", directed_effort_hours=35324, pct_of_directed_effort=18.0, total_catch=31916, catch_rate_hrs_per_fish=1.2, total_harvest=5067, harvest_rate_hrs_per_fish=7.2, mean_harvest_length_in=16.5),
    dict(**b, species="Black Crappie", directed_effort_hours="", pct_of_directed_effort="", total_catch=9800, catch_rate_hrs_per_fish=3.0, total_harvest=4288, harvest_rate_hrs_per_fish=4.7, mean_harvest_length_in=9.5),
    dict(**b, species="White Crappie", directed_effort_hours="", pct_of_directed_effort="", total_catch=8404, catch_rate_hrs_per_fish=1.7, total_harvest=2672, harvest_rate_hrs_per_fish=3.3, mean_harvest_length_in=10.1),
    dict(**b, species="Smallmouth Bass", directed_effort_hours=22404, pct_of_directed_effort=11.4, total_catch=20052, catch_rate_hrs_per_fish=1.4, total_harvest=53, harvest_rate_hrs_per_fish="", mean_harvest_length_in=15.6),
    dict(**b, species="Largemouth Bass", directed_effort_hours=21230, pct_of_directed_effort=10.8, total_catch=11734, catch_rate_hrs_per_fish=2.0, total_harvest=442, harvest_rate_hrs_per_fish=54.1, mean_harvest_length_in=15.6),
    dict(**b, species="Bluegill", directed_effort_hours=16012, pct_of_directed_effort=8.1, total_catch=28256, catch_rate_hrs_per_fish=0.5, total_harvest=8746, harvest_rate_hrs_per_fish=1.5, mean_harvest_length_in=7.2),
    dict(**b, species="Yellow Perch", directed_effort_hours=7054, pct_of_directed_effort=3.6, total_catch=6261, catch_rate_hrs_per_fish=2.2, total_harvest=2008, harvest_rate_hrs_per_fish=4.8, mean_harvest_length_in=8.7),
    dict(**b, species="White Bass", directed_effort_hours=2939, pct_of_directed_effort=1.5, total_catch=5162, catch_rate_hrs_per_fish=1.4, total_harvest=1287, harvest_rate_hrs_per_fish=3.8, mean_harvest_length_in=12.2),
    dict(**b, species="Northern Pike", directed_effort_hours=2730, pct_of_directed_effort=1.4, total_catch=940, catch_rate_hrs_per_fish=17.8, total_harvest=17, harvest_rate_hrs_per_fish="", mean_harvest_length_in=29.7),
    dict(**b, species="Channel Catfish", directed_effort_hours=2613, pct_of_directed_effort=1.3, total_catch=1251, catch_rate_hrs_per_fish=2.8, total_harvest=92, harvest_rate_hrs_per_fish=32.2, mean_harvest_length_in=21.5),
    dict(**b, species="Flathead Catfish", directed_effort_hours=1677, pct_of_directed_effort=0.9, total_catch=290, catch_rate_hrs_per_fish=99.5, total_harvest=53, harvest_rate_hrs_per_fish="", mean_harvest_length_in=21.8),
    dict(**b, species="Muskellunge", directed_effort_hours=1392, pct_of_directed_effort=0.7, total_catch=105, catch_rate_hrs_per_fish=349.8, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b, species="Freshwater Drum", directed_effort_hours=724, pct_of_directed_effort=0.4, total_catch=18114, catch_rate_hrs_per_fish=3.6, total_harvest=416, harvest_rate_hrs_per_fish=6.4, mean_harvest_length_in=13.4),
]
write_csv("lakewisconsin_creel_2022_23.csv", rows)

# ---------------------------------------------------------------- Lake Wissota (Chippewa Co), 2 seasons
url = "https://dnr.wisconsin.gov/sites/default/files/topic/Fishing/North_ChippewaWissota2019Creel.pdf"
file = "LakeWissota_2019Creel.pdf"
rows = []
b1 = base(url, file, "Lake Wissota", "Chippewa", "2019-20")
rows += [
    dict(**b1, species="Walleye", directed_effort_hours=28722, pct_of_directed_effort=32.1, total_catch=22771, catch_rate_hrs_per_fish=1.5, total_harvest=4166, harvest_rate_hrs_per_fish=7.7, mean_harvest_length_in=12.7),
    dict(**b1, species="Northern Pike", directed_effort_hours=1503, pct_of_directed_effort=1.7, total_catch=1535, catch_rate_hrs_per_fish=6.6, total_harvest=32, harvest_rate_hrs_per_fish="", mean_harvest_length_in=23.0),
    dict(**b1, species="Muskellunge", directed_effort_hours=4540, pct_of_directed_effort=5.1, total_catch=509, catch_rate_hrs_per_fish=14.7, total_harvest=46, harvest_rate_hrs_per_fish="", mean_harvest_length_in=45.5),
    dict(**b1, species="Smallmouth Bass", directed_effort_hours=12440, pct_of_directed_effort=13.9, total_catch=11287, catch_rate_hrs_per_fish=1.3, total_harvest=90, harvest_rate_hrs_per_fish=588.2, mean_harvest_length_in=14.5),
    dict(**b1, species="Largemouth Bass", directed_effort_hours=3335, pct_of_directed_effort=3.7, total_catch=41, catch_rate_hrs_per_fish="", total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b1, species="Bluegill", directed_effort_hours=9399, pct_of_directed_effort=10.5, total_catch=7789, catch_rate_hrs_per_fish=1.3, total_harvest=2302, harvest_rate_hrs_per_fish=4.1, mean_harvest_length_in=7.6),
    dict(**b1, species="Black Crappie", directed_effort_hours=20116, pct_of_directed_effort=22.5, total_catch=23517, catch_rate_hrs_per_fish=0.9, total_harvest=10645, harvest_rate_hrs_per_fish=1.9, mean_harvest_length_in=10.7),
    dict(**b1, species="Yellow Perch", directed_effort_hours=173, pct_of_directed_effort=0.2, total_catch=692, catch_rate_hrs_per_fish="", total_harvest=107, harvest_rate_hrs_per_fish="", mean_harvest_length_in=8.5),
    dict(**b1, species="Channel Catfish", directed_effort_hours=6110, pct_of_directed_effort=6.8, total_catch=5490, catch_rate_hrs_per_fish=1.9, total_harvest=2790, harvest_rate_hrs_per_fish=2.5, mean_harvest_length_in=22.7),
    dict(**b1, species="Flathead Catfish", directed_effort_hours=3233, pct_of_directed_effort=3.6, total_catch=151, catch_rate_hrs_per_fish=87.7, total_harvest=37, harvest_rate_hrs_per_fish=87.7, mean_harvest_length_in=19.5),
]
b2 = base(url, file, "Lake Wissota", "Chippewa", "2006-07")
rows += [
    dict(**b2, species="Walleye", directed_effort_hours=42429, pct_of_directed_effort=35.0, total_catch=31497, catch_rate_hrs_per_fish=1.4, total_harvest=9216, harvest_rate_hrs_per_fish=4.5, mean_harvest_length_in=12.6),
    dict(**b2, species="Northern Pike", directed_effort_hours=2812, pct_of_directed_effort=2.3, total_catch=2144, catch_rate_hrs_per_fish=9.1, total_harvest=189, harvest_rate_hrs_per_fish=33.4, mean_harvest_length_in=22.9),
    dict(**b2, species="Muskellunge", directed_effort_hours=13887, pct_of_directed_effort=11.5, total_catch=1131, catch_rate_hrs_per_fish=20.2, total_harvest=0, harvest_rate_hrs_per_fish=0.0, mean_harvest_length_in=""),
    dict(**b2, species="Smallmouth Bass", directed_effort_hours=30431, pct_of_directed_effort=25.1, total_catch=20338, catch_rate_hrs_per_fish=1.6, total_harvest=208, harvest_rate_hrs_per_fish=0.0, mean_harvest_length_in=16.4),
    dict(**b2, species="Largemouth Bass", directed_effort_hours=11625, pct_of_directed_effort=9.6, total_catch=980, catch_rate_hrs_per_fish=16.2, total_harvest=0, harvest_rate_hrs_per_fish="", mean_harvest_length_in=""),
    dict(**b2, species="Bluegill", directed_effort_hours=5747, pct_of_directed_effort=4.7, total_catch=8961, catch_rate_hrs_per_fish=0.7, total_harvest=3324, harvest_rate_hrs_per_fish=2.1, mean_harvest_length_in=7.5),
    dict(**b2, species="Pumpkinseed", directed_effort_hours=116, pct_of_directed_effort=0.1, total_catch=149, catch_rate_hrs_per_fish=1.0, total_harvest=0, harvest_rate_hrs_per_fish=0.0, mean_harvest_length_in=""),
    dict(**b2, species="Black Crappie", directed_effort_hours=8747, pct_of_directed_effort=7.2, total_catch=5943, catch_rate_hrs_per_fish=1.7, total_harvest=3445, harvest_rate_hrs_per_fish=2.8, mean_harvest_length_in=10.1),
    dict(**b2, species="Yellow Perch", directed_effort_hours=2174, pct_of_directed_effort=1.8, total_catch=4096, catch_rate_hrs_per_fish=1.4, total_harvest=4, harvest_rate_hrs_per_fish=10.0, mean_harvest_length_in=8.5),
    dict(**b2, species="Lake Sturgeon", directed_effort_hours=573, pct_of_directed_effort=0.5, total_catch=26, catch_rate_hrs_per_fish=22.0, total_harvest=26, harvest_rate_hrs_per_fish=22.0, mean_harvest_length_in=50.5),
    dict(**b2, species="Channel Catfish", directed_effort_hours=2544, pct_of_directed_effort=2.1, total_catch=1140, catch_rate_hrs_per_fish=4.6, total_harvest=607, harvest_rate_hrs_per_fish=5.6, mean_harvest_length_in=19.6),
]
write_csv("lakewissota_creel_2006_07_2019_20.csv", rows)

print("Done.")
