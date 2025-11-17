# exportar_csv.py
import sqlite3
import csv
import sys

# --- Configurações ---
DB_FILE = "academic.db"
CSV_FILE = "relatorio_presenca.csv"
RA_PARA_IGNORAR = "no_one"  

print(f"Iniciando exportação do banco '{DB_FILE}' para '{CSV_FILE}'...")
print(f"Ignorando registros com o RA: '{RA_PARA_IGNORAR}'")

try:
    #Conectar ao banco de dados
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    #Criar a consulta SQL
    #Junta (JOIN) as tabelas para pegar o nome
    #filtro (WHERE) para remover o RA indesejado.
    query = f"""
    SELECT
        p.data_hora,
        p.status,
        p.aluno_ra,
        a.nome_completo
    FROM
        presenca AS p
    LEFT JOIN
        alunos AS a ON p.aluno_ra = a.ra
    WHERE
        p.aluno_ra != ?  --
    ORDER BY
        p.data_hora
    """
    
    #Executar a consulta
    #Passamos o RA a ignorar como um parâmetro seguro
    cursor.execute(query, (RA_PARA_IGNORAR,))
    rows = cursor.fetchall()

    if not rows:
        print("Nenhum registro de presença (válido) encontrado no banco de dados.")
        sys.exit()

    print(f"Encontrados {len(rows)} registros válidos. Escrevendo no arquivo CSV...")

    # Escrever no arquivo CSV
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        
        # Escreve o cabeçalho
        writer.writerow(['Data_Hora', 'Status', 'RA', 'Nome_Completo'])
        
        # Escreve os dados
        writer.writerows(rows)

    print(f"\nSUCESSO! Relatório de presença salvo em '{CSV_FILE}'.")
    print("O RA 'no_one' foi ignorado.")

except sqlite3.Error as e:
    print(f"[ERRO DE BANCO DE DADOS]: {e}")
except Exception as e:
    print(f"[ERRO INESPERADO]: {e}")
finally:
    #Fechar a conexão com o banco
    if 'conn' in locals() and conn:
        conn.close()