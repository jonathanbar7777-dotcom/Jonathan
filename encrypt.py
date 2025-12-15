import os
import base64
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from constants import CHUNK_SIZE

class Encryption:
    def __init__(self, rsa_private_key_path=None, rsa_public_key_path=None):
        """
        אם צד הלקוח: מספקים rsa_public_key_path של השרת
        אם צד השרת: מספקים rsa_private_key_path
        """
        self.aes_key = os.urandom(32)  # AES 256
        self.nonce = os.urandom(12)    # AES-GCM nonce
        self.rsa_public_key = None
        self.rsa_private_key = None

        if rsa_public_key_path:
            with open(rsa_public_key_path, 'rb') as f:
                self.rsa_public_key = RSA.import_key(f.read())
        if rsa_private_key_path:
            with open(rsa_private_key_path, 'rb') as f:
                self.rsa_private_key = RSA.import_key(f.read())

    # -----------------------------
    # AES ENCRYPT/DECRYPT
    # -----------------------------
    def encrypt_data(self, data: bytes) -> bytes:
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=self.nonce)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return ciphertext + tag

    def decrypt_data(self, data: bytes) -> bytes:
        ciphertext, tag = data[:-16], data[-16:]
        cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=self.nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)

    # -----------------------------
    # SOCKET MESSAGE AES
    # -----------------------------
    def send_encrypted_message(self, sock, message: str):
        if isinstance(message, str):
            message = message.encode()
        encrypted_bytes = self.encrypt_data(message)
        sock.sendall(len(encrypted_bytes).to_bytes(4, byteorder='big'))
        sock.sendall(encrypted_bytes)

    def receive_encrypted_message(self, sock) -> str:
        raw_length = sock.recv(4)
        if not raw_length:
            return ""
        message_length = int.from_bytes(raw_length, byteorder='big')
        data = b''
        while len(data) < message_length:
            chunk = sock.recv(min(CHUNK_SIZE, message_length - len(data)))
            if not chunk:
                break
            data += chunk
        decrypted = self.decrypt_data(data)
        return decrypted.decode()

    # -----------------------------
    # AES KEY EXCHANGE
    # -----------------------------
    def send_aes_key(self, sock):
        """
        שולח את AES key לשרת (מוצפן עם public key של השרת)
        """
        if not self.rsa_public_key:
            raise ValueError("RSA public key not set")
        cipher_rsa = PKCS1_OAEP.new(self.rsa_public_key)
        payload = self.aes_key + self.nonce
        encrypted_payload = cipher_rsa.encrypt(payload)
        sock.sendall(len(encrypted_payload).to_bytes(4, 'big'))
        sock.sendall(encrypted_payload)

    def receive_aes_key(self, sock):
        """
        מקבל את AES key מהלקוח (מוצפן עם private key של השרת)
        """
        if not self.rsa_private_key:
            raise ValueError("RSA private key not set")
        raw_length = sock.recv(4)
        if not raw_length:
            raise ValueError("Failed to receive AES key length")
        length = int.from_bytes(raw_length, 'big')
        data = b''
        while len(data) < length:
            chunk = sock.recv(min(CHUNK_SIZE, length - len(data)))
            if not chunk:
                raise ValueError("Incomplete AES key received")
            data += chunk
        cipher_rsa = PKCS1_OAEP.new(self.rsa_private_key)
        payload = cipher_rsa.decrypt(data)
        self.aes_key = payload[:32]
        self.nonce = payload[32:]
