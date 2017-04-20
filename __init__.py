from flask import Flask, render_template, flash, request, url_for, redirect, session
import os
from os import path

from functools import wraps
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
from dbconnect import connection
from content_management import content
from time import gmtime, strftime
import gc

app = Flask(__name__)
app.secret_key = 'my_random_key'

extra_dirs = ['/static/css/', '/templates/']
extra_files = extra_dirs[:]

for extra_dir in extra_dirs:
    for dirname, dirs, files in os.walk(extra_dir):
        for filename in files:
            filename = path.join(dirname, filename)
            if path.isfile(filename):
                extra_files.append(filename)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session['Admin'] == True:
            return f(*args, **kwargs)
        else:
            flash("You are not admin")
            session.clear()
            return redirect(url_for('login_page'))
    return wrap


@app.route('/')
def home():
    return render_template("header.html")


@app.route("/logout/")
@login_required
def logout():
    with open('log.txt', 'a') as logfile:
        logfile.writelines('\n\n%s: %s logged out at %s;' % (session['utype'], session['username'], str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))))
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('login_page'))


@app.route('/login/', methods=["GET", "POST"])
def login_page():
    error, data = '', ''
    try:
        c, conn = connection()
        if request.method == "POST":
            usertype = request.form['usertype']
            if usertype == 'Admin':
                data = c.execute("SELECT * FROM luser WHERE uid = ('%s');" % thwart(request.form['username']))
                data = c.fetchone()[4]
                print(data)
            elif usertype == 'Student':
                data = c.execute("SELECT * FROM luser WHERE uid = ('%s');" % thwart(request.form['username']))
                data = c.fetchone()[4]
            elif usertype == 'Faculty':
                data = c.execute("SELECT * FROM luser WHERE uid = ('%s');" % thwart(request.form['username']))
                data = c.fetchone()[4]
            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['utype'] = usertype
                session['username'] = request.form['username']
                session[usertype] = True
                flash("You are now logged in !!")
                if usertype == 'Admin':
                    with open('log.txt', 'a') as logfile:
                        logfile.writelines('\n\n%s: %s logged in at %s;' % (usertype, session['username'], str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))))
                    return redirect(url_for("admin_page"))
                elif usertype == 'Student' or usertype == 'Faculty':
                    with open('log.txt', 'a') as logfile:
                        logfile.writelines('\n\n%s: %s logged in at %s;' % (usertype, session['username'], str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))))
                    return redirect(url_for("user_page"))
            else:
                error = "Invalid Credentials, try again !!"
        gc.collect()
        return render_template("login.html", error=error)
    except Exception as e:
        flash(e)
        error = "Invalid Credentials, try again !!"
        return render_template("login.html", error=error)


def get_profile():
    c, conn = connection()
    username = session['username']
    profile = c.execute("SELECT * FROM luser WHERE uid = '%s';" % username);
    profile = c.fetchone()
    return profile


def get_books(uid):
    c, conn = connection()
    books = c.execute("SELECT * FROM Book WHERE uid = '%s';" % uid)
    books = c.fetchall()
    return books


@app.route('/dashboard/user', methods=['POST', 'GET'])
@login_required
def user_page():
    error = ''
    books = content()
    c, conn = connection()
    username = session['username']
    profile = c.execute("SELECT * FROM luser WHERE uid = '%s';" % username);
    profile = c.fetchone()
    user_books = get_books(username)
    try:
        if request.method == "POST":
            if "searchbyname" in request.form:
                text = request.form['search']
                data = c.execute("SELECT * FROM Book WHERE title LIKE '%{}%';".format(text))
                data = c.fetchall()
                books = []
                for book in data:
                    authors = tuple()
                    bid = book[0]
                    data = c.execute("SELECT aname FROM Author WHERE bid = ('%s');" % bid)
                    data = c.fetchall()
                    for author in data:
                        authors += (author[0],)
                    books.append([book[0], book[1], book[2], book[3], book[4], book[5], authors])
                print books
                return render_template('user.html', error=error, books=books, profile=profile, user_books=get_books(username))
            elif "searchbyauthor" in request.form:
                text = request.form['search']
                data = c.execute("SELECT * FROM Author WHERE aname LIKE '%{}%';".format(text))
                data = c.fetchall()
                books = []
                for row in data:
                    book, authors = [], tuple()
                    bid = row[1]
                    data = c.execute("SELECT * FROM Book WHERE bid = ('%s');" % bid)
                    data = c.fetchone()
                    book.append(data[0])
                    book.append(data[1])
                    book.append(data[2])
                    book.append(data[3])
                    book.append(data[4])
                    book.append(data[5])
                    data = c.execute("SELECT aname FROM Author WHERE bid = ('%s');" % bid)
                    data = c.fetchall()
                    for author in data:
                        authors += (author[0],)
                    book.append(authors)
                    books.append(book)
                return render_template('user.html', error=error, books=books, profile=profile, user_books=get_books(username))
            else:
                error = "Something went Wrong!! Please Try Again."
                return render_template('user.html', error=error, books=books, profile=profile, user_books=get_books(username))
        else:
            return render_template('user.html', error=error, books=books, profile=profile, user_books=get_books(username))
    except Exception as e:
        flash(e)
        error = "Please Try Again"
        return render_template('dashboard.html', error=error, books=books, profile=profile, user_books=get_books(username))


