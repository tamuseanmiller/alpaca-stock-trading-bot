"""
Script for importing old data to MongoDB

Usage:
  mongoImport.py [--stock-name=<stock-ticker>] [--db-name=<db-name>]

Options:
  --stock-name=<stock-ticker>   The name of the stock (eg. AMD, GE)
  --db-name=<db-name>   The name of the database on MongoDB
"""

import pymongo
import datetime
from tqdm import tqdm
import mmap
import creds
from docopt import docopt
import os


def get_num_lines(file_path):
    fp = open(file_path, "r+")
    buf = mmap.mmap(fp.fileno(), 0)
    lines = 0
    while buf.readline():
        lines += 1
    return lines


def start():

    # Imported from creds.py
    client = creds.getClient()

    # Connect to DB and get collection
    db = client[db_name]
    collection = db.get_collection(stock_name)
    file = open("data/" + stock_name + "_trading_data.csv", "r")

    # Traverses lines of file and imports to MongoDB database
    for line in tqdm(file, total=get_num_lines("data/" + stock_name + "_trading_data.csv")):
        cols = line.split(",")
        date = cols[0].split("/")
        time = cols[1].split(":")
        collection.insert_one({"Datetime": datetime.datetime(int(date[2]), int(date[0]), int(date[1]), int(time[0]),
                                                             int(time[1]), int(time[2])),
                               "Action": cols[2],
                               "Price": float(cols[3][1:])})


if __name__ == "__main__":
    args = docopt(__doc__)

    # Arguments
    stock_name = str(args['--stock-name'])
    db_name = str(args['--db-name'])

    start()
