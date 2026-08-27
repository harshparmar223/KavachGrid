import hashlib
import os
import base64

def make_mosquitto_hash(password):
    salt = os.urandom(12)
    iterations = 101
    key = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, iterations, dklen=64)
    salt_b64 = base64.b64encode(salt).decode('ascii').replace('=', '')
    key_b64 = base64.b64encode(key).decode('ascii').replace('=', '')
    return f"$7${iterations}${salt_b64}${key_b64}"

users = {
    "feeder_node": "feeder123",
    "consumer_node": "consumer123",
    "localization_node": "local123",
    "kavachgrid_backend": "backend123",
    "dashboard": "dashboard123"
}

with open("mqtt/passwd", "w") as f:
    for user, pwd in users.items():
        f.write(f"{user}:{make_mosquitto_hash(pwd)}\n")
