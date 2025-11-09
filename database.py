import sqlite3

def init_db():
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE,
        username TEXT,
        ton_address TEXT,
        referral_id INTEGER DEFAULT NULL,
        rating_count INTEGER DEFAULT 0,
        rating_sum INTEGER DEFAULT 0,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        referral_earnings REAL DEFAULT 0
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS deals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER,
        seller_id INTEGER,
        currency TEXT,
        amount REAL,
        description TEXT,
        state TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        deal_tx_hash TEXT,
        memo TEXT,
        referral_id INTEGER DEFAULT NULL
    )''')
    cur.execute('''
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
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    # تسجيل المستخدم (أو التعديل إذا كان سابقًا)
    cur.execute('INSERT OR IGNORE INTO users (tg_id, username, ton_address, referral_id) VALUES (?, ?, ?, ?)',
                (tg_id, username, ton_address, referral_id))
    conn.commit()
    conn.close()

def get_user_wallet(tg_id):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('SELECT ton_address FROM users WHERE tg_id=?', (tg_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_user(tg_id):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE tg_id=?', (tg_id,))
    row = cur.fetchone()
    conn.close()
    return row

def add_deal(buyer_id, seller_id, currency, amount, description, memo, referral_id=None):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('''INSERT INTO deals
        (buyer_id, seller_id, currency, amount, description, state, memo, referral_id)
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)''',
        (buyer_id, seller_id, currency, amount, description, memo, referral_id))
    deal_id = cur.lastrowid
    conn.commit()
    conn.close()
    return deal_id

def get_deal(deal_id):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('SELECT * FROM deals WHERE id=?', (deal_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_deal_state(deal_id, new_state):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('UPDATE deals SET state=? WHERE id=?', (new_state, deal_id))
    conn.commit()
    conn.close()

def set_deal_tx_hash(deal_id, tx_hash):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('UPDATE deals SET deal_tx_hash=? WHERE id=?', (tx_hash, deal_id))
    conn.commit()
    conn.close()

def complete_deal(deal_id):
    import datetime
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('UPDATE deals SET state=?, completed_at=? WHERE id=?', ("completed", datetime.datetime.now(), deal_id))
    conn.commit()
    conn.close()

def add_rating(deal_id, from_user, to_user, rating, comment):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('''INSERT INTO ratings (deal_id, from_user, to_user, rating, comment)
        VALUES (?,?,?,?,?)''', (deal_id, from_user, to_user, rating, comment))
    # إضافة للتقييم العائد للمستخدم
    cur.execute('UPDATE users SET rating_count=rating_count+1, rating_sum=rating_sum+? WHERE tg_id=?', (rating, to_user))
    conn.commit()
    conn.close()

def add_referral(from_user_id, user_id, amount, deal_id):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('''INSERT INTO referrals (user_id, from_user, amount, deal_id)
        VALUES (?,?,?,?)''', (user_id, from_user_id, amount, deal_id))
    # زيادة أرباح المحيل
    cur.execute('UPDATE users SET referral_earnings=referral_earnings+? WHERE tg_id=?', (amount, from_user_id))
    conn.commit()
    conn.close()

def get_user_deals(tg_id):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('''SELECT * FROM deals WHERE buyer_id=? OR seller_id=? ORDER BY created_at DESC''', (tg_id, tg_id))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_deals_by_state(state):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('SELECT * FROM deals WHERE state=?', (state,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_to_blacklist(tg_id, reason):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('INSERT INTO blacklist (tg_id, reason) VALUES (?,?)', (tg_id, reason))
    conn.commit()
    conn.close()

def is_blacklisted(tg_id):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM blacklist WHERE tg_id=?', (tg_id,))
    row = cur.fetchone()
    conn.close()
    return bool(row)

def get_blacklist():
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('SELECT tg_id, reason FROM blacklist ORDER BY created_at DESC')
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_rating(tg_id):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('SELECT rating_count, rating_sum FROM users WHERE tg_id=?', (tg_id,))
    row = cur.fetchone()
    conn.close()
    if not row or row[0] == 0:
        return (0, 0)
    return (row[0], row[1])

def get_user_referrals(tg_id):
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute('SELECT * FROM referrals WHERE from_user=?', (tg_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_admin_earnings():
    conn = sqlite3.connect("db.sqlite3")
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount*0.02) as total FROM deals WHERE state='completed'")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0