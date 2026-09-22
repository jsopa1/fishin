"""Builds docs/design/wireframe_accessible.html: the field-guide style with visibility and accessibility
improvements. Run from the repo root, then screenshot the HTML with Chrome."""
import io
from pathlib import Path

OUT = Path(__file__).with_name("wireframe_accessible.html")
SP = "../../webapp/static/img/species/"
S = "spot_samples/"
TILE = "https://tile.openstreetmap.org/13/"

ICON = ('<svg class="mark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round"><path d="M3 12c2.5-4 7-6 11-6 3 0 6 2 7 6-1 4-4 6-7 6-4 0-8.5-2-11-6z"/><path d="M3 12L1 8M3 12l-2 4M20 9v6"/>'
        '<circle cx="15" cy="10.2" r=".8" fill="currentColor"/></svg>')


def nav(active):
    items = [("Home", "M3 11l9-7 9 7v9H3z"), ("Explore", "M9 4l6 2 6-2v14l-6 2-6-2-6 2V6z"), ("Fish", "M3 12c2.5-4 7-6 11-6 3 0 6 2 7 6-1 4-4 6-7 6-4 0-8.5-2-11-6z"),
             ("Profile", "M12 12a4 4 0 100-8 4 4 0 000 8zM4 21a8 8 0 0116 0")]
    out = '<nav class="bar" aria-label="Primary">'
    for name, d in items:
        cur = ' class="on" aria-current="page"' if name == active else ""
        out += f'<a{cur}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="{d}"/></svg><span>{name}</span></a>'
    return out + "</nav>"


def tag(kind):
    if kind == "c":
        return '<span class="tag ok"><b aria-hidden="true">&#10003;</b> Confirmed</span>'
    return '<span class="tag lk"><b aria-hidden="true">~</b> Likely</span>'


def meter(feed, spawn, now, label):
    z = ""
    if spawn:
        z += f'<b style="left:{spawn[0]}%;width:{spawn[1]-spawn[0]}%"></b>'
    z += f'<i style="left:{feed[0]}%;width:{feed[1]-feed[0]}%"></i><u style="left:{now}%"></u>'
    return f'<div class="meter" role="img" aria-label="{label}">{z}</div><p class="mtxt">{label}</p>'


def mapthumb(x0, y0, dx, dy):
    tiles = "".join(f'<img src="{TILE}{x0+i}/{y0+j}.png" style="left:{i*256}px;top:{j*256}px" alt="">' for j in range(2) for i in range(2))
    return f'<div class="cmap" aria-hidden="true"><div class="ct" style="left:{dx}px;top:{dy}px">{tiles}</div><span class="pin"></span></div>'


def drawing():
    return ('<div class="cmap draw" aria-hidden="true"><svg viewBox="0 0 96 96"><rect width="96" height="96" fill="#dfe9c9"/>'
            '<path d="M0 60 Q24 50 48 60 T96 58 V96 H0Z" fill="#3f78b0"/><path d="M0 70 Q24 62 48 70 T96 68" fill="none" stroke="#fff" stroke-width="2"/>'
            '<path d="M10 60 L10 38 M10 38 L4 48 M10 38 L16 48" stroke="#0d2a22" stroke-width="3" fill="none"/></svg></div>')


P1 = f"""
<div class="phone"><a class="skip">Skip to main content</a>
  <header class="top">{ICON}<span>Home</span></header>
  <h1>Wisconsin fishing conditions</h1>
  
  <h2>Recommended Spots</h2>
  <p class="cap-note">Each card shows the best picture we have, in this order: a real photo, the map, then a drawing.</p>
  <article class="card"><figure class="photo"><img src="{S}genesee.jpg" alt="Middle Genesee Lake shoreline"><figcaption>Photo, 4 m away &middot; CC BY-SA 3.0 &middot; Awkwafaba</figcaption></figure>
    <h3>Middle Genesee Lake</h3><p class="sub">Waukesha County &middot; Boat launch</p>
    <div class="nums"><div><b>6</b><span>species in range now</span></div><div><b>67&deg;F</b><span>estimated water temp</span></div></div>
    <p class="names">{tag("c")} Walleye &nbsp; {tag("c")} Brook Trout</p></article>
  <article class="card"><div class="row">{mapthumb(2061, 3007, -112, -174)}<div><h3>Hwy 12 Boat Launch</h3><p class="sub">Lake Menomin &middot; Dunn County</p></div></div>
    <div class="nums"><div><b>6</b><span>species in range now</span></div><div><b>67&deg;F</b><span>estimated water temp</span></div></div></article>
  <article class="card"><div class="row">{drawing()}<div><h3>Riverside Landing</h3><p class="sub">No map available offline</p></div></div></article>
  {nav("Home")}
</div>"""

