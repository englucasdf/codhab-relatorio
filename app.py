from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json, base64, io, os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from pdf_generator import gerar_pdf

app = Flask(__name__)
CORS(app)

PASTA_RAIZ = "CODHAB"
SCOPES = ["https://www.googleapis.com/auth/drive"]

def get_drive_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise Exception("GOOGLE_CREDENTIALS não configurado")
    creds_info = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

def obter_ou_criar_pasta(service, nome, parent_id=None):
    q = f"name='{nome}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = service.files().list(q=q, fields="files(id,name)").execute()
    arquivos = res.get("files", [])
    if arquivos:
        return arquivos[0]["id"]
    meta = {"name": nome, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        meta["parents"] = [parent_id]
    pasta = service.files().create(body=meta, fields="id").execute()
    return pasta["id"]

def salvar_no_drive(pdf_bytes, nome_arquivo, ra):
    service = get_drive_service()
    id_codhab = obter_ou_criar_pasta(service, PASTA_RAIZ)
    id_ra = obter_ou_criar_pasta(service, ra, id_codhab)
    meta = {"name": nome_arquivo, "parents": [id_ra]}
    media = MediaIoBaseUpload(io.BytesIO(pdf_bytes), mimetype="application/pdf")
    arquivo = service.files().create(body=meta, media_body=media, fields="id,webViewLink").execute()
    return arquivo.get("webViewLink", "")

@app.route("/", methods=["GET"])
def index():
    return send_from_directory(".", "index.html")

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/gerar", methods=["POST"])
def gerar():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"ok": False, "erro": "Dados inválidos"}), 400

        print(f"Gerando PDF para: {dados.get('ra')} - {dados.get('endereco')}")
        buf = io.BytesIO()
        gerar_pdf(dados, buf)
        pdf_bytes = buf.getvalue()
        print(f"PDF gerado: {len(pdf_bytes)} bytes")

        nome = dados.get("endereco", "relatorio") + ".pdf"
        ra = dados.get("ra", "Geral")
        print(f"Salvando no Drive: CODHAB/{ra}/{nome}")
        url = salvar_no_drive(pdf_bytes, nome, ra)
        print(f"Salvo com sucesso: {url}")

        return jsonify({"ok": True, "nome": nome, "pasta": ra, "url": url})

    except Exception as e:
        import traceback
        print(f"ERRO: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"ok": False, "erro": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
