# Micro Onduleur Hypontech 🌞

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Intégration Home Assistant complète pour les micro-onduleurs **Hypontech HMS-800W-C**.

Inclut toutes les données globales **plus** le suivi par panneau individuel.

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
| Capteur | Unité |
|---------|-------|
| Puissance solaire | W |
| Production aujourd'hui | kWh |
| Production totale | kWh |
| Production ce mois | kWh |
| Production cette année | kWh |
| Consommation maison | W |
| Puissance réseau | W |
| Puissance batterie | W |
| Batterie | % |
| CO2 économisé | kg |
| Arbres équivalents | |

### 🔲 Données par panneau
| Capteur | Unité |
|---------|-------|
| Panneau 1 - Puissance | W |
| Panneau 1 - Tension | V |
| Panneau 1 - Courant | A |
| Panneau 2 - Puissance | W |
| Panneau 2 - Tension | V |
| Panneau 2 - Courant | A |
| Puissance totale DC | W |
| Tension AC réseau | V |
| Fréquence réseau | Hz |
| Température onduleur | °C |

## Compatibilité
- Testé avec : **Hypontech HMS-800W-C**
- Cloud : **hypon.cloud**
- Mise à jour : toutes les **5 minutes**
