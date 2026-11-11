#!/usr/bin/env python3
"""
Fabrique rooms/<id>.json (pack de référence) à partir des photos d'un précédent
état des lieux rangé sur le Drive BP IMMO.

Arborescence attendue (Drive BP monté par Google Drive pour ordinateur) :
    H:\\My Drive\\BP<n> CH<m>\\EDL <Prénom>\\*.HEIC|*.jpg

Exemples :
    python tools/drive_to_pack.py "BP2 CH4" --publie             # dernier dossier EDL, mode entrée, mis en ligne
    python tools/drive_to_pack.py "BP2 CH4" --mode sortie --lease 1796387
    python tools/drive_to_pack.py "BP2 CH4" --edl "EDL Aubin" --max 15
    python tools/drive_to_pack.py "D:\\photos\\EDL x" --logement BP9 --chambre CH1

Dépendances : Python 3 + Pillow, et ffmpeg (≥ 7) dans le PATH pour les HEIC d'iPhone.
"""
import argparse, base64, io, json, os, re, secrets, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageOps

DRIVE = Path(os.environ.get("BP_DRIVE", r"H:\My Drive"))
IMG_EXT = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp"}


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:40] or "x"


def open_image(path: Path) -> Image.Image:
    if path.suffix.lower() in (".heic", ".heif"):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "x.jpg"
            # ffmpeg ≥ 7 assemble la grille de tuiles HEIF (stream_group) en une seule image
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-frames:v", "1", "-q:v", "2", str(out)],
                               capture_output=True, text=True)
            if r.returncode or not out.exists():
                raise RuntimeError(f"ffmpeg n'a pas pu lire {path.name} : {r.stderr.strip()[:200]}")
            img = Image.open(out); img.load(); return img.convert("RGB")
    img = Image.open(path)
    return ImageOps.exif_transpose(img).convert("RGB")


def to_data_url(img: Image.Image, max_side=1200, q=78) -> str:
    img = img.copy(); img.thumbnail((max_side, max_side), Image.LANCZOS)
    buf = io.BytesIO(); img.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def pick_edl_dir(room_dir: Path, name: str | None) -> Path:
    if name:
        d = room_dir / name
        if not d.is_dir(): sys.exit(f"Dossier introuvable : {d}")
        return d
    subs = [d for d in room_dir.iterdir() if d.is_dir() and d.name.lower().startswith("edl")]
    has_imgs = lambda d: any(f.suffix.lower() in IMG_EXT for f in d.iterdir())
    subs = [d for d in subs if has_imgs(d)]
    if not subs:
        if has_imgs(room_dir): return room_dir
        sys.exit(f"Aucun dossier « EDL … » avec des photos dans {room_dir}")
    # le plus récent = date de modification la plus récente de ses photos
    return max(subs, key=lambda d: max(f.stat().st_mtime for f in d.iterdir() if f.suffix.lower() in IMG_EXT))


def main():
    for st in (sys.stdout, sys.stderr): st.reconfigure(encoding="utf-8", errors="replace")  # console Windows (cp1252)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("room", help='nom du dossier sur le Drive BP (ex. "BP2 CH4") ou chemin complet')
    ap.add_argument("--edl", help='sous-dossier à utiliser (défaut : le plus récent « EDL … »)')
    ap.add_argument("--mode", choices=["entree", "sortie"], default="entree")
    ap.add_argument("--lease", type=int, help="ID du bail Rentila")
    ap.add_argument("--property", type=int, help="ID du bien Rentila")
    ap.add_argument("--id", help="identifiant du pack (défaut : bp2-ch4-<aléatoire>)")
    ap.add_argument("--logement"); ap.add_argument("--chambre"); ap.add_argument("--adresse", default="")
    ap.add_argument("--max", type=int, default=30, help="nombre max de photos (réparties uniformément)")
    ap.add_argument("--whatsapp", default=""); ap.add_argument("--email", default=""); ap.add_argument("--contact", default="")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "rooms"))
    ap.add_argument("--publie", action="store_true", help="publie le pack sur le site (git add + commit + push)")
    a = ap.parse_args()

    room_dir = Path(a.room) if Path(a.room).is_absolute() else DRIVE / a.room
    if not room_dir.is_dir(): sys.exit(f"Introuvable : {room_dir}")
    edl = pick_edl_dir(room_dir, a.edl)
    files = sorted((f for f in edl.iterdir() if f.suffix.lower() in IMG_EXT and not f.name.startswith(".")), key=lambda f: f.name)
    if len(files) > a.max:  # sous-échantillonnage régulier
        step = len(files) / a.max; files = [files[int(i * step)] for i in range(a.max)]

    m = re.match(r"(BP\s*\d+)\s*(CH\s*\d+)", room_dir.name, re.I)
    logement = a.logement or (m.group(1).upper().replace(" ", "") if m else room_dir.name)
    chambre = a.chambre or (("Chambre " + re.sub(r"\D", "", m.group(2))) if m else "Chambre")
    pid = slug(a.id) if a.id else f"{slug(room_dir.name)}-{secrets.token_hex(2)}"

    refs = []
    for i, f in enumerate(files, 1):
        print(f"  [{i}/{len(files)}] {f.name}", flush=True)
        try:
            refs.append({"id": f"p{i:02d}", "label": f"Vue {i}", "hint": "Reprenez exactement ce cadrage", "src": to_data_url(open_image(f))})
        except Exception as e:
            print(f"    ignorée : {e}")
    pack = {"id": pid, "mode": a.mode, "logement": logement, "chambre": chambre, "adresse": a.adresse, "proprietaire": "BP IMMO",
            "contact": {"nom": a.contact, "whatsapp": a.whatsapp, "email": a.email},
            "rentila": {"lease_id": a.lease, "property_id": a.property},
            "source": f"{edl.name} (Drive BP — {room_dir.name})", "refs": refs}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{pid}.json"
    dest.write_text(json.dumps(pack, ensure_ascii=False), encoding="utf-8")
    size = dest.stat().st_size / 1e6
    print(f"\n✓ {dest}  ({len(refs)} photos, {size:.1f} Mo, source : {edl})")
    print("  Renommez les vues dans …/?admin si besoin, ou directement dans le .json (champ label).")
    repo = Path(__file__).resolve().parent.parent
    if a.publie:
        git = lambda *c: subprocess.run(["git", "-C", str(repo), *c], check=True)
        git("add", str(dest)); git("commit", "-q", "-m", f"Ajoute le pack de référence {room_dir.name} ({edl.name})"); git("push", "-q")
        print("  Publié : le lien marche d'ici 1 à 2 minutes (le temps que GitHub Pages se mette à jour).")
    else:
        print("  ⚠ PAS ENCORE EN LIGNE : relancez avec --publie, ou faites git add / commit / push.")
    print(f"  Lien locataire : https://madofly35.github.io/edl/?room={pid}" + ("&sortie" if a.mode == "sortie" else ""))


if __name__ == "__main__":
    main()
