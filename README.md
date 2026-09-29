# CosmétiquePro - Logiciel de Gestion Cosmétique (Stock + Caisse + Code-barre)

Application de bureau complète de haute finition pour commerce de cosmétique et parfumerie en Algérie, développée en **Python** avec interface moderne **CustomTkinter**, base de données **SQLite** redondante (Partitions C: et D:), compatible **douchette code-barre HID** et **imprimante thermique ESC/POS**.

---

## 🌟 Fonctionnalités Clés

### 1. Point de Vente & Caisse Tactile (POS)
- **Scan ultra-rapide** : Compatible avec toutes les douchettes USB en mode HID (clavier standard).
- **Catalogue tactile & visuel** : Recherche instantanée et filtrage par catégorie cosmétique (Soins visage, Maquillage, Parfumerie, etc.).
- **Panier intelligent** : Gestion des remises par ligne ou globale, gestion des quantités, vérification du stock en direct.
- **Règlement multi-modes** : Espèces avec boutons de billets rapides (1 000, 2 000, 5 000 DA) et calcul automatique du rendu de monnaie, Carte CIB/Edahabia.
- **Impression ticket thermique** : Compatible ESC/POS et sauvegarde automatique au format texte / ticket.
- **Clôture de caisse journalière** : Saisie du fond de caisse à l'ouverture, calcul automatique du chiffre d'affaires, du théorique en caisse et des écarts (Surplus / Manquant).

### 2. Gestion des Produits & Codes-barres
- Fiche produit complète : Désignation, Marque, Catégorie, Code-barres (EAN-13 / Code128), Prix d'achat (PA), Prix de vente (PV), Seuil d'alerte, Date de péremption, Fournisseur.
- **Générateur EAN-13 intégré** : Génère automatiquement des codes-barres valides avec préfixe 613 (Algérie) et clé de contrôle.
- **Créateur d'étiquettes à imprimer** : Génère des étiquettes autocollantes prêtes à imprimer contenant la désignation, le prix en DA et le code-barres.

### 3. Gestion des Stocks, Réceptions & Inventaire
- **Réception Marchandise au Scanner** : Scan continu des cartons de livraison avec mise à jour immédiate du stock et du prix d'achat.
- **Inventaire Physique Douchette** : Comptage en rayon au scanner avec comparaison automatique contre le stock théorique et application des ajustements en un clic.
- **Journal d'Audit des Mouvements** : Traçabilité totale (Ventes, Réceptions, Ajustements, Pertes/Casses, Opérateur, Date).

### 4. Alertes Multi-Niveaux & Réapprovisionnement
- **Alerte Rupture** : Stock = 0.
- **Alerte Stock Bas** : Stock inférieur ou égal au seuil minimum.
- **Alerte Péremption** : Détection des cosmétiques expirant sous 30, 60 ou 90 jours.
- **Génération automatique de Bons de Commande** : Crée en 1 clic les bons de commande d'achat auprès des fournisseurs pour les produits en alerte.

### 5. Tableaux de Bord & Analyse Financière
- **KPIs en direct** : Chiffre d'affaires du jour, du mois, marge bénéficiaire brute, valeur du stock.
- **Graphiques Matplotlib intégrés** : Évolution du CA sur 7 jours et Top des produits vendus.
- **Export Excel (.xlsx)** : Export du journal des ventes formaté avec totaux.

### 6. Sécurité & Redondance C: / D:
- **Rôles & Permissions** : Administrateur (accès complet) vs Caissier (accès caisse et alertes).
- **Double Sauvegarde Automatique** : La base SQLite est enregistrée sur `C:\CosmetiqueApp\cosmetique.db` et synchronisée automatiquement sur `D:\CosmetiqueApp\cosmetique_backup.db`. Si le lecteur D: est absent, l'application fonctionne sans aucun plantage.

---

## 🔑 Identifiants par Défaut (Premier Démarrage)

| Rôle | Identifiant | Mot de passe | Accès |
|---|---|---|---|
| **Administrateur** | `admin` | `admin123` | Accès complet à tous les modules |
| **Caissier** | `caissier` | `1234` | Accès Caisse, Scan et Clôture |

---

## 🚀 Lancement & Utilisation

### Mode Développement :
Double-cliquez sur `lancer_application.bat` ou lancez en ligne de commande :
```bash
python main.py
```

### Exécution des Tests Automatisés :
```bash
python test_app.py
```

### Compilation en Exécutable Windows (.EXE) Autonome :
Double-cliquez sur `compiler_exe.bat` ou lancez :
```bash
python build_exe.py
```
L'exécutable autonome sera généré dans le dossier `dist/CosmetiquePro/`.
