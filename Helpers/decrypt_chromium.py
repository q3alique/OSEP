#!/usr/bin/env python3
import os
import sys
import base64
import sqlite3
import shutil
from Crypto.Cipher import AES

# To install dependencies: pip3 install pycryptodome

def decrypt_password(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16].decode()  # Remove suffix bytes
        return decrypted_pass
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 decrypt_chromium.py <B64_MASTER_KEY> <LOGIN_DATA_FILE>")
        sys.exit(1)

    master_key_b64 = sys.argv[1]
    login_data_file = sys.argv[2]

    # 1. Decode Master Key
    master_key = base64.b64decode(master_key_b64)

    # 2. Copy DB to avoid 'file in use' errors
    temp_db = "temp_login_data.db"
    shutil.copyfile(login_data_file, temp_db)

    # 3. Connect to DB
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
        print(f"{'URL':<50} | {'Username':<30} | {'Password'}")
        print("-" * 100)

        for row in cursor.fetchall():
            url = row[0]
            username = row[1]
            password_blob = row[2]

            if password_blob.startswith(b'v10') or password_blob.startswith(b'v11'):
                password = decrypt_password(password_blob, master_key)
            else:
                password = "[Legacy DPAPI - Use different method]"

            if username or password:
                print(f"{url:<50} | {username:<30} | {password}")

    except Exception as e:
        print(f"[-] Error querying database: {e}")
    finally:
        conn.close()
        os.remove(temp_db)

if __name__ == "__main__":
    main()
