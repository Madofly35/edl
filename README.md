# État des lieux autonome BP Immo — mode d'emploi

Web app en **un seul fichier** (`index.html`), sans serveur ni abonnement.
Tout se passe sur le téléphone du locataire, qui vous envoie à la fin un **rapport PDF** et un **ZIP de photos**.

## Nouveautés (nov. 2026)

### Charte BP Immo
Logo proposé par Olivier (`assets/logo.png`, `mark.png`, icônes d'écran d'accueil), noir + or sur fond ivoire,
titres en Cormorant Garamond. Le PDF porte le logo en en-tête.

### Intelligence embarquée (tout se passe sur le téléphone)
Chaque photo est vérifiée juste après la prise :
- **netteté** (variance du laplacien, comparée à la photo de référence) et **exposition** (trop sombre / contre-jour) ;
- **bon endroit** : corrélation des contours + similarité MobileNet avec la photo de référence ;
- **bon objet** (propreté) : MobileNet reconnaît four, évier, lavabo, toilettes, douche… (mots-clés modifiables).
En cas de doute : écran « Refaire / Garder quand même ». Rien n'est bloquant ; le verdict est écrit dans le PDF,
`donnees.json` et les observations Rentila. Sans réseau, le modèle ne se charge pas et seuls netteté/exposition/contours s'appliquent.

### État des lieux de sortie + propreté
Lien `…/edl/?room=<id>&sortie` (ou `"mode": "sortie"` dans le pack).
Étape **Propreté** : four, micro-ondes, plaques, hotte, frigo, lave-vaisselle, évier, toilettes, lavabo, douche,
sol, placard, poubelles — photo + « Propre / À reprendre » + commentaire, nombre de clés rendues.
Liste modifiable dans `?admin` ou dans le pack (`proprete`). Les photos de propreté d'une sortie deviennent la
référence « à l'entrée » du locataire suivant.

### Photos de référence depuis le Drive BP
```
python tools/drive_to_pack.py "BP2 CH4" --publie              # dernier dossier « EDL … », HEIC compris, mis en ligne
python tools/drive_to_pack.py "BP2 CH4" --mode sortie --lease 1796387 --max 15 --publie
```
Lit `H:\My Drive\BP<n> CH<m>\EDL <Prénom>\`, convertit (ffmpeg pour les HEIC), réduit à 1200 px et écrit
`rooms/<id>.json`. Les vues s'appellent « Vue 1… » : renommez-les dans le .json si besoin.

### Import dans Rentila et signature officielle
Le ZIP du locataire contient `rentila.json` (corps `create_handover` : pièces, équipements avec état d'usure,
propreté, clés, observations, contrôle auto).
1. `python tools/zip_to_rentila.py <ZIP>` → `rentila_create.json` + `rentila_photos.json` ;
2. demander à Claude « importe l'EDL de X dans Rentila » (skill `edl-rentila`) : brouillon créé via l'API Rentila,
   photos déposées pièce par pièce dans le formulaire Rentila ;
3. **vous** lancez la signature dans Rentila (onglet Signature : votre signature + code SMS) — l'API Rentila
   ne permet pas encore de la démarrer. Le locataire reçoit l'invitation par e-mail/SMS.


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
