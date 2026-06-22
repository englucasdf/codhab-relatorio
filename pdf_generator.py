from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, PageBreak, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect, String, Line, PolyLine
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
import io, base64, os, json, sys
from PIL import Image as PILImage

# ── Cores ──────────────────────────────────────────────────────────────────
AZUL_HEADER = colors.HexColor("#b6b6b6")
AZUL_ETAPA  = colors.HexColor("#999999")
AZUL_CLARO  = colors.HexColor("#cccccc")
CINZA_LINHA = colors.HexColor("#b6b6b6")
PRETO       = colors.black
BRANCO      = colors.white
CINZA_ETAPA = colors.HexColor("#b6b6b6")   # linhas de etapa
CINZA_HEADER= colors.HexColor("#999999")   # header da tabela
CINZA_SUB   = colors.HexColor("#cccccc")   # subtítulos
AZUL_GRAFICO= colors.HexColor("#4185f4")   # barras do gráfico
VERDE_G1    = colors.HexColor("#d9e9d3")   # grupo 1º conclusão
AMARELO_G2  = colors.HexColor("#ffe499")   # grupo 2º conclusão
VERMELHO_G3 = colors.HexColor("#e99999")   # grupo 3º conclusão

W, H = A4  # 595 x 842 pt

# ── Estilos ────────────────────────────────────────────────────────────────
def estilos():
    centro     = ParagraphStyle("centro",     fontName="Helvetica-Bold", fontSize=7,  alignment=TA_CENTER, leading=9)
    centro_med = ParagraphStyle("centro_med", fontName="Helvetica-Bold", fontSize=8,  alignment=TA_CENTER, leading=10)
    normal_s   = ParagraphStyle("normal_s",   fontName="Helvetica",      fontSize=7,  alignment=TA_LEFT,   leading=9)
    bold_s     = ParagraphStyle("bold_s",     fontName="Helvetica-Bold", fontSize=7,  alignment=TA_LEFT,   leading=9)
    bold_c     = ParagraphStyle("bold_c",     fontName="Helvetica-Bold", fontSize=7,  alignment=TA_CENTER, leading=9)
    titulo     = ParagraphStyle("titulo",     fontName="Helvetica-Bold", fontSize=11, alignment=TA_CENTER, leading=13)
    subtitulo  = ParagraphStyle("subtitulo",  fontName="Helvetica-Bold", fontSize=8,  alignment=TA_CENTER, leading=10)
    italic_s   = ParagraphStyle("italic_s",   fontName="Helvetica-Oblique", fontSize=7, alignment=TA_LEFT, leading=9)
    bold_exp   = ParagraphStyle("bold_exp",   fontName="Helvetica-Bold", fontSize=8,  alignment=TA_LEFT,   leading=11)
    return dict(centro=centro, centro_med=centro_med, normal_s=normal_s,
                bold_s=bold_s, bold_c=bold_c, titulo=titulo,
                subtitulo=subtitulo, italic_s=italic_s, bold_exp=bold_exp)

ST = estilos()

LOGO_CODHAB = "/home/claude/logo_p1_0.png"
LOGO_GDF    = "/home/claude/logo_p1_1.png"

# ── Cabeçalho institucional ────────────────────────────────────────────────
def cabecalho(gerencia="Gerência de Patrimônio - GEPAT"):
    txt = (
        "<b>GOVERNO DO DISTRITO FEDERAL</b><br/>"
        "Companhia de Desenvolvimento Habitacional do Distrito Federal - CODHAB<br/>"
        "Grupo de Trabalho Gestão de Patrimônio e Comercialização de Imóveis<br/>"
        f"{gerencia}<br/>"
        "Diretória Imobiliária - DIMOB"
    )
    p = ParagraphStyle("cab", fontName="Helvetica", fontSize=7, alignment=TA_CENTER, leading=9)
    pb = ParagraphStyle("cab_b", fontName="Helvetica-Bold", fontSize=7, alignment=TA_CENTER, leading=9)

    logo_c = Image(LOGO_CODHAB, width=18*mm, height=16*mm)
    logo_g = Image(LOGO_GDF,    width=22*mm, height=10*mm)

    linhas = txt.split("<br/>")
    cells = []
    for i, l in enumerate(linhas):
        s = pb if i == 0 else p
        cells.append(Paragraph(l.replace("<b>","").replace("</b>",""), s))

    cab_table = Table(
        [[logo_c, cells, logo_g]],
        colWidths=[22*mm, 122*mm, 26*mm]
    )
    cab_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",  (1,0), (1,0),   "CENTER"),
        ("ALIGN",  (2,0), (2,0),   "RIGHT"),
        ("LEFTPADDING",  (0,0), (-1,-1), 2),
        ("RIGHTPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING",   (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0), (-1,-1), 2),
    ]))
    return cab_table

