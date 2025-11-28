import psycopg2

class PostgresConnection:
    def __init__(self, host: str, dbname: str, user: str, password: str, port: int):
            self.host=host
            self.dbname=dbname
            self.user=user
            self.password=password
            self.port=port
            self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                port=self.port
            )
            print("[OK] Connected to PostgreSQL")
            return self.conn
        except Exception as e:
            print(f"[FAIL] Failed to connect to PostgreSQL: {e}")
            raise
    
    def close(self):
        if self.conn:
            self.conn.close()
            print("PostgreSQL connection closed.")