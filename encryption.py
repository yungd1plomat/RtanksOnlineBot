import hashlib
import logging

class AesEncryption:

    def __init__(self, last_key = 1, private_key = 1):
        self.last_key = last_key
        self.private_key = private_key

    def parse_key(self, data):
        bytes_data = [int(x) & 0xFF for x in data.split(",")]
        bytes_data = bytes(bytes_data)
        md5_hash = hashlib.md5(bytes_data).hexdigest()
        if md5_hash == "8dd0ce3a2d70d540a655fabbb68a3d4d":
            self.private_key = 2
        elif md5_hash == "72e4f70e0f4b3741b037156cca10bfdf":
            self.private_key = 5
        elif md5_hash == "102d10b47526a101b1f96fe778a9a760":
            self.private_key = 7
        elif md5_hash == "859f33c3119665cde3cbf27f086427ac":
            self.private_key = 10
        elif md5_hash == "8aabe5b1e1635f17c99dab8c38679178":
            self.private_key = 12
        elif md5_hash == "aec19fd4b4f2a32e1f52dd3bb452b6ef":
            self.private_key = 13
        elif md5_hash == "58d035242d91e6b7cd6f56720cbc8167":
            self.private_key = 22
        elif md5_hash == "439c905f13fc7fb0bbef8c0980111588":
            self.private_key = 26
        elif md5_hash == "eb7f0ea4fc5dbd8d02369af6f5648ef3":
            self.private_key = 28
        elif md5_hash == "7ec1b047be1b86dc63f44cf80e9682ef":
            self.private_key = 32
        else:
            raise ValueError("Failed to parse private key:", md5_hash)
        logging.debug(f"Parsed private key: {self.private_key}")

    def encrypt(self, data):
        key = (self.last_key + 1) % 9
        if key <= 0:
            key = 1
        self.last_key = key
        w = list(map(ord, data))
        for i in range(len(w)):
            w[i] += key + self.private_key
        data = ''.join(map(chr, w))
        encrypted_data = str(key) + data + "end~"
        return encrypted_data

    def decrypt(self, data):
        key = int(data[0])
        data_string = data[1:].replace("end~", "")
        w = list(map(ord, data_string))
        for i in range(len(w)):
            w[i] -= key + self.private_key
        data_string = ''.join(map(chr, w))
        return data_string
