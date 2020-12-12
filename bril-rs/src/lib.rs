use serde::{Deserialize, Serialize};
use std::io::{self, Read, Write};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Program {
    pub functions: Vec<Function>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Function {
    pub name: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub args: Vec<Argument>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub r#type: Option<Type>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub instrs: Vec<Code>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Argument {
    pub name: String,
    pub r#type: Type,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(untagged)]
pub enum Code {
    Label { label: String },
    Instruction(Instruction),
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(untagged)]
pub enum Instruction {
    Constant {
        op: ConstOps,
        dest: String,
        r#type: Type,
        value: Literal,
    },
    Value {
        op: ValueOps,
        dest: String,
        r#type: Type,
        #[serde(default, skip_serializing_if = "Vec::is_empty")]
        args: Vec<String>,
        #[serde(default, skip_serializing_if = "Vec::is_empty")]
        funcs: Vec<String>,
        #[serde(default, skip_serializing_if = "Vec::is_empty")]
        labels: Vec<String>,
    },
    Effect {
        op: EffectOps,
        #[serde(default, skip_serializing_if = "Vec::is_empty")]
        args: Vec<String>,
        #[serde(default, skip_serializing_if = "Vec::is_empty")]
        funcs: Vec<String>,
        #[serde(default, skip_serializing_if = "Vec::is_empty")]
        labels: Vec<String>,
    },
}

#[derive(Serialize, Deserialize, Debug, Copy, Clone, PartialEq, Eq, Hash)]
pub enum ConstOps {
    #[serde(rename = "const")]
    Const,
}

#[derive(Serialize, Deserialize, Debug, Copy, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "lowercase")]
pub enum EffectOps {
    #[serde(rename = "jmp")]
    Jump,
    #[serde(rename = "br")]
    Branch,
    Call,
    #[serde(rename = "ret")]
    Return,
    Print,
    Nop,
    #[cfg(feature = "memory")]
    Store,
    #[cfg(feature = "memory")]
    Free,
    #[cfg(feature = "speculate")]
    Speculate,
    #[cfg(feature = "speculate")]
    Commit,
    #[cfg(feature = "speculate")]
    Guard,
}

#[derive(Serialize, Deserialize, Debug, Copy, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "lowercase")]
pub enum ValueOps {
    Add,
    Sub,
    Mul,
    Div,
    Eq,
    Lt,
    Gt,
    Le,
    Ge,
    Not,
    And,
    Or,
    Call,
    Id,
    #[cfg(feature = "ssa")]
    Phi,
    #[cfg(feature = "float")]
    Fadd,
    #[cfg(feature = "float")]
    Fsub,
    #[cfg(feature = "float")]
    Fmul,
    #[cfg(feature = "float")]
    Fdiv,
    #[cfg(feature = "float")]
    Feq,
    #[cfg(feature = "float")]
    Flt,
    #[cfg(feature = "float")]
    Fgt,
    #[cfg(feature = "float")]
    Fle,
    #[cfg(feature = "float")]
    Fge,
    #[cfg(feature = "memory")]
    Alloc,
    #[cfg(feature = "memory")]
    Load,
    #[cfg(feature = "memory")]
    PtrAdd,
}

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "lowercase")]
pub enum Type {
    Int,
    Bool,
    #[cfg(feature = "float")]
    Float,
    #[cfg(feature = "memory")]
    #[serde(rename = "ptr")]
    Pointer(Box<Type>),
}

#[derive(Serialize, Deserialize, Debug, Copy, Clone, PartialEq)]
#[serde(untagged)]
pub enum Literal {
    Int(i64),
    Bool(bool),
    #[cfg(feature = "float")]
    Float(f64),
}

pub fn load_program() -> Program {
    let mut buffer = String::new();
    io::stdin().read_to_string(&mut buffer).unwrap();
    serde_json::from_str(&buffer).unwrap()
}

pub fn output_program(p: &Program) {
    io::stdout()
        .write_all(serde_json::to_string(p).unwrap().as_bytes())
        .unwrap();
}
