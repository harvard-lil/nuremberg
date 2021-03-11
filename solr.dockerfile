FROM solr:8.8.1

USER root
RUN ls /var/solr/data/

USER root
RUN mkdir -p /var/solr/data/nuremberg_dev
RUN cp -pr /opt/solr-8.8.1/example/files/conf /var/solr/data/nuremberg_dev

USER solr
COPY solr_conf/* /var/solr/data/nuremberg_dev/conf/
