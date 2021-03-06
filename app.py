from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, jsonify, json
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import requests
from os import environ


app = Flask(__name__)
app.config['DEBUG']
app.config.from_envvar('APP_SETTINGS')
app.config['access_key']=environ.get('access_key')



# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
#app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

#Articles = Articles()

# Index


@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')


# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


# Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",
                    (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute(
            "SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard


@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# Article Checkout Form Class


class ArticleForm(Form):
    phone = StringField('Phone', [validators.Length(min=1, max=200)])
    #TODO : with selectfield to select the list of country code's
    country = StringField('Country Code', [validators.Length(min=1, max=200)])

# Add Article Checkout


@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        phone = form.phone.data
        country = form.country.data
        url = "http://apilayer.net/api/validate"
# Need to read the  access key from the environment using  app.config['access_key']
        querystring = {"access_key": "81f511599e67f381ac1ff12743ca4753",
                       "number": phone, "country_code": country, "format": "1"}

        headers = {
            'cache-control': "no-cache"
        }

        response = requests.request(
            "POST", url, headers=headers, params=querystring)
        #unicode_to_list = list(response)
        a = json.loads(response.text)
        if(a['valid'] == True):
            # Create Cursor
            cur = mysql.connection.cursor()

            # Execute
            cur.execute("INSERT INTO articles(phone,author) VALUES(%s, %s)",
                        (phone, session['username']))

            # Commit to DB
            mysql.connection.commit()

            # Close connection
            cur.close()

            flash('Article Checkout form Created', 'success')
        else:
            flash('phone number not valid', 'error')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article check out form
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.phone.data = article['phone']

    if request.method == 'POST' and form.validate():
        phone = request.form['phone']
        country = request.form['country']
        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(phone)
        # Execute
        cur.execute("UPDATE articles SET phone=%s,country=%s WHERE id=%s", (phone,country,id))
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article checkout form Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article


@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('Article Check out form Deleted', 'success')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