P2 = f"""
<div class="phone">
  <header class="top">{ICON}<span>Spot report</span></header>
  <a class="back">&larr; Back to Explore</a>
  <div class="band"><h1>Middle Genesee Lake</h1><p>Waukesha County</p><a class="btn ghost">&#9734; Save this spot</a></div>
  <figure class="photo flat"><img src="{S}genesee.jpg" alt="Middle Genesee Lake shoreline"><figcaption>Photo of the water, 4 m from this spot &middot; CC BY-SA 3.0 &middot; Awkwafaba &middot; <u>source</u></figcaption></figure>
  <div class="stats"><div><span>Water</span><b>67&deg;F</b><em>estimated</em></div><div><span>Air</span><b>63&deg;F</b><em>Clear</em></div><div><span>Wind</span><b>10 mph E</b></div><div><span>Moon</span><b>Waxing Gibbous</b></div></div>
  <h2>Active fish <em>6 in range</em></h2>
  <div class="frow"><div class="fh"><img src="{SP}walleye.jpg" alt="Walleye"><b>Walleye</b>{tag("c")}</div>{meter((41.7,58.4),None,58.4,"Feeding range 55&ndash;75&deg;F. Now 67&deg;F: inside.")}</div>
  <div class="frow"><div class="fh"><img src="{SP}white_sucker.jpg" alt="White Sucker"><b>White Sucker</b>{tag("c")}</div>{meter((75,83),(40,58),50,"Spawning range 39&ndash;64&deg;F. Now 60&deg;F: inside spawning range.")}</div>
  <p class="key"><span><i class="kf"></i>Feeding range</span><span><i class="ks"></i>Spawning range</span><span><i class="kn"></i>Today</span></p>
  {nav("Explore")}
</div>"""

P3 = f"""
<div class="phone">
  <header class="top">{ICON}<span>Spot report</span></header>
  <a class="back">&larr; Back to Explore</a>
  <div class="band"><h1>Hwy 12 Boat Launch</h1><p>Lake Menomin, Dunn County</p><a class="btn ghost">&#9734; Save this spot</a></div>
  <div class="bigmap" role="img" aria-label="Map showing this access point on Lake Menomin"><div class="bt">
    {"".join(f'<img src="{TILE}{2020+i}/{2900+j}.png" style="left:{i*256}px;top:{j*256}px" alt="">' for j in range(2) for i in range(2))}</div><span class="pin big"></span></div>
  <p class="cap-note">No photo of this spot exists in open collections, so we show where it is. <a class="lnk">Open in your maps app</a></p>
  <div class="stats"><div><span>Water</span><b>67&deg;F</b><em>estimated</em></div><div><span>Air</span><b>63&deg;F</b><em>Clear</em></div></div>
  <div class="frow"><div class="fh"><img src="{SP}brook_trout.jpg" alt="Brook Trout"><b>Brook Trout</b>{tag("c")}</div>{meter((41.7,58.4),None,52,"Feeding range 55&ndash;75&deg;F. Now 67&deg;F: inside.")}</div>
  {nav("Explore")}
</div>"""

P4 = f"""
<div class="phone">
  <header class="top">{ICON}<span>Fish</span></header>
  <a class="back">&larr; Back to Hwy 12 Boat Launch</a>
  <div class="hero"><img src="{SP}walleye.jpg" alt="Walleye underwater"><small>Public domain &middot; USFWS &middot; <u>source</u></small><div><h1>Walleye</h1><i>Sander vitreus</i></div></div>
  <div class="tiles"><div><span>Active range</span><b>55&ndash;75&deg;F</b></div><div><span>Spawning</span><b>40&ndash;52&deg;F</b></div><div><span>Feeds</span><b>Low light</b></div></div>
  <h2>Documented activity</h2>
  <p class="lead">Temperature ranges from published research, not a prediction of whether the fish will bite.</p>
  <details open><summary>Source note</summary><p class="lead">WDNR / agency data &mdash; the note opens in place, and the whole row is a 44 px target.</p></details>
  <h2>Recommended bait</h2>
  <div class="bait"><div class="bi"></div><div><b>Leeches</b><p class="sub">Bait-cast or still fish from an anchored boat.</p></div></div>
  {nav("Fish")}
</div>"""

