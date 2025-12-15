from Crypto.PublicKey import RSA

# מיקום הקבצים
private_key_file = "server_private.pem"
public_key_file = "server_public.pem"

# יצירת מפתח פרטי 2048 ביט
key = RSA.generate(2048)

# שמירת המפתח הפרטי
with open(private_key_file, "wb") as f:
    f.write(key.export_key())

# יצירת המפתח הציבורי
public_key = key.publickey()
with open(public_key_file, "wb") as f:
    f.write(public_key.export_key())

print("Keys generated successfully!")
print(f"Private key: {private_key_file}")
print(f"Public key: {public_key_file}")
