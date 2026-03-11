from lark import Tree, Token
from typing import List, Optional, Union
from .ast_nodes import *

class LuaParser:
    def __init__(self):
        from .lexer import LuaLexer
        self.lexer = LuaLexer()
    
    def parse(self, code: str) -> Chunk:
        tree = self.lexer.parse(code)
        return self._transform(tree)
    
    def _transform(self, tree: Tree) -> ASTNode:
        if tree.data == 'chunk':
            return Chunk(body=[self._transform(child) for child in tree.children])
        
        elif tree.data == 'block':
            statements = []
            for child in tree.children:
                node = self._transform(child)
                if isinstance(node, list):
                    statements.extend(node)
                else:
                    statements.append(node)
            return Block(statements=statements)
        
        elif tree.data == 'assign':
            targets = self._transform(tree.children[0])
            values = self._transform(tree.children[1])
            if not isinstance(targets, list):
                targets = [targets]
            if not isinstance(values, list):
                values = [values]
            return Assignment(targets=targets, values=values)
        
        elif tree.data == 'local':
            names_tree = tree.children[0]
            names = [str(token) for token in names_tree.children]
            values = []
            if len(tree.children) > 1:
                values = self._transform(tree.children[1])
                if not isinstance(values, list):
                    values = [values]
            return LocalAssignment(names=names, values=values)
        
        elif tree.data == 'call':
            return self._transform(tree.children[0])
        
        elif tree.data == 'call_args':
            func = self._transform(tree.children[0])
            args = self._transform(tree.children[1])
            if not isinstance(args, list):
                args = [args]
            return FunctionCall(func=func, args=args)
        
        elif tree.data == 'args_paren':
            if not tree.children:
                return []
            return self._transform(tree.children[0])
        
        elif tree.data == 'string_exp':
            token = tree.children[0]
            value = str(token)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            elif value.startswith('[[[') and value.endswith(']]]'):
                value = value[3:-3]
            elif value.startswith('[[[') and value.endswith(']]]'):
                value = value[3:-3]
            return String(value=value)
        
        elif tree.data == 'number_exp':
            token = tree.children[0]
            val = str(token)
            if '.' in val:
                return Number(value=float(val))
            return Number(value=int(val))
        
        elif tree.data == 'var_name':
            return Name(id=str(tree.children[0]))
        
        elif tree.data == 'nil_exp':
            return Name(id='nil')
        
        elif tree.data == 'true_exp':
            return Name(id='true')
        
        elif tree.data == 'false_exp':
            return Name(id='false')
        
        elif tree.data == 'bin_exp':
            left = self._transform(tree.children[0])
            op = str(tree.children[1])
            right = self._transform(tree.children[2])
            return BinOp(op=op, left=left, right=right)
        
        elif tree.data == 'un_exp':
            op = str(tree.children[0])
            operand = self._transform(tree.children[1])
            return UnOp(op=op, operand=operand)
        
        elif tree.data == 'if_stmt':
            cond = self._transform(tree.children[0])
            then_block = self._transform(tree.children[1])
            else_block = None
            if len(tree.children) > 2:
                else_block = self._transform(tree.children[-1])
            return If(cond=cond, then_block=then_block, else_block=else_block)
        
        elif tree.data == 'while_stmt':
            cond = self._transform(tree.children[0])
            body = self._transform(tree.children[1])
            return While(cond=cond, body=body)
        
        elif tree.data == 'for_num':
            name = str(tree.children[0])
            start = self._transform(tree.children[1])
            end = self._transform(tree.children[2])
            step = None
            body_idx = 3
            if len(tree.children) > 4:
                step = self._transform(tree.children[3])
                body_idx = 4
            body = self._transform(tree.children[body_idx])
            return For(name=name, start=start, end=end, step=step, body=body)
        
        elif tree.data == 'func_def':
            name_tree = tree.children[0]
            name_parts = [str(t) for t in name_tree.children]
            name = '.'.join(name_parts)
            body = self._transform(tree.children[1])
            return FunctionDef(name=name, params=body.params, body=body.body, local=False)
        
        elif tree.data == 'local_func':
            name = str(tree.children[0])
            body = self._transform(tree.children[1])
            return FunctionDef(name=name, params=body.params, body=body.body, local=True)
        
        elif tree.data == 'funcbody':
            params = []
            if tree.children[0].data == 'parlist':
                parlist = tree.children[0]
                params = [str(p) for p in parlist.children if isinstance(p, Token)]
            body = self._transform(tree.children[-1])
            return type('FuncBody', (), {'params': params, 'body': body})()
        
        elif tree.data == 'return_empty':
            return Return(values=[])
        
        elif tree.data == 'retstat':
            if not tree.children:
                return Return(values=[])
            values = self._transform(tree.children[0])
            if not isinstance(values, list):
                values = [values]
            return Return(values=values)
        
        elif tree.data == 'explist':
            return [self._transform(child) for child in tree.children]
        
        elif tree.data == 'varlist':
            return [self._transform(child) for child in tree.children]
        
        elif tree.data == 'prefix_var':
            return self._transform(tree.children[0])
        
        elif tree.data == 'prefix_paren':
            return self._transform(tree.children[0])
        
        elif tree.data == 'break_stmt':
            return Break()
        
        elif tree.data == 'vararg_exp':
            return Vararg()
        
        elif tree.data == 'table_exp':
            return self._transform(tree.children[0])
        
        elif tree.data == 'tableconstructor':
            fields = []
            for child in tree.children:
                field = self._transform(child)
                if isinstance(field, list):
                    fields.extend(field)
                else:
                    fields.append(field)
            return TableConstructor(fields=fields)
        
        elif tree.data == 'field_exp':
            return ('exp', self._transform(tree.children[0]))
        
        elif tree.data == 'field_name':
            name = str(tree.children[0])
            value = self._transform(tree.children[1])
            return ('name', name, value)
        
        elif tree.data == 'field_index':
            key = self._transform(tree.children[0])
            value = self._transform(tree.children[1])
            return ('index', key, value)
        
        elif tree.data == 'func_exp':
            return self._transform(tree.children[0])
        
        elif tree.data == 'call_method':
            obj = self._transform(tree.children[0])
            method = str(tree.children[1])
            args = self._transform(tree.children[2])
            if not isinstance(args, list):
                args = [args]
            func = MemberAccess(obj=obj, member=method)
            return FunctionCall(func=func, args=args)
        
        elif tree.data == 'var_member':
            obj = self._transform(tree.children[0])
            member = str(tree.children[1])
            return MemberAccess(obj=obj, member=member)
        
        elif tree.data == 'var_index':
            obj = self._transform(tree.children[0])
            idx = self._transform(tree.children[1])
            return Index(obj=obj, idx=idx)
        
        elif tree.data == 'do_block':
            return self._transform(tree.children[0])
        
        elif tree.data == 'repeat_stmt':
            body = self._transform(tree.children[0])
            cond = self._transform(tree.children[1])
            return Block(statements=[
                body,
                While(cond=UnOp(op='not', operand=cond), body=Block(statements=[Break()]))
            ])
        
        else:
            if not tree.children:
                return Block(statements=[])
            results = []
            for child in tree.children:
                if isinstance(child, Tree):
                    results.append(self._transform(child))
                elif isinstance(child, Token):
                    results.append(str(child))
            return results[0] if len(results) == 1 else results