P5 = f"""
<div class="phone">
  <header class="top">{ICON}<span>Explore</span></header>
  <h1>Explore</h1>
  <div class="seg" role="tablist"><a class="on" role="tab">Map</a><a role="tab">List</a></div>
  <div class="fbtn">&#9776; Filters <em>2 active</em></div>
  <p class="legend"><span><svg viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="#0d2a22"/></svg>Boat ramp</span><span><svg viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" fill="#3f6a24"/></svg>Carry-in</span><span><svg viewBox="0 0 16 16"><path d="M8 2l7 12H1z" fill="#8a5a00"/></svg>Shore</span></p>
  <p class="cap-note">Marker <b>shape</b> as well as colour tells the type apart.</p>
  <div class="bigmap short"><div class="bt">{"".join(f'<img src="{TILE}{2020+i}/{2900+j}.png" style="left:{i*256}px;top:{j*256}px" alt="">' for j in range(2) for i in range(2))}</div>
    <svg class="mk" style="left:60px;top:40px" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="#0d2a22" stroke="#fff" stroke-width="2"/></svg>
    <svg class="mk" style="left:150px;top:90px" viewBox="0 0 16 16"><rect x="1" y="1" width="14" height="14" fill="#3f6a24" stroke="#fff" stroke-width="2"/></svg>
    <svg class="mk" style="left:230px;top:50px" viewBox="0 0 16 16"><path d="M8 1l7.5 14H.5z" fill="#8a5a00" stroke="#fff" stroke-width="2"/></svg></div>
  {nav("Explore")}
</div>"""

P6 = f"""
<div class="phone">
  <header class="top">{ICON}<span>Profile</span></header>
  <h1>Profile</h1><p class="sub">Guest &middot; saved on this device only</p>
  <h2>Appearance</h2>
  <div class="pref"><b>Theme</b><div class="tri"><u class="on">Match device</u><u>Light</u><u>Dark</u></div></div>
  <div class="pref"><b>Text size</b><div class="tri"><u class="on">Standard</u><u>Large</u><u>Largest</u></div></div>
  <p class="cap-note">New: Large and Largest scale every size in the app. Motion is reduced automatically when your device asks for it.</p>
  <h2>Fishing preferences</h2>
  <div class="pref"><b>Boat launches</b><div class="tri"><u class="on">Prefer</u><u>OK</u><u>Avoid</u></div></div>
  <div class="pref"><b>Shore spots</b><div class="tri"><u>Prefer</u><u>OK</u><u class="on">Avoid</u></div></div>
  <div class="focus"><a class="btn">Focus ring: 3 px, always visible on keyboard</a></div>
  {nav("Profile")}
</div>"""

P7 = f"""
<div class="phone night"><header class="top">{ICON}<span>Spot report</span></header>
  <div class="band"><h1>Hwy 12 Boat Launch</h1><p>Lake Menomin, Dunn County</p><a class="btn ghost">&#9734; Save this spot</a></div>
  <div class="stats"><div><span>Water</span><b>67&deg;F</b><em>estimated</em></div><div><span>Air</span><b>63&deg;F</b><em>Clear</em></div></div>
  <div class="seg"><a class="on">Map</a><a>List</a></div>
  <div class="frow"><div class="fh"><img src="{SP}brook_trout.jpg" alt="Brook Trout"><b>Brook Trout</b>{tag("c")}</div>{meter((41.7,58.4),(20,30),52,"Feeding range 55&ndash;75&deg;F. Now 67&deg;F: inside.")}</div>
  <p class="cap-note">Dark theme: button text is now near-black on the light-green fill (9.1:1, was white at 2.1:1).</p>
  {nav("Explore")}
</div>"""

