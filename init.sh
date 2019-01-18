#!/usr/bin/env bash

echo "Setting up development database"
docker-compose exec db mysql -e "CREATE DATABASE IF NOT EXISTS nuremberg_dev"
docker-compose exec db mysql -e "CREATE USER nuremberg; GRANT ALL ON nuremberg_dev.* TO nuremberg"
docker-compose exec -T db mysql -unuremberg nuremberg_dev < nuremberg/core/tests/data.sql

echo "Setting up peristent test database"
docker-compose exec db mysql -e "CREATE DATABASE IF NOT EXISTS test_nuremberg_dev"
docker-compose exec db mysql -e "GRANT ALL ON test_nuremberg_dev.* TO nuremberg"
docker-compose exec -T db mysql -unuremberg test_nuremberg_dev < nuremberg/core/tests/data.sql

echo "Migrating databases"
docker-compose exec web python manage.py migrate

echo "Setting up solr index (slow)"
docker-compose exec solr curl -sSL 'http://localhost:8983/solr/admin/cores?action=CREATE&name=nuremberg_dev&instanceDir=/opt/solr/example/solr/nuremberg_dev&schema=schema.xml'
docker-compose exec web python manage.py rebuild_index --noinput
