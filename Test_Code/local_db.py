import couchdb

couch = couchdb.Server('http://admin:admin@127.0.0.1:5984')
db = couch.create('test')

