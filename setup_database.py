# setup_database.py
import sqlite3

try:
    # Conecta ao banco (cria o arquivo 'academic.db' se não existir)
    conn = sqlite3.connect('academic.db')
    cursor = conn.cursor()

    # 1. Tabela de Alunos (Guarda o RA e o Nome)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            ra TEXT PRIMARY KEY NOT NULL,
            nome_completo TEXT NOT NULL
        )
    ''')

    # 2. Tabela de Presença (Guarda o histórico de entradas/saídas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presenca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_ra TEXT NOT NULL,
            data_hora TEXT NOT NULL,
            status TEXT NOT NULL,  -- "entrada" ou "saida"
            FOREIGN KEY (aluno_ra) REFERENCES alunos (ra)
        )
    ''')

    print("SUCESSO: Banco de dados 'academic.db' e tabelas criados.")

except sqlite3.Error as e:
    print(f"ERRO: Ocorreu um erro ao configurar o banco de dados: {e}")

finally:
    if conn:
        conn.commit()
        conn.close()