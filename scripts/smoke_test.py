#!/usr/bin/env python3
"""Quick smoke test to verify DB init and config loading."""
import logging
from Src import config, database

def main():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    logging.info('Running smoke test...')
    try:
        database.init_db()
        logging.info('Database initialized (DB_FILE=%s)', config.DB_FILE)
    except Exception as e:
        logging.exception('Database init failed: %s', e)
        raise

    logging.info('Config ADMIN_IDS: %s', config.ADMIN_IDS)
    print('SMOKE TEST OK')

if __name__ == '__main__':
    main()