# ── Página 1: Identificação + Medição das Etapas ──────────────────────────
def pagina1(dados):
    story = []
    story.append(cabecalho("Gerência de Patrimônio - GEPAT"))
    story.append(Spacer(1, 3*mm))

    # Título principal
    tit = Table([[Paragraph("RELATÓRIO DE MEDIÇÃO DE OBRA - CODHAB", ST["titulo"])]],
                colWidths=[170*mm])
    tit.setStyle(TableStyle([
        ("BOX",        (0,0),(0,0), 0.5, PRETO),
        ("BACKGROUND", (0,0),(0,0), AZUL_CLARO),
        ("TOPPADDING", (0,0),(0,0), 4),
        ("BOTTOMPADDING",(0,0),(0,0), 4),
    ]))
    story.append(tit)

    # Subtítulo identificação
    sub = Table([[Paragraph("IDENTIFICAÇÃO DO EMPREDIMENTO", ST["subtitulo"])]],
                colWidths=[170*mm])
    sub.setStyle(TableStyle([
        ("BOX",        (0,0),(0,0), 0.5, PRETO),
        ("TOPPADDING", (0,0),(0,0), 3),
        ("BOTTOMPADDING",(0,0),(0,0), 3),
    ]))
    story.append(sub)

    # Campos de identificação
    def campo(label, valor):
        return Table([[Paragraph(f"{label}: {valor}", ST["normal_s"])]],
                     colWidths=[170*mm])

    perc_total = calcular_total(dados)

    for label, val in [
        ("Endereço", f"{dados['ra']} - {dados['endereco']}"),
        ("Responsável Técnico", "Lucas Diniz Souza Mat.13676"),
        ("Data da Medição", dados["data"]),
        ("Percentual Acumulado de Execução da Obra", f"{perc_total:.0f}%"),
    ]:
        t = campo(label, val)
        t.setStyle(TableStyle([
            ("BOX",        (0,0),(0,0), 0.5, PRETO),
            ("TOPPADDING", (0,0),(0,0), 2),
            ("BOTTOMPADDING",(0,0),(0,0), 2),
            ("LEFTPADDING",(0,0),(0,0), 4),
        ]))
        story.append(t)

    story.append(Spacer(1, 3*mm))

    # Título medição das etapas
    med = Table([[Paragraph("MEDIÇÃO DAS ETAPAS", ST["titulo"])]],
                colWidths=[170*mm])
    med.setStyle(TableStyle([
        ("BOX",        (0,0),(0,0), 0.5, PRETO),
        ("BACKGROUND", (0,0),(0,0), AZUL_CLARO),
        ("TOPPADDING", (0,0),(0,0), 4),
        ("BOTTOMPADDING",(0,0),(0,0), 4),
    ]))
    story.append(med)

    # Tabela de subetapas
    cw = [10*mm, 82*mm, 22*mm, 27*mm, 29*mm]
    header = [
        Paragraph("ITEM",        ST["bold_c"]),
        Paragraph("ETAPA",       ST["bold_c"]),
        Paragraph("(%)PESO",     ST["bold_c"]),
        Paragraph("(%) EXECUTADO",ST["bold_c"]),
        Paragraph("(%)CONTRIBUIÇÃO",ST["bold_c"]),
    ]
    rows = [header]

    ETAPAS = [
        ("1.0","FUNDAÇÃO", [
            ("1.1","Nivelamento de terreno",             15.0),
            ("1.2","Escavação e montagem das fôrmas",    15.0),
            ("1.3","Montagem e armação da fundação",     30.0),
            ("1.4","Concretagem da fundação",            40.0),
        ]),
        ("2.0","ESTRUTURA", [
            ("2.1","Montagem de fôrmas para pilares e vigas", 25.0),
            ("2.2","Armação de aço da estrutura",              35.0),
            ("2.3","Concretagem da estrutura",                 40.0),
        ]),
        ("3.0","ALVENARIA", [
            ("3.1","Levantamento de paredes externas",   20.0),
            ("3.2","Levantamento de paredes internas",   25.0),
            ("3.4","Chapisco aplicado em alvenaria externa", 9.0),
            ("3.5","Reboco aplicado em alvenaria externa",  11.5),
            ("3.4","Chapisco aplicado em alvenaria interna", 9.0),
            ("3.5","Reboco aplicado em alvenaria interna",  11.5),
            ("3.6","Pintura aplicada em alvenaria externa",  7.0),
            ("3.7","Pintura aplicada em alvenaria interna",  7.0),
        ]),
        ("4.0","ESGOTO", [
            ("4.1","Instalação de redes externas",    30.0),
            ("4.2","Instalação de caixa de inspeção", 15.0),
            ("4.3","Instalação de caixa de gordura",  15.0),
            ("4.4","Instalação de tubos de esgoto",   40.0),
        ]),
        ("5.0","AGUA FRIA", [
            ("5.1","Instalação de hidrometro",         20.0),
            ("5.2","Instalação de tubulação hidráulica",45.0),
            ("5.3","Instalação de caixa d'água",        35.0),
        ]),
        ("6.0","ELETRICA", [
            ("6.1","Instalação de quadro elétrico de entrada", 15.0),
            ("6.2","Montagem de quadros elétricos",            15.0),
            ("6.3","Instalação de conduítes e caixas",         25.0),
            ("6.4","Passagem de fiação",                       45.0),
        ]),
        ("7.0","COBERTURA", [
            ("7.1","Montagem da estrutura de telhado", 35.0),
            ("7.2","Instalação de telhas",              45.0),
            ("7.3","Execução de calhas e rufos",        20.0),
        ]),
        ("8.0","ACABAMENTO", [
            ("8.1","Revestimento em piso",            45.0),
            ("8.2","Instalação de esquadrias",         30.0),
            ("8.3","Instalação de portões, grades",    25.0),
        ]),
    ]

    chave_map = {
        "1.0":"fundacao","2.0":"estrutura","3.0":"alvenaria",
        "4.0":"esgoto","5.0":"agua_fria","6.0":"eletrica",
        "7.0":"cobertura","8.0":"acabamento"
    }
    sub_map = {
        "1.1":"fund_1","1.2":"fund_2","1.3":"fund_3","1.4":"fund_4",
        "2.1":"est_1","2.2":"est_2","2.3":"est_3",
        "3.1":"alv_1","3.2":"alv_2","3.4a":"alv_3","3.5a":"alv_4",
        "3.4b":"alv_5","3.5b":"alv_6","3.6":"alv_7","3.7":"alv_8",
        "4.1":"esg_1","4.2":"esg_2","4.3":"esg_3","4.4":"esg_4",
        "5.1":"agu_1","5.2":"agu_2","5.3":"agu_3",
        "6.1":"ele_1","6.2":"ele_2","6.3":"ele_3","6.4":"ele_4",
        "7.1":"cob_1","7.2":"cob_2","7.3":"cob_3",
        "8.1":"acb_1","8.2":"acb_2","8.3":"acb_3",
    }

    style_commands = [
        ("FONTNAME",  (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 7),
        ("GRID",      (0,0), (-1,-1), 0.5, PRETO),
        ("ALIGN",     (2,0), (-1,-1), "CENTER"),
        ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",(0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("LEFTPADDING",(0,0),(-1,-1), 3),
        ("BACKGROUND",(0,0),(-1,0), AZUL_ETAPA),
        ("TEXTCOLOR", (0,0),(-1,0), PRETO),
    ]

    row_idx = 1
    for etapa_id, etapa_nome, subs in ETAPAS:
        chave = chave_map[etapa_id]
        perc_etapa = calcular_etapa(dados, etapa_id, subs)
        etapa_row = [
            Paragraph(etapa_id, ST["bold_c"]),
            Paragraph(f"<b>{etapa_nome}</b>", ST["bold_s"]),
            Paragraph("", ST["bold_c"]),
            Paragraph("", ST["bold_c"]),
            Paragraph(f"<b>{perc_etapa:.1f}%</b>", ST["bold_c"]),
        ]
        rows.append(etapa_row)
        style_commands.append(("BACKGROUND", (0,row_idx),(-1,row_idx), CINZA_LINHA))
        row_idx += 1

        # contador para alvenaria com itens duplicados de número
        alv_counter = {"3.4": 0, "3.5": 0}

        for sub_id, sub_nome, peso in subs:
            # pegar % executado da subetapa
            if etapa_id == "3.0":
                if sub_id == "3.4":
                    alv_counter["3.4"] += 1
                    sk = f"alv_{2 + alv_counter['3.4']}"  # alv_3, alv_5
                    if alv_counter["3.4"] == 2:
                        sk = "alv_5"
                    else:
                        sk = "alv_3"
                elif sub_id == "3.5":
                    alv_counter["3.5"] += 1
                    if alv_counter["3.5"] == 2:
                        sk = "alv_6"
                    else:
                        sk = "alv_4"
                elif sub_id == "3.1": sk = "alv_1"
                elif sub_id == "3.2": sk = "alv_2"
                elif sub_id == "3.6": sk = "alv_7"
                elif sub_id == "3.7": sk = "alv_8"
                else: sk = None
            else:
                prefix = {
                    "1.0":"fund","2.0":"est","4.0":"esg",
                    "5.0":"agu","6.0":"ele","7.0":"cob","8.0":"acb"
                }[etapa_id]
                n = sub_id.split(".")[1]
                sk = f"{prefix}_{n}"

            exec_val = dados.get("subetapas", {}).get(sk, 100.0) if sk else 100.0
            contrib  = peso * exec_val / 100.0

            rows.append([
                Paragraph(sub_id, ST["bold_c"]),
                Paragraph(sub_nome, ST["normal_s"]),
                Paragraph(f"{peso:.1f}%", ST["bold_c"]),
                Paragraph(f"{exec_val:.1f}%", ST["bold_c"]),
                Paragraph(f"{contrib:.1f}%", ST["bold_c"]),
            ])
            row_idx += 1

    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle(style_commands))
    story.append(t)
    story.append(PageBreak())
    return story

