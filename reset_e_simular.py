import sqlite3
from datetime import datetime

def simular():
    conn = sqlite3.connect('inspecao.db')
    cursor = conn.cursor()

    # 1. Limpa as inspeções antigas para não dar erro
    cursor.execute('DELETE FROM inspecoes')

    # 2. Dados para simular (Injetora, Data no formato AAAA-MM-DD, Status)
    dados_simulados = [
        (4, '2026-03-28', 'Verde'),
        (4, '2026-03-27', 'Verde'),
        (4, '2026-02-15', 'Vermelho'),
        (5, '2026-03-28', 'Vermelho'),
        (6, '2026-03-28', 'Verde'),
        (11, '2026-01-10', 'Verde'),
        (16, '2026-03-28', 'Verde')
    ]

    # 3. Insere os dados
    cursor.executemany('INSERT INTO inspecoes (id_maquina, data, status_ficha) VALUES (?, ?, ?)', dados_simulados)

    conn.commit()
    conn.close()
    print("✅ Banco de dados populado com sucesso!")

if __name__ == "__main__":
    simular()