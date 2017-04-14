from flask import Flask, render_template, flash, request, url_for, redirect, session

app = Flask(__name__)
app.secret_key = 'my_random_key'

@app.route('/')
def home():
	return render_template("header.html")

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html')
	
@app.errorhandler(405)
def method_not_found(e):
	return render_template('405.html')

if __name__ == "__main__":
	app.run(debug=True, port=8000)

