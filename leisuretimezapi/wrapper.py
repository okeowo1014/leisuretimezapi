"""
SSH tunnel wrapper for connecting to a remote MySQL database.

Uses SSHTunnelForwarder to create an SSH tunnel and provides
Django-compatible database configuration.
"""

import logging
import os

import paramiko

# Monkey-patch: newer paramiko versions removed DSSKey (DSA support),
# but sshtunnel still references it. Provide a stub to prevent AttributeError.
if not hasattr(paramiko, 'DSSKey'):
    paramiko.DSSKey = paramiko.RSAKey

from sshtunnel import SSHTunnelForwarder

logger = logging.getLogger(__name__)


class SSHDBWrapper:
    """Singleton SSH tunnel manager for remote MySQL database access."""

    _instance = None
    _is_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._is_initialized:
            self.ssh_host = os.environ.get('SSH_HOST', 'premium296.web-hosting.com')
            self.ssh_port = int(os.environ.get('SSH_PORT', '21098'))
            self.ssh_user = os.environ.get('SSH_USER', '')
            self.ssh_password = os.environ.get('SSH_PASSWORD', '')
            self.ssh_key = os.environ.get('SSH_KEY_PATH', None) or None

            self.db_name = os.environ.get('DB_NAME', '')
            self.db_user = os.environ.get('DB_USER', '')
            self.db_password = os.environ.get('DB_PASSWORD', '')
            self.db_port = int(os.environ.get('DB_PORT', '3306'))
            self.local_bind_port = int(os.environ.get('DB_LOCAL_PORT', '5522'))

            self.tunnel = None
            self.local_port = None
            self._is_initialized = True

    def connect(self):
        """Establish SSH tunnel connection."""
        try:
            if self.tunnel is None or not self.tunnel.is_active:
                self.tunnel = SSHTunnelForwarder(
                    (self.ssh_host, self.ssh_port),
                    ssh_username=self.ssh_user,
                    ssh_password=self.ssh_password if self.ssh_password else None,
                    ssh_pkey=self.ssh_key if self.ssh_key else None,
                    remote_bind_address=('127.0.0.1', self.db_port),
                    local_bind_address=('127.0.0.1', self.local_bind_port),
                )
                self.tunnel.start()
                self.local_port = self.tunnel.local_bind_port
                logger.info(
                    "SSH tunnel established on local port: %s", self.local_port
                )
        except Exception:
            logger.exception("Error establishing SSH tunnel")
            raise

    def close(self):
        """Close SSH tunnel connection."""
        if self.tunnel and self.tunnel.is_active:
            self.tunnel.stop()
            self.tunnel = None
            logger.info("SSH tunnel closed")

    def get_database_config(self):
        """Get Django database configuration dictionary."""
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
            },
        }

    def test_connection(self):
        """Test database connection through SSH tunnel."""
        import mysql.connector

        try:
            if not self.tunnel or not self.tunnel.is_active:
                self.connect()

            config = self.get_database_config()
            conn = mysql.connector.connect(
                host=config['HOST'],
                port=config['PORT'],
                database=config['NAME'],
                user=config['USER'],
                password=config['PASSWORD'],
            )
            logger.info("Database connection successful!")
            conn.close()
            return True
        except Exception:
            logger.exception("Database connection failed")
            return False
