from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import io, os
from pdf_generator import gerar_pdf

app = Flask(__name__)
CORS(app)

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

        ra = dados.get("ra", "Geral")
        endereco = dados.get("endereco", "relatorio")
        print(f"Gerando PDF para: {ra} - {endereco}")

        buf = io.BytesIO()
        gerar_pdf(dados, buf)
        pdf_bytes = buf.getvalue()
        print(f"PDF gerado: {len(pdf_bytes)} bytes")

        # Nome do arquivo: RA_Endereco.pdf (sem caracteres problemáticos)
        nome = f"{ra}_{endereco}.pdf".replace("/", "-").replace("\\", "-")

        response = make_response(pdf_bytes)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f'attachment; filename="{nome}"'
        response.headers["Content-Length"] = len(pdf_bytes)
        return response

    except Exception as e:
        import traceback
        print(f"ERRO: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"ok": False, "erro": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
