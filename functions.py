import sqlite3

# Wrapper for sqlite3 to make life easier
class Connection(object):
    def __init__(self, db=None):
        assert db != None, "A database must be specified"
        self.conn = sqlite3.connect("databases/{}.db".format(db), detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()

    def query(self, arg):
        self.cur.execute(arg)
        self.conn.commit()
        return self.cur

    def queryWithValues(self, arg, values):
        self.cur.execute(arg, values)
        self.conn.commit()
        return self.cur

    def __del__(self):
        self.conn.close()
