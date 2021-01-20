# -*- coding: utf-8 -*-
import csv
import datetime
import json
import os


import elasticsearch.helpers
from elasticsearch import Elasticsearch, RequestsHttpConnection, serializer, compat, exceptions


TYPE = 'record'


# see https://github.com/elastic/elasticsearch-py/issues/374
class JSONSerializerPython2(serializer.JSONSerializer):
    """Override elasticsearch library serializer to ensure it encodes utf characters during json dump.
    See original at: https://github.com/elastic/elasticsearch-py/blob/master/elasticsearch/serializer.py#L42
    A description of how ensure_ascii encodes unicode characters to ensure they can be sent across the wire
    as ascii can be found here: https://docs.python.org/2/library/json.html#basic-usage
    """

    def dumps(self, data):
        # don't serialize strings
        if isinstance(data, compat.string_types):
            return data
        try:
            return json.dumps(data, default=self.default, ensure_ascii=True)
        except (ValueError, TypeError) as e:
            raise exceptions.SerializationError(data, e)


class ESLoader(object):
    def __init__(self, file_name, index_name, drop_existing=False, alias=None, host='localhost:9200'):
        """
        :param file_name
        :param index_name: the es index to upload to
        :param drop_existing:
        :param alias: the es alias to associate the index with
        """
        self.file_name = file_name
        self.index_name = index_name
        self.drop_existing = drop_existing
        self.alias = alias
        self.es = Elasticsearch([host], serializer=JSONSerializerPython2())

    def load(self):
        if not self.es.indices.exists(self.index_name):
            print ('creating index ' + self.index_name)
            self.__create_index()
        elif self.drop_existing:
            print('deleting index ' + self.index_name)
            self.es.indices.delete(index=self.index_name)
            print ('creating index ' + self.index_name)
            self.__create_index()
        
        print('indexing ' + self.file_name)
        try:
            self.__load_file(self.file_name)
        except RuntimeError as e:
            print(e)
            print("Failed to load " + self.file_name)

        print("Finished indexing")

    def __load_file(self, file):
        doc_count = 0
        data = []

        with open(file) as f:
            print("Starting indexing on " + f.name)
            reader = csv.DictReader(f)

            for row in reader:
                # gracefully handle empty locations
                if (row['decimalLatitude'] == '' or row['decimalLongitude'] == ''): 
                    row['location'] = ''
                else:
                    row['location'] = row['decimalLatitude'] + "," + row['decimalLongitude'] 

                data.append({k: v for k, v in row.items() if v})  # remove any empty values

            elasticsearch.helpers.bulk(client=self.es, index=self.index_name, actions=data, doc_type=TYPE,
                                       raise_on_error=True, chunk_size=10000, request_timeout=60)
            doc_count += len(data)
            print("Indexed {} documents in {}".format(doc_count, f.name))

        return doc_count

    def __create_index(self):
        request_body = {
            "mappings": {
                TYPE: {
                    "properties": {
                        "measurementType": {"type": "text"},
                        "measurementValue": {"type": "float"},
                        "decimalLatitude": { "type": "float" },
                        "decimalLongitude": { "type": "float" },
                        "location": { "type": "geo_point" }                        
                    }
                }
            }
        }
        self.es.indices.create(index=self.index_name, body=request_body)

index = 'futres'
drop_existing = True
alias = 'futres'
host =  'tarly.cyverse.org:80'
#file_name = 'data/futres_data_processed.csv'
file_name = 'loadertest.csv'

loader = ESLoader(file_name, index, drop_existing, alias, host)
loader.load()