ROWS = [
    ("Before", "After", "Where"),
    ("2.07 : 1", "9.12 : 1", "Dark theme: text on green buttons and active toggles"),
    ("3.78 : 1", "5.80 : 1", "Light theme: footer &ldquo;updated&rdquo; line"),
    ("2.26 : 1", "4.15 : 1", "Spawning-range bar against the page (graphics need 3 : 1)"),
    ("3.11 : 1", "4.62 : 1", "Feeding-range bar against the page"),
    ("11.5 px", "12.8 px+", "Smallest text (bottom-nav labels); body text 15 px &rarr; 16 px"),
    ("19&ndash;40 px", "44 px+", "Tap targets: buttons, chips, toggles, tags, links, form fields, map zoom"),
    ("none", "added", "Skip-to-content link; 3 px focus ring; reduced-motion support"),
    ("colour only", "shape + text", "Map marker types; Confirmed / Likely carry a &#10003; / ~ mark"),
]
table = "".join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in ROWS[1:])
P8 = f"""
<div class="phone sheet"><header class="top">{ICON}<span>Accessibility checklist</span></header>
  <h1>Measured, then fixed</h1>
  <p class="lead">Ratios were measured on the live pages in both themes. WCAG AA needs 4.5 : 1 for text, 3 : 1 for graphics and large text.</p>
  <table class="ct2"><thead><tr><th>Before</th><th>After</th><th>Where</th></tr></thead><tbody>{table}</tbody></table>
  <p class="cap-note">Still true after the change: no bite scores, wording unchanged, same square, flat field-guide style.</p>
</div>"""

CAPS = [
    ("1 &middot; Home", "Best picture first: a real photo (credited, with distance) &rarr; the map &rarr; a drawn water scene if tiles cannot load. Numbers first, plain words."),
    ("2 &middot; Spot with a photo", "Photo of the water under the header, credit and source on the image, a spawning bar in a second colour, and the numbers printed under each meter."),
    ("3 &middot; Spot without a photo", "Most spots have no open photo, so the map is the hero, with an Open in maps link. Never a fish photo standing in for the place."),
    ("4 &middot; Fish", "Same style, larger reading text, every disclosure a 44 px row that opens in place."),
    ("5 &middot; Explore", "Type is told apart by shape as well as colour; 44 px toggles and filters; 44 px map zoom."),
    ("6 &middot; Profile", "Adds a Text size choice; theme and preferences are large segmented controls; motion follows the device setting."),
    ("7 &middot; Dark theme", "Same layout on deep green with corrected button text and lighter meter colours."),
    ("8 &middot; What changed", "The measured before and after for every fix."),
]

