from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import zlib
import random

class StringEncryptor:
    def __init__(self):
        self.encrypted_strings = {}
        self.counter = 0
    
    def encrypt(self, text: str) -> tuple:
        if text in self.encrypted_strings:
            return self.encrypted_strings[text]
        
        key = get_random_bytes(32)
        iv = get_random_bytes(16)
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        compressed = zlib.compress(text.encode('utf-8'), level=9)
        padded = pad(compressed, AES.block_size)
        encrypted = cipher.encrypt(padded)
        
        combined = iv + encrypted
        encoded = base64.b64encode(combined).decode('utf-8')
        
        key_b64 = base64.b64encode(key).decode('utf-8')
        
        var_name = self._generate_var_name()
        self.encrypted_strings[text] = (var_name, encoded, key_b64)
        
        return var_name, encoded, key_b64
    
    def _generate_var_name(self) -> str:
        chars = 'Il1|'
        length = random.randint(15, 25)
        return '_' + ''.join(random.choice(chars) for _ in range(length))
    
    def get_decrypt_function(self) -> str:
        decrypt_code = '''
local function _D(k, d)
    local function b64(s)
        local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        s = string.gsub(s, '[^'..b..'=]', '')
        return (s:gsub('.', function(x)
            if x == '=' then return '' end
            local r, f = '', b:find(x) - 1
            for i = 6, 1, -1 do r = r .. (f % 2^i - f % 2^(i-1) > 0 and '1' or '0') end
            return r
        end):gsub('%d%d%d?%d?%d?%d?%d?%d?', function(x)
            if #x ~= 8 then return '' end
            local c = 0
            for i = 1, 8 do c = c + (x:sub(i, i) == '1' and 2^(8-i) or 0) end
            return string.char(c)
        end))
    end
    
    local function unpad(data)
        local len = #data
        local pad_len = string.byte(data:sub(len, len))
        return data:sub(1, len - pad_len)
    end
    
    local key = b64(k)
    local data = b64(d)
    
    local iv = data:sub(1, 16)
    local encrypted = data:sub(17)
    
    local cipher = {}
    for i = 1, #key do cipher[i] = string.byte(key:sub(i, i)) end
    
    local plain = {}
    local prev = {string.byte(iv, 1, #iv)}
    
    for i = 1, #encrypted, 16 do
        local block = {string.byte(encrypted:sub(i, i + 15))}
        local decrypted = {}
        
        for j = 1, 16 do
            decrypted[j] = bit32.bxor(block[j], cipher[(j % #cipher) + 1], prev[j])
        end
        
        for j = 1, 16 do
            if i + j - 1 <= #encrypted then
                plain[i + j - 1] = decrypted[j]
            end
        end
        
        prev = block
    end
    
    local result = ''
    for i = 1, #plain do
        result = result .. string.char(plain[i])
    end
    
    return unpad(result)
end
'''
        return decrypt_code