# ── Calcular totais ────────────────────────────────────────────────────────
PESOS_ETAPA = {
    "1.0":7,"2.0":25,"3.0":15,"4.0":5,
    "5.0":5,"6.0":10,"7.0":15,"8.0":18
}
SUBS_ETAPA = {
    "1.0": [("fund_1",15),("fund_2",15),("fund_3",30),("fund_4",40)],
    "2.0": [("est_1",25),("est_2",35),("est_3",40)],
    "3.0": [("alv_1",20),("alv_2",25),("alv_3",9),("alv_4",11.5),
            ("alv_5",9),("alv_6",11.5),("alv_7",7),("alv_8",7)],
    "4.0": [("esg_1",30),("esg_2",15),("esg_3",15),("esg_4",40)],
    "5.0": [("agu_1",20),("agu_2",45),("agu_3",35)],
    "6.0": [("ele_1",15),("ele_2",15),("ele_3",25),("ele_4",45)],
    "7.0": [("cob_1",35),("cob_2",45),("cob_3",20)],
    "8.0": [("acb_1",45),("acb_2",30),("acb_3",25)],
}

def calcular_etapa(dados, etapa_id, subs_raw):
    subs = SUBS_ETAPA[etapa_id]
    total = 0
    for sk, peso in subs:
        exec_val = dados.get("subetapas", {}).get(sk, 100.0)
        total += peso * exec_val / 100.0
    return total

