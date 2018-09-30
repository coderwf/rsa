# -*- coding:utf-8 -*-
import requests
import  rsa
from bigint import *
public_key = '89b7ad1090fe776044d393a097e52f99fc3f97690c90215ecb01f1b3dfc4d8b0226a4b16f51a884e0c1545180eb40365dbec848cc0df52f515512e2317bf9d82b6f4c9cafcc94082fd86c97e77a4d3aa44cba54f8d94f5757ce3cc82c3adf31082738cfe531b4b4675f35a0c8401745dbed15c92d0747c6349915378fff22b9b'
pub_key , pri_key = rsa.newkeys(1024)
pub_key.n = bi_from_hex(public_key)
pub_key.e = bi_from_hex("10001")
def LoginByPost():
    s=requests.session()
    loginUrl='https://pass.hust.edu.cn/cas/login'
    username = rsa.encrypt('M201776077',pub_key)
    password = rsa.encrypt('wzh1422256013',pub_key)
    postData={'username':username,'password':password}
    res=s.post(loginUrl,postData)
    res.encoding='utf-8'
    print res.content
    print res.status_code



if __name__ == "__main__":
    LoginByPost()
