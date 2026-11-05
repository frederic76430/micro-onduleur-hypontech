<p align="center">
  <img src="custom_components/micro_onduleur_hypontech/brand/logo.png" alt="Micro Onduleur Hypontech" width="200"/>
</p>

# Micro Onduleur Hypontech 🌞

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/frederic76430/micro-onduleur-hypontech/actions/workflows/validate.yml/badge.svg)](https://github.com/frederic76430/micro-onduleur-hypontech/actions/workflows/validate.yml)

Intégration Home Assistant complète pour les micro-onduleurs **Hypontech HMS-800W-C**.

Inclut toutes les données globales **plus** le suivi par panneau individuel.

## ✨ Fonctionnalités

- 📊 Toutes les données globales de production
- 🔲 Suivi **par panneau individuel** (pv1, pv2, pv3, pv4)
- 🔋 Détection automatique de la **batterie**
- ⚡ Détection automatique des **onduleurs 4 entrées**
- 🌙 Gestion intelligente **nuit/jour** — pas d'appel API inutile la nuit
- 🔄 Mise à jour toutes les **60 secondes** (30 minutes la nuit)
- 📅 Production mois/année mise à jour **1 fois par heure**
- 🔑 **Reconnexion automatique** quand le jeton expire, et demande de ressaisie du mot de passe s'il a changé
- 🛡️ **Jamais de 0 inventé** : si le cloud ne répond pas, les dernières valeurs sont gardées, puis les capteurs passent « indisponible » au bout de 15 minutes
- 📈 **Compteurs fiables** : une valeur en retard du cloud ne fait jamais baisser un compteur (pas de pics dans le tableau de bord Énergie)
- 🕐 Heures de **Home Assistant** (jour / nuit, changement de jour et de mois)

## Installation via HACS

1. Dans HACS → cliquez sur ⋮ → **Dépôts personnalisés**
2. Ajoutez : `https://github.com/frederic76430/micro-onduleur-hypontech`
3. Type : **Intégration**
4. Cherchez **"Micro Onduleur Hypontech"** et installez
5. Redémarrez Home Assistant
6. **Paramètres → Appareils & Services → + Ajouter → "Micro Onduleur Hypontech"**
7. Entrez votre email et mot de passe **hypon.cloud**

## Capteurs disponibles

### 📊 Données globales
| Capteur | Unité | Activé par défaut |
|---------|-------|:-----------------:|
| Production aujourd'hui | kWh | ✅ |
| Production totale | kWh | ✅ |
| Production ce mois | kWh | ✅ |
| Production cette année | kWh | ✅ |
| Production instantanée | W | ✅ |
| CO2 économisé | kg | ✅ |
| Arbres équivalents | | ✅ |
| Puissance solaire | W | ❌ |
| Puissance réseau | W | ❌ |
| Puissance batterie | W | 🔋 auto |
| Batterie | % | 🔋 auto |

### 🔲 Données par panneau
| Capteur | Unité | Activé par défaut |
|---------|-------|:-----------------:|
| Panneau 1 - Puissance | W | ✅ |
| Panneau 1 - Tension | V | ✅ |
| Panneau 1 - Courant | A | ✅ |
| Panneau 2 - Puissance | W | ✅ |
| Panneau 2 - Tension | V | ✅ |
| Panneau 2 - Courant | A | ✅ |
| Panneau 3 - Puissance | W | ⚡ auto |
| Panneau 3 - Tension | V | ⚡ auto |
| Panneau 3 - Courant | A | ⚡ auto |
| Panneau 4 - Puissance | W | ⚡ auto |
| Panneau 4 - Tension | V | ⚡ auto |
| Panneau 4 - Courant | A | ⚡ auto |
| Puissance totale DC | W | ❌ |
| Tension AC réseau | V | ✅ |
| Fréquence réseau | Hz | ✅ |
| Température onduleur | °C | ✅ |

> 🔋 **auto** = activé automatiquement si une batterie est détectée
> ⚡ **auto** = activé automatiquement si un onduleur 4 entrées est détecté
> ❌ = désactivé par défaut, activable manuellement

## Compatibilité
- Testé avec : **Hypontech HMS-800W-C**
- Cloud : **hypon.cloud**
- Mise à jour : toutes les **60 secondes** (30 min la nuit)
- Home Assistant : **2025.2.0** minimum

## Historique des versions

### v1.1.0
- **Coupure du cloud** : les capteurs ne passent plus à 0 (ce qui créait des pics dans le tableau de bord Énergie) ; dernière valeur gardée, puis « indisponible » après 15 minutes
- **Compteurs d'énergie** : ne baissent jamais, sauf au changement de jour, de mois ou d'année
- **Reconnexion** : nouvelle connexion automatique si le jeton expire ; si le mot de passe a changé, Home Assistant propose de le ressaisir (sans créer de doublon)
- **Panneaux le soir** : puissance et courant des panneaux remis à 0 dès que l'onduleur ne produit plus (avant, la dernière mesure de la journée restait affichée jusqu'à 22 h)
- **Fuseau horaire** : jour / nuit et changement de jour ou de mois à l'heure de Home Assistant (et non plus en UTC)
- **Identifiants stables** basés sur l'installation Hypontech, avec migration automatique : les noms d'entités ne changent pas
- Manifeste conforme (hassfest), logo dans `brand/` de l'intégration, vérifications et tests automatiques sur GitHub
- Version minimale : Home Assistant 2025.2.0

### v1.0.8
- Architecture améliorée — classe de base `entity.py`
- Logger centralisé dans `const.py`
- Réauthentification automatique si mot de passe change
- Gestion des erreurs inconnues

### v1.0.6
- Mise à jour toutes les 60 secondes (au lieu de 5 minutes)
- Production mois/année mise à jour 1 fois par heure seulement
- Gestion intelligente nuit/jour

### v1.0.5
- Détection automatique batterie
- Détection automatique onduleur 4 entrées (pv3/pv4)
- "Consommation maison" renommé en "Production instantanée"

### v1.0.1
- Correction production ce mois
- Correction production cette année

## Licence

Distribué sous licence [MIT](LICENSE). Intégration non officielle, non affiliée à Hypontech.
