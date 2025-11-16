# add_aluno.py
import sqlite3
import sys

def adicionar_aluno(ra, nome):
    # Verifica se os argumentos foram passados corretamente
    if not ra or not nome:
        print("ERRO: RA e Nome são obrigatórios.")
        print("Uso: python add_aluno.py <RA> \"<Nome Completo>\"")
        return

    try:
        conn = sqlite3.connect('academic.db')
        cursor = conn.cursor()
        
        # O comando "REPLACE" é ótimo:
        # Se o RA não existe, ele insere.
        # Se o RA já existe, ele atualiza o nome.
        cursor.execute("REPLACE INTO alunos (ra, nome_completo) VALUES (?, ?)", (ra, nome))
        
        conn.commit()
        print(f"SUCESSO: Aluno {nome} (RA: {ra}) salvo no banco.")
        
    except sqlite3.Error as e:
        print(f"ERRO ao adicionar aluno: {e}")
    finally:
        if conn:
            conn.close()

# --- Ponto de entrada do script ---
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python add_aluno.py <RA> \"<Nome Completo>\"")
        print("Exemplo: python add_aluno.py 12345 \"Joao da Silva\"")
        # As aspas duplas são importantes se o nome tiver espaços
    else:
        adicionar_aluno(sys.argv[1], sys.argv[2])



# Comandos utilizados para adicionar os alunos
# py add_aluno.py joao-2023014145 "Joao Cazuni"
#  py add_aluno.py victor-2022024077 "Victor A. M. dos Santos"