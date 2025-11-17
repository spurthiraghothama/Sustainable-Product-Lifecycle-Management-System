import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',           
        password='Spurthi1-5',  
        database='circular_economy_db'
    )
    return conn
