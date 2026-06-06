"""database.py — SQLite + WAL, all data access"""
import sqlite3, os
from datetime import date, timedelta

def _get_db_path():
    """
    Palauttaa tietokannan polun oikein sekä kehitys- että PyInstaller-ympäristössä.

    PyInstaller --onefile purkaa tiedostot väliaikaiseen _MEIxxxxxx-kansioon
    joka poistetaan sulkemisen yhteydessä. Tietokanta täytyy tallentaa
    pysyvaan paikkaan: AppData/Local/BallPythonDB/ballpython.db

    Kehitysymparistossa (run.bat / python main.py) kaytetaan samaa
    AppData-polkua jotta data on aina samassa paikassa.
    """
    # AppData\Local\BallPythonDB\ — pysyvä, ei vaadi admin-oikeuksia
    app_data = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    data_dir = os.path.join(app_data, "BallPythonDB")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "ballpython.db")

DB_PATH = _get_db_path()

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")   # off — we manage integrity manually
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS animals (
        id            TEXT PRIMARY KEY,
        name          TEXT,
        sex           TEXT,
        dob           TEXT,
        acquired      TEXT,
        price         REAL,
        breeder       TEXT,
        morph         TEXT,
        het           TEXT,
        genetic_notes TEXT,
        rack          TEXT,
        rack_level    TEXT,
        weight_g      REAL,
        status        TEXT DEFAULT 'Active',
        notes         TEXT,
        sire_id       TEXT,
        dam_id        TEXT,
        feed_interval INTEGER DEFAULT 7,
        created_at    TEXT DEFAULT (date('now'))
    );
    CREATE TABLE IF NOT EXISTS husbandry (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        date           TEXT NOT NULL,
        animal_id      TEXT NOT NULL,
        event_type     TEXT NOT NULL,
        prey_type      TEXT,
        prey_weight    REAL,
        fed            TEXT,
        refusal_reason TEXT,
        weight_g       REAL,
        length_cm      REAL,
        in_blue        TEXT,
        complete_shed  TEXT,
        shed_date      TEXT,
        defecation     TEXT,
        cleaning       TEXT,
        logged_by      TEXT,
        notes          TEXT
    );
    CREATE TABLE IF NOT EXISTS health (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        date          TEXT NOT NULL,
        animal_id     TEXT NOT NULL,
        event_type    TEXT NOT NULL,
        description   TEXT,
        medication    TEXT,
        dosage        TEXT,
        duration_days INTEGER,
        vet           TEXT,
        next_checkup  TEXT,
        mite_check    TEXT,
        outcome       TEXT,
        cost          REAL,
        notes         TEXT
    );
    CREATE TABLE IF NOT EXISTS clutches (
        id               TEXT PRIMARY KEY,
        season           TEXT,
        sire_id          TEXT,
        dam_id           TEXT,
        pairing_start    TEXT,
        lock_date        TEXT,
        lock_count       INTEGER,
        pairing_end      TEXT,
        ovulation_date   TEXT,
        prelay_shed      TEXT,
        lay_date         TEXT,
        total_eggs       INTEGER,
        good_eggs        INTEGER,
        slugs            INTEGER,
        incubation_temp  REAL,
        humidity_pct     REAL,
        incubator        TEXT,
        incubation_start TEXT,
        hatch_date_actual TEXT,
        hatchling_count  INTEGER,
        status           TEXT DEFAULT 'Pairing',
        notes            TEXT
    );
    CREATE TABLE IF NOT EXISTS hatchlings (
        id              TEXT PRIMARY KEY,
        clutch_id       TEXT,
        dam_id          TEXT,
        sire_id         TEXT,
        hatch_date      TEXT,
        birth_weight_g  REAL,
        sex             TEXT,
        confirmed_morph TEXT,
        possible_morph  TEXT,
        het_genes       TEXT,
        first_shed      TEXT,
        first_feed      TEXT,
        prey_offered_g  REAL,
        status          TEXT DEFAULT 'Available',
        sale_price      REAL,
        buyer_name      TEXT,
        buyer_contact   TEXT,
        sale_date       TEXT,
        paid            TEXT,
        notes           TEXT
    );
    """)
    # Migration: add feed_interval if missing
    try:
        conn.execute("ALTER TABLE animals ADD COLUMN feed_interval INTEGER DEFAULT 7")
        conn.commit()
    except: pass
    # Migration: remove microchip if present (ignored on read, harmless)
    conn.commit()
    conn.close()

def fetchall(sql, params=()):
    conn = get_conn()
    try:    return conn.execute(sql, params).fetchall()
    finally: conn.close()

def fetchone(sql, params=()):
    conn = get_conn()
    try:    return conn.execute(sql, params).fetchone()
    finally: conn.close()

def execute(sql, params=()):
    conn = get_conn()
    try:
        conn.execute(sql, params)
        conn.commit()
    finally: conn.close()

# ── Animals ────────────────────────────────────────────────────────────────────
ANIMAL_COLS = ["id","name","sex","dob","acquired","price","breeder","morph","het",
               "genetic_notes","rack","rack_level","weight_g","status","notes",
               "sire_id","dam_id","feed_interval"]

def get_all_animals(status_filter=None):
    if status_filter and status_filter != "All":
        return fetchall("SELECT * FROM animals WHERE status=? ORDER BY id",(status_filter,))
    return fetchall("SELECT * FROM animals ORDER BY id")

def get_animal(aid):
    if not aid: return None
    return fetchone("SELECT * FROM animals WHERE id=?", (aid,))

def save_animal(data: dict, is_new=True):
    clean = {}
    for k in ANIMAL_COLS:
        v = data.get(k)
        clean[k] = None if v in ("", None) else v
    for f in ("price","weight_g"):
        if clean.get(f) is not None:
            try:    clean[f] = float(str(clean[f]))
            except: clean[f] = None
    if clean.get("feed_interval") is not None:
        try:    clean["feed_interval"] = int(str(clean["feed_interval"]))
        except: clean["feed_interval"] = 7
    conn = get_conn()
    try:
        if is_new:
            cols = list(clean.keys())
            conn.execute(f"INSERT INTO animals ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
                         list(clean.values()))
        else:
            aid = clean.pop("id")
            sets = ",".join([f"{c}=?" for c in clean])
            conn.execute(f"UPDATE animals SET {sets} WHERE id=?",
                         list(clean.values()) + [aid])
        conn.commit()
    finally: conn.close()

def delete_animal(aid):
    execute("DELETE FROM animals WHERE id=?", (aid,))

def get_animal_ids(status="Active"):
    rows = fetchall(f"SELECT id,name FROM animals WHERE status=? ORDER BY id",(status,))
    return [f"{r['id']} – {r['name'] or ''}" for r in rows]

def resolve_combo(val):
    """'BP-001 – Monty' → 'BP-001', or return as-is"""
    if val and " – " in str(val):
        return val.split(" – ")[0].strip()
    return val or None

# ── Husbandry ──────────────────────────────────────────────────────────────────
HUS_COLS = ["date","animal_id","event_type","prey_type","prey_weight","fed",
            "refusal_reason","weight_g","length_cm","in_blue","complete_shed",
            "shed_date","defecation","cleaning","logged_by","notes"]

def get_husbandry(animal_id=None, limit=500):
    if animal_id:
        return fetchall(
            "SELECT h.*,a.name AS animal_name FROM husbandry h "
            "LEFT JOIN animals a ON h.animal_id=a.id "
            "WHERE h.animal_id=? ORDER BY h.date DESC LIMIT ?", (animal_id,limit))
    return fetchall(
        "SELECT h.*,a.name AS animal_name FROM husbandry h "
        "LEFT JOIN animals a ON h.animal_id=a.id "
        "ORDER BY h.date DESC LIMIT ?", (limit,))

def save_husbandry(data: dict):
    clean = {k: (data.get(k) or None) for k in HUS_COLS}
    for f in ("prey_weight","weight_g","length_cm"):
        if clean.get(f):
            try:    clean[f] = float(clean[f])
            except: clean[f] = None
    conn = get_conn()
    try:
        hid = data.get("id")
        if hid:
            sets = ",".join([f"{c}=?" for c in clean])
            conn.execute(f"UPDATE husbandry SET {sets} WHERE id=?",
                         list(clean.values())+[hid])
        else:
            cols = list(clean.keys())
            conn.execute(f"INSERT INTO husbandry ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
                         list(clean.values()))
        conn.commit()
    finally: conn.close()

def delete_husbandry(hid):
    execute("DELETE FROM husbandry WHERE id=?", (hid,))

# ── Health ─────────────────────────────────────────────────────────────────────
HEALTH_COLS = ["date","animal_id","event_type","description","medication","dosage",
               "duration_days","vet","next_checkup","mite_check","outcome","cost","notes"]

def get_health(animal_id=None, limit=500):
    if animal_id:
        return fetchall(
            "SELECT h.*,a.name AS animal_name FROM health h "
            "LEFT JOIN animals a ON h.animal_id=a.id "
            "WHERE h.animal_id=? ORDER BY h.date DESC LIMIT ?", (animal_id,limit))
    return fetchall(
        "SELECT h.*,a.name AS animal_name FROM health h "
        "LEFT JOIN animals a ON h.animal_id=a.id ORDER BY h.date DESC LIMIT ?", (limit,))

def save_health(data: dict):
    clean = {k: (data.get(k) or None) for k in HEALTH_COLS}
    if clean.get("cost"):
        try:    clean["cost"] = float(clean["cost"])
        except: clean["cost"] = None
    if clean.get("duration_days"):
        try:    clean["duration_days"] = int(clean["duration_days"])
        except: clean["duration_days"] = None
    conn = get_conn()
    try:
        hid = data.get("id")
        if hid:
            sets = ",".join([f"{c}=?" for c in clean])
            conn.execute(f"UPDATE health SET {sets} WHERE id=?",
                         list(clean.values())+[hid])
        else:
            cols = list(clean.keys())
            conn.execute(f"INSERT INTO health ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
                         list(clean.values()))
        conn.commit()
    finally: conn.close()

def delete_health(hid):
    execute("DELETE FROM health WHERE id=?", (hid,))

# ── Clutches ───────────────────────────────────────────────────────────────────
CLUTCH_COLS = ["id","season","sire_id","dam_id","pairing_start","lock_date","lock_count",
               "pairing_end","ovulation_date","prelay_shed","lay_date","total_eggs",
               "good_eggs","slugs","incubation_temp","humidity_pct","incubator",
               "incubation_start","hatch_date_actual","hatchling_count","status","notes"]

def get_all_clutches():
    return fetchall("""
        SELECT c.*,s.name AS sire_name,s.morph AS sire_morph,
               d.name AS dam_name,d.morph AS dam_morph
        FROM clutches c
        LEFT JOIN animals s ON c.sire_id=s.id
        LEFT JOIN animals d ON c.dam_id=d.id
        ORDER BY c.lay_date DESC,c.pairing_start DESC""")

def get_clutch(cid):
    return fetchone("SELECT * FROM clutches WHERE id=?", (cid,))

def get_clutch_ids():
    return [r["id"] for r in fetchall("SELECT id FROM clutches ORDER BY id")]

def save_clutch(data: dict, is_new=True):
    clean = {k: (data.get(k) or None) for k in CLUTCH_COLS}
    for f in ("lock_count","total_eggs","good_eggs","slugs","hatchling_count"):
        if clean.get(f):
            try:    clean[f] = int(str(clean[f]))
            except: clean[f] = None
    for f in ("incubation_temp","humidity_pct"):
        if clean.get(f):
            try:    clean[f] = float(str(clean[f]))
            except: clean[f] = None
    conn = get_conn()
    try:
        if is_new:
            cols = list(clean.keys())
            conn.execute(f"INSERT INTO clutches ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
                         list(clean.values()))
        else:
            cid = clean.pop("id")
            sets = ",".join([f"{c}=?" for c in clean])
            conn.execute(f"UPDATE clutches SET {sets} WHERE id=?",
                         list(clean.values())+[cid])
        conn.commit()
    finally: conn.close()

def delete_clutch(cid):
    execute("DELETE FROM clutches WHERE id=?", (cid,))

# ── Hatchlings ─────────────────────────────────────────────────────────────────
HATCH_COLS = ["id","clutch_id","dam_id","sire_id","hatch_date","birth_weight_g","sex",
              "confirmed_morph","possible_morph","het_genes","first_shed","first_feed",
              "prey_offered_g","status","sale_price","buyer_name","buyer_contact",
              "sale_date","paid","notes"]

def get_hatchlings(clutch_id=None):
    if clutch_id:
        return fetchall("SELECT * FROM hatchlings WHERE clutch_id=? ORDER BY id", (clutch_id,))
    return fetchall("SELECT * FROM hatchlings ORDER BY hatch_date DESC,id")

def save_hatchling(data: dict, is_new=True):
    clean = {k: (data.get(k) or None) for k in HATCH_COLS}
    for f in ("birth_weight_g","prey_offered_g","sale_price"):
        if clean.get(f):
            try:    clean[f] = float(str(clean[f]))
            except: clean[f] = None
    conn = get_conn()
    try:
        if is_new:
            cols = list(clean.keys())
            conn.execute(f"INSERT INTO hatchlings ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
                         list(clean.values()))
        else:
            hid = clean.pop("id")
            sets = ",".join([f"{c}=?" for c in clean])
            conn.execute(f"UPDATE hatchlings SET {sets} WHERE id=?",
                         list(clean.values())+[hid])
        conn.commit()
    finally: conn.close()

def delete_hatchling(hid):
    execute("DELETE FROM hatchlings WHERE id=?", (hid,))

def next_hatchling_id(clutch_id):
    """Return next available hatchling number for a clutch."""
    rows = fetchall("SELECT id FROM hatchlings WHERE clutch_id=?", (clutch_id,))
    nums = []
    for r in rows:
        try:
            suffix = r["id"].replace(clutch_id,"").lstrip("-")
            nums.append(int(suffix))
        except: pass
    return max(nums)+1 if nums else 1

# ── Pedigree / CoI ─────────────────────────────────────────────────────────────
def get_ancestors(animal_id, depth=4):
    result = {}
    def recurse(aid, gen, path):
        if not aid or gen > depth: return
        a = get_animal(aid)
        if not a: return
        result[path] = dict(a)
        recurse(a["sire_id"], gen+1, path+"S")
        recurse(a["dam_id"],  gen+1, path+"D")
    recurse(animal_id, 1, "")
    return result

def calc_coi(sire_id, dam_id, depth=5):
    sa = _anc_set(sire_id, depth)
    da = _anc_set(dam_id,  depth)
    coi = 0.0
    for anc in set(sa) & set(da):
        for sp in sa[anc]:
            for dp in da[anc]:
                coi += 0.5 ** (len(sp)+len(dp)+1)
    return coi

def _anc_set(aid, depth, path="", seen=None):
    if seen is None: seen = {}
    if not aid or len(path) >= depth: return seen
    a = get_animal(aid)
    if not a: return seen
    seen.setdefault(aid,[]).append(path)
    _anc_set(a["sire_id"], depth, path+"S", seen)
    _anc_set(a["dam_id"],  depth, path+"D", seen)
    return seen

# ── Dashboard queries ──────────────────────────────────────────────────────────
def get_summary():
    conn = get_conn()
    try:
        def q(sql): return conn.execute(sql).fetchone()[0]
        return {
            "total_active":   q("SELECT COUNT(*) FROM animals WHERE status='Active'"),
            "males":          q("SELECT COUNT(*) FROM animals WHERE status='Active' AND sex='Male'"),
            "females":        q("SELECT COUNT(*) FROM animals WHERE status='Active' AND sex='Female'"),
            "total_clutches": q("SELECT COUNT(*) FROM clutches"),
            "active_clutches":q("SELECT COUNT(*) FROM clutches WHERE status NOT IN ('Hatched','Failed')"),
            "total_eggs":     q("SELECT COALESCE(SUM(total_eggs),0) FROM clutches"),
            "good_eggs":      q("SELECT COALESCE(SUM(good_eggs),0) FROM clutches"),
            "total_hatch":    q("SELECT COALESCE(SUM(hatchling_count),0) FROM clutches"),
            "available":      q("SELECT COUNT(*) FROM hatchlings WHERE status='Available'"),
            "reserved":       q("SELECT COUNT(*) FROM hatchlings WHERE status='Reserved'"),
            "sold_count":     q("SELECT COUNT(*) FROM hatchlings WHERE status='Sold'"),
            "sold_revenue":   q("SELECT COALESCE(SUM(sale_price),0) FROM hatchlings WHERE status='Sold'"),
            "feed_30":        q("SELECT COUNT(*) FROM husbandry WHERE event_type='Feeding' AND fed='Yes' AND date>=date('now','-30 days')"),
            "refusal_30":     q("SELECT COUNT(*) FROM husbandry WHERE event_type='Feeding' AND fed='No' AND date>=date('now','-30 days')"),
        }
    finally: conn.close()

def get_feeding_alerts():
    """
    Returns list of dicts for animals whose next feeding is due or overdue.
    Uses per-animal feed_interval (default 7 days).
    Warning shown 3 days before due date.
    """
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT a.id, a.name, a.morph, a.feed_interval,
                   MAX(h.date) AS last_fed,
                   CAST(julianday('now') - julianday(MAX(h.date)) AS INTEGER) AS days_since
            FROM animals a
            LEFT JOIN husbandry h ON a.id=h.animal_id
                AND h.event_type='Feeding' AND h.fed='Yes'
            WHERE a.status='Active'
            GROUP BY a.id
        """).fetchall()
    finally:
        conn.close()

    alerts = []
    today = date.today()
    for r in rows:
        interval  = r["feed_interval"] or 7
        last_fed  = r["last_fed"]
        days_since= r["days_since"]

        if last_fed is None:
            next_date  = None
            days_until = None
            level      = "overdue"
            msg        = "Never fed"
        else:
            try:
                last_date  = date.fromisoformat(last_fed)
                next_date  = last_date + timedelta(days=interval)
                days_until = (next_date - today).days
            except:
                next_date = None; days_until = None; level = "overdue"; msg = "Date error"
                alerts.append({"id":r["id"],"name":r["name"],"morph":r["morph"],
                                "last_fed":last_fed,"next_due":str(next_date) if next_date else "",
                                "days_until":days_until,"days_since":days_since,
                                "interval":interval,"level":level,"msg":msg})
                continue

            if days_until < 0:
                level = "overdue"
                msg   = f"Overdue by {-days_until} day(s)"
            elif days_until <= 3:
                level = "warning"
                msg   = f"Due in {days_until} day(s)"
            else:
                continue   # fine, skip

        alerts.append({
            "id":r["id"],"name":r["name"],"morph":r["morph"],
            "last_fed":last_fed or "Never","next_due":str(next_date) if next_date else "—",
            "days_until":days_until,"days_since":days_since,
            "interval":interval,"level":level,"msg":msg,
        })
    alerts.sort(key=lambda x: (x["level"]!="overdue", x["days_until"] or -999))
    return alerts

