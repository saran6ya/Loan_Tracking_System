
import os
import mysql.connector
import streamlit as st


def get_connection():
    # Use cloud database credentials when deployed.
    if "database" in st.secrets:
        config = dict(st.secrets["database"])
    else:
        # Local MySQL configuration.
        config = {
            "host": "127.0.0.1",
            "port": 3306,
            "user": "root",
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": "loantracking",
            "use_pure": True,
        }

    return mysql.connector.connect(**config)
