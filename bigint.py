# -*- coding:utf-8 -*-

BiRadixBase       = 2             #2为基底
BiRadixBits       = 16            #一个digit为16位
BitsPerDigit      = BiRadixBits
BiRadix           = 1 << 16       #一个digit的底 即遇到BiRadix进位
MaxDigitVal       = BiRadix - 1   #一个digit最大的值
BiRadixSquired    = BiRadix * BiRadix #平方
BiHalfRadix       = BiRadix / 2   #digit的底的一半
#取高位值,掩码值

HighBitsMasks     = [
    0x0000,0x8000,0xc000,0xe000,0xf000,
    0xf800,0xfc00,0xfe00,0xff00,0xff80,
    0xffc0,0xffe0,0xfff0,0xfff8,0xfffc,
    0xfffe,0xffff
]
#取低位掩码值
LowBitsMasks     = [
    0x0000,0x0001,0x0003,0x0007,0x000f,
    0x001f,0x003f,0x007f,0x00ff,0x01ff,
    0x03ff,0x07ff,0x0fff,0x1fff,0x3fff,
    0x7fff,0xffff
]

"""
big-int 中digit中数字只能为正数
符号单独用isNeg表示即可
"""
class BigInt(object):
    def __init__(self,length=30):
        self.digits       = [0 for i in range(0,length)]
        self.length       = length
        self.isNeg        = False
    #求最高非零位的索引
    def deep_copy(self):
        res = BigInt(length=self.length)
        res.isNeg = self.isNeg
        res.digits = self.digits[:]
        return res

    def modify_length(self,length):
        more = length - len(self.digits)
        for i in range(0,more):
            self.digits.append(0)
        if more <= 0:
            more = 0
        self.length = self.length + more

    def h_index(self):
        index = self.length - 1
        while index >= 0 and self.digits[index] == 0:
            index -= 1
        return index

    def dump(self):
        da = ""
        hx = self.h_index()
        for i in range(0,hx+1):
            if i == hx:
                da = da + str(self.digits[i])
            else:
                da = da + str(self.digits[i])+ " "
        return ("-" if self.isNeg else "") + da

    def __str__(self):
        return str(self.digits)

    #两个大数字相乘
    def copy(self,start,des,des_start,n):
        n = min(n,self.length - start,des.length - des_start)
        for i in range(0 , n):
            des.digits[i + des_start] = self.digits[i+start]

    def multiplyByBigInt(self,y):  #溢出位保存
        l = max(30,self.h_index() + y.h_index() + 3)
        result = BigInt(length=l)
        xh = self.h_index()
        yh = y.h_index()
        for i in range(0,xh+1):
            overflow = 0
            for j in range(0,yh+1):
                temp_uv = self.digits[i] * y.digits[j] + overflow + result.digits[i+j] #可能有溢出
                overflow = (temp_uv / BiRadix)
                result.digits[j+i] = temp_uv & MaxDigitVal
            result.digits[i + 1 + yh] = overflow
        result.isNeg = self.isNeg != y.isNeg
        return result

    #digits是一个16bit的整数
    def multiplyByDigit(self,digit):
        l = max(30,self.h_index()+2)
        res = BigInt(length=l)
        xh = self.h_index()
        overflow = 0 #溢出
        for i in range(0, xh+1):
            temp_uv = self.digits[i] * digit + overflow
            overflow = (temp_uv / BiRadix)
            res.digits[i] = temp_uv & MaxDigitVal
        res.digits[xh + 1] = overflow
        res.isNeg = self.isNeg
        return res

    def multiplyByRadixPower(self,n):
        l = max(30,(self.h_index()+1) * n + 1)
        res = BigInt(length=l)
        self.copy(0,res,n,res.length - n)
        return res

    def divideByRadixPower(self,n):
        res = BigInt()
        self.copy(n,res,0,self.length - n)
        return res

    #后n位
    def modByRadixPower(self,n):
        res = BigInt()
        self.copy(0,res,0,n)
        return res

    #相对于本bigint结构的右移,本bigint会减少
    def shiftRight(self,n):
        digitCount = int(n / BitsPerDigit)
        bits = n % BitsPerDigit
        rightBits = BitsPerDigit - bits
        res = BigInt()
        self.copy(digitCount,res,0,self.length - digitCount)
        for i in range(0,self.length - 1):
            j = i + 1
            res.digits[i] = ((res.digits[j] &LowBitsMasks[bits]) << rightBits) |\
                            ((res.digits[i] & HighBitsMasks[rightBits]) >> bits)
        res.digits[res.length-1] =(( res.digits[res.length-1] & HighBitsMasks[rightBits]) >> bits)
        res.isNeg = self.isNeg
        return res

    #真实右移
    def shiftLeft(self,n):
        digitCount = int(n / BitsPerDigit)
        bits = n % BitsPerDigit
        leftBits = BitsPerDigit - bits
        res = BigInt()
        self.copy(0,res,digitCount,self.length - digitCount)
        for i in range(self.length - 1,0,-1):
            j = i - 1
            res.digits[i] = ((res.digits[j] & HighBitsMasks[bits]) >> leftBits) |\
                            ((res.digits[i] & LowBitsMasks[leftBits]) << bits)
        res.digits[0] =((res.digits[0] & LowBitsMasks[leftBits]) << bits)
        res.isNeg = self.isNeg
        return res

    #n次方,采用二分法快速对称平方
    #快速求幂和快速取模
    #偶数则不断平方 奇数则乘上去
    #不管奇数偶数总有一个temp一直在平方
    #任何数字都可以由二进制表示,只有二进制位为1的才需要计算上去
    #比如34 = 100010 = 32 + 2
    #所以x^34 = x^32*x^2 即二进制位第二位和第6位相乘,第二位为x^2 第六位为x^32,将这两个位的平方数乘到结果即可
    #而这两个数都是x不断平方的结果,所以x不断平方并在合适的时候乘到结果上取
    def pow(self,n):
        res = BigInt()
        res.digits[0] = 1
        temp = self.deep_copy()
        while True:
            if n == 0:
                break
            if (n & 1) == 1:   #表示这一位是1 需要乘到结果上去
                res = res.multiplyByBigInt(temp)
            temp = temp.multiplyByBigInt(temp)   #每一位都不断平方即可
            n >>= 1
        return res
    #乘以x并modm
    def multiplyMod(self,x,m):
        return
    #self的n次方mod m
    def powMod(self,n,m):
        pass

    #求他的总bit位数,最高位去掉多余的0
    def numBits(self):
        hx = self.h_index()
        m = (hx + 1) * BitsPerDigit
        d = self.digits[hx]
        for result in range(m,m - BitsPerDigit,-1):
            if (d & 0x8000) != 0:
                break
            d <<= 1
        return result

    #减 减完了以后如果最高位不够则需要重新补位
    def subTract(self,y):
        length = max(self.length , y.length)
        self.modify_length(length)
        y.modify_length(length)
        if self.isNeg != y.isNeg:
            y.isNeg = not y.isNeg
            res = self.add(y)
            y.isNeg = not y.isNeg
            return res
        #符号相同
        length = max(self.length, y.length)
        res = BigInt(length = length + 1)
        c = 0
        for i in range(0,length):
            temp = self.digits[i] - y.digits[i] + c
            res.digits[i] = temp % BiRadix
            if res.digits[i] < 0:
                res.digits[i] = res.digits[i] + BiRadix
            c = 0 - int(temp < 0)
        if c == 0:
            res.isNeg = self.isNeg
            return res   #x >= y
        c = 0
        for i in range(0,length):
            temp = 0 - res.digits[i] + c
            res.digits[i] = temp % BiRadix
            if res.digits[i] < 0:
                res.digits[i] = res.digits[i] + BiRadix
            c = 0 - int(temp < 0)
            res.isNeg = not self.isNeg
        return res
        # x < y



    #加 , 溢出也只能溢出 1 溢出 overflow > Maxdigitval
    def add(self,y):
        length = max(self.length, y.length)
        self.modify_length(length)
        y.modify_length(length)
        res = BigInt(length = length + 1)
        #同符号
        if self.isNeg == y.isNeg:
            c = 0
            for i in range(0,length):
                temp = self.digits[i] + y.digits[i] + c
                res.digits[i] = temp % BiRadix    #余数留下来
                c = int(temp > MaxDigitVal)
            res.digits[length] = c
            res.isNeg = self.isNeg
            return res
        #符号不一样
        y.isNeg = not y.isNeg
        res = self.subTract(y)
        y.isNeg = not y.isNeg
        return res


    #根据big1,big2长度返回两个长度相等的副本
    @staticmethod
    def balanceCopy(big1,big2):
        length = max(big1.length,big2.length)
        big11 = BigInt(length=length)
        big11.isNeg = big1.isNeg
        big22 = BigInt(length=length)
        big22.isNeg = big2.isNeg
        big1.copy(0,big11,0,length)
        big2.copy(0,big22,0,length)
        return big11,big22

    #比较两个数字的大小 1 大于 0 等于 -1 小于
    def compare(self,y):
        if self.length == y.length:
            b1 , b2 = self , y
        else:
            b1 , b2 = self.balanceCopy(self,y)
        if b1.isNeg != b2.isNeg:
            return 1 - 2 * b1.isNeg
        #符号一样
        for i in range(b1.length-1,-1,-1):
            if b1.digits[i] == b2.digits[i]:
                continue

            if b1.isNeg:
                return 1 - 2 * (b1.digits[i] > b2.digits[i])
            else:
                return 1 - 2 * (b1.digits[i] < b2.digits[i])
        return 0

    #除以 最后将熵和余数一起返回(q,r)
    def divideMod(self,y):