def calcular_total(dados):
    total = 0
    for etapa_id, peso_etapa in PESOS_ETAPA.items():
        perc_etapa = calcular_etapa(dados, etapa_id, None)
        total += peso_etapa * perc_etapa / 100.0
    return total

def get_perc_etapa_dict(dados):
    result = {}
    for etapa_id in PESOS_ETAPA:
        result[etapa_id] = calcular_etapa(dados, etapa_id, None)
    return result

# ── Página 2: Medição Total ────────────────────────────────────────────────
def pagina2(dados):
    story = []
    story.append(cabecalho("Gerência de Fiscalização e Retomada de Imóveis - GEFIS"))
    story.append(Spacer(1, 3*mm))

    med = Table([[Paragraph("MEDIÇÃO TOTAL DA OBRA", ST["titulo"])]],
                colWidths=[170*mm])
    med.setStyle(TableStyle([
        ("BOX",        (0,0),(0,0), 0.5, PRETO),
        ("BACKGROUND", (0,0),(0,0), AZUL_CLARO),
        ("TOPPADDING", (0,0),(0,0), 4),
        ("BOTTOMPADDING",(0,0),(0,0), 4),
    ]))
    story.append(med)

    cw = [10*mm, 82*mm, 22*mm, 27*mm, 29*mm]
    header = [
        Paragraph("ITEM",           ST["bold_c"]),
        Paragraph("ETAPA",          ST["bold_c"]),
        Paragraph("(%)PESO",        ST["bold_c"]),
        Paragraph("(%) EXECUTADO",  ST["bold_c"]),
        Paragraph("(%)CONTRIBUIÇÃO",ST["bold_c"]),
    ]

    NOMES = {
        "1.0":"FUNDAÇÃO","2.0":"ESTRUTURA","3.0":"ALVENARIA","4.0":"ESGOTO",
        "5.0":"AGUA FRIA","6.0":"ELETRICA","7.0":"COBERTURA","8.0":"ACABAMENTO"
    }

    percs = get_perc_etapa_dict(dados)
    total_obra = calcular_total(dados)

    rows = [header]
    for etapa_id, peso in PESOS_ETAPA.items():
        perc = percs[etapa_id]
        contrib = peso * perc / 100.0
        rows.append([
            Paragraph(etapa_id, ST["bold_c"]),
            Paragraph(NOMES[etapa_id], ST["normal_s"]),
            Paragraph(f"{peso}%",      ST["bold_c"]),
            Paragraph(f"{perc:.1f}%",  ST["bold_c"]),
            Paragraph(f"{contrib:.0f}%", ST["bold_c"]),
        ])

    rows.append([
        Paragraph("", ST["bold_c"]),
        Paragraph("", ST["bold_c"]),
        Paragraph("", ST["bold_c"]),
        Paragraph("<b>TOTAL EXECUTADO DA OBRA=</b>", ST["bold_c"]),
        Paragraph(f"<b>{total_obra:.0f}%</b>", ST["bold_c"]),
    ])

    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE",  (0,0), (-1,-1), 7),
        ("GRID",      (0,0), (-1,-1), 0.5, PRETO),
        ("ALIGN",     (2,0), (-1,-1), "CENTER"),
        ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",(0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("LEFTPADDING",(0,0),(-1,-1), 3),
        ("BACKGROUND",(0,0),(-1,0), AZUL_ETAPA),
        ("TEXTCOLOR", (0,0),(-1,0), PRETO),
        ("BACKGROUND",(0,-1),(-1,-1), colors.HexColor("#b6b6b6")),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    # Texto de explicação
    explicacoes = [
        ("Fundação", "Inclui atividades complexas e essenciais no início da obra, mas geralmente representa uma parcela menor do custo e esforço total."),
        ("Estrutura", "Geralmente é a etapa mais pesada, pois envolve muitos materiais e mão de obra intensiva."),
        ("Alvenaria", "Outra etapa de grande importância, proporcional ao tamanho da edificação."),
        ("Cobertura", "Representa menos impacto no total por ter menos materiais e menor complexidade relativa."),
        ("Hidráulica e Elétrica", "Divididas igualmente, cada uma com um peso significativo devido à necessidade de precisão e materiais específicos."),
        ("Esgoto", "Como é mais específico e menos intensivo, tem peso menor."),
        ("Acabamento", "É crucial para o aspecto final da obra, mas representa menor complexidade estrutural."),
    ]

    exp_rows = [[Paragraph("<b>Explicação:</b>", ST["bold_exp"])]]
    for titulo, texto in explicacoes:
        exp_rows.append([Paragraph(f"<b>{titulo}:</b> {texto}", ST["bold_exp"])])

    exp_table = Table(exp_rows, colWidths=[170*mm])
    exp_table.setStyle(TableStyle([
        ("BOX",        (0,0),(0,-1), 0.5, PRETO),
        ("TOPPADDING", (0,0),(0,-1), 3),
        ("BOTTOMPADDING",(0,0),(0,-1), 3),
        ("LEFTPADDING",(0,0),(0,-1), 6),
    ]))
    story.append(exp_table)
    story.append(PageBreak())
    return story

