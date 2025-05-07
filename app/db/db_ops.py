# import psycopg2
# print(f"Connecting to the database...")
# conn = psycopg2.connect(
#     database = "taippa",
#     host="magmostafa-4523.postgres.pythonanywhere-services.com",
#     user="super",
#     password="drowsapp_2025",
#     port="14523"
# )
# cursor = conn.cursor()
# cursor.execute("INSERT INTO dummy VALUES ('test');")
# conn.commit()
# cursor.close()
# conn.close()

import psycopg2
import sshtunnel

sshtunnel.SSH_TIMEOUT = 10.0
sshtunnel.TUNNEL_TIMEOUT = 10.0

postgres_hostname = "magmostafa-4523.postgres.pythonanywhere-services.com"  # You will have your own here
postgres_host_port = 14523  #  You will have your own port here

def test():
    with sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username='magmostafa',
            ssh_password='Drowssap_2024',
            remote_bind_address=(postgres_hostname, postgres_host_port)
    ) as tunnel:
        connection = psycopg2.connect(
            user='super', password='drowsapp_2025',
            host='127.0.0.1', port=tunnel.local_bind_port,
            database='taippa',
        )
        # Do stuff inside the context manager block
        cursor = connection.cursor()
        cursor.execute("INSERT INTO dummy VALUES ('test33345');")
        connection.commit()
        print('entry added successfully')
        cursor.close()
        connection.close()
        connection.close()
    return 'Done'