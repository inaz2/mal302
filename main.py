import os
from flask import Flask, render_template, request, abort, redirect, url_for
import psycopg2
import psycopg2.extras
import urlparse
import socket

app = Flask(__name__)

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
    cursor_factory=psycopg2.extras.DictCursor,
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<str_id>', methods=['GET'])
def forward(str_id):
    url_id = base36decode(str_id)
    try:
        cur = conn.cursor()
        cur.execute("SELECT url FROM urls WHERE id = %s LIMIT 1", (url_id,))
        result = cur.fetchone()
        if result:
            url = result['url']
            remote_addr = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
            remote_host = socket.gethostbyaddr(remote_addr)[0] if remote_addr else None
            cur.execute("INSERT INTO visitors (url_id, remote_addr, remote_host, user_agent, accept_language, referrer) VALUES (%s, %s, %s, %s, %s, %s)",
                        (url_id, remote_addr, remote_host, request.environ.get('HTTP_USER_AGENT'), request.environ.get('HTTP_ACCEPT_LANGUAGE'), request.environ.get('HTTP_REFERER')))
            conn.commit()
            return redirect(url)
        else:
            return abort(404)
    finally:
        cur.close()

@app.route('/<str_id>+', methods=['GET'])
def visitors(str_id):
    url_id = base36decode(str_id)
    try:
        cur = conn.cursor()
        cur.execute("SELECT url FROM urls WHERE id = %s LIMIT 1", (url_id,))
        result = cur.fetchone()
        if result:
            url = result['url']
        else:
            return abort(404)
        cur.execute("SELECT * FROM visitors WHERE url_id = %s ORDER BY id", (url_id,))
        visitors = cur.fetchall()
        return render_template('visitors.html', str_id=str_id, url=url, visitors=visitors)
    finally:
        cur.close()

@app.route('/create', methods=['POST'])
def create():
    url = request.form['url']
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO urls (url) VALUES (%s) RETURNING id", (url,))
        result = cur.fetchone()
        if result:
            url_id = result['id']
            conn.commit()
            str_id = base36encode(url_id)
            return redirect(url_for('visitors', str_id=str_id))
        else:
            conn.rollback()
            return abort(500)
    finally:
        cur.close()

def base36encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')

    base36 = ''
    sign = ''

    if number < 0:
        sign = '-'
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return sign + base36

def base36decode(number):
    return int(number, 36)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
