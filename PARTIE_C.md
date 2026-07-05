# Partie C — Réflexion système

## 1. Production : « j'ai payé mais je n'ai pas accès au cours »
Ma démarche, étape par étape :

Identifier la transaction : je demande au client une référence (numéro de commande, email, heure du paiement, reçu Wave/OM).
Vérifier la commande en base : quel est son statut ? pending ou paid ?
Vérifier le registre PaymentEvent : un événement existe-t-il pour cette commande ?

Aucun événement → le webhook n'est jamais arrivé (panne agrégateur, mauvaise URL, incident réseau). Je vérifie le dashboard de l'agrégateur : le paiement y est-il confirmé ? Si oui, je demande un rejeu du webhook ou je régularise manuellement.
Événement présent mais commande pending : je consulte les logs : y a-t-il une anomalie tracée (montant incohérent ?) ou une erreur applicative au moment du traitement ?
Commande paid mais pas d'accès le problème est en aval, dans la livraison : je vérifie les logs de livraison et le système d'accès aux cours.

Corriger et prévenir : je régularise le client immédiatement (débloquer l'accès), puis je traite la cause racine pour que ça ne se reproduise pas.

## 2. Performance : 3 leviers pour une page Next.js rapide en 3G
Les images : c'est le poste le plus lourd. Formats modernes (WebP/AVIF), dimensionnement adapté au mobile, lazy loading. le composant next/image fait tout ça. Sur une page produit, ça peut diviser le poids par 3-5.

La stratégie de rendu : SSG/ISR plutôt que SSR : générer les pages à l'avance (statiques) et les servir depuis un CDN avec un point de présence proche de l'Afrique de l'Ouest. En 3G, chaque aller-retour serveur coûte cher ; du HTML pré-généré arrive vite et s'affiche immédiatement.

Réduire le JavaScript : privilégier les Server Components (zéro JS envoyé au client par défaut), charger les composants lourds en dynamique (next/dynamic), éviter les librairies volumineuses. Moins de JS = moins à télécharger ET moins à exécuter sur des téléphones d'entrée de gamme, souvent plus limités par le CPU que par le réseau.

## 3. Qualité : stratégie de tests pour 2 devs sans QA
Concentrer les tests automatisés là où une régression coûte de l'argent ou de la confiance : les flux critiques, paiements, inscriptions, accès aux cours. C'est ce que j'ai appliqué dans ce test : chaque protection du webhook (rejeu, signature, montant) a son test, car un bug là egale perte financière directe.
Le curseur que je propose : tests unitaires/intégration systématiques sur la logique métier critique et les cas limites connus ; pas de course au "100% de couverture" sur le CRUD simple ou l'UI. le coût de maintenance dépasserait le bénéfice pour une petite équipe. En complément : revue de code croisée entre les 2 devs (chaque PR relue par l'autre), les tests lancés automatiquement avant chaque déploiement, et un test manuel rapide des parcours clés avant les mises en production importantes.
## 4. Dette : un raccourci acceptable et son signal de remboursement
Le raccourci : livrer la livraison d'accès aux cours en traitement synchrone (directement dans la requête du webhook, comme mon appel sortant avec retry simple), plutôt que de mettre en place une file d'attente asynchrone (Celery + Redis). En startup, c'est acceptable : simple, débuggable, suffisant à faible volume et l'infrastructure d'une file d'attente a un coût de mise en place et de maintenance injustifié au départ.
Le signal qu'il faut rembourser : quand le volume monte et que les temps de réponse du webhook s'allongent (l'agrégateur peut alors considérer le webhook en timeout et le rejouer), ou quand les échecs de livraison nécessitent des reprises manuelles régulières. Concrètement : si je vois dans les logs des timeouts ou plus de quelques échecs de livraison par semaine, c'est le moment de passer en asynchrone avec une vraie file de retry.