#把十六进制字符转化为十进制的数字
def hex_char_to_digit(char):
    char = ord(char)
    zero = 48
    nine = zero + 9
    little_a = 97
    little_z = little_a + 25
    big_a    = 65
    big_z    = big_a + 25
    if char >= zero and char <= nine:
        return char - zero
    elif char >= little_a and char <= little_z:
        return char - little_a + 10
    elif char >= big_a and char <= big_z:
        return char - big_a + 10
    else:
        return 0

#把一个四位的16进制字符串转化为十进制数
def hex_str_to_digit(s):
    result = 0
    length = min(4,len(s))
    for i in range(0,length):
        result <<= 4
        result |= hex_char_to_digit(s[i])
    return result

def bi_from_hex_str(s):
    big_int = BigInt()
    length = len(s)
    k = 0
    for i in range(length,-1,-4):
        min_index = max(i-4,0)
        step = min(4,i)
        st = s[min_index:min_index+step]
        big_int.digits[k] = hex_str_to_digit(st)
        k += 1
    return big_int


if __name__ == "__main__":
    hex_str1 = "abc300ffabc564c567ddfaa88834947bgf8g40"
    hex_str2 = "1234154acf1dc1aaa1cf54cca124dee2e2ccaaa111ffffc"
    b1 = bi_from_hex_str(hex_str1)
    b2 = bi_from_hex_str(hex_str2)
    bb1 = b1.pow(22)
    print bb1.subTract(b2).dump()







