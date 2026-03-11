import random
import base64
from typing import List, Dict
from .ast_nodes import *

class VMGenerator:
    def __init__(self):
        self.opcodes = {}
        self._generate_opcodes()
    
    def _generate_opcodes(self):
        ops = ['LOADK', 'LOADNIL', 'LOADBOOL', 'LOADNUMBER', 'GETUPVAL', 
               'GETGLOBAL', 'GETTABLE', 'SETGLOBAL', 'SETUPVAL', 'SETTABLE',
               'NEWTABLE', 'SELF', 'ADD', 'SUB', 'MUL', 'DIV', 'MOD', 'POW',
               'UNM', 'NOT', 'LEN', 'CONCAT', 'JMP', 'EQ', 'LT', 'LE', 'TEST',
               'TESTSET', 'CALL', 'TAILCALL', 'RETURN', 'FORLOOP', 'FORPREP',
               'TFORLOOP', 'SETLIST', 'CLOSE', 'CLOSURE', 'VARARG', 'MOVE']
        
        used = set()
        for op in ops:
            while True:
                code = random.randint(0, 255)
                if code not in used:
                    used.add(code)
                    self.opcodes[op] = code
                    break
    
    def compile_ast(self, node: ASTNode) -> List[Dict]:
        instructions = []
        constants = []
        const_map = {}
        
        def add_const(val):
            if val in const_map:
                return const_map[val]
            idx = len(constants)
            constants.append(val)
            const_map[val] = idx
            return idx
        
        def emit(op, a=0, b=0, c=0):
            instructions.append({
                'op': self.opcodes[op],
                'a': a,
                'b': b,
                'c': c,
                'name': op
            })
        
        def compile_node(n, target_reg=0):
            if isinstance(n, Number):
                idx = add_const(n.value)
                emit('LOADK', target_reg, idx)
            
            elif isinstance(n, String):
                idx = add_const(n.value)
                emit('LOADK', target_reg, idx)
            
            elif isinstance(n, Name):
                if n.id in ('nil', 'true', 'false'):
                    emit('LOADBOOL' if n.id != 'nil' else 'LOADNIL', 
                         target_reg, 1 if n.id == 'true' else 0)
                else:
                    idx = add_const(n.id)
                    emit('GETGLOBAL', target_reg, idx)
            
            elif isinstance(n, BinOp):
                compile_node(n.left, target_reg)
                compile_node(n.right, target_reg + 1)
                
                op_map = {
                    '+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV',
                    '%': 'MOD', '^': 'POW', '..': 'CONCAT'
                }
                emit(op_map.get(n.op, 'ADD'), target_reg, target_reg, target_reg + 1)
            
            elif isinstance(n, UnOp):
                compile_node(n.operand, target_reg)
                op_map = {'-': 'UNM', 'not': 'NOT', '#': 'LEN'}
                emit(op_map.get(n.op, 'UNM'), target_reg, target_reg)
            
            elif isinstance(n, FunctionCall):
                compile_node(n.func, target_reg)
                for i, arg in enumerate(n.args):
                    compile_node(arg, target_reg + 1 + i)
                emit('CALL', target_reg, len(n.args) + 1, 1)
            
            elif isinstance(n, Assignment):
                if len(n.targets) == 1 and isinstance(n.targets[0], Name):
                    compile_node(n.values[0], target_reg)
                    idx = add_const(n.targets[0].id)
                    emit('SETGLOBAL', target_reg, idx)
        
        if isinstance(node, Block):
            for stmt in node.statements:
                compile_node(stmt)
        else:
            compile_node(node)
        
        emit('RETURN', 0, 1)
        
        return {'instructions': instructions, 'constants': constants}
    
    def generate_vm(self, bytecode: Dict) -> str:
        vm_code = self._get_vm_template()
        
        inst_bytes = self._encode_instructions(bytecode['instructions'])
        const_data = bytecode['constants']
        
        vm_code = vm_code.replace('__INSTRUCTIONS__', str(inst_bytes))
        vm_code = vm_code.replace('__CONSTANTS__', str(const_data))
        vm_code = vm_code.replace('__OPCODES__', str(self.opcodes))
        
        return vm_code
    
    def _encode_instructions(self, instructions: List[Dict]) -> List[int]:
        bytes_list = []
        for inst in instructions:
            bytes_list.append(inst['op'])
            bytes_list.append(inst['a'])
            bytes_list.append(inst['b'])
            bytes_list.append(inst['c'])
        return bytes_list
    
    def _get_vm_template(self) -> str:
        return '''
local _VM = function()
    local _I = __INSTRUCTIONS__
    local _K = __CONSTANTS__
    local _OP = __OPCODES__
    
    local _R = {}
    local _PC = 1
    
    local _OPS = {}
    
    _OPS[_OP.LOADK] = function(a, b, c)
        _R[a] = _K[b + 1]
        _PC = _PC + 1
    end
    
    _OPS[_OP.LOADNIL] = function(a, b, c)
        _R[a] = nil
        _PC = _PC + 1
    end
    
    _OPS[_OP.LOADBOOL] = function(a, b, c)
        _R[a] = (b == 1)
        _PC = _PC + 1
    end
    
    _OPS[_OP.GETGLOBAL] = function(a, b, c)
        local name = _K[b + 1]
        _R[a] = _ENV[name]
        _PC = _PC + 1
    end
    
    _OPS[_OP.SETGLOBAL] = function(a, b, c)
        local name = _K[b + 1]
        _ENV[name] = _R[a]
        _PC = _PC + 1
    end
    
    _OPS[_OP.ADD] = function(a, b, c)
        _R[a] = _R[b] + _R[c]
        _PC = _PC + 1
    end
    
    _OPS[_OP.SUB] = function(a, b, c)
        _R[a] = _R[b] - _R[c]
        _PC = _PC + 1
    end
    
    _OPS[_OP.MUL] = function(a, b, c)
        _R[a] = _R[b] * _R[c]
        _PC = _PC + 1
    end
    
    _OPS[_OP.DIV] = function(a, b, c)
        _R[a] = _R[b] / _R[c]
        _PC = _PC + 1
    end
    
    _OPS[_OP.MOD] = function(a, b, c)
        _R[a] = _R[b] % _R[c]
        _PC = _PC + 1
    end
    
    _OPS[_OP.POW] = function(a, b, c)
        _R[a] = _R[b] ^ _R[c]
        _PC = _PC + 1
    end
    
    _OPS[_OP.UNM] = function(a, b, c)
        _R[a] = -_R[b]
        _PC = _PC + 1
    end
    
    _OPS[_OP.NOT] = function(a, b, c)
        _R[a] = not _R[b]
        _PC = _PC + 1
    end
    
    _OPS[_OP.LEN] = function(a, b, c)
        _R[a] = #_R[b]
        _PC = _PC + 1
    end
    
    _OPS[_OP.CONCAT] = function(a, b, c)
        _R[a] = _R[b] .. _R[c]
        _PC = _PC + 1
    end
    
    _OPS[_OP.CALL] = function(a, b, c)
        local func = _R[a]
        local args = {}
        for i = 1, b - 1 do
            args[i] = _R[a + i]
        end
        _R[a] = func(table.unpack(args))
        _PC = _PC + 1
    end
    
    _OPS[_OP.RETURN] = function(a, b, c)
        return _R[a]
    end
    
    _OPS[_OP.JMP] = function(a, b, c)
        _PC = _PC + b + 1
    end
    
    _OPS[_OP.EQ] = function(a, b, c)
        if (_R[b] == _R[c]) ~= (a == 1) then
            _PC = _PC + 1
        end
        _PC = _PC + 1
    end
    
    _OPS[_OP.LT] = function(a, b, c)
        if (_R[b] < _R[c]) ~= (a == 1) then
            _PC = _PC + 1
        end
        _PC = _PC + 1
    end
    
    _OPS[_OP.LE] = function(a, b, c)
        if (_R[b] <= _R[c]) ~= (a == 1) then
            _PC = _PC + 1
        end
        _PC = _PC + 1
    end
    
    _OPS[_OP.TEST] = function(a, b, c)
        if not _R[a] then
            _PC = _PC + 1
        end
        _PC = _PC + 1
    end
    
    _OPS[_OP.FORLOOP] = function(a, b, c)
        local step = _R[a + 2]
        _R[a] = _R[a] + step
        local limit = _R[a + 1]
        if (step > 0 and _R[a] <= limit) or (step < 0 and _R[a] >= limit) then
            _PC = _PC + b
            _R[a + 3] = _R[a]
        else
            _PC = _PC + 1
        end
    end
    
    _OPS[_OP.FORPREP] = function(a, b, c)
        _R[a] = _R[a] - _R[a + 2]
        _PC = _PC + b
    end
    
    while _PC <= #_I / 4 do
        local idx = (_PC - 1) * 4 + 1
        local op = _I[idx]
        local a = _I[idx + 1]
        local b = _I[idx + 2]
        local c = _I[idx + 3]
        
        local handler = _OPS[op]
        if handler then
            local result = handler(a, b, c)
            if result ~= nil then
                return result
            end
        else
            _PC = _PC + 1
        end
    end
end

return _VM()
'''
