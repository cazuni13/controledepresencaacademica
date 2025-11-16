# main_tm.py
import cv2
import numpy as np
import tensorflow.keras as keras
import sqlite3
from datetime import datetime
import sys
import os

# --- CONFIGURAÇÕES ---
MODEL_PATH = "keras_model.h5"
LABELS_PATH = "labels.txt"
DB_FILE = "academic.db"
SAIDA_TIMEOUT = 60 # Segundos sem ver o aluno para registrar "saida"
CONFIDENCE_THRESHOLD = 0.95 # Confiança mínima (95%)
# --- FIM DAS CONFIGURAÇÕES ---

# 1. Carregar o modelo e os labels
try:
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # Ignora avisos do TensorFlow
    model = keras.models.load_model(MODEL_PATH, compile=False)
    with open(LABELS_PATH, 'r') as f:
        # Pega apenas o nome da classe (ex: "12345" ou "Fundo")
        labels = [line.strip().split(' ', 1)[1] for line in f if line.strip()]
    print(f"[INFO] Modelo e labels carregados. Classes: {labels}")
except Exception as e:
    print(f"[ERRO] Falha ao carregar modelo/labels: {e}")
    sys.exit(1)

# 2. Funções do Banco de Dados
alunos_presentes = {} # Dicionário para rastrear quem está na sala

def connect_db():
    try:
        return sqlite3.connect(DB_FILE)
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao DB: {e}")
        return None

def get_student_info(conn, ra):
    """Busca o nome do aluno no DB a partir do RA."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT nome_completo FROM alunos WHERE ra = ?", (ra,))
        result = cursor.fetchone()
        return result[0] if result else "RA Nao Cadastrado"
    except sqlite3.Error:
        return "Erro DB"

def log_presence(conn, ra, status):
    """Registra entrada ou saída no banco de dados."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO presenca (aluno_ra, data_hora, status) VALUES (?, ?, ?)",
                       (ra, timestamp, status))
        conn.commit()
        nome = get_student_info(conn, ra)
        print(f"LOG: {status} de {ra} ({nome}) registrada às {timestamp}")
    except sqlite3.Error as e:
        print(f"Erro ao registrar presença para {ra}: {e}")

def check_for_saida(conn):
    """Verifica se algum aluno presente atingiu o timeout para 'saida'."""
    agora = datetime.now()
    ras_para_remover = []
    for ra, info in alunos_presentes.items():
        segundos_desde_visto = (agora - info['last_seen']).total_seconds()
        if segundos_desde_visto > SAIDA_TIMEOUT:
            log_presence(conn, ra, 'saida')
            ras_para_remover.append(ra)
    for ra in ras_para_remover:
        del alunos_presentes[ra]

# 3. Início da Execução
db_conn = connect_db()
if db_conn is None:
    sys.exit("Falha na conexão com o banco de dados. Saindo.")

print("[INFO] Iniciando câmera... (Pressione 'q' para sair)")
video_capture = cv2.VideoCapture(0) # 0 para a webcam padrão

# --- LOOP PRINCIPAL ---
while True:
    ret, frame = video_capture.read()
    if not ret:
        print("Erro ao capturar frame. Encerrando.")
        break

    agora = datetime.now()
    
    # 4. Pré-processamento da Imagem (padrão do Teachable Machine)
    img_resized = cv2.resize(frame, (224, 224))
    img_array = np.asarray(img_resized, dtype=np.float32)
    img_normalized = (img_array / 127.0) - 1
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = img_normalized

    # 5. Fazer a Predição (CNN em ação)
    # verbose=0 desliga os logs de "predicting" do TensorFlow
    prediction = model.predict(data, verbose=0) 
    index = np.argmax(prediction)
    ra_predito = labels[index]
    confianca = prediction[0][index]
    
    nome_display = "---"
    ra_display = "---"

    # 6. Lógica de Presença
    if confianca > CONFIDENCE_THRESHOLD:
        # Se for uma classe de aluno (e não a classe "Fundo")
        if ra_predito != "Fundo": 
            ra = ra_predito
            ra_display = ra
            nome_display = get_student_info(db_conn, ra)
            
            # Lógica de ENTRADA: Se o aluno não está na lista, registre.
            if ra not in alunos_presentes:
                log_presence(db_conn, ra, 'entrada')
            
            # De qualquer forma, atualize a última vez que o aluno foi visto
            alunos_presentes[ra] = {'last_seen': agora, 'status': 'entrada'}
        else:
            nome_display = "Fundo"
    else:
        nome_display = "Desconhecido"

    # 7. Lógica de SAÍDA (Verifica timeouts)
    check_for_saida(db_conn)

    # 8. Exibir informações na tela
    cv2.putText(frame, f"RA: {ra_display}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Nome: {nome_display}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Confianca: {confianca*100:.2f}%", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow('Controle de Presenca (Teachable Machine)', frame)

    # Pressione 'q' para sair
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- FIM DO LOOP ---
print("[INFO] Encerrando aplicação...")
# Registra a saída de todos que ainda estavam "presentes"
for ra in alunos_presentes:
    log_presence(db_conn, ra, 'saida')

video_capture.release()
cv2.destroyAllWindows()
db_conn.close()
print("Aplicação encerrada.")