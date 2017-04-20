import MySQLdb


def connection():
    conn = MySQLdb.connect(host="localhost", user="root", passwd="wonttellu", db="Library")
    c = conn.cursor()
    return c, conn
