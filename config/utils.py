from Crypto.Cipher import AES
import base64
import os
from django.conf import settings
from twilio.rest import Client


class AESEncryption:
    def __init__(self):
        self.key = settings.DATA_ENCRYPTION_KEY[:32].encode("utf-8")

    def pad(self, text):
        return text + (16 - len(text) % 16) * chr(16 - len(text) % 16)

    def unpad(self, text):
        return text[:-ord(text[-1])]

    def encrypt(self, raw):
        raw = self.pad(raw)
        iv = os.urandom(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode("utf-8"))).decode()

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(enc[16:]).decode("utf-8"))

def send_sms(to, message):
    print(" FAKE SMS SENT")
    print(f"To      : {to}")
    print(f"Message : {message}")
    print("-" * 40)
    return True




#def send_sms(to, message):
    """
    Sends an SMS notification using Twilio.
    """
    #try:
    #    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    #    message = client.messages.create(
    #        body=message,
    #        from_=settings.TWILIO_PHONE_NUMBER,
    #       to=to
    #    )
    #    print(f"SMS sent: {message.sid}")
    #    return True
    #except Exception as e:
       # print(f"SMS error: {str(e)}")
        #return False
