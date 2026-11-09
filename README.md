# État des lieux autonome — mode d'emploi

Web app en **un seul fichier** (`index.html`), sans serveur ni abonnement.
Tout se passe sur le téléphone du locataire, qui vous envoie à la fin un **rapport PDF** et un **ZIP de photos**.

## 1. Mettre en ligne (une fois, ~10 min, gratuit)
La caméra ne marche qu'en **HTTPS** → GitHub Pages (ou Netlify Drop).
1. Créez un dépôt GitHub, par ex. `edl` (public).
2. Déposez `index.html` et le dossier `rooms/` (« Add file › Upload files »).
3. Settings › Pages › Branch `main` / `root` › Save.
4. Site : `https://<votre-compte>.github.io/edl/`
   Testez la démo : `https://<votre-compte>.github.io/edl/?room=demo`
   (à l'écran : une chambre dessinée, l'auto-déclenchement ne se fera évidemment pas sur votre vraie pièce).

## 2. Préparer une chambre (à chaque nouveau logement / chambre)
1. Ouvrez `…/edl/?admin`.
2. Identifiant non devinable, ex. `bp3-ch2-k7f4`, logement, chambre, contact (WhatsApp / e-mail).
3. « Ajouter des photos » : les **photos globales** de l'ancien état des lieux (depuis le Drive BP), dans l'ordre de la visite. Renommez-les si besoin.
4. Ajustez la liste des équipements (`*` = obligatoire, `|` sépare le conseil).
5. « Tester » pour essayer tout de suite, puis « Télécharger le .json ».
6. Déposez `bp3-ch2-k7f4.json` dans `rooms/` sur GitHub.

## 3. Envoyer au locataire
`https://<votre-compte>.github.io/edl/?room=bp3-ch2-k7f4`

Le locataire : nom → photos guidées (photo fantôme + pastille à ramener dans le cercle, déclenchement automatique quand c'est cadré et stable) → défauts → détecteur/équipements → signature → envoi PDF + ZIP par WhatsApp / mail.
S'il ferme l'appli, tout est conservé sur son téléphone : il reprend où il en était.

## 4. Boucle automatique pour le locataire suivant
Le ZIP reçu contient `reference_prochain_locataire/<id>.json` : ce sont les **nouvelles photos**, prêtes à servir de référence.
→ Remplacez simplement `rooms/<id>.json` par ce fichier à la prochaine entrée. Plus besoin du mode admin.

## Contenu du ZIP
- `EDL_<id>_<locataire>_<date>.pdf` — synthèse, équipements, certification signée, photos avant/après côte à côte, défauts
- `photos/` — vues pleine résolution (1600 px)
- `defauts/` — photos de défauts (avec emplacement + commentaire dans le PDF)
- `donnees.json` — données brutes (horodatages, cadrage auto, réponses)
- `reference_prochain_locataire/<id>.json`

## Bon à savoir
- Lien ouvert dans WhatsApp : si la caméra ne s'ouvre pas, l'appli propose « ouvrir dans Safari/Chrome » et bascule sinon sur l'appareil photo natif avec l'ancienne photo affichée en exemple.
- Les packs `rooms/*.json` sont lisibles par toute personne qui connaît l'identifiant : d'où l'identifiant aléatoire.
- Autre hébergement possible : `?r=<URL d'un .json accessible en CORS>`.
