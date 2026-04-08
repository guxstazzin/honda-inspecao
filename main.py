from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import calendar

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 CHAVE DO SEU COFRE FIREBASE
FIREBASE_URL = "https://honda-qualidade-default-rtdb.firebaseio.com/"

# --- FUNÇÕES DE COMUNICAÇÃO COM O COFRE (FIREBASE) ---

def salvar_no_cofre(caminho: str, dados: Any):
    url = f"{FIREBASE_URL}{caminho}.json"
    requests.put(url, json=dados)

def ler_do_cofre(caminho: str):
    url = f"{FIREBASE_URL}{caminho}.json"
    response = requests.get(url)
    dados = response.json()
    
    # 🛡️ VACINA: Se o Firebase transformar números de matrícula em Listas, isso reverte pra Dicionário
    if isinstance(dados, list):
        return {str(i): v for i, v in enumerate(dados) if v is not None}
    
    return dados if dados is not None else {}

# --- MODELOS DE DADOS ---

class Usuario(BaseModel):
    nome: str
    matricula: str
    senha: str
    setor: Optional[str] = "LPDC"

class LoginRequest(BaseModel):
    matricula: str
    senha: str

class AssinaturaRequest(BaseModel):
    chave: str 
    cargo: str 
    matricula: str
    senha: str
    assinatura: str 

# --- ROTAS DO SISTEMA ---

@app.get("/")
def home():
    return {"status": "Jarvis Online", "database": "Conectado ao Firebase Cloud"}

@app.post("/cadastrar")
def cadastrar(u: Usuario):
    usuarios = ler_do_cofre("usuarios")
    if u.matricula in usuarios:
        return JSONResponse(status_code=400, content={"erro": "Matrícula já cadastrada!"})
    
    usuarios[u.matricula] = {
        "nome": u.nome,
        "senha": u.senha,
        "setor": u.setor,
        "assinatura": ""
    }
    salvar_no_cofre("usuarios", usuarios)
    return {"status": "ok"}

@app.post("/login")
def login(req: LoginRequest):
    usuarios = ler_do_cofre("usuarios")
    u = usuarios.get(req.matricula)
    
    if not u or u.get("senha") != req.senha:
        return JSONResponse(status_code=400, content={"erro": "Matrícula ou senha incorretos!"})
        
    return {
        "nome": u["nome"], 
        "assinatura": u.get("assinatura", ""),
        "setor": u.get("setor", "LPDC"),
        "ok": True
    }

@app.get("/maquinas")
def listar_maquinas():
    hoje = datetime.now()
    dia, mes = str(hoje.day), str(hoje.month)
    
    plantas = [
        {"id": "4", "nome": "MAQ 4", "setor": "LPDC"},
        {"id": "5", "nome": "MAQ 5", "setor": "LPDC"},
        {"id": "6", "nome": "MAQ 6", "setor": "LPDC"},
        {"id": "7", "nome": "MAQ 7", "setor": "LPDC"},
        {"id": "9", "nome": "MAQ 9", "setor": "LPDC"},
        {"id": "11", "nome": "MAQ 11", "setor": "LPDC"},
        {"id": "12", "nome": "MAQ 12", "setor": "LPDC"},
        {"id": "13", "nome": "MAQ 13", "setor": "LPDC"},
        {"id": "14", "nome": "MAQ 14", "setor": "LPDC"},
        {"id": "15", "nome": "MAQ 15", "setor": "LPDC"},
        {"id": "16", "nome": "MAQ 16", "setor": "LPDC"},
        {"id": "HTOP2", "nome": "H-TOP 2", "setor": "MACHEIRA"},
        {"id": "HTOP3", "nome": "H-TOP 3", "setor": "MACHEIRA"},
        {"id": "HTOP4", "nome": "H-TOP 4", "setor": "MACHEIRA"},
        {"id": "HTOP5", "nome": "H-TOP 5", "setor": "MACHEIRA"},
        {"id": "HTOP6", "nome": "H-TOP 6", "setor": "MACHEIRA"},
        {"id": "HTOP7", "nome": "H-TOP 7", "setor": "MACHEIRA"},
        {"id": "VTOP1", "nome": "V-TOP 1", "setor": "MACHEIRA"},
        {"id": "VTOP2", "nome": "V-TOP 2", "setor": "MACHEIRA"},
        {"id": "VTOP3", "nome": "V-TOP 3", "setor": "MACHEIRA"},
        {"id": "HPDC2", "nome": "INJ. 2", "setor": "HPDC"},
        {"id": "HPDC7", "nome": "INJ. 7", "setor": "HPDC"},
        {"id": "HPDC8", "nome": "INJ. 8", "setor": "HPDC"},
        {"id": "HPDC9", "nome": "INJ. 9", "setor": "HPDC"},
        {"id": "HPDC12", "nome": "INJ. 12", "setor": "HPDC"},
        {"id": "HPDC13", "nome": "INJ. 13", "setor": "HPDC"},
        {"id": "HPDC15", "nome": "INJ. 15", "setor": "HPDC"},
        {"id": "HPDC16", "nome": "INJ. 16", "setor": "HPDC"},
        {"id": "HPDC17", "nome": "INJ. 17", "setor": "HPDC"},
        {"id": "HPDC18", "nome": "INJ. 18", "setor": "HPDC"},
        {"id": "HPDC19", "nome": "INJ. 19", "setor": "HPDC"},
        {"id": "HPDC20", "nome": "INJ. 20", "setor": "HPDC"},
        {"id": "HPDC21", "nome": "INJ. 21", "setor": "HPDC"},
        {"id": "HPDC22", "nome": "INJ. 22", "setor": "HPDC"}
    ]
    
    banco = ler_do_cofre("banco_inspecoes")
    turno_atual = 3
    if 7 <= hoje.hour < 15: turno_atual = 1
    elif 15 <= hoje.hour < 23: turno_atual = 2

    for m in plantas:
        m["turno_atual"] = turno_atual
        chave1 = f"{m['id']}-{mes}-{dia}-{turno_atual}-1"
        chave2 = f"{m['id']}-{mes}-{dia}-{turno_atual}-2"
        m["insp1"] = chave1 in banco
        m["insp2"] = chave2 in banco
        
    return plantas

