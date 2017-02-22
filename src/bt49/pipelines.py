# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
from scrapy.conf import settings
from bson.binary import Binary


class Bt49Pipeline(object):

    def process_item(self, item, spider):
        return item


collectionCached = {}


class MongoDBPipeline(object):

    def process_item(self, item, spider):
        itemTypeName = type(item).__name__

        itemDic = {}

        for field in item:
            if field == 'threadId' and itemTypeName == 'ThreadItem':
                itemDic[settings['MONGODB_UNIQ_KEY']] = item[field]

            itemDic[field] = item[field]

            if field == 'fileString':
                itemDic[field] = Binary(item[field])

        self.collection = MongoStatic.get_collection_obj(itemTypeName)

        if itemTypeName == 'ThreadItem':
            model = self.collection.find_one(
                {"_id": itemDic[settings['MONGODB_UNIQ_KEY']]})
            if model is None:
                self.collection.insert_one(itemDic)
        elif itemTypeName == 'ThreadFile':
            model = self.collection.find_one(
                {"url": itemDic["url"]})
            if model is None:
                self.collection.insert_one(itemDic)
        else:
            self.collection.insert_one(itemDic)

        return item


class MongoStatic(object):

    @staticmethod
    def get_collection_obj(name):
        xCollection = collectionCached.get(name)
        if xCollection is None:
            connection = pymongo.MongoClient(
                settings['MONGODB_SERVER'], settings['MONGODB_PORT'])
            db = connection[settings['MONGODB_DB']]
            xCollection = db[name]
            collectionCached[name] = xCollection
        return xCollection