def get_latest_weights():
    """Latest weight entry per animal."""
    return fetchall("""
        SELECT a.id, a.name, h.weight_g, h.date
        FROM animals a
        JOIN husbandry h ON a.id=h.animal_id AND h.event_type='Weight Check'
        WHERE a.status='Active'
          AND h.date = (
            SELECT MAX(h2.date) FROM husbandry h2
            WHERE h2.animal_id=a.id AND h2.event_type='Weight Check'
          )
        ORDER BY a.id
    """)

def get_active_clutches():
    return fetchall("""
        SELECT c.id,c.status,c.lay_date,c.good_eggs,c.hatchling_count,
               c.hatch_date_actual,c.incubation_start,
               s.name AS sire_name, d.name AS dam_name
        FROM clutches c
        LEFT JOIN animals s ON c.sire_id=s.id
        LEFT JOIN animals d ON c.dam_id=d.id
        WHERE c.status NOT IN ('Hatched','Failed')
        ORDER BY c.lay_date DESC
    """)

# ── CSV export / import ────────────────────────────────────────────────────────
import csv, io

def export_csv(table):
    """Export table to CSV string."""
    table_map = {
        "animals":    "SELECT * FROM animals",
        "husbandry":  "SELECT * FROM husbandry",
        "health":     "SELECT * FROM health",
        "clutches":   "SELECT * FROM clutches",
        "hatchlings": "SELECT * FROM hatchlings",
    }
    rows = fetchall(table_map.get(table, f"SELECT * FROM {table}"))
    if not rows: return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=rows[0].keys())
    w.writeheader()
    for r in rows:
        w.writerow(dict(r))
    return buf.getvalue()

def import_csv(table, csv_text):
    """Import CSV string into table, skipping duplicates."""
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    if not rows: return 0
    cols = rows[0].keys()
    ph = ",".join(["?"]*len(cols))
    conn = get_conn()
    imported = 0
    try:
        for row in rows:
            vals = [row.get(c) or None for c in cols]
            try:
                conn.execute(f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) VALUES ({ph})", vals)
                imported += 1
            except: pass
        conn.commit()
    finally: conn.close()
    return imported

if __name__ == "__main__":
    init_db()
    print("DB OK:", DB_PATH)
