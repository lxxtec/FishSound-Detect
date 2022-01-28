from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import base64
from PyQt5.QtCore import QSettings
from datetime import timedelta, datetime
from datetime import date
from random import choice
import argparse
from uuid import getnode


class Encryption:
    def __init__(self, appID="fishdetect"):
        self.privateKey = """-----BEGIN RSA PRIVATE KEY-----
                            MIICXAIBAAKBgQDR//qsgNjfQ0R8m6L9vglWKNvA0V/aCIonkK81JJolnadEbzX7
                            FXe/7JL5CSoJNYn89vn3L74EzYCA1yHNej6cvIPvtZQ9OczBdp/tP/VrTCr3/89d
                            P2FrJKh4QT04NGQ7Ed3GlzmGKzwCKeXrh2INeNSWBPDs+wCJeXy6bvnccwIDAQAB
                            AoGAHIRBwpYWnS7RyIgL+KALPYd72/GyrfV16UyE9lb7lbsUYT8m2es+4TGbfbTo
                            X+rEy7SwGgiCKb3MQvKz1ObSRJBBaFQdtu1kvzu1WWNpzRkvrUI3WP2Ak6YzH3UD
                            IE7FBqNIHcMAchLebHnwBCHpb+yfC4yf79HKY15BXLLn+iECQQDUlb6zzs/dufoW
                            YTEzxQB5NY6eGI6v/PRU0YHHwm5eZdax2oqHjk455rPy811EF5lTm2s2HvuFa/ws
                            5ZuR8rnhAkEA/OMV4VYwap+vCp8nfoNGxEQO/Rpm6/kIzdUpEcbsAzQoY8m7FkO7
                            XSz+sipYPjYxaEqUdZM09zxLWYrpLc+o0wJAXmY4jsPxjjY9lZ6HKMP8V9auhAnH
                            ouKi5N870CbIt+ZlFglDprpMhm2pzuK+sbQBBB1p2FidvDudeZpkIMU2QQJANquB
                            F23imapb1RgDGb6XleaAtwb2KR11YcorTsSKUUb9VFVQNMf/wWzwwuOUoB5nH/y/
                            i4t/b9OBFqKJNnYmMQJBAJHHwbg+pIu1KmswAUwoezIf/VKAVY/5KoaI4y4y4pEe
                            k5L2B7+48xZhfvVHCJyNyRxPuAS76CK3MLGLsL3Re1s=
                            -----END RSA PRIVATE KEY-----"""

        self.settings = QSettings(
            "HKEY_CURRENT_USER\\Software\\SilentCode", QSettings.NativeFormat)
        self.tryMode = False
        self.singleReg = False
        self.outDated = False
        self.mac = self.AES_encrypt(self.get_mac())
        self.settings.beginGroup(appID)
        if self.settings.value('regMask') == None:  # 初次运行，自动进入试用模式
            self.settings.setValue('regMask', self.mac)
            self.settings.setValue('isRegistered', 0)
            self.settings.setValue('isTryMode', 1)
            self.settings.setValue('lastDate', self.AES_encrypt(
                str(date.today()+timedelta(days=10))))
            self.settings.setValue(
                'firstRun', self.AES_encrypt(str(date.today())))
            self.settings.setValue(
                'thisRun', self.AES_encrypt(str(date.today())))
            self.tryMode = True

        self.checkRegStatus()
        self.checkWorking()

    def get_mac(self):
        address = hex(getnode())[2:]
        mac = '-'.join(address[i:i + 2] for i in range(0, len(address), 2))
        return mac

    def checkRegStatus(self):
        if self.settings.value('isRegistered') == 0:
            self.isRegistered = False
        else:
            self.isRegistered = True

        if self.settings.value('isTryMode') == 0:
            self.tryMode = False
        else:
            self.tryMode = True
        self.localCode = self.settings.value('regMask')
        self.lastDate = self.AES_decrypt(str(self.settings.value('lastDate')))
        self.firstDate = self.AES_decrypt(str(self.settings.value('firstRun')))
        self.thisDate = self.AES_decrypt(str(self.settings.value('thisRun')))

    def checkWorking(self):
        # if self.tryMode==True or self.isRegistered==True:
        #     self.working=True
        hasLeft = (datetime.strptime(self.lastDate,
                   '%Y-%m-%d').date()-date.today()).days > 2
        if hasLeft == False:
            self.outDated = True
        isValid1 = (date.today()-datetime.strptime(self.firstDate,
                    '%Y-%m-%d').date()).days > -1
        isValid2 = (date.today()-datetime.strptime(self.thisDate,
                    '%Y-%m-%d').date()).days > -1
        isValid3 = (self.mac == self.localCode)
        if hasLeft and isValid1 and isValid2 and isValid3:
            self.working = True
        else:
            self.working = False

    def decrypt(self, code):
        if code == '':
            return
        if self.settings.value('lastCode') == code:
            return
        pri_key = RSA.importKey(self.privateKey)
        cipher = PKCS1_cipher.new(pri_key)
        back_text = cipher.decrypt(base64.b64decode(code), 0)
        ss = back_text.decode('utf-8')
        s1, s2 = ss.split('.')
        if s1 == self.localCode:
            self.isRegistered = True
            self.tryMode = False
            self.settings.setValue('isRegistered', 1)
            self.settings.setValue('isTryMode', 0)
            # 当前最晚日期
            lastDate = datetime.strptime(self.lastDate, '%Y-%m-%d').date()
            self.settings.setValue('lastDate', self.AES_encrypt(
                str(lastDate+timedelta(days=30*eval(s2)))))
            # 重制机器码
            #self.settings.setValue('regMask', self.randStr(10))
            self.checkRegStatus()
            self.checkWorking()
            self.singleReg = True
            self.settings.setValue('lastCode', code)
            # print('解密成功')

    @staticmethod
    def randStr(num):
        H = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        salt = ''
        for i in range(num):
            salt += choice(H)
        return salt

    def AES_encrypt(self, message):
        key = 'aes_keysaes_keysaes_keys'
        mode = AES.MODE_OFB
        cryptor = AES.new(key.encode('utf-8'), mode, b'0000000000000000')
        length = 16
        count = len(message)
        if count % length != 0:
            add = length - (count % length)
        else:
            add = 0
        message = message + ('\0' * add)
        ciphertext = cryptor.encrypt(message.encode('utf-8'))
        result = b2a_hex(ciphertext)
        return result.decode('utf-8')

    def AES_decrypt(self, code):
        key = 'aes_keysaes_keysaes_keys'
        mode = AES.MODE_OFB
        cryptor = AES.new(key.encode('utf-8'), mode, b'0000000000000000')
        plain_text = cryptor.decrypt(a2b_hex(code))
        return plain_text.decode('utf-8').rstrip('\0')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--appID', type=str, default='', help='软件id')
    parser.add_argument('--checkWorking', type=int, default=0, help='检查是否工作')
    parser.add_argument('--checkTryMode', type=int, default=0, help='检查是否试用')
    parser.add_argument('--checkEndDate', type=int, default=0, help='检查截至日期')
    parser.add_argument('--activateCode', type=str, default='', help='输入注册码')

    args = parser.parse_args()

    crypt = Encryption(args.appID)
    if args.checkWorking:
        print(crypt.working, crypt.localCode)

    if args.checkEndDate:
        print(crypt.lastDate)

    if args.checkTryMode:
        print(crypt.tryMode)

    if args.activateCode:
        crypt.decrypt(str(args.activateCode))
        print(crypt.working, crypt.localCode)
