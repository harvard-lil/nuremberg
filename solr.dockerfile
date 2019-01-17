# The official solr images don't go back to version 4...
# This repo/image eventually became the official docker solr image.
# https://github.com/makuk66/docker-solr/commits/master
#
# Readme:
# https://github.com/makuk66/docker-solr/blob/9d2b2d48207231d274176d8059ba5161c6812c73/4.10/README-solr4.md
FROM makuk66/docker-solr:4.10.4

RUN mkdir /opt/solr/example/solr/nuremberg_dev \
    && cp -pR /opt/solr/example/solr/collection1/conf /opt/solr/example/solr/nuremberg_dev

COPY schema.xml /opt/solr/example/solr/nuremberg_dev/conf/schema.xml
