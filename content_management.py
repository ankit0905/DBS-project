import gc
from dbconnect import connection


def content():
    c, conn = connection()
    books = []
    x = c.execute("SELECT * FROM Book")
    x = c.fetchall()
    for data in x:
        book, authors = list(), tuple()
        book.append(data[0])
        book.append(data[1])
        book.append(data[2])
        book.append(data[3])
        book.append(data[4])
        book.append(data[5])
        bid = data[0]
        y = c.execute("SELECT aname FROM Author WHERE bid = ('%s');" % bid)
        y = c.fetchall()
        for author in y:
            authors += (author[0],)
        book.append(authors)
        books.append(book)
    c.close()
    conn.close()
    gc.collect()
    return books