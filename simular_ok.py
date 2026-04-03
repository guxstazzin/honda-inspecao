import sqlite3
from datetime import datetime

conn = sqlite3.connect('inspecao.db')
cursor = conn.cursor()

# Simulando um "OK" (Verde) na Injetora 4 hoje!
data_hoje = datetime.now().strftime('%Y-%m-%d')
cursor.execute('INSERT INTO inspecoes (id_maquina, data, status_ficha) VALUES (?, ?, ?)', 
               (4, data_hoje, 'Verde'))

conn.commit()
conn.close()
print(f"Inspeção realizada com sucesso para o dia {data_hoje}!")