from dataclasses import dataclass
from typing import List, Optional, Union, Any

@dataclass
class ASTNode:
    pass

@dataclass
class Chunk(ASTNode):
    body: List[ASTNode]

@dataclass
class Block(ASTNode):
    statements: List[ASTNode]

@dataclass
class Assignment(ASTNode):
    targets: List[ASTNode]
    values: List[ASTNode]

@dataclass
class LocalAssignment(ASTNode):
    names: List[str]
    values: List[ASTNode]

@dataclass
class FunctionCall(ASTNode):
    func: ASTNode
    args: List[ASTNode]

@dataclass
class String(ASTNode):
    value: str
    encrypted: bool = False

@dataclass
class Number(ASTNode):
    value: Union[int, float]

@dataclass
class Name(ASTNode):
    id: str

@dataclass
class BinOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

@dataclass
class UnOp(ASTNode):
    op: str
    operand: ASTNode

@dataclass
class If(ASTNode):
    cond: ASTNode
    then_block: Block
    else_block: Optional[Block] = None

@dataclass
class While(ASTNode):
    cond: ASTNode
    body: Block

@dataclass
class For(ASTNode):
    name: str
    start: ASTNode
    end: ASTNode
    step: Optional[ASTNode]
    body: Block

@dataclass
class FunctionDef(ASTNode):
    name: Optional[str]
    params: List[str]
    body: Block
    local: bool = False

@dataclass
class Return(ASTNode):
    values: List[ASTNode]

@dataclass
class TableConstructor(ASTNode):
    fields: List[tuple]

@dataclass
class Index(ASTNode):
    obj: ASTNode
    idx: ASTNode

@dataclass
class MemberAccess(ASTNode):
    obj: ASTNode
    member: str

@dataclass
class Vararg(ASTNode):
    pass

@dataclass
class Break(ASTNode):
    pass

@dataclass
class EncryptedBlock(ASTNode):
    data: bytes
    key: bytes
