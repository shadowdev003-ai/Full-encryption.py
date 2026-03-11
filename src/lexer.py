from lark import Lark, Token, Transformer
from lark.grammar import Rule
import re

LUA_GRAMMAR = r'''
    ?start: chunk
    
    chunk: block
    
    block: (stat [";"])* (retstat [";"])?
    
    ?stat: varlist "=" explist                    -> assign
         | "local" namelist ["=" explist]         -> local
         | functioncall                           -> call
         | "if" exp "then" block ("elseif" exp "then" block)* ["else" block] "end" -> if_stmt
         | "while" exp "do" block "end"           -> while_stmt
         | "for" NAME "=" exp "," exp ["," exp] "do" block "end" -> for_num
         | "for" namelist "in" explist "do" block "end" -> for_in
         | "function" funcname funcbody           -> func_def
         | "local" "function" NAME funcbody       -> local_func
         | "repeat" block "until" exp             -> repeat_stmt
         | "do" block "end"                       -> do_block
         | "break"                                -> break_stmt
         | "return"                               -> return_empty
    
    retstat: "return" explist?
    
    funcname: NAME ("." NAME)* [":" NAME]
    
    varlist: var ("," var)*
    
    ?var: NAME                                     -> var_name
        | prefixexp "[" exp "]"                    -> var_index
        | prefixexp "." NAME                       -> var_member
    
    namelist: NAME ("," NAME)*
    
    ?explist: (exp ",")* exp
    
    ?exp: "nil"                                    -> nil_exp
        | "false"                                  -> false_exp
        | "true"                                   -> true_exp
        | NUMBER                                   -> number_exp
        | STRING                                   -> string_exp
        | "..."                                    -> vararg_exp
        | functiondef                              -> func_exp
        | prefixexp                                -> prefix_exp
        | tableconstructor                         -> table_exp
        | exp binop exp                            -> bin_exp
        | unop exp                                 -> un_exp
    
    ?prefixexp: var                                -> prefix_var
             | functioncall                        -> prefix_call
             | "(" exp ")"                         -> prefix_paren
    
    functioncall: prefixexp args                   -> call_args
                | prefixexp ":" NAME args          -> call_method
    
    ?args: "(" [explist] ")"                       -> args_paren
         | tableconstructor                       -> args_table
         | STRING                                 -> args_string
    
    functiondef: "function" funcbody
    
    funcbody: "(" [parlist] ")" block "end"
    
    parlist: namelist ["," "..."] | "..."
    
    tableconstructor: "{" [fieldlist] "}"
    
    fieldlist: field (fieldsep field)* [fieldsep]
    
    field: "[" exp "]" "=" exp                     -> field_index
         | NAME "=" exp                            -> field_name
         | exp                                     -> field_exp
    
    fieldsep: "," | ";"
    
    binop: "+" | "-" | "*" | "/" | "^" | "%" | ".." 
         | "<" | "<=" | ">" | ">=" | "==" | "~=" 
         | "and" | "or"
    
    unop: "-" | "not" | "#"
    
    %import common.CNAME -> NAME
    %import common.SIGNED_NUMBER -> NUMBER
    STRING: /"[^"]*"/ | /'[^']*'/ | /\[\[.*?\]\]/s
    
    %import common.WS
    %ignore WS
    
    COMMENT: /--[^\n]*/
    %ignore COMMENT
    
    LONG_COMMENT: /--\[\[.*?\]\]/s
    %ignore LONG_COMMENT
'''

class LuaLexer:
    def __init__(self):
        self.parser = Lark(LUA_GRAMMAR, parser='lalr', propagate_positions=True)
    
    def parse(self, code: str):
        return self.parser.parse(code)
    
    def get_tokens(self, code: str):
        tree = self.parse(code)
        return tree
