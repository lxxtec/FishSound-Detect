from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import base64
from PyQt5.QtCore import QSettings
from datetime import timedelta,datetime
from datetime import date
from random import choice

class Encryption:
    def __init__(self):
        self.privateKey="""-----BEGIN RSA PRIVATE KEY-----
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

        self.settings = QSettings("HKEY_CURRENT_USER\\Software\\SilentCode", QSettings.NativeFormat)
        self.tryMode=False
        self.singleReg=False
        self.outDated=False
        if self.settings.value('regMask')==None: # 初次运行，自动进入试用模式
            self.settings.setValue('regMask',self.randStr())
            self.settings.setValue('isRegistered', 0)
            self.settings.setValue('isTryMode', 1)
            self.settings.setValue('lastDate',str(date.today()+timedelta(days=10)))
            self.settings.setValue('firstRun',str(date.today()))
            self.settings.setValue('thisRun', str(date.today()))
            self.tryMode = True


        self.checkRegStatus()
        self.checkWorking()

    def checkRegStatus(self):
        if self.settings.value('isRegistered')==0:
            self.isRegistered=False
        else:
            self.isRegistered=True

        if self.settings.value('isTryMode')==0:
            self.tryMode=False
        else:
            self.tryMode=True
        self.localCode=self.settings.value('regMask')
        self.lastDate = str(self.settings.value('lastDate'))
        self.firstDate=str(self.settings.value('firstRun'))
        self.thisDate=str(self.settings.value('thisRun'))

    def checkWorking(self):
        # if self.tryMode==True or self.isRegistered==True:
        #     self.working=True
        hasLeft=(datetime.strptime(self.lastDate,'%Y-%m-%d').date()-date.today()).days>2
        if hasLeft==False: self.outDated=True
        isValid1=(date.today()-datetime.strptime(self.firstDate,'%Y-%m-%d').date()).days > -1
        isValid2=(date.today()-datetime.strptime(self.thisDate,'%Y-%m-%d').date()).days > -1
        if hasLeft and isValid1 and isValid2:
            self.working=True
        else:
            self.working=False

    def decrypt(self,code):
        if code=='':return
        pri_key = RSA.importKey(self.privateKey)
        cipher = PKCS1_cipher.new(pri_key)
        back_text = cipher.decrypt(base64.b64decode(code), 0)
        ss=back_text.decode('utf-8')
        s1,s2=ss.split('.')
        if s1==self.localCode:
            self.isRegistered=True
            self.tryMode=False
            self.settings.setValue('isRegistered',1)
            self.settings.setValue('isTryMode', 0)
            # 当前最晚日期
            lastDate=datetime.strptime(self.lastDate, '%Y-%m-%d').date()
            self.settings.setValue('lastDate',str(lastDate+timedelta(days=365*eval(s2))))
            # 重制机器码
            self.settings.setValue('regMask', self.randStr())
            self.checkRegStatus()
            self.checkWorking()
            self.singleReg=True
            print('解密成功')
            
    @staticmethod
    def randStr():
        H = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        salt = ''
        for i in range(10):
            salt += choice(H)
        return salt

if __name__=="__main__":
    crypt=Encryption()
    crypt.decrypt()