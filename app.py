#encoding:utf-8
import pymongo
from bson.objectid import ObjectId
from flask import Flask, url_for, json, request, Response
import json_util
import datetime
import solr

#configuration
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

# create the little application object
app = Flask(__name__)
app.config.from_object(__name__)

# connect to the database
connection = pymongo.Connection(app.config['MONGODB_HOST'], app.config['MONGODB_PORT'])
items = connection['condom']['item']
items2 = connection['condom']['item2']
brands = connection['condom']['brand']
comments = connection['condom']['comment']

# connection to solr server
solrConnection = solr.SolrConnection('http://127.0.0.1:8983/solr')

def json_load(data):
    return json.loads(data, object_hook=json_util.object_hook)

def json_dump(data):
    return json.dumps(data, default=json_util.default)

@app.route('/api/items')
def list_items():
    start = request.args.get('start')
    count = request.args.get('count')
    brand_id = request.args.get('brand_id')
    if brand_id:
        filter = items2.find({'brand':brand_id})
    else:
        filter = items.find()
    if start and count:
        result = filter.sort('_id',1).skip(int(str(start))).limit(int(str(count)))
    else:
        result = filter

    js = json_dump(list(result))
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route('/api/brands')
def list_brands():
    result = brands.find().sort('brand_id',1)
    js = json_dump(list(result))
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route('/api/addComment',methods=['GET', 'POST'])
def add_comment():
    author = request.form['author']
    content = request.form['content']
    item_id = request.form['item_id']
    comment = {"item_id": item_id, "author": author, "date": datetime.datetime.utcnow(), "content": content}
    comments.insert(comment)
    return ''

@app.route('/api/comments')
def list_comments():
    item_id = request.args.get('item_id')
    if item_id:
        result = comments.find({'item_id':item_id})
    else:
        result = comments.find().sort('date')
    js = json_dump(list(result))
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route('/api/query')
def query():
    keyword = request.args.get('kw')
    results = []
    if keyword:
        #查询solr
        response = solrConnection.query('all:' + keyword, rows=100)
        for hit in response.results:
            id = hit['id']
            _id = ObjectId(id)
            #根据id从数据库中获取记录
            doc = items.find_one({"_id": _id})
            results.append(doc)

    js = json_dump(list(results))
    resp = Response(js, status=200, mimetype='application/json')
    return resp


if __name__ == '__main__':
    app.run(debug=True)