@app.post("/salvar-inspecao")
def salvar_inspecao(dados: Dict[str, Any]):
    chave = f"{dados['injetora']}-{dados['mes']}-{dados['dia']}-{dados['turno']}-{dados['inspecao']}"
    banco = ler_do_cofre("banco_inspecoes")
    banco[chave] = dados
    salvar_no_cofre("banco_inspecoes", banco)
    
    if dados.get("assinatura_inspetor") and dados.get("matricula_inspetor"):
        usuarios = ler_do_cofre("usuarios")
        mat = dados["matricula_inspetor"]
        if mat in usuarios:
            usuarios[mat]["assinatura"] = dados["assinatura_inspetor"]
            salvar_no_cofre("usuarios", usuarios)
            
    return {"status": "ok", "chave": chave}

# 🔥 NOVO: Mostra o calendário completo de 12 meses
@app.get("/maquinas/{id_m}/meses")
def listar_meses(id_m: str):
    nomes_meses = {1:"Janeiro", 2:"Fevereiro", 3:"Março", 4:"Abril", 5:"Maio", 6:"Junho", 7:"Julho", 8:"Agosto", 9:"Setembro", 10:"Outubro", 11:"Novembro", 12:"Dezembro"}
    res = []
    for m in range(1, 13):
        res.append({"id_mes": m, "nome": nomes_meses[m]})
    return res

# 🔥 NOVO: Mostra todos os dias do mês, pintando de Verde se tiver ficha e de Cinza se não tiver
@app.get("/maquinas/{id_m}/meses/{id_mes}/dias")
def listar_dias(id_m: str, id_mes: int):
    banco = ler_do_cofre("banco_inspecoes")
    dias_com_ficha = set()
    
    # Procura quais dias têm fichas salvas
    for chave in banco:
        partes = chave.split('-')
        if partes[0] == id_m and partes[1] == str(id_mes):
            dias_com_ficha.add(int(partes[2]))
            
    hoje = datetime.now()
    try:
        _, num_dias = calendar.monthrange(hoje.year, id_mes)
    except:
        num_dias = 31

    res = []
    for d in range(1, num_dias + 1):
        cor_do_card = "Verde" if d in dias_com_ficha else "Cinza"
        res.append({"dia": d, "status_ficha": cor_do_card})
        
    return res

@app.get("/maquinas/{id_m}/meses/{id_mes}/dias/{dia}/resumo")
def resumo_dia(id_m: str, id_mes: int, dia: int):
    banco = ler_do_cofre("banco_inspecoes")
    res = {"1": {"insp1": False, "insp2": False}, "2": {"insp1": False, "insp2": False}, "3": {"insp1": False, "insp2": False}}
    for t in ["1","2","3"]:
        for i in ["1","2"]:
            if f"{id_m}-{id_mes}-{dia}-{t}-{i}" in banco:
                res[t][f"insp{i}"] = True
    return res

@app.get("/ver-ficha/{id_m}/{id_mes}/{dia}/{turno}/{insp}")
def ver_ficha(id_m: str, id_mes: int, dia: int, turno: int, insp: int):
    banco = ler_do_cofre("banco_inspecoes")
    chave = f"{id_m}-{id_mes}-{dia}-{turno}-{insp}"
    ficha = banco.get(chave)
    if not ficha:
        return JSONResponse(status_code=404, content={"erro": "Ficha não encontrada"})
    return ficha

@app.post("/salvar-quadro")
def salvar_quadro(dados: Dict[str, Any]):
    salvar_no_cofre("quadro_producao", dados)
    return {"status": "ok"}

@app.get("/obter-quadro")
def obter_quadro():
    return ler_do_cofre("quadro_producao")

@app.post("/assinar-ficha")
def assinar_ficha(req: AssinaturaRequest):
    usuarios = ler_do_cofre("usuarios")
    u = usuarios.get(req.matricula)
    
    if not u or u.get("senha") != req.senha:
        return JSONResponse(status_code=400, content={"erro": "Credenciais de chefia inválidas"})
    
    banco = ler_do_cofre("banco_inspecoes")
    if req.chave not in banco:
        return JSONResponse(status_code=400, content={"erro": "Ficha não encontrada"})
    
    img_assinatura = req.assinatura if len(req.assinatura) > 100 else u.get("assinatura", "")
    
    banco[req.chave][req.cargo] = {
        "nome": u["nome"],
        "assinatura": img_assinatura
    }
    salvar_no_cofre("banco_inspecoes", banco)
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)