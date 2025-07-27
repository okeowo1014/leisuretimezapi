import mysql
# # from .wrapper import SSHDBWrapper

# class SSHDBWrapper:
#     def __init__(self):
#         self.ssh_host = 'www.findpropty.com'
#         self.ssh_username = 'id_rsa'
#         self.ssh_password = 'aXIR{378tkSf'
#         self.ssh_private_key_path = 'SHA256:ELntcWox0oOSfBC7sodVV5wm48hdpKnmrkMnqHRmrww'
        
#         self.database_name = 'findepbl_leisuretimez_data'
#         self.database_user = 'findepbl_leisuretimez',
#         self.database_password = 'K1Z#vApAn7KA'
#         self.database_port = 3306


# db_wrapper.py

from sshtunnel import SSHTunnelForwarder
import mysql.connector
# from decouple import config

class SSHDBWrapper:
    _instance = None
    _is_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SSHDBWrapper, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._is_initialized:
            # SSH Configuration
            # self.ssh_host = config('SSH_HOST')
            # self.ssh_user = config('SSH_USER')
            # self.ssh_password = config('SSH_PASSWORD', default=None)
            # self.ssh_key = config('SSH_KEY_PATH', default=None)

            # # Database Configuration
            # self.db_name = config('DB_NAME')
            # self.db_user = config('DB_USER')
            # self.db_password = config('DB_PASSWORD')
            # self.db_port = config('DB_PORT', default=3306, cast=int)
            self.ssh_host = 'premium296.web-hosting.com'
            self.ssh_user = 'findepbl'
            self.ssh_password = 'temiTITAYO@05023'
            self.ssh_key = None #'SHA256:ELntcWox0oOSfBC7sodVV5wm48hdpKnmrkMnqHRmrww'
        
            self.db_name = 'findepbl_leisuretimez_data'
            self.db_user = 'findepbl_leisuretimez'
            self.db_password = 'K1Z#vApAn7KA'
            self.db_port = 3306

            self.tunnel = None
            self.local_port = None
            self._is_initialized = True

    def connect(self):
        """Establish SSH tunnel connection"""
        try:
            if self.tunnel is None or not self.tunnel.is_active:
                self.tunnel = SSHTunnelForwarder(
                    (self.ssh_host, 21098),
                    ssh_username=self.ssh_user,
                    ssh_password=self.ssh_password if self.ssh_password else None,
                    ssh_pkey=self.ssh_key if self.ssh_key else None,
                    remote_bind_address=('127.0.0.1', self.db_port),
                    local_bind_address=('127.0.0.1', 5522)
                )
                self.tunnel.start()
                self.local_port = self.tunnel.local_bind_port
                print(f"SSH tunnel established on local port: {self.local_port}")
        except Exception as e:
            print(f"Error establishing SSH tunnel: {e}")
            raise

    def close(self):
        """Close SSH tunnel connection"""
        if self.tunnel and self.tunnel.is_active:
            self.tunnel.stop()
            self.tunnel = None
            print("SSH tunnel closed")

    def get_database_config(self):
        """Get Django database configuration"""
        if not self.tunnel or not self.tunnel.is_active:
            self.connect()
        
        return {
            'ENGINE': 'mysql.connector.django',
            'NAME': self.db_name,
            'USER': self.db_user,
            'PASSWORD': self.db_password,
            'HOST': '127.0.0.1',
            'PORT': self.local_port,
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'use_pure': True,
                'autocommit': True,
                'connection_timeout': 180,
                'buffered': True,
            }
        }

    def test_connection(self):
        """Test database connection through SSH tunnel"""
        try:
            if not self.tunnel or not self.tunnel.is_active:
                self.connect()
                print("SSH tunnel connection successful!")
            
            config = self.get_database_config()
            print("Testing database connection...")
            print(config)
            conn = mysql.connector.connect(
                host=config['HOST'],
                port=config['PORT'],
                database=config['NAME'],
                user=config['USER'],
                password=config['PASSWORD']
            )
            print(conn)
            print("Database connection successful!")
            conn.close()
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

def test_connection():
    wrapper = SSHDBWrapper()
    wrapper.connect()
    
    try:
        connection = mysql.connector.connect(
            **wrapper.get_database_config()
        )
        print("Successfully connected to database!")
        connection.close()
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        wrapper.close()

connect=SSHDBWrapper().test_connection()