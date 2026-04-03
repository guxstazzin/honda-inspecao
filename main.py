from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import calendar
import json
import os
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ARQUIVO_BD = "banco_dados.json"
ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_QUADRO = "quadro_producao.json"

def carregar_dados(arquivo):
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def salvar_dados(dados, arquivo):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

historico_inspecoes = carregar_dados(ARQUIVO_BD)
banco_usuarios = carregar_dados(ARQUIVO_USUARIOS)
quadro_producao = carregar_dados(ARQUIVO_QUADRO)

def limpar_chave(k):
    return str(k).upper().replace(" ", "").replace("-", "").replace("_", "")

def obter_hora_manaus():
    return datetime.utcnow() - timedelta(hours=4)

@app.get("/")
async def abrir_dashboard(): return FileResponse("index.html")

@app.get("/inspecao")
async def abrir_ficha(): return FileResponse("ficha.html")

@app.post("/cadastrar")
async def cadastrar(dados: dict):
    matricula = str(dados.get("matricula", ""))
    if matricula in banco_usuarios:
        return JSONResponse(content={"erro": "Esta matrícula já está cadastrada!"}, status_code=400)
    
    # 🔥 AGORA SALVA O SETOR DO INSPETOR NA HORA DO CADASTRO 🔥
    banco_usuarios[matricula] = {
        "nome": dados.get("nome"), 
        "senha": dados.get("senha"),
        "setor": dados.get("setor", "LPDC") # Salva se é LPDC ou HPDC
    }
    salvar_dados(banco_usuarios, ARQUIVO_USUARIOS)
    return {"status": "ok", "nome": dados.get("nome"), "setor": dados.get("setor")}

@app.post("/login")
async def login(dados: dict):
    matricula = str(dados.get("matricula", ""))
    senha = str(dados.get("senha", ""))
    usuario = banco_usuarios.get(matricula)
    
    if not usuario or str(usuario.get("senha", "")) != senha:
        return JSONResponse(content={"erro": "Matrícula ou senha incorretos!"}, status_code=401)
        
    # Se o usuário for antigo e não tiver setor, o sistema define como LPDC pra não dar erro
    setor_usuario = usuario.get("setor", "LPDC")
        
    return {
        "status": "ok", 
        "nome": usuario.get("nome", "Usuário"), 
        "assinatura": usuario.get("assinatura", ""),
        "setor": setor_usuario
    }

@app.get("/maquinas")
async def listar_maquinas():
    agora = obter_hora_manaus()
    dia_atual = agora.day
    mes_atual = agora.month
    hora = agora.hour
    
    if 7 <= hora < 15: turno_atual = 1
    elif 15 <= hora < 23: turno_atual = 2
    else: turno_atual = 3

    maquinas_lista = []
    
    for i in range(4, 17):
        maquinas_lista.append({"id": str(i), "nome": f"MAQ {i}", "setor": "LPDC"})
    
    macheiras = ["H-TOP 1", "H-TOP 2", "H-TOP 3", "H-TOP 4", "H-TOP 5", "V-TOP 1", "V-TOP 2", "V-TOP 3", "H-TOP 6"]
    for m in macheiras:
        id_macheira = m.replace(" ", "").replace("-", "")
        maquinas_lista.append({"id": id_macheira, "nome": m, "setor": "MACHEIRA"})

    hpdc_nums = [2, 7, 8, 9, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22]
    for i in hpdc_nums:
        maquinas_lista.append({"id": f"HPDC{i}", "nome": f"INJ. {i}", "setor": "HPDC"})

    maquinas_status = []
    for maq in maquinas_lista:
        m_id = maq["id"]
        chave1 = limpar_chave(f"{m_id}{mes_atual}{dia_atual}{turno_atual}1")
        chave2 = limpar_chave(f"{m_id}{mes_atual}{dia_atual}{turno_atual}2")
        
        insp1 = any(limpar_chave(k) == chave1 for k in historico_inspecoes.keys())
        insp2 = any(limpar_chave(k) == chave2 for k in historico_inspecoes.keys())
        
        maquinas_status.append({
            "id": m_id, "nome": maq["nome"], "setor": maq["setor"],
            "turno_atual": turno_atual, "insp1": insp1, "insp2": insp2
        })
    return maquinas_status

@app.get("/maquinas/{id}/meses")
async def listar_meses(id: str):
    nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    return [{"id_mes": i+1, "nome": n} for i, n in enumerate(nomes)]

