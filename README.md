# Test technique Xarala — Développement Full-Stack

**Candidate : Ndeye Adama Diop**

Projet Django REST Framework couvrant la Partie A (webhook de paiement fiable)
et la Partie B2 (API d'inscription anti-doublons).

## Installation et lancement

```bash
python -m venv venv
venv\Scripts\activate       
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Lancer les tests (6 tests : 3 pour la partie A, 3 pour la B2) :

```bash
python manage.py test
```

## Partie A — Webhook de paiement (`POST /webhooks/payment`)

Reçoit les confirmations de paiement de l'agrégateur mobile money, marque la
commande payée et déclenche la livraison (simulée par un log).

### Mes choix techniques

- **Idempotence par contrainte d'unicité en base** (`unique=True` sur
  `transaction_id` dans `PaymentEvent`) : un simple `if` en Python laisserait
  passer deux webhooks simultanés (race condition). La contrainte en base est
  la seule garantie absolue car la base traite les écritures une par une.
  Le doublon lève `IntegrityError`, attrapée pour répondre « Déjà traité ».
- **Signature HMAC-SHA256** avec secret partagé (`payments/utils.py`),
  comparaison via `hmac.compare_digest` (protection contre les timing attacks).
- **Cohérence des montants** : montant du webhook ≠ montant de la commande →
  pas de validation, anomalie tracée dans les logs (montants + transaction_id).
- **Transaction atomique élargie** : l'enregistrement de l'événement ET le
  passage de la commande en `paid` sont dans un même bloc
  `transaction.atomic()` — un crash en plein traitement ne peut pas laisser un
  paiement à moitié traité (au rejeu de l'agrégateur, tout se refait proprement).
- **Réponses HTTP réfléchies** : l'agrégateur rejoue sur non-2xx, donc 200
  même pour un doublon ou une anomalie (= « bien reçu, dossier clos »). 403
  réservé à la signature invalide (ce n'est pas l'agrégateur qui parle).
- **DecimalField** pour les montants (jamais de float pour l'argent).

## Partie B2 : API d'inscription (`POST /registrations`)

Inscription à un événement gratuit à fort trafic : validation stricte,
anti-doublons, anti-abus, webhook sortant.

### Mes choix techniques

- **Validation** : champs requis, téléphone international (regex `^\+\d{8,15}$`),
  email (regex basique). Normalisation avant contrôle : trim, email en
  minuscules, espaces retirés du téléphone.
- **Anti-doublons** : `unique=True` sur email ET sur téléphone (l'énoncé :
  même email OU même téléphone = même personne). Même technique que la
  partie A ; réponse propre « Vous êtes déjà inscrit(e) » en 200.
- **Anti-abus** : throttling DRF 10 requêtes/minute par IP (429 au-delà).
  Simple et suffisant contre les bots basiques, sans sur-ingénierie.
  Stratégie complémentaire possible : champ honeypot caché dans le
  formulaire + CAPTCHA léger si le monitoring révèle des abus.
- **Webhook sortant** vers une URL d'automatisation mockée, avec retry
  simple (3 tentatives, timeout 5 s) et échecs tracés dans les logs.

## Ce que mes tests m'ont appris

Mon test du doublon a révélé un vrai bug : attraper une `IntegrityError`
sans bloc `transaction.atomic()` casse la transaction englobante
(TransactionManagementError dans les tests). Correction : le `create()` est
enveloppé dans son propre bloc atomique.

## Limites assumées / avec plus de temps

- **SQLite** pour la simplicité du test → PostgreSQL en production.
- **Secret en dur** dans settings.py → variable d'environnement en production.
- **Signature dans le corps du message** (comme spécifié par l'énoncé) → les
  agrégateurs réels la placent plutôt dans un header HTTP.
- **Livraison synchrone simulée par un log** → en production : file
  asynchrone (Celery) avec retries, dès que le volume ou les timeouts
  le justifient.
- **Statut `failed` non reporté** sur la commande → à ajouter pour informer
  le client d'un paiement échoué.
- **Validation email basique** → la validation ultime serait un email de
  confirmation (double opt-in).


## Transparence sur l'usage de l'IA

J'ai travaillé avec un assistant IA (Claude) comme guide pédagogique, à ma
demande selon une méthode stricte : ne jamais avancer tant qu'une étape
n'était pas comprise. Concrètement : explication des concepts (idempotence,
HMAC, transactions atomiques, race conditions) par analogies avant tout
code, décomposition du travail en petites étapes, aide au diagnostic des
erreurs, et relecture. L'IA me posait régulièrement des questions de
vérification (« pourquoi une contrainte d'unicité en base plutôt qu'un if ? »,
« que se passe-t-il au deuxième envoi du même webhook ? ») auxquelles je
devais répondre avec mes propres mots avant de continuer y compris une
simulation d'entretien technique sur la Partie A.

La structure du code (modèles, vues, tests) a été co-construite : l'IA
proposait, j'exécutais, je testais chaque scénario manuellement avec curl
avant de l'automatiser, et je me suis assurée de comprendre et pouvoir
justifier chaque décision technique (contrainte d'unicité vs if, codes HTTP
choisis, élargissement du bloc atomique, retry du webhook sortant). Les
réponses de la Partie C reflètent les leçons vécues pendant le développement.