@app.route('/dashboard/admin', methods=['POST', 'GET'])
@login_required
@admin_required
def admin_page():
    error = ''
    books = content()
    c, conn = connection()
    username = session['username']
    profile = c.execute("SELECT * FROM luser WHERE uid = '%s';" % username);
    profile = c.fetchone()
    user_books = get_books(username)
    try:
        if request.method == "POST":
            if "bookadd" in request.form:
                bid = thwart(request.form['bid'])
                title = thwart(request.form['title'])
                author = thwart(request.form['author']) if thwart(request.form['author']) != '' else 'NULL'
                category = thwart(request.form['category']) if thwart(request.form['category']) != '' else 'NULL'
                publication = thwart(request.form['publication']) if thwart(request.form['publication']) != '' else 'NULL'
                duedate = thwart(request.form['duedate']) if thwart(request.form['duedate']) != '' else 'NULL'
                borrower = thwart(request.form['borrower']) if thwart(request.form['borrower']) != '' else 'available'
                if author != 'NULL' and author is not None:
                    author = author.split(',')
                else:
                    author = []
                #print author
                #print bid, title, category, publication, duedate, borrower
                x = c.execute("SELECT * FROM Book WHERE bid = ('%s');" % (bid))
                if int(x) > 0:
                    flash("The Book ID already exists. Please try again.")
                    return render_template('dashboard.html', books=books, profile=profile, user_books=get_books(username))
                else:
                    data = c.execute("INSERT INTO Book (bid, title, category, publication, dueDate, uid) VALUES (%s, %s, %s, %s, %s, %s);", (bid, title, category, publication, duedate, borrower))
                    conn.commit()
                    for name in author:
                        name = name.lstrip().rstrip()
                        data = c.execute("INSERT INTO Author (aname, bid) VALUES (%s, %s);", (name, bid))
                        conn.commit()
                    gc.collect()
                    username = session['username']
                    profile = c.execute("SELECT * FROM luser WHERE uid = '%s';" % username);
                    profile = c.fetchone()
                    flash("Book Added")
                    with open('log.txt', 'a') as logfile:
                        logfile.writelines('\n\n%s: %s(id) added Book with BID = %s at %s;' % (session['utype'], session['username'], bid, str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))))
                    books = content()
                    return render_template('dashboard.html', error=error, books=books, profile=get_profile(), user_books=get_books(username))
            elif "bookupdate" in request.form:
                bid = thwart(request.form['bid'])
                x = c.execute("SELECT * FROM Book WHERE bid = ('%s');" % (bid))
                if int(x) <= 0:
                    flash("No Book with such BID exists.")
                    return render_template('dashboard.html', books=books, user_books=get_books(username))
                else:
                    details = c.fetchone()
                    print details
                    dbtitle, title = details[1], request.form['title']
                    dbcategory, category = details[2], request.form['category']
                    dbpublication, publication = details[3], request.form['publication']
                    dbduedate, duedate = details[4], request.form['duedate']
                    dbuid, uid = details[5], request.form['borrower']
                    author = request.form['author']
                    if author != '' and author is not None:
                        author = author.split(',')
                        data = c.execute("DELETE FROM Author WHERE bid = ('%s')" % (bid))
                        conn.commit()
                        for name in author:
                            name = name.lstrip().rstrip()
                            data = c.execute("INSERT INTO Author (aname, bid) VALUES (%s, %s);", (name, bid))
                            conn.commit()
                    #print(bid)
                    #print(title, category, publication, duedate, author)
                    if title == '' or title is None:
                        title = dbtitle
                    if category == '' or category is None:
                        category = dbcategory
                    if publication == '' or publication is None:
                        publication = dbpublication
                    if duedate == '' or duedate is None:
                        duedate = dbduedate
                    if uid == '' or uid is None:
                        uid = dbuid
                    data = c.execute("UPDATE Book SET title='%s', category='%s', publication='%s', duedate='%s', uid='%s' WHERE bid = ('%s');" % (title, category, publication, duedate, uid, bid))
                    conn.commit()
                    gc.collect()
                    flash("Book details Updated")
                    with open('log.txt', 'a') as logfile:
                        logfile.writelines('\n\n%s: %s (id) updated Book with BID = %s at %s;' % (session['utype'], session['username'], bid, str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))))
                    books = content()
                    return render_template('dashboard.html', error=error, books=books, profile=get_profile(), user_books=get_books(username))
            elif "bookdelete" in request.form:
                bid = thwart(request.form['bid'])
                c, conn = connection()
                data = c.execute("SELECT * FROM Book WHERE bid = '%s';" % bid)
                if int(data) <= 0:
                    flash("No such Book exists")
                else:
                    data = c.execute("DELETE FROM Author WHERE bid = '%s';" % bid)
                    conn.commit()
                    data = c.execute("DELETE FROM Book WHERE bid = '%s';" % bid)
                    conn.commit()
                    gc.collect()
                    flash("Deleted Successfully!!")
                    with open('log.txt', 'a') as logfile:
                        logfile.writelines('\n\n%s: %s (id) deleted Book with BID = %s at %s;' % (session['utype'], session['username'], bid, str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))))
                    return render_template('dashboard.html', error=error, books=books, profile=get_profile(), user_books=get_books(username))
            elif "userinsert" in request.form:
                user_type = thwart(request.form['usertype'])
                uid = thwart(request.form['uid'])
                uname = thwart(request.form['uname'])
                email = thwart(request.form['email']) if thwart(request.form['email']) != '' else 'NULL'
                phone = thwart(request.form['phone']) if thwart(request.form['phone']) != '' else 'NULL'
                fine = 0
                if fine is None:
                    fine = 0
                else:
                    fine = int(fine)
                print user_type, uid, uname, email, phone, "fine"
                data = c.execute("SELECT * FROM luser WHERE uid = '%s';" % uid)
                data = c.fetchone()
                if data is not None and int(data) > 0:
                    flash("User ID already exists. Please try again")
                    return render_template(url_for('admin_page'))
                data = c.execute("SELECT * FROM luser WHERE email = '%s';" % email)
                data = c.fetchone()
                if data is not None and int(data) > 0:
                    flash("Email ID is already taken. Please try again")
                    return render_template(url_for('admin_page'))
                data = c.execute("SELECT * FROM luser WHERE phone = '%s';" % phone)
                data = c.fetchone()
                if data is not None and int(data) > 0:
                    flash("Phone No. is already taken. Please try again")
                    return render_template(url_for('admin_page'))
                else:
                    password = sha256_crypt.encrypt(uid)
                    data = c.execute("INSERT INTO luser VALUES ('%s', '%s', '%s', '%s', '%s', %d, '%s');" % (uid, uname, email, phone, password, fine, user_type))
                    conn.commit()
                    profile = c.execute("SELECT * FROM luser WHERE uid = '%s';" % username);
                    profile = c.fetchone()
                    gc.collect()
                    flash("User Added Successfully!!")
                    with open('log.txt', 'a') as logfile:
                        logfile.writelines('\n\n%s: %s (id) Added with UID = %s at %s;' % (session['utype'], session['username'], uid, str(strftime("%Y-%m-%d %H:%M:%S", gmtime()))))
                    return render_template('dashboard.html', error=error, books=books, profile=get_profile(), user_books=get_books(username))
            elif "searchbyname" in request.form:
                text = request.form['search']
                data = c.execute("SELECT * FROM Book WHERE title LIKE '%{}%';" .format(text))
                data = c.fetchall()
                books = []
                for book in data:
                    authors = tuple()
                    bid = book[0]
                    data = c.execute("SELECT aname FROM Author WHERE bid = ('%s');" % bid)
                    data = c.fetchall()
                    for author in data:
                        authors += (author[0],)
                    books.append([book[0],book[1],book[2],book[3],book[4],book[5],authors])
                print books
                return render_template('dashboard.html', error=error, books=books, profile=get_profile(), user_books=get_books(username))
            elif "searchbyauthor" in request.form:
                text = request.form['search']
                data = c.execute("SELECT * FROM Author WHERE aname LIKE '%{}%';" .format(text))
                data = c.fetchall()
                books = []
                for row in data:
                    book, authors = [], tuple()
                    bid = row[1]
                    data = c.execute("SELECT * FROM Book WHERE bid = ('%s');" % bid)
                    data = c.fetchone()
                    book.append(data[0])
                    book.append(data[1])
                    book.append(data[2])
                    book.append(data[3])
                    book.append(data[4])
                    book.append(data[5])
                    data = c.execute("SELECT aname FROM Author WHERE bid = ('%s');" % bid)
                    data = c.fetchall()
                    for author in data:
                        authors += (author[0],)
                    book.append(authors)
                    books.append(book)
                print books
                return render_template('dashboard.html', error=error, books=books, profile=get_profile(), user_books=get_books(username))
            else:
                error = "Bad Request"
        return render_template('dashboard.html', error=error, books=books, profile=get_profile(), user_books=get_books(username))
    except Exception as e:
        flash(e)
        error = "Please Try Again"
        return render_template('dashboard.html', error=error, books=books, profile=get_profile(), user_books=get_books(username))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


@app.errorhandler(405)
def method_not_found(e):
    return render_template('405.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=8000, extra_files=extra_files)

# CREATE DATABASE Library
# USE Library
# CREATE TABLE user (uid VARCHAR(15) PRIMARY KEY, name VARCHAR(30), email VARCHAR(40), phone VARCHAR(15), password VARCHAR(fine INT(10))
#20), fine INT(10))
# CREATE TABLE books (bid VARCHAR(15) )
# CREATE TABLE admin (aid VARCHAR(15) PRIMARY KEY, name VARCHAR(30), email VARCHAR(40), phone VARCHAR(15))

