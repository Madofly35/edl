#!/usr/bin/env python3
"""
Prépare l'import dans Rentila d'un état des lieux reçu du locataire (ZIP de l'appli).

    python tools/zip_to_rentila.py "C:\\Users\\Pierre\\Downloads\\EDL_xxx_photos.zip" [--lease 1796387]

- décompresse le ZIP dans un dossier voisin (EDL_xxx_photos/) ;
- écrit rentila_create.json : corps exact pour create_handover (MCP / API Rentila),
  sans les champs internes (_photos) ;
- écrit rentila_photos.json : pour chaque pièce, la liste des photos à déposer
  (chemins absolus, par lots de ≤ 9 Mo pour l'outil d'upload du navigateur).

La suite (création du brouillon, dépôt des photos, lancement de la signature)
est décrite dans le skill « edl-rentila » et dans le README.
"""
import argparse, json, sys, zipfile
from pathlib import Path

LOT_MAX = 9_000_000  # octets par lot d'upload


def main():
    for st in (sys.stdout, sys.stderr): st.reconfigure(encoding="utf-8", errors="replace")  # console Windows (cp1252)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zip")
    ap.add_argument("--lease", type=int, help="ID du bail Rentila (si absent du pack)")
    a = ap.parse_args()

    z = Path(a.zip)
    if not z.is_file(): sys.exit(f"ZIP introuvable : {z}")
    out = z.with_suffix("")
    with zipfile.ZipFile(z) as zf:
        for m in zf.infolist():
            # protection contre les chemins sortant du dossier (« zip slip »)
            target = (out / m.filename).resolve()
            if not str(target).startswith(str(out.resolve())): sys.exit(f"Chemin suspect dans le ZIP : {m.filename}")
        zf.extractall(out)

    rj = out / "rentila.json"
    if not rj.exists(): sys.exit("rentila.json absent : ZIP produit par une ancienne version de l'appli ?")
    payload = json.loads(rj.read_text(encoding="utf-8"))
    if a.lease: payload["lease_id"] = a.lease

    photos = []
    for room in payload["rooms"]:
        files = [str((out / f).resolve()) for f in room.pop("_photos", []) if (out / f).exists()]
        lots, cur, size = [], [], 0
        for f in files:
            s = Path(f).stat().st_size
            if cur and size + s > LOT_MAX: lots.append(cur); cur, size = [], 0
            cur.append(f); size += s
        if cur: lots.append(cur)
        photos.append({"room": room["name"], "lots": lots, "count": len(files)})
    if not payload.get("lease_id"): payload.pop("lease_id", None)

    (out / "rentila_create.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "rentila_photos.json").write_text(json.dumps(photos, ensure_ascii=False, indent=2), encoding="utf-8")
    pdf = next(out.glob("*.pdf"), None)
    print(f"Dossier         : {out}")
    print(f"Type            : {payload['handover_type']}   bail : {payload.get('lease_id') or 'À CHOISIR'}")
    print(f"Nom             : {payload['name']}")
    print(f"Pièces          : " + ", ".join(f"{p['room']} ({p['count']} photos)" for p in photos))
    print(f"Rapport PDF     : {pdf}")
    print(f"→ {out / 'rentila_create.json'}\n→ {out / 'rentila_photos.json'}")


if __name__ == "__main__":
    main()
