import random
import string
from typing import Dict, Set
from .ast_nodes import *
from .parser import LuaParser
from .string_encrypt import StringEncryptor
from .control_flow import ControlFlowFlattener
from .vm_generator import VMGenerator

class LuaObfuscator:
    def __init__(self):
        self.parser = LuaParser()
        self.string_encryptor = StringEncryptor()
        self.control_flattener = ControlFlowFlattener()
        self.vm_generator = VMGenerator()
        self.name_map: Dict[str, str] = {}
        self.used_names: Set[str] = set()
        self.options = {
            'encrypt_strings': True,
            'control_flow': True,
            'vm_based': True,
            'anti_tamper': True,
            'anti_debug': True
        }
    
    def obfuscate(self, code: str, **options) -> str:
        self.options.update(options)
        
        ast = self.parser.parse(code)
        
        self._collect_names(ast)
        self._rename_variables(ast)
        
        if self.options['encrypt_strings']:
            self._encrypt_all_strings(ast)
        
        if self.options['control_flow']:
            ast = self._apply_control_flow(ast)
        
        if self.options['vm_based']:
            return self._generate_vm_output(ast)
        
        return self._generate_code(ast)
    
    def _collect_names(self, node: ASTNode):
        if isinstance(node, Name):
            if len(node.id) > 1 and node.id not in ('nil', 'true', 'false', 'and', 'or', 'not', 'function', 'end', 'if', 'then', 'else', 'elseif', 'while', 'do', 'repeat', 'until', 'for', 'in', 'local', 'return', 'break', 'true', 'false'):
                if node.id not in self.name_map:
                    self.name_map[node.id] = self._generate_obfuscated_name()
        
        for attr in ['body', 'statements', 'targets', 'values', 'left', 'right', 
                     'cond', 'then_block', 'else_block', 'func', 'args', 'operand',
                     'obj', 'idx', 'start', 'end', 'step']:
            if hasattr(node, attr):
                val = getattr(node, attr)
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, ASTNode):
                            self._collect_names(item)
                elif isinstance(val, ASTNode):
                    self._collect_names(val)
    
    def _generate_obfuscated_name(self) -> str:
        chars = 'Il1|'
        while True:
            length = random.randint(10, 20)
            name = '_' + ''.join(random.choice(chars) for _ in range(length))
            if name not in self.used_names:
                self.used_names.add(name)
                return name
    
    def _rename_variables(self, node: ASTNode):
        if isinstance(node, Name):
            if node.id in self.name_map:
                node.id = self.name_map[node.id]
        
        for attr in ['body', 'statements', 'targets', 'values', 'left', 'right',
                     'cond', 'then_block', 'else_block', 'func', 'args', 'operand',
                     'obj', 'idx', 'start', 'end', 'step']:
            if hasattr(node, attr):
                val = getattr(node, attr)
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, ASTNode):
                            self._rename_variables(item)
                elif isinstance(val, ASTNode):
                    self._rename_variables(val)
    
    def _encrypt_all_strings(self, node: ASTNode):
        if isinstance(node, String) and not node.encrypted:
            var_name, encoded, key = self.string_encryptor.encrypt(node.value)
            node.value = var_name
            node.encrypted = True
        
        for attr in ['body', 'statements', 'targets', 'values', 'left', 'right',
                     'cond', 'then_block', 'else_block', 'func', 'args', 'operand',
                     'obj', 'idx', 'start', 'end', 'step']:
            if hasattr(node, attr):
                val = getattr(node, attr)
                if isinstance(val, list):
                    for item in val:
                        if isinstance(item, ASTNode):
                            self._encrypt_all_strings(item)
                elif isinstance(val, ASTNode):
                    self._encrypt_all_strings(val)
    
    def _apply_control_flow(self, node: ASTNode) -> ASTNode:
        if isinstance(node, Block):
            return self.control_flattener.flatten(node)
        elif isinstance(node, Chunk):
            node.body = self._apply_control_flow(node.body)
        return node
    
    def _generate_vm_output(self, ast: ASTNode) -> str:
        bytecode = self.vm_generator.compile_ast(ast.body if isinstance(ast, Chunk) else ast)
        vm_code = self.vm_generator.generate_vm(bytecode)
        
        header = self._generate_anti_tamper() if self.options['anti_tamper'] else ''
        header += self.string_encryptor.get_decrypt_function() if self.string_encryptor.encrypted_strings else ''
        
        encrypted_vars = ''
        for original, (var_name, encoded, key) in self.string_encryptor.encrypted_strings.items():
            encrypted_vars += f'local {var_name} = _D("{key}", "{encoded}")\n'
        
        return header + encrypted_vars + vm_code
    
    def _generate_code(self, ast: ASTNode) -> str:
        header = self._generate_anti_tamper() if self.options['anti_tamper'] else ''
        header += self.string_encryptor.get_decrypt_function() if self.string_encryptor.encrypted_strings else ''
        
        encrypted_vars = ''
        for original, (var_name, encoded, key) in self.string_encryptor.encrypted_strings.items():
            encrypted_vars += f'local {var_name} = _D("{key}", "{encoded}")\n'
        
        body = self._ast_to_lua(ast)
        
        return header + encrypted_vars + body
    
    def _generate_anti_tamper(self) -> str:
        return '''
local _AT = function()
    local _D = debug.getinfo
    local _T = 0
    for i = 1, 5 do
        local info = _D(i)
        if info then _T = _T + 1 end
    end
    if _T > 3 then
        while true do end
    end
    
    local _S = string.dump
    if _S then
        local _F = function() end
        local _C = _S(_F)
        if #_C > 0 then
            -- Anti-decompilation
        end
    end
end
_AT()
'''
    
    def _ast_to_lua(self, node: ASTNode) -> str:
        if isinstance(node, Chunk):
            return '\n'.join(self._ast_to_lua(stmt) for stmt in node.body.statements)
        
        elif isinstance(node, Block):
            return '\n'.join(self._ast_to_lua(stmt) for stmt in node.statements)
        
        elif isinstance(node, Assignment):
            targets = ', '.join(self._ast_to_lua(t) for t in node.targets)
            values = ', '.join(self._ast_to_lua(v) for v in node.values)
            return f'{targets} = {values}'
        
        elif isinstance(node, LocalAssignment):
            names = ', '.join(node.names)
            if node.values:
                values = ', '.join(self._ast_to_lua(v) for v in node.values)
                return f'local {names} = {values}'
            return f'local {names}'
        
        elif isinstance(node, FunctionCall):
            func = self._ast_to_lua(node.func)
            args = ', '.join(self._ast_to_lua(a) for a in node.args)
            return f'{func}({args})'
        
        elif isinstance(node, String):
            return f'"{node.value}"' if not node.encrypted else node.value
        
        elif isinstance(node, Number):
            if isinstance(node.value, float):
                return str(node.value)
            return str(node.value)
        
        elif isinstance(node, Name):
            return node.id
        
        elif isinstance(node, BinOp):
            left = self._ast_to_lua(node.left)
            right = self._ast_to_lua(node.right)
            return f'({left} {node.op} {right})'
        
        elif isinstance(node, UnOp):
            operand = self._ast_to_lua(node.operand)
            return f'({node.op}{operand})'
        
        elif isinstance(node, If):
            cond = self._ast_to_lua(node.cond)
            then_block = self._ast_to_lua(node.then_block)
            code = f'if {cond} then\n{then_block}\n'
            if node.else_block:
                else_block = self._ast_to_lua(node.else_block)
                code += f'else\n{else_block}\n'
            code += 'end'
            return code
        
        elif isinstance(node, While):
            cond = self._ast_to_lua(node.cond)
            body = self._ast_to_lua(node.body)
            return f'while {cond} do\n{body}\nend'
        
        elif isinstance(node, For):
            start = self._ast_to_lua(node.start)
            end = self._ast_to_lua(node.end)
            step = ''
            if node.step:
                step = ', ' + self._ast_to_lua(node.step)
            body = self._ast_to_lua(node.body)
            return f'for {node.name} = {start}, {end}{step} do\n{body}\nend'
        
        elif isinstance(node, FunctionDef):
            params = ', '.join(node.params)
            body = self._ast_to_lua(node.body)
            prefix = 'local ' if node.local else ''
            name = node.name or ''
            return f'{prefix}function {name}({params})\n{body}\nend'
        
        elif isinstance(node, Return):
            if not node.values:
                return 'return'
            values = ', '.join(self._ast_to_lua(v) for v in node.values)
            return f'return {values}'
        
        elif isinstance(node, TableConstructor):
            fields = []
            for field in node.fields:
                if field[0] == 'exp':
                    fields.append(self._ast_to_lua(field[1]))
                elif field[0] == 'name':
                    fields.append(f'{field[1]} = {self._ast_to_lua(field[2])}')
                elif field[0] == 'index':
                    fields.append(f'[{self._ast_to_lua(field[1])}] = {self._ast_to_lua(field[2])}')
            return '{' + ', '.join(fields) + '}'
        
        elif isinstance(node, Index):
            obj = self._ast_to_lua(node.obj)
            idx = self._ast_to_lua(node.idx)
            return f'{obj}[{idx}]'
        
        elif isinstance(node, MemberAccess):
            obj = self._ast_to_lua(node.obj)
            return f'{obj}.{node.member}'
        
        elif isinstance(node, Vararg):
            return '...'
        
        elif isinstance(node, Break):
            return 'break'
        
        return ''