CSS = """
*{box-sizing:border-box}body{margin:0;background:#0b1512;font-family:'Nunito',Arial,sans-serif;color:#0d2a22}
.lab{display:grid;grid-template-columns:repeat(4,400px);gap:44px 36px;justify-content:center;padding:30px}
.cell .cap{color:#dfe9c9;padding:12px 6px}.cell .cap b{display:block;font-size:17px;margin-bottom:4px;color:#fff}.cell .cap p{margin:0;font-size:14px;line-height:1.45;color:#c6d5c9}
.phone{position:relative;width:400px;height:880px;overflow:hidden;background:#f7f2e4;border:8px solid #16231e;border-radius:34px;padding:0 16px 84px;font-size:16px;line-height:1.5}
.phone.night{background:#0d1f1a;color:#eef3e6}.phone.night .top{background:#0d1f1a;color:#9cc06a}.night .band{background:#06140f}
.skip{position:absolute;left:10px;top:8px;background:#0d2a22;color:#fff;padding:8px 12px;font-weight:800;font-size:14px;z-index:5;outline:3px solid #f2d678}
.top{display:flex;align-items:center;gap:12px;margin:0 -16px 8px;padding:34px 16px 10px;font-weight:800;color:#2f6b4f;font-size:17px;border-bottom:1px solid #d9d2b8}
.top .mark{width:30px;height:30px}
h1{font-size:28px;line-height:1.1;font-weight:900;margin:12px 0 6px;color:inherit}h2{font-size:19px;font-weight:800;border-bottom:1px solid #d9d2b8;padding-bottom:4px;margin:16px 0 8px;display:flex;justify-content:space-between}
h2 em{font-style:normal;font-size:14px;color:#3f6a24;font-weight:800}.night h2 em{color:#cfe6a8}h3{margin:8px 0 0;font-size:18px;font-weight:800}
.lead,.sub{margin:2px 0 8px;font-size:15px;color:#4a5f54}.night .lead,.night .sub{color:#adc0b3}
.cap-note{font-size:13.5px;color:#4a5f54;margin:6px 0}.night .cap-note{color:#adc0b3}
.card{background:#fff;border:1px solid #d9d2b8;padding:12px;margin:10px 0}.row{display:flex;gap:12px;align-items:flex-start}
.photo{margin:-12px -12px 8px;position:relative}.photo.flat{margin:0 -16px 8px}.photo img{width:100%;height:96px;object-fit:cover;display:block}
figcaption{font-size:12.8px;background:#0d2a22;color:#fff;padding:5px 10px}
.nums{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #ece6d2;margin-top:8px;padding-top:8px;gap:8px}.nums b{display:block;font-size:26px;line-height:1;color:#0d2a22}.nums span{font-size:13px;color:#4a5f54}
.names{margin:8px 0 0;font-size:15px;line-height:2}
.tag{padding:0 4px;font-size:13.5px;font-weight:800;margin-left:4px}.tag b{font-weight:900}.ok{background:linear-gradient(transparent 36%,#d3e3ae 36%,#d3e3ae 94%,transparent 94%);color:#146c43}.lk{background:linear-gradient(transparent 36%,#f1dc94 36%,#f1dc94 94%,transparent 94%);color:#5e4708}
.night .ok{background:linear-gradient(transparent 36%,#2f5a2c 36%,#2f5a2c 94%,transparent 94%);color:#e3f2c6}.night .lk{background:linear-gradient(transparent 36%,#5a4a17 36%,#5a4a17 94%,transparent 94%);color:#f7e39a}
.cmap{position:relative;flex:none;width:96px;height:96px;overflow:hidden;border:1px solid #d9d2b8;border-top:3px solid #55772f}.ct{position:absolute;width:512px;height:512px}.ct img{position:absolute;width:256px;height:256px}
.pin{position:absolute;left:50%;top:50%;width:14px;height:14px;margin:-7px 0 0 -7px;background:#00332a;border:2px solid #fff;box-shadow:0 0 0 1px #00332a}.pin.big{width:20px;height:20px;margin:-10px 0 0 -10px}
.draw svg{width:100%;height:100%}
.bar{position:absolute;left:0;right:0;bottom:0;height:72px;display:grid;grid-template-columns:repeat(4,1fr);background:#fffdf6;border-top:1px solid #d9d2b8}.night .bar{background:#0d1f1a;border-color:#2a4034}
.bar a{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;font-size:13px;font-weight:800;color:#33453a;min-height:44px}.night .bar a{color:#adc0b3}.bar svg{width:24px;height:24px}.bar a.on{color:#00332a;box-shadow:inset 0 3px #55772f}.night .bar a.on{color:#cfe6a8;box-shadow:inset 0 3px #9cc06a}
.back{display:inline-flex;align-items:center;min-height:44px;color:#2f6b4f;font-weight:800;font-size:15px}.night .back{color:#9cc06a}
.band{background:#00332a;color:#fff;margin:0 -16px;padding:12px 16px 14px;border-bottom:3px solid #55772f}.band h1{margin:0;font-size:26px}.band p{margin:2px 0 10px;color:#cfe6a8}
.btn{display:inline-flex;align-items:center;min-height:44px;padding:0 16px;font-weight:800;font-size:15px;background:#2f6b4f;color:#fff}.btn.ghost{background:transparent;border:1px solid rgba(255,255,255,.7)}
.stats{display:grid;grid-template-columns:1fr 1fr;background:#fff;border:1px solid #d9d2b8;border-top:3px solid #55772f;margin:0 0 4px}.night .stats{background:#132a22;border-color:#2a4034}
.stats div{padding:8px 12px;display:flex;flex-direction:column}.stats span{font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#4a5f54}.night .stats span{color:#adc0b3}.stats b{font-size:21px}.stats em{font-style:normal;font-size:13.5px;color:#4a5f54}.night .stats em{color:#adc0b3}
.frow{padding:8px 0;border-bottom:1px solid #ece6d2}.night .frow{border-color:#2a4034}.fh{display:flex;align-items:center;gap:10px}.fh img{width:64px;height:44px;object-fit:cover}.fh b{font-size:17px;flex:1}
.meter{position:relative;height:9px;background:#e8e2cf;margin:10px 0 4px}.night .meter{background:#243a30}.meter i{position:absolute;top:0;bottom:0;background:#55772f}.meter b{position:absolute;top:0;bottom:0;background:#3f78b0}.meter u{position:absolute;top:-5px;width:3px;height:19px;background:#0d2a22}
.night .meter i{background:#9cc06a}.night .meter b{background:#7aa7d6}.night .meter u{background:#eef3e6}
.mtxt{margin:0;font-size:13.5px;color:#33453a}.night .mtxt{color:#c6d5c9}
.key{display:flex;gap:14px;font-size:13px;color:#4a5f54;margin:8px 0}.key i{display:inline-block;margin-right:5px;vertical-align:middle}.kf,.ks{width:16px;height:7px}.kf{background:#55772f}.ks{background:#3f78b0}.kn{width:3px;height:14px;background:#0d2a22}
.bigmap{position:relative;height:210px;overflow:hidden;margin:0 -16px;border-bottom:3px solid #55772f}.bigmap.short{height:300px;margin:6px 0}.bt{position:absolute;left:-140px;top:-160px;width:512px;height:512px}.bt img{position:absolute;width:256px;height:256px}
.mk{position:absolute;width:30px;height:30px}
.lnk{color:#2f6b4f;font-weight:800;text-decoration:underline;display:inline-block;min-height:44px;line-height:44px}
.hero{position:relative;margin:0 -16px;height:220px;background:#00332a}.hero img{width:100%;height:220px;object-fit:cover;display:block}.hero small{position:absolute;right:10px;top:8px;color:#fff;font-size:12.8px;text-shadow:0 1px 2px #000}.hero div{position:absolute;left:0;right:0;bottom:0;padding:40px 16px 12px;background:linear-gradient(transparent,rgba(0,26,20,.92));color:#fff}.hero h1{margin:0;color:#fff;font-size:32px}.hero i{font-family:Georgia,serif;color:#e7f1c9}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);margin-top:10px}.tiles div{background:#fff;border:1px solid #d9d2b8;border-top:3px solid #55772f;padding:6px 8px}.tiles span{display:block;font-size:12.8px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:#4a5f54}.tiles b{font-size:17px}
details{border-bottom:1px solid #d9d2b8}summary{min-height:44px;display:flex;align-items:center;font-weight:800;color:#2f6b4f}
.bait{display:flex;gap:12px;align-items:center;padding:8px 0}.bi{width:70px;height:54px;background:#dfe9c9;border:1px solid #d9d2b8}
.seg{display:grid;grid-template-columns:1fr 1fr;border:2px solid #2f6b4f;margin:8px 0}.seg a{display:flex;align-items:center;justify-content:center;min-height:44px;font-weight:800;color:#2f6b4f}.seg a.on{background:#2f6b4f;color:#fff}.night .seg{border-color:#9cc06a}.night .seg a{color:#9cc06a}.night .seg a.on{background:#9cc06a;color:#06140f}
.fbtn{display:flex;justify-content:space-between;align-items:center;min-height:44px;padding:0 12px;border:1px solid #b9b090;background:#fff;font-weight:800}.fbtn em{font-style:normal;color:#3f6a24;font-size:14px}
.legend{display:flex;gap:14px;font-size:14px;margin:10px 0 2px;font-weight:700}.legend svg{width:16px;height:16px;vertical-align:-3px;margin-right:5px}
.pref{display:flex;justify-content:space-between;align-items:center;min-height:52px;border-bottom:1px solid #ece6d2;gap:8px}.tri{display:inline-grid;grid-auto-flow:column;border:2px solid #2f6b4f}.tri u{text-decoration:none;min-height:44px;display:flex;align-items:center;padding:0 9px;font-size:13.5px;font-weight:800;color:#2f6b4f;border-right:1px solid #2f6b4f}.tri u:last-child{border:0}.tri u.on{background:#2f6b4f;color:#fff}
.focus{margin-top:14px}.focus .btn{outline:3px solid #0d2a22;outline-offset:3px;font-size:14px;white-space:normal;text-align:center}
.ct2{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:6px}.ct2 th{text-align:left;border-bottom:2px solid #2f6b4f;padding:4px}.ct2 td{border-bottom:1px solid #ece6d2;padding:7px 4px;vertical-align:top}.ct2 td:nth-child(2){font-weight:900;color:#146c43;white-space:nowrap}.ct2 td:first-child{color:#8a2a1c;font-weight:800;white-space:nowrap}
"""

parts = [P1, P2, P3, P4, P5, P6, P7, P8]
cells = "".join(f'<div class="cell">{p}<div class="cap"><b>{t}</b><p>{c}</p></div></div>' for p, (t, c) in zip(parts, CAPS))
html = ("<!doctype html><meta charset=utf-8><title>fishin accessible wireframes</title>"
        '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&display=swap" rel="stylesheet">'
        f"<style>{CSS}</style><div class=lab>{cells}</div>")
io.open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT)
