# Documentation du service cf_proxy_ping_aggregator

## 🧠 Description

`cf_proxy_ping_aggregator` est un service HTTP léger conçu pour fonctionner sous Linux sans dépendances externes. Il agit comme un proxy intelligent qui reçoit des requêtes HTTP, les rejoue vers une liste de services locaux, agrège les réponses, et renvoie une réponse consolidée selon des règles spécifiques.

---

## ⚙️ Fonctionnement

1. **Écoute HTTP** sur un port défini via `--port`  
2. **Rejeu de la requête** vers une liste de ports locaux définis via `--lport`  
3. **Agrégation des réponses** :
   - Si toutes les réponses ont un statut HTTP `200` **et** un corps égal à `pong`, la première réponse est utilisée. Les détails de l’agrégation sont affichés dans la sortie standard
   - Sinon, la réponse **la plus rapide** parmi celles en erreur est utilisée (statut ≠ 200 ou corps ≠ pong). Les logs sont redirigés vers la sortie d’erreur (stderr) pour faciliter le diagnostic.
4. **Réponse au client initial** avec le statut et le corps déterminés.

---

## 🚀 Utilisation

### Lancer le service :

```bash
python3 cf_proxy_ping_aggregator.py --port 8080 --lport 3001 --lport 3002 --lport 3000
```

## Usage Linux

### Construction du package debian
Générer un package debian
```
dpkg --build cf_proxy_ping_aggregator
```

### Installation
```
sudo dkpg -i cf_proxy_ping_aggregator.deb
sudo systemctl start cf_proxy_ping_aggregator.service
sudo systemctl status cf_proxy_ping_aggregator.service
journalctl -u cf_proxy_ping_aggregator.service
```