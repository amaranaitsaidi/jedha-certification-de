# Démarrage Rapide ⚡

Guide ultra-rapide pour démarrer le projet en 5 minutes.

## 1. Démarrer les bases de données

```bash
# À la racine du projet
docker-compose -f docker-compose.postgres.yml up -d

# Puis dans src_code/
cd src_code
docker-compose -f docker-compose.mongodb.yml up -d
```

⏱️ **Attendre 1-2 minutes** pour que PostgreSQL charge les données (première fois uniquement).

## 2. Configurer les credentials

```bash
# Dans src_code/
cp .env.example .env
```

Éditer `.env` et remplir :
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_BUCKET`
- Credentials Snowflake

PostgreSQL et MongoDB sont déjà configurés ✓

## 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

## 4. Lancer le pipeline

```bash
python scripts/pipeline.py --all
```

Durée : ~5 minutes

## Vérifier que tout fonctionne

```bash
# PostgreSQL
docker exec -it amazon_postgres_db psql -U admin -d amazon_db -c "SELECT COUNT(*) FROM product;"
# Résultat attendu : 42858

# MongoDB
docker exec -it amazon-reviews-mongodb mongosh -u admin -p changeme --eval "use amazon_reviews; db.pipeline_logs.countDocuments()"

# Snowflake
python scripts/verify_snowflake.py
# Résultat attendu : 111322 rows
```

## En cas de problème

```bash
# Voir les conteneurs
docker ps

# Voir les logs PostgreSQL
docker logs amazon_postgres_db

# Voir les logs MongoDB
docker logs amazon-reviews-mongodb

# Redémarrer tout
docker-compose -f docker-compose.postgres.yml restart
cd src_code && docker-compose -f docker-compose.mongodb.yml restart
```

## Arrêter tout

```bash
docker-compose -f docker-compose.postgres.yml down
cd src_code && docker-compose -f docker-compose.mongodb.yml down
```

---

📖 Pour plus de détails, voir `README.md` et `src_code/README.md`
