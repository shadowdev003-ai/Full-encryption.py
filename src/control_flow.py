import random
from typing import List
from .ast_nodes import *

class ControlFlowFlattener:
    def __init__(self):
        self.state_counter = 0
        self.states = []
    
    def flatten(self, block: Block) -> Block:
        self.states = []
        self.state_counter = 0
        
        for stmt in block.statements:
            self._process_statement(stmt)
        
        dispatcher = self._create_dispatcher()
        return Block(statements=[dispatcher])
    
    def _process_statement(self, stmt: ASTNode):
        state_id = self.state_counter
        self.state_counter += 1
        
        next_state = self.state_counter
        
        if isinstance(stmt, If):
            self.states.append({
                'id': state_id,
                'type': 'if',
                'cond': stmt.cond,
                'then': next_state,
                'else': next_state + 1 if stmt.else_block else next_state,
                'code': stmt.then_block
            })
            if stmt.else_block:
                self.state_counter += 1
                self._process_block(stmt.else_block, next_state + 1)
            else:
                self._process_block(stmt.then_block, next_state)
        elif isinstance(stmt, While):
            self.states.append({
                'id': state_id,
                'type': 'while',
                'cond': stmt.cond,
                'body': next_state,
                'exit': next_state + 1,
                'code': stmt.body
            })
            self.state_counter += 1
            self._process_block(stmt.body, next_state)
        else:
            self.states.append({
                'id': state_id,
                'type': 'normal',
                'next': next_state,
                'code': stmt
            })
    
    def _process_block(self, block: Block, start_id: int):
        for stmt in block.statements:
            self._process_statement(stmt)
    
    def _create_dispatcher(self) -> LocalAssignment:
        state_var = Name(id='_S')
        
        cases = []
        for state in self.states:
            case_body = self._generate_case_body(state)
            cases.append((Number(value=state['id']), case_body))
        
        while_node = While(
            cond=BinOp(op='<=', left=Name(id='_S'), right=Number(value=len(self.states))),
            body=Block(statements=[
                FunctionCall(
                    func=Name(id='_SW'),
                    args=[Name(id='_S')]
                )
            ])
        )
        
        return LocalAssignment(
            names=['_S'],
            values=[Number(value=0)]
        )
    
    def _generate_case_body(self, state: dict) -> Block:
        statements = []
        
        if state['type'] == 'normal':
            if isinstance(state['code'], Assignment):
                statements.append(state['code'])
            elif isinstance(state['code'], LocalAssignment):
                statements.append(state['code'])
            elif isinstance(state['code'], FunctionCall):
                statements.append(state['code'])
            
            statements.append(Assignment(
                targets=[Name(id='_S')],
                values=[Number(value=state['next'])]
            ))
        
        elif state['type'] == 'if':
            statements.append(If(
                cond=state['cond'],
                then_block=Block(statements=[
                    Assignment(
                        targets=[Name(id='_S')],
                        values=[Number(value=state['then'])]
                    )
                ]),
                else_block=Block(statements=[
                    Assignment(
                        targets=[Name(id='_S')],
                        values=[Number(value=state['else'])]
                    )
                ])
            ))
        
        return Block(statements=statements)
    
    def generate_switch_function(self) -> str:
        code = 'local function _SW(_S)\n'
        
        for state in self.states:
            code += f'    if _S == {state["id"]} then\n'
            
            if state['type'] == 'normal':
                code += f'        -- Execute state {state["id"]}\n'
                code += f'        _S = {state["next"]}\n'
            elif state['type'] == 'if':
                code += f'        -- If state {state["id"]}\n'
            
            code += '        return\n'
            code += '    end\n'
        
        code += 'end\n'
        return code