@app.get("/maquinas/{id}/meses/{id_mes}/dias")
async def listar_dias(id: str, id_mes: int):
    _, ultimo = calendar.monthrange(2026, id_mes)
    dias = []
    for d in range(1, ultimo + 1):
        prefixo = limpar_chave(f"{id}{id_mes}{d}")
        tem_ficha = any(limpar_chave(k).startswith(prefixo) for k in historico_inspecoes.keys())
        dias.append({"dia": d, "status_ficha": "Verde" if tem_ficha else "Cinza"})
    return dias

@app.get("/maquinas/{id}/meses/{id_mes}/dias/{dia}/resumo")
async def resumo_dia(id: str, id_mes: int, dia: int):
    resumo = {}
    for turno in [1, 2, 3]:
        c1 = limpar_chave(f"{id}{id_mes}{dia}{turno}1")
        c2 = limpar_chave(f"{id}{id_mes}{dia}{turno}2")
        achou1 = any(limpar_chave(k) == c1 for k in historico_inspecoes.keys())
        achou2 = any(limpar_chave(k) == c2 for k in historico_inspecoes.keys())
        resumo[str(turno)] = {"insp1": achou1, "insp2": achou2}
    return resumo

@app.get("/ver-ficha/{maquina}/{mes}/{dia}/{turno}/{inspecao}")
async def buscar_ficha(maquina: str, mes: int, dia: int, turno: int, inspecao: int):
    chave_esperada = limpar_chave(f"{maquina}{mes}{dia}{turno}{inspecao}")
    for k, v in historico_inspecoes.items():
        if limpar_chave(k) == chave_esperada:
            return v
    return JSONResponse(content={"erro": "Ficha não encontrada."}, status_code=404)

@app.post("/salvar-inspecao")
async def salvar(dados: dict):
    try:
        injetora = limpar_chave(dados.get('injetora', ''))
        mes = str(dados.get('mes', ''))
        dia = str(dados.get('dia', ''))
        turno = str(dados.get('turno', ''))
        inspecao = str(dados.get('inspecao', ''))
        
        chave_oficial = f"{injetora}-{mes}-{dia}-{turno}-{inspecao}"
        
        chave_busca = limpar_chave(chave_oficial)
        if any(limpar_chave(k) == chave_busca for k in historico_inspecoes.keys()):
            return JSONResponse(content={"erro": "Ficha já salva! O inspetor não pode regravar inspeções concluídas."}, status_code=403)
        
        historico_inspecoes[chave_oficial] = dados
        salvar_dados(historico_inspecoes, ARQUIVO_BD)

        mat = str(dados.get("matricula_inspetor", ""))
        ass = dados.get("assinatura_inspetor", "")
        if mat and ass and mat in banco_usuarios:
            if not banco_usuarios[mat].get("assinatura"):
                banco_usuarios[mat]["assinatura"] = ass
                salvar_dados(banco_usuarios, ARQUIVO_USUARIOS)

        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(content={"erro": f"Erro interno: {str(e)}"}, status_code=500)

@app.get("/obter-quadro")
async def obter_quadro():
    return quadro_producao

@app.post("/salvar-quadro")
async def salvar_quadro_endpoint(dados: dict):
    global quadro_producao
    for chave, valores in dados.items():
        quadro_producao[chave] = valores
    salvar_dados(quadro_producao, ARQUIVO_QUADRO)
    return {"status": "ok"}

@app.post("/assinar-ficha")
async def assinar_ficha(dados: dict):
    try:
        chave = limpar_chave(dados.get("chave", ""))
        cargo = str(dados.get("cargo", ""))
        matricula = str(dados.get("matricula", ""))
        senha = str(dados.get("senha", ""))
        nova_assinatura = dados.get("assinatura", "")

        usuario = banco_usuarios.get(matricula)
        if not usuario or str(usuario.get("senha", "")) != senha:
            return JSONResponse(content={"erro": "Matrícula ou senha incorretos!"}, status_code=401)
        
        if not usuario.get("assinatura") and nova_assinatura:
            usuario["assinatura"] = nova_assinatura
            salvar_dados(banco_usuarios, ARQUIVO_USUARIOS)
        elif not usuario.get("assinatura") and not nova_assinatura:
            return JSONResponse(content={"erro": "Você precisa desenhar sua assinatura no primeiro acesso!"}, status_code=400)

        for k in historico_inspecoes.keys():
            if limpar_chave(k) == chave:
                historico_inspecoes[k][cargo] = {"nome": usuario.get("nome", "Usuário"), "assinatura": usuario.get("assinatura", "")}
                salvar_dados(historico_inspecoes, ARQUIVO_BD)
                return {"status": "ok"}
        
        return JSONResponse(content={"erro": "Ficha não encontrada."}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"erro": f"Falha no servidor: {str(e)}"}, status_code=500)