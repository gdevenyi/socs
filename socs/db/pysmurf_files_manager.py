"""
Script to create, update, or drop the `pysmurf_files` database
"""
import argparse
import mysql.connector
import getpass


class Column:
    def __init__(self, name, type, opts="", fmt="%s"):
        self.name = name
        self.type = type
        self.opts = opts
        self.fmt = fmt

    def __str__(self):
        return " ".join([self.name, self.type, self.opts])


columns = [
    Column("id", "INT", opts="NOT NULL AUTO_INCREMENT PRIMARY KEY"),
    Column("path", "VARCHAR(260)", opts="UNIQUE NOT NULL"),
    Column("type", "VARCHAR(32)", opts="NOT NULL"),
    Column("timestamp", "TIMESTAMP"),
    Column("action_timestamp", "INT"),
    Column("format", "VARCHAR(32)"),
    Column("plot", "TINYINT(1)"),
    Column("site", "VARCHAR(32)"),
    Column("pub_id", "VARCHAR(32)"),
    Column("script_id", "VARCHAR(32)"),
    Column("instance_id", "VARCHAR(32)"),
    Column("copied", "TINYINT(1)"),
    Column("failed_copy_attempts", "INT"),
    Column("md5sum", "BINARY(16)", opts="NOT NULL", fmt="UNHEX(%s)"),
    Column("pysmurf_version", "VARCHAR(64)"),
    Column("socs_version", "VARCHAR(64)"),
]
col_dict = {c.name: c for c in columns}


def add_entry(cur, entry):
    """
    Adds entry to table.
    """

    if not set(col_dict.keys()).issuperset(entry.keys()):
        raise RuntimeError(
            "Invalid file entry provided... \n"
            "Keys given: {}\n"
            "Keys allowed: {}".format(entry.keys(), col_dict.keys())
        )

    keys, vals, fmts = [], [], []
    for k in list(entry.keys()):
        if entry[k] is None:
            continue
        keys.append(k)
        vals.append(entry[k])
        fmts.append(col_dict[k].fmt)

    query = "INSERT INTO pysmurf_files ({}) VALUES ({})"\
            .format(", ".join(keys), ", ".join(fmts))

    cur.execute(query, tuple(vals))


def create_table(cur, update=True):
    """
    Creates new pysmurf_files table from scratch.

    Args:
        cur (MySQL Cursor):
            cursor to files db
        update (optional, bool):
            Add additional columns if existing table is not up to date.
    """

    cur.execute("SHOW TABLES;")
    table_names = [x[0] for x in cur.fetchall()]

    if 'pysmurf_files' not in table_names:
        print("Creating pysmurf_files table...")
        col_strings = [str(c) for c in columns]
        query = "CREATE TABLE pysmurf_files ({});".format(", ".join(col_strings))

        try:
            cur.execute(query)
            print("Created table pysmurf_files")
        except mysql.connector.errors.ProgrammingError as e:
            print(e)
    elif update:
        print("Found pysmurf_files table. Calling update_columns")
        update_columns(cur)
    else:
        print("Found pysmurf_files table and not updating")


def update_columns(cur):
    """
    Makes sure columns of existing table are up to date, and adds any that are
    missing.
    """
    cur.execute("DESCRIBE pysmurf_files");
    existing_cols = set([c[0] for c in cur.fetchall()])

    try:
        for c in columns:
            if c.name not in existing_cols:
                cur.execute("ALTER TABLE pysmurf_files ADD {}".format(str(c)))
                print("Added column {}".format(c.name))
    except mysql.connector.errors.ProgrammingError as e:
        print(e)


def drop_table(cur):
    """
    Drops pysmurf_files.
    """
    try:
        cur.execute("DROP TABLE pysmurf_files;")
        con.commit()
        print("pysmurf_files dropped.")
    except mysql.connector.errors.ProgrammingError as e:
        print(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', choices=['create', 'update', 'drop', 'test'])
    parser.add_argument('--password', '-p', type=str,
                        help="Password for development database")
    args = parser.parse_args()

    sql_config = {
        'user': 'development',
        'database': 'files',
        'passwd': args.password
    }

    if sql_config['passwd'] is None:
        sql_config['passwd'] = getpass.getpass("Password for development db: ")

    con = mysql.connector.connect(**sql_config)
    cur = con.cursor()
    try:
        if args.cmd == 'test':
            import datetime
            entry = {
                'path':'/data/pysmurf_test/1568779322_fake_tuning4.txt',
                'type': 'fake_tuning',
                'timestamp': datetime.datetime(2019, 9, 18, 4, 2, 2, 188764),
                'plot': 1,
                'format': 'txt',
                'md5sum': '7ac66c0f148de9519b8bd264312c4d64',
                'site': 'observatory',
                'instance_id': 'pysmurf-monitor',
                'copied': 0,
                'failed_copy_attempts': 0,
                'socs_version': '0+untagged.140.g5307c6b.dirty'
            }

            add_entry(cur, entry)
            con.commit()
        if args.cmd == 'create':
            create_table(cur)
            con.commit()
        elif args.cmd == 'update':
            update_columns(cur)
            con.commit()
        elif args.cmd == 'drop':
            while True:
                resp = input("Are you sure you want to drop pysmurf_files? [y/n]: ")
                if resp.lower().strip() == 'y':
                    drop_table(cur)
                    con.commit()
                    break
                elif resp.lower().strip() == 'n':
                    break
                else:
                    print("Could not recognize input")
    finally:
        print("Closing connection")
        con.close()



