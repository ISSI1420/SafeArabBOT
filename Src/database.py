import psycopg2
from .config import DATABASE_URL
from datetime import datetime

def db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn, conn.cursor()

def init_db():
    conn, cur = db()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        tg_id BIGINT UNIQUE,
        username TEXT,
        ton_address TEXT,
        referral_id BIGINT DEFAULT NULL,
        rating_count INTEGER DEFAULT 0,
        rating_sum INTEGER DEFAULT 0,
        referral_earnings REAL DEFAULT 0
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS deals (
        id SERIAL PRIMARY KEY,
        buyer_id BIGINT,
        seller_id BIGINT,
        currency TEXT,
        amount REAL,
        description TEXT,
        state TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        deal_tx_hash TEXT,
        memo TEXT,
        referral_id BIGINT DEFAULT NULL
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        id SERIAL PRIMARY KEY,
        deal_id BIGINT,
        from_user BIGINT,
        to_user BIGINT,
        rating INTEGER,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        from_user BIGINT,
        amount REAL DEFAULT 0,
        deal_id BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS blacklist (
        id SERIAL PRIMARY KEY,
        tg_id BIGINT,
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


# ----------------------------
# Users
# ----------------------------
def add_user(tg_id, username, ton_address, referral_id=None):
    conn, cur = db()
    cur.execute('''
        INSERT INTO users (tg_id, username, ton_address, referral_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (tg_id) DO NOTHING
    ''', (tg_id, username, ton_address, referral_id))
    conn.commit()
    conn.close()

def get_user(tg_id):
    conn, cur = db()
    cur.execute('SELECT * FROM users WHERE tg_id=%s', (tg_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_user_wallet(tg_id):
    conn, cur = db()
    cur.execute('SELECT ton_address FROM users WHERE tg_id=%s', (tg_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_user_rating(tg_id):
    conn, cur = db()
    cur.execute('SELECT rating_count, rating_sum FROM users WHERE tg_id=%s', (tg_id,))
    row = cur.fetchone()
    conn.close()
    if not row or row[0] == 0: 
        return (0, 0)
    return (row[0], row[1])

def get_user_referrals(tg_id):
    conn, cur = db()
    cur.execute('SELECT * FROM referrals WHERE from_user=%s', (tg_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


# ----------------------------
# Deals
# ----------------------------
def add_deal(buyer_id, seller_id, currency, amount, description, memo, referral_id=None):
    conn, cur = db()
    cur.execute('''
        INSERT INTO deals (buyer_id, seller_id, currency, amount, description, state, memo, referral_id)
        VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s) RETURNING id
    ''', (buyer_id, seller_id, currency, amount, description, memo, referral_id))
    deal_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return deal_id

def get_deal(deal_id):
    conn, cur = db()
    cur.execute('SELECT * FROM deals WHERE id=%s', (deal_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_user_deals(tg_id):
    conn, cur = db()
    cur.execute('SELECT * FROM deals WHERE buyer_id=%s OR seller_id=%s ORDER BY created_at DESC', (tg_id, tg_id))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_deals_by_state(state):
    conn, cur = db()
    cur.execute('SELECT * FROM deals WHERE state=%s', (state,))
    rows = cur.fetchall()
    conn.close()
    return rows

def update_deal_state(deal_id, new_state):
    conn, cur = db()
    cur.execute('UPDATE deals SET state=%s WHERE id=%s', (new_state, deal_id))
    conn.commit()
    conn.close()

def set_deal_tx_hash(deal_id, tx_hash):
    conn, cur = db()
    cur.execute('UPDATE deals SET deal_tx_hash=%s WHERE id=%s', (tx_hash, deal_id))
    conn.commit()
    conn.close()

def complete_deal(deal_id):
    conn, cur = db()
    cur.execute('UPDATE deals SET state=%s, completed_at=%s WHERE id=%s', ("completed", datetime.now(), deal_id))
    conn.commit()
    conn.close()


# ----------------------------
# Ratings
# ----------------------------
def add_rating(deal_id, from_user, to_user, rating, comment):
    conn, cur = db()
    cur.execute('INSERT INTO ratings (deal_id, from_user, to_user, rating, comment) VALUES (%s, %s, %s, %s, %s)', 
                (deal_id, from_user, to_user, rating, comment))
    cur.execute('UPDATE users SET rating_count=rating_count+1, rating_sum=rating_sum+%s WHERE tg_id=%s', (rating, to_user))
    conn.commit()
    conn.close()


# ----------------------------
# Referrals
# ----------------------------
def add_referral(from_user_id, user_id, amount, deal_id):
    conn, cur = db()
    cur.execute('INSERT INTO referrals (user_id, from_user, amount, deal_id) VALUES (%s, %s, %s, %s)', 
                (user_id, from_user_id, amount, deal_id))
    cur.execute('UPDATE users SET referral_earnings=referral_earnings+%s WHERE tg_id=%s', (amount, from_user_id))
    conn.commit()
    conn.close()


# ----------------------------
# Blacklist
# ----------------------------
def add_to_blacklist(tg_id, reason):
    conn, cur = db()
    cur.execute('INSERT INTO blacklist (tg_id, reason) VALUES (%s, %s)', (tg_id, reason))
    conn.commit()
    conn.close()

def is_blacklisted(tg_id):
    conn, cur = db()
    cur.execute('SELECT 1 FROM blacklist WHERE tg_id=%s', (tg_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row)

def get_blacklist():
    conn, cur = db()
    cur.execute('SELECT tg_id, reason FROM blacklist ORDER BY created_at DESC')
    rows = cur.fetchall()
    conn.close()
    return rows


# ----------------------------
# Admin earnings
# ----------------------------
def get_admin_earnings():
    conn, cur = db()
    cur.execute("SELECT SUM(amount*0.02) as total FROM deals WHERE state='completed'")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0    cur.execute('''
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deal_id INTEGER,
        from_user INTEGER,
        to_user INTEGER,
        rating INTEGER,
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        from_user INTEGER,
        amount REAL DEFAULT 0,
        deal_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS blacklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def add_user(tg_id, username, ton_address, referral_id=None):
    conn, cur = db()
    cur.execute('INSERT OR IGNORE INTO users (tg_id, username, ton_address, referral_id) VALUES (?, ?, ?, ?)', (tg_id, username, ton_address, referral_id))
    conn.commit()
    conn.close()

def get_user_wallet(tg_id):
    conn, cur = db()
    cur.execute('SELECT ton_address FROM users WHERE tg_id=?', (tg_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else None

def get_user(tg_id):
    conn, cur = db()
    cur.execute('SELECT * FROM users WHERE tg_id=?', (tg_id,))
    row = cur.fetchone()
    conn.close()
    return row

def add_deal(buyer_id, seller_id, currency, amount, description, memo, referral_id=None):
    conn, cur = db()
    cur.execute('''INSERT INTO deals
        (buyer_id, seller_id, currency, amount, description, state, memo, referral_id)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)''',
        (buyer_id, seller_id, currency, amount, description, memo, referral_id))
    deal_id = cur.lastrowid
    conn.commit()
    conn.close()
    return deal_id

def get_deal(deal_id):
    conn, cur = db()
    cur.execute('SELECT * FROM deals WHERE id=?', (deal_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_deal_state(deal_id, new_state):
    conn, cur = db()
    cur.execute('UPDATE deals SET state=? WHERE id=?', (new_state, deal_id))
    conn.commit()
    conn.close()

def set_deal_tx_hash(deal_id, tx_hash):
    conn, cur = db()
    cur.execute('UPDATE deals SET deal_tx_hash=? WHERE id=?', (tx_hash, deal_id))
    conn.commit()
    conn.close()

def complete_deal(deal_id):
    import datetime
    conn, cur = db()
    cur.execute('UPDATE deals SET state=?, completed_at=? WHERE id=?', ("completed", datetime.datetime.now(), deal_id))
    conn.commit()
    conn.close()

def add_rating(deal_id, from_user, to_user, rating, comment):
    conn, cur = db()
    cur.execute('''INSERT INTO ratings (deal_id, from_user, to_user, rating, comment)
        VALUES (?,?,?,?,?)''', (deal_id, from_user, to_user, rating, comment))
    cur.execute('UPDATE users SET rating_count=rating_count+1, rating_sum=rating_sum+? WHERE tg_id=?', (rating, to_user))
    conn.commit()
    conn.close()

def add_referral(from_user_id, user_id, amount, deal_id):
    conn, cur = db()
    cur.execute('''INSERT INTO referrals (user_id, from_user, amount, deal_id)
        VALUES (?,?,?,?)''', (user_id, from_user_id, amount, deal_id))
    cur.execute('UPDATE users SET referral_earnings=referral_earnings+? WHERE tg_id=?', (amount, from_user_id))
    conn.commit()
    conn.close()

def get_user_deals(tg_id):
    conn, cur = db()
    cur.execute('''SELECT * FROM deals WHERE buyer_id=? OR seller_id=? ORDER BY created_at DESC''', (tg_id, tg_id))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_deals_by_state(state):
    conn, cur = db()
    cur.execute('SELECT * FROM deals WHERE state=?', (state,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_to_blacklist(tg_id, reason):
    conn, cur = db()
    cur.execute('INSERT INTO blacklist (tg_id, reason) VALUES (?,?)', (tg_id, reason))
    conn.commit()
    conn.close()

def is_blacklisted(tg_id):
    conn, cur = db()
    cur.execute('SELECT 1 FROM blacklist WHERE tg_id=?', (tg_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row)

def get_blacklist():
    conn, cur = db()
    cur.execute('SELECT tg_id, reason FROM blacklist ORDER BY created_at DESC')
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_rating(tg_id):
    conn, cur = db()
    cur.execute('SELECT rating_count, rating_sum FROM users WHERE tg_id=?', (tg_id,))
    row = cur.fetchone()
    conn.close()
    if not row or row[0] == 0: return (0, 0)
    return (row[0], row[1])

def get_user_referrals(tg_id):
    conn, cur = db()
    cur.execute('SELECT * FROM referrals WHERE from_user=?', (tg_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_admin_earnings():
    conn, cur = db()
    cur.execute("SELECT SUM(amount*0.02) as total FROM deals WHERE state='completed'")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0
