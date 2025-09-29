# Configure PyMySQL as MySQLdb so Django's MySQL backend works without mysqlclient
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    # Do not fail at import time; if database is used, Django will raise a clearer error
    pass