# ── Página 3: Conclusão + Fotos + Observações ─────────────────────────────
def pagina3(dados):
    story = []
    story.append(cabecalho("Gerência de Fiscalização e Retomada de Imóveis - GEFIS"))
    story.append(Spacer(1, 3*mm))

    total_obra = calcular_total(dados)
    percs      = get_perc_etapa_dict(dados)

    # Conclusão
    conc = Table([[Paragraph("CONCLUSÃO", ST["titulo"])]],
                 colWidths=[170*mm])
    conc.setStyle(TableStyle([
        ("BOX",        (0,0),(0,0), 0.5, PRETO),
        ("BACKGROUND", (0,0),(0,0), AZUL_CLARO),
        ("TOPPADDING", (0,0),(0,0), 3),
        ("BOTTOMPADDING",(0,0),(0,0), 3),
    ]))
    story.append(conc)

    texto_conc = (
        f"Após a análise detalhada das etapas e subetapas executadas até a presente data, a obra encontra-se com "
        f"{total_obra:.0f}% de execução acumulada.\n"
        "Segue a a ordem das etapas mais adiantadas :"
    )
    tc = Table([[Paragraph(texto_conc, ST["normal_s"])]],
               colWidths=[170*mm])
    tc.setStyle(TableStyle([
        ("BOX",        (0,0),(0,0), 0.5, PRETO),
        ("TOPPADDING", (0,0),(0,0), 4),
        ("BOTTOMPADDING",(0,0),(0,0), 4),
        ("LEFTPADDING",(0,0),(0,0), 6),
    ]))
    story.append(tc)

    # Tabela de ordem — ordenada por % decrescente, agrupada por faixa
    NOMES = {
        "1.0":"FUNDAÇÃO","2.0":"ESTRUTURA","3.0":"ALVENARIA","4.0":"ESGOTO",
        "5.0":"AGUA FRIA","6.0":"ELETRICA","7.0":"COBERTURA","8.0":"ACABAMENTO"
    }

    # Cores dos grupos (igual ao original)
    COR_G = [
        colors.HexColor("#d9e9d3"),  # 1º - 100% → verde
        colors.HexColor("#ffe499"),  # 2º - 50–99% → amarelo
        colors.HexColor("#e99999"),  # 3º - <50% → vermelho
    ]

    def gi_de(perc):
        if perc >= 99.95: return 0
        elif perc >= 50:  return 1
        else:             return 2

    # Ordenar: primeiro por grupo (0→1→2), depois por % decrescente dentro do grupo
    ordem_etapas = sorted(percs.items(), key=lambda x: (gi_de(x[1]), -x[1]))

    ord_header = [
        Paragraph("ITEM",  ST["bold_c"]),
        Paragraph("ETAPA", ST["bold_c"]),
        Paragraph("%",     ST["bold_c"]),
        Paragraph("ORDEM", ST["bold_c"]),
    ]
    ord_rows   = [ord_header]
    ord_styles = [
        ("FONTSIZE",     (0,0),(-1,-1), 7),
        ("GRID",         (0,0),(-1,-1), 0.5, PRETO),
        ("ALIGN",        (0,0),(-1,-1), "CENTER"),
        ("ALIGN",        (1,1),(1,-1),  "LEFT"),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("LEFTPADDING",  (1,1),(1,-1),  3),
        ("BACKGROUND",   (0,0),(-1,0),  colors.HexColor("#999999")),
        ("TEXTCOLOR",    (0,0),(-1,0),  PRETO),
    ]

    ord_labels  = {0:"1º", 1:"2º", 2:"3º"}
    grupo_visto = set()
    ultimo_gi   = -1
    row_i = 1

    for etapa_id, perc in ordem_etapas:
        gi = gi_de(perc)
        bg = COR_G[gi]

        # Rótulo de ordem só na primeira linha de cada grupo
        lbl = ord_labels[gi] if gi not in grupo_visto else ""
        grupo_visto.add(gi)

        # Linha separadora entre grupos diferentes
        if ultimo_gi != -1 and gi != ultimo_gi:
            ord_styles.append(("LINEABOVE", (0,row_i),(-1,row_i), 1, PRETO))

        ord_rows.append([
            Paragraph(etapa_id,         ST["bold_c"]),
            Paragraph(NOMES[etapa_id],  ST["normal_s"]),
            Paragraph(f"{perc:.1f}%",   ST["bold_c"]),
            Paragraph(lbl,              ST["bold_c"]),
        ])
        ord_styles.append(("BACKGROUND", (0,row_i),(-1,row_i), bg))
        ord_styles.append(("TEXTCOLOR",  (0,row_i),(-1,row_i), PRETO))
        ultimo_gi = gi
        row_i += 1

    ord_t = Table(ord_rows, colWidths=[12*mm, 98*mm, 35*mm, 25*mm])
    ord_t.setStyle(TableStyle(ord_styles))
    story.append(ord_t)
    story.append(Spacer(1, 3*mm))

    # Gráfico de barras
    grafico = gerar_grafico(percs)
    story.append(grafico)
    story.append(Spacer(1, 3*mm))

    # Relatório fotográfico
    foto_title = Table([[Paragraph("RELÁTORIO FOTOGRAFICO", ST["subtitulo"])]],
                       colWidths=[170*mm])
    foto_title.setStyle(TableStyle([
        ("BOX",        (0,0),(0,0), 0.5, PRETO),
        ("TOPPADDING", (0,0),(0,0), 3),
        ("BOTTOMPADDING",(0,0),(0,0), 3),
    ]))
    story.append(foto_title)

    # Fotos
    fotos = dados.get("fotos", [])
    foto_cells = []
    for fb64 in fotos[:2]:
        img_data = base64.b64decode(fb64)
        img_buf  = io.BytesIO(img_data)
        foto_cells.append(Image(img_buf, width=75*mm, height=50*mm))
    while len(foto_cells) < 2:
        foto_cells.append(Paragraph("", ST["normal_s"]))

    foto_table = Table([foto_cells], colWidths=[85*mm, 85*mm])
    foto_table.setStyle(TableStyle([
        ("BOX",  (0,0),(-1,-1), 0.5, PRETO),
        ("ALIGN",(0,0),(-1,-1), "CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    story.append(foto_table)
    story.append(Spacer(1, 3*mm))

    # Observações
    obs_title = Table([[Paragraph("OBSERVAÇÕES", ST["subtitulo"])]],
                      colWidths=[170*mm])
    obs_title.setStyle(TableStyle([
        ("BOX",        (0,0),(0,0), 0.5, PRETO),
        ("TOPPADDING", (0,0),(0,0), 3),
        ("BOTTOMPADDING",(0,0),(0,0), 3),
    ]))
    story.append(obs_title)

    # Checkboxes automáticos baseados nos dados
    sub = dados.get("subetapas", {})
    lote_cercado = sub.get("alv_1", 0) > 0 or sub.get("alv_2", 0) > 0
    lote_vazio   = all(sub.get(k, 100) == 0 for k in ["alv_1","alv_2","est_1","fund_1"])
    quadro_el    = sub.get("ele_1", 0) > 0
    hidrometro   = sub.get("agu_1", 0) > 0

    def x_cell(cond): return ("X" if cond else "", "" if cond else "X")

    obs_data = [
        ["", "", "SIM", "NAO"],
        ["", "LOTE CERCADO",           *x_cell(lote_cercado)],
        ["", "LOTE VAZIO",             *x_cell(lote_vazio)],
        ["", "QUADRO ELETRICO INSTALADO", *x_cell(quadro_el)],
        ["", "HIDROMETRO INSTALADO",   *x_cell(hidrometro)],
    ]
    obs_rows_p = [[Paragraph(str(c), ST["bold_c"]) for c in row] for row in obs_data]
    obs_t = Table(obs_rows_p, colWidths=[10*mm, 105*mm, 28*mm, 27*mm])
    obs_t.setStyle(TableStyle([
        ("FONTSIZE",  (0,0),(-1,-1), 7),
        ("GRID",      (0,0),(-1,-1), 0.5, PRETO),
        ("ALIGN",     (2,0),(-1,-1), "CENTER"),
        ("VALIGN",    (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ("BACKGROUND",(2,0),(-1,0), CINZA_LINHA),
    ]))
    story.append(obs_t)
    story.append(Spacer(1, 4*mm))

    # Assinatura
    ass_style = ParagraphStyle("ass", fontName="Helvetica-BoldOblique", fontSize=16,
                               alignment=TA_CENTER, leading=18)
    sub_ass   = ParagraphStyle("sub_ass", fontName="Helvetica-Bold", fontSize=7,
                               alignment=TA_CENTER, leading=9)
    ass_data = [
        [Paragraph("<i>Lucas Diniz Souza</i>", ass_style)],
        [Paragraph("CODHAB/PRESI/DIMOB/GEFIS", sub_ass)],
        [Paragraph("Técnico em Edificações", sub_ass)],
        [Paragraph("Matr  1367-6", sub_ass)],
        [HRFlowable(width="80%", thickness=0.5, color=PRETO)],
        [Paragraph("Responsável Técnico: Lucas Diniz Souza Mat.13676", sub_ass)],
    ]
    ass_t = Table(ass_data, colWidths=[170*mm])
    ass_t.setStyle(TableStyle([
        ("ALIGN",  (0,0),(-1,-1), "CENTER"),
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1), 1),
        ("BOTTOMPADDING",(0,0),(-1,-1), 1),
    ]))
    story.append(ass_t)
    return story

# ── Gráfico de barras ──────────────────────────────────────────────────────
def gerar_grafico(percs):
    NOMES_CURTOS = {
        "1.0":"FUNDAÇÃO","5.0":"AGUA FRIA","6.0":"ELETRICA",
        "3.0":"ALVENARIA","7.0":"COBERTURA","8.0":"ACABAMENTO",
        "2.0":"ESTRUTURA","4.0":"ESGOTO"
    }
    ordem = ["1.0","5.0","6.0","3.0","7.0","8.0","2.0","4.0"]
    valores = [percs.get(k, 0) for k in ordem]
    labels  = [NOMES_CURTOS[k] for k in ordem]

    d = Drawing(W - 40*mm, 90)
    bc = VerticalBarChart()
    bc.x = 30
    bc.y = 20
    bc.width  = (W - 40*mm) - 40
    bc.height = 60
    bc.data   = [valores]
    bc.categoryAxis.categoryNames = labels
    bc.categoryAxis.labels.fontName  = "Helvetica"
    bc.categoryAxis.labels.fontSize  = 5
    bc.categoryAxis.labels.angle     = 45
    bc.categoryAxis.labels.dy        = -8
    bc.valueAxis.valueMin  = 0
    bc.valueAxis.valueMax  = 120
    bc.valueAxis.valueStep = 50
    bc.valueAxis.labels.fontName = "Helvetica"
    bc.valueAxis.labels.fontSize = 6
    bc.bars[0].fillColor = colors.HexColor("#4185f4")
    bc.bars[0].strokeColor = None
    d.add(bc)
    return d

# ── Gerar PDF final ────────────────────────────────────────────────────────
def gerar_pdf(dados, output_path):
    doc = SimpleDocTemplate(
        output_path,  # pode ser path string ou buffer BytesIO
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=10*mm,  bottomMargin=10*mm,
    )
    story = []
    story += pagina1(dados)
    story += pagina2(dados)
    story += pagina3(dados)
    doc.build(story)
    print(f"PDF gerado: {output_path}")

# ── Teste com dados de exemplo ────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            dados = json.load(f)
    else:
        dados = {
            "ra": "Brazlândia",
            "endereco": "CCDN Bloco F Loja 4",
            "data": "16/04/2026",
            "subetapas": {
                "fund_1":100,"fund_2":100,"fund_3":100,"fund_4":100,
                "est_1":100,"est_2":100,"est_3":100,
                "alv_1":100,"alv_2":100,"alv_3":100,"alv_4":100,
                "alv_5":100,"alv_6":100,"alv_7":100,"alv_8":100,
                "esg_1":100,"esg_2":100,"esg_3":100,"esg_4":100,
                "agu_1":100,"agu_2":100,"agu_3":100,
                "ele_1":100,"ele_2":100,"ele_3":100,"ele_4":100,
                "cob_1":100,"cob_2":100,"cob_3":100,
                "acb_1":100,"acb_2":100,"acb_3":100,
            },
            "fotos": []
        }
    gerar_pdf(dados, "/mnt/user-data/outputs/relatorio_teste.pdf")
