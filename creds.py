"""
Helper Class
"""

import pymongo

mongoInfo = ""

client = pymongo.MongoClient(mongoInfo)


def getMongoInfo():
    return mongoInfo


def getClient():
    return client

