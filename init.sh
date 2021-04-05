#!/usr/bin/env bash

echo "Setting up development database"
docker-compose exec db mysql -e "CREATE DATABASE IF NOT EXISTS nuremberg_dev"
docker-compose exec db mysql -e "CREATE USER nuremberg; GRANT ALL ON nuremberg_dev.* TO nuremberg"
docker-compose exec -T db mysql -unuremberg nuremberg_dev < nuremberg/core/tests/data.sql

echo "Setting up persistent test database"
docker-compose exec db mysql -e "CREATE DATABASE IF NOT EXISTS test_nuremberg_dev"
docker-compose exec db mysql -e "GRANT ALL ON test_nuremberg_dev.* TO nuremberg"
docker-compose exec -T db mysql -unuremberg test_nuremberg_dev < nuremberg/core/tests/data.sql

echo "Migrating databases"
docker-compose exec web python manage.py migrate

echo "Setting up solr index (slow)"

docker-compose exec -u root solr mkdir -p /var/solr/data/nuremberg_dev
docker-compose exec -u root solr cp -pr "/opt/solr-8.8.1/example/files/conf" "/var/solr/data/nuremberg_dev/"
docker cp solr_conf/schema.xml nuremberg_solr_1:/var/solr/data/nuremberg_dev/conf/
docker cp solr_conf/solrconfig.xml nuremberg_solr_1:/var/solr/data/nuremberg_dev/conf/
docker-compose exec -u root solr chown -R solr:solr /var/solr/data

docker-compose exec solr curl -sSL 'http://localhost:8983/solr/admin/cores?action=CREATE&name=nuremberg_dev&instanceDir=/var/solr/data/nuremberg_dev&schema=schema.xml'
docker-compose exec web python manage.py rebuild_index --noinput
