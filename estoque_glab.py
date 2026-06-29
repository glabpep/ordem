import pandas as pd
import os
import json
import math
from datetime import date
import unicodedata
import re


def sanitizar_texto(texto):
    """Remove caracteres perigosos para evitar injeção de HTML/JS."""
    if not isinstance(texto, str):
        texto = str(texto)
    # Remove tags HTML e caracteres de controle
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = texto.replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#x27;').replace('`', '&#x60;')
    return texto.strip()


def parse_promo(val):
    """
    Lê o valor da coluna PROMOÇÃO e retorna um float entre 0 e 1 representando o desconto.
    Aceita: '10%', '0.10', '10', '', None, NaN.
    Retorna 0.0 se não houver promoção válida.
    """
    if val is None:
        return 0.0
    try:
        if isinstance(val, float) and math.isnan(val):
            return 0.0
    except Exception:
        pass
    s = str(val).strip().replace(',', '.')
    if not s or s.lower() in ('nan', 'none', ''):
        return 0.0
    s = s.replace('%', '')
    try:
        n = float(s)
        # Se veio como 10, interpreta como 10%
        if n > 1:
            n = n / 100.0
        # Clamp entre 0 e 1
        n = max(0.0, min(1.0, n))
        return n
    except ValueError:
        return 0.0


def gerar_site_vendas_completo():
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))

    arquivo_dados = None
    for nome in ['stock_0202 - NOVA.xlsx', 'stock_2901.xlsx - Plan1.csv']:
        caminho = os.path.join(diretorio_atual, nome)
        if os.path.exists(caminho):
            arquivo_dados = caminho
            break
    if not arquivo_dados:
        print(f"Erro: Arquivo não encontrado em: {diretorio_atual}")
        return

    infos_tecnicas = {
        
        "AOD 9604": {"desc": "Análogo Lipolítico do hGH: Focado no isolamento das propriedades de queima de gordura do GH sem induzir efeitos hiperglicêmicos. Aplicado em estudos de obesidade e regeneração de cartilagem.", "cat": "Metabolismo", "icon": "🔥"},
        "HGH FRAGMENT": {"desc": "Modulador de Lipídios: Parte terminal do GH responsável pela quebra de gordura. Mostra capacidade de inibir a formação de nova gordura e acelerar a lipólise visceral sem alterar a insulina.", "cat": "Metabolismo", "icon": "🔥"},
        "MOTS-C": {"desc": "Peptídeo Derivado da Mitocôndria: Regulador hormonal do metabolismo sistêmico. Melhora a homeostase da glicose e combate a resistência à insulina via ativação da via AMPK.", "cat": "Metabolismo", "icon": "🔥"},
        "SLU PP": {"desc": "Agonista Pan-ERR (Pílula do Exercício): Ativa receptores ERRα, β, γ. Aumenta drasticamente a biogênese mitocondrial e a resistência física, comparável ao treino de alta intensidade.", "cat": "Metabolismo", "icon": "🔥"},
        "CJC-1295": {"desc": "Secretagogo de GH de Longa Duração: Análogo do GHRH que aumenta secreção de GH e IGF-1. Aplicado em antienvelhecimento, melhora da composição corporal e síntese proteica acelerada.", "cat": "Hormônios", "icon": "💉"},
        "IPAMORELIN": {"desc": "Agonista de Grelina Seletivo: Estimula a liberação pulsátil de GH sem elevar cortisol ou prolactina. Seguro para indução de anabolismo e melhora da density mineral óssea.", "cat": "Hormônios", "icon": "💉"},
        "CJC-1295 + IPAMORELIN": {"desc": "Sinergia Hormonal Dual: Combinação de GHRH com GHRP. Mimetiza a liberação fisiológica natural, resultando em secreção de GH significativamente maior que o uso isolado.", "cat": "Hormônios", "icon": "💉"},
        "IGF-1 LR3": {"desc": "Análogo de IGF-1 de Meia-vida Longa: Permanece ativo por até 20 horas. Principal mediador da hiperplasia (criação de novas fibras musculares) e transporte de acesso de aminoácidos.", "cat": "Hormônios", "icon": "💉"},
        "SERMORELIN": {"desc": "Estimulador de Eixo Natural: Mimetiza o GHRH natural. Promove melhorias na qualidade do sono profundo, vitalidade da pele e recuperação pós-esforço.", "cat": "Hormônios", "icon": "💉"},
        "BPC-157": {"desc": "Pentadecapeptídeo Gástrico: Acelera a angiogênese e cicatrização. Estudado para cura de rupturas de tendões, ligamentos, danos musculares e tecidos moles.", "cat": "Recuperação", "icon": "🩹"},
        "TB-500": {"desc": "Timosina Beta-4 Sintética: Essencial para migração celular e reparo de tecidos. Promove formação de novos vasos e reduz inflamação articular e miocárdica.", "cat": "Recuperação", "icon": "🩹"},
        "TB-500 + BPC": {"desc": "Protocolo de Reparo Total: União sinérgica do TB-500 (sistêmico) com BPC-157 (tecido). Padrão ouro para recuperação de lesões atléticas graves.", "cat": "Recuperação", "icon": "🩹"},
        "GHK-CU": {"desc": "Complexo Peptídeo-Cobre: Atua na remodelação do DNA e síntese de colágeno I e III. Possui propriedades antioxidantes e anti-inflamatórias para pele e tecidos conectivos.", "cat": "Estética", "icon": "✨"},
        "GLOW": {"desc": "Bioestimulação Dérmica (GHK-Cu + BPC + TB): Blend estético-regenerativo focado em rejuvenescimento cutâneo, redução de cicatrizes e regeneração da matriz extracelular.", "cat": "Estética", "icon": "✨"},
        "ARA 290": {"desc": "Agonista de Receptor de Reparo Inato: Derivado da eritropoietina sem efeitos hematológicos. Pesquisado para dor neuropática severa e regeneração nervosa periférica.", "cat": "Recuperação", "icon": "🩹"},
        "KPV": {"desc": "Tripeptídeo Anti-inflamatório: Inibe vias inflamatórias (NF-κB). Possui propriedades antimicrobianas e é utilizado em estudos sobre dermatite e colite.", "cat": "Imunidade", "icon": "🛡️"},
        "KLOW": {"desc": "Quarteto de Reparo Profundo (GHK+BPC+TB+KPV): Projetado para sinalização celular máxima em remodelação de tecidos complexos e equilíbrio imunológico.", "cat": "Recuperação", "icon": "🩹"},
        "TIRZEPATIDE": {"desc": "Agonista Dual GIP/GLP-1: Supera a Semaglutida na perda de peso. Promove saciedade central e melhora drástica na sensibilidade à insulina.", "cat": "Emagrecimento", "icon": "⚖️"},
        "RETATRUTIDE": {"desc": "Agonista Triplo (GIP/GLP-1/GCGR): Aumenta o gasto calórico basal e a oxidação de gordura no fígado. Promete perdas de peso superiores a 24%.", "cat": "Emagrecimento", "icon": "⚖️"},
        "SEMAGLUTIDE": {"desc": "Agonista de GLP-1: Retarda o esvaziamento gástrico e sinaliza saciedade ao hipotálamo. Base para tratamento de obesidade e controle glicêmico.", "cat": "Emagrecimento", "icon": "⚖️"},
        "SELANK": {"desc": "Ansiolítico Regulador: Modula serotonina e norepinefrina. Reduz ansiedade e melhora o foco cognitivo sem o efeito sedativo dos ansiolíticos comuns.", "cat": "Cognitivo", "icon": "🧠"},
        "SEMAX": {"desc": "Nootrópico Neuroprotetor: Eleva níveis de BDNF e NGF no hipocampo. Aplicado em recuperação pós-AVC e otimização do aprendizado sob estresse.", "cat": "Cognitivo", "icon": "🧠"},
        "PINEALON": {"desc": "Bioregulador de Cadeia Curta: Atua na expressão gênica neuronal. Restaura o ritmo circadiano e protege contra o estresse oxidativo cerebral.", "cat": "Cognitivo", "icon": "🧠"},
        "NAD+": {"desc": "Coenzima de Vitalidade: Essencial para reparação do DNA e sirtuínas. Associado à reversão de marcadores de envelhecimento e aumento da energia celular.", "cat": "Longevidade", "icon": "⏳"},
        "DSIP": {"desc": "Indutor de Sono Delta: Neuromodulador que sincroniza ritmos biológicos, promove sono profundo e mitiga sintomas de estresse emocional.", "cat": "Cognitivo", "icon": "🧠"},
        "OXYTOCIN": {"desc": "Neuromodulador Social: Regula confiança, redução de medo e ansiedade social. Explorado também na regulação do apetite por carboidratos.", "cat": "Cognitivo", "icon": "🧠"},
        "EPITHALON": {"desc": "Ativador da Telomerase: Induz o alongamento dos telômeros. Focado na extensão da vida celular e restauração da secreção de melatonina.", "cat": "Longevidade", "icon": "⏳"},
        "PT-141": {"desc": "Tratamento de Disfunção Sexual: Atua via SNC nos centros de excitação do cérebro. Indicado para desejo sexual hipoativo.", "cat": "Sexual", "icon": "❤️"},
        "BACTERIOSTATIC WATER": {"desc": "Solvente Bacteriostático: Água com 0,9% de Álcool Benzílico. Impede proliferação bacteriana, permitindo uso seguro por até 30 dias.", "cat": "Acessório", "icon": "💧"},
        "SS-31": {"desc": "Protetor de Cardiolipina: Previne a formação de radicais livres na mitocôndria e restaura a produção de ATP.", "cat": "Longevidade", "icon": "⏳"},
        "TESAMORELIN": {"desc": "Redutor de Lipodistrofia: Único aprovado para reduzir gordura visceral abdominal severa.", "cat": "Metabolismo", "icon": "🔥"},
    }

    cat_colors = {
        "Metabolismo":    {"bg": "rgba(255,107,53,0.12)",  "border": "#ff6b35", "text": "#ff6b35"},
        "Hormônios":      {"bg": "rgba(0,150,255,0.12)",   "border": "#0096ff", "text": "#0096ff"},
        "Recuperação":    {"bg": "rgba(76,175,80,0.12)",   "border": "#4caf50", "text": "#4caf50"},
        "Estética":       {"bg": "rgba(233,30,99,0.12)",   "border": "#e91e63", "text": "#e91e63"},
        "Imunidade":      {"bg": "rgba(156,39,176,0.12)",  "border": "#9c27b0", "text": "#9c27b0"},
        "Emagrecimento":  {"bg": "rgba(255,193,7,0.12)",   "border": "#ffc107", "text": "#ffc107"},
        "Cognitivo":      {"bg": "rgba(0,188,212,0.12)",   "border": "#00bcd4", "text": "#00bcd4"},
        "Longevidade":    {"bg": "rgba(121,85,72,0.12)",   "border": "#c49b68", "text": "#c49b68"},
        "Sexual":         {"bg": "rgba(244,67,54,0.12)",   "border": "#f44336", "text": "#f44336"},
        "Suplemento":     {"bg": "rgba(96,125,139,0.12)",  "border": "#78909c", "text": "#78909c"},
        "Acessório":      {"bg": "rgba(158,158,158,0.12)", "border": "#9e9e9e", "text": "#9e9e9e"},
    }

    try:
        if arquivo_dados.endswith('.xlsx'):
            df = pd.read_excel(arquivo_dados)
        else:
            df = pd.read_csv(arquivo_dados)
        df.columns = [str(col).strip() for col in df.columns]

        produtos_base = []
        for idx, row in df.iterrows():
            nome_prod_raw = str(row.get('PRODUTO', 'N/A')).strip()
            # Sanitize all text from spreadsheet before embedding in HTML/JS
            nome_prod = sanitizar_texto(nome_prod_raw)
            volume    = sanitizar_texto(str(row.get('VOLUME', '')))
            medida    = sanitizar_texto(str(row.get('MEDIDA', '')))

            info = {"desc": "Informação técnica não disponível.", "cat": "Outro", "icon": "📦"}
            for chave, dados in infos_tecnicas.items():
                if chave in nome_prod.upper():
                    info = dados
                    break

            cat = info["cat"]
            cc  = cat_colors.get(cat, {"bg": "rgba(158,158,158,0.12)", "border": "#9e9e9e", "text": "#9e9e9e"})

            estoque_raw   = str(row.get('ESTOQUE', row.get('STATUS', ''))).strip().upper()
            is_available  = "DISPONÍVEL" in estoque_raw

            # ── PROMOÇÃO ────────────────────────────────────────────────────
            promo_raw   = row.get('PROMOÇÃO', row.get('PROMOCAO', row.get('Promoção', None)))
            promo_pct   = parse_promo(promo_raw)   # float 0..1
            preco_orig  = float(row.get('Preço (R$)', 0) or 0)
            preco_final = round(preco_orig * (1 - promo_pct), 2) if promo_pct > 0 else preco_orig

            produtos_base.append({
                "id":          idx,
                "nome":        nome_prod,
                "espec":       f"{volume} {medida}".strip(),
                "precoOrig":   preco_orig,
                "preco":       preco_final,   # effective price (discounted)
                "promoPct":    promo_pct,     # 0 = no promo, e.g. 0.10 = 10% off
                "info":        info["desc"],
                "cat":         cat,
                "icon":        info["icon"],
                "catBg":       cc["bg"],
                "catBorder":   cc["border"],
                "catText":     cc["text"],
                "available":   is_available,
                "imagem":      f"imagens_produtos/{nome_prod}.webp",
            })

        js_produtos = json.dumps(produtos_base, ensure_ascii=False)

    except Exception as e:
        print(f"Erro ao ler os dados: {e}")
        return

    # ── Category filter buttons ──────────────────────────────────────────────
    all_cats = sorted(set(p["cat"] for p in produtos_base))
    cat_buttons_html = '<button class="cat-btn active" data-cat="all" onclick="filtrarCat(\'all\')">Todos</button>\n'
    for cat in all_cats:
        cc = cat_colors.get(cat, {"border": "#9e9e9e"})
        border_color = cc["border"]
        cat_buttons_html += (
            f'<button class="cat-btn" data-cat="{cat}" '
            f'onclick="filtrarCat(\'{cat}\')" '
            f'style="--cat-color:{border_color}">{cat}</button>\n'
        )

    # ── Product cards ────────────────────────────────────────────────────────
    table_rows = ""
    for p in produtos_base:
        idx           = p["id"]
        produto       = p["nome"]
        espec         = p["espec"]
        preco_orig    = p["precoOrig"]
        preco_final   = p["preco"]
        promo_pct     = p["promoPct"]
        cat           = p["cat"]
        icon          = p["icon"]
        is_available  = p["available"]
        estoque_label = "DISPONÍVEL" if is_available else "EM ESPERA"
        cc            = cat_colors.get(cat, {"bg": "rgba(158,158,158,0.12)", "border": "#9e9e9e", "text": "#9e9e9e"})
        cc_text       = cc["text"]
        cc_bg         = cc["bg"]
        cc_border     = cc["border"]

        # Price display block
        if promo_pct > 0:
            pct_label   = f"{round(promo_pct * 100)}% OFF"
            preco_html  = f'''
                <div class="pc-price-wrap promo">
                  <span class="pc-badge-promo">{pct_label}</span>
                  <span class="pc-price-orig">R$ {preco_orig:,.2f}</span>
                  <span class="pc-price promo-price">R$ {preco_final:,.2f}</span>
                </div>'''
        else:
            preco_html = f'''
                <div class="pc-price-wrap">
                  <span class="pc-price">R$ {preco_orig:,.2f}</span>
                </div>'''

        table_rows += f"""
        <div class="product-card" data-cat="{cat}" data-available="{'1' if is_available else '0'}">
            <div class="pc-top">
                <div class="pc-icon">{icon}</div>
                <div class="pc-info">
                    <h3 class="pc-name">{produto}</h3>
                    <span class="pc-spec">{espec}</span>
                    <span class="pc-cat"
                          style="color:{cc_text};background:{cc_bg};border:1px solid {cc_border};">{cat}</span>
                </div>
            </div>
            <div class="pc-bottom">
                <div class="pc-price-status">
                    {preco_html}
                    <span class="pc-status {'st-ok' if is_available else 'st-out'}">{estoque_label}</span>
                </div>
                <div class="pc-actions">
                    <button class="btn-detail" onclick="abrirInfo({idx})">Detalhes</button>
                    <button class="btn-cart" onclick="adicionar({idx})" {'disabled' if not is_available else ''}>
                        {'Adicionar' if is_available else 'Indisponível'}
                    </button>
                </div>
            </div>
        </div>
"""

    # ════════════════════════════════════════════════════════════════════════
    html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<!--
  ╔══════════════════════════════════════════════════════════════════╗
  ║  SECURITY NOTES (server-operator checklist):                     ║
  ║  • Serve this file over HTTPS only (TLS 1.2+).                   ║
  ║  • Add Content-Security-Policy header on the web server:          ║
  ║      default-src 'self'; script-src 'self' 'unsafe-inline';       ║
  ║      style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;║
  ║      connect-src 'self' https://viacep.com.br                     ║
  ║        https://brasilapi.com.br https://wa.me;                    ║
  ║      font-src https://fonts.gstatic.com;                          ║
  ║      img-src 'self' data:;                                        ║
  ║  • Add X-Frame-Options: DENY and X-Content-Type-Options: nosniff  ║
  ║  • The WhatsApp number is hardcoded — change before deploy.        ║
  ╚══════════════════════════════════════════════════════════════════╝
-->
<title>G-LAB PEPTIDES — Catálogo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --bg:#07080a;--surface:#0e1117;--surface2:#161b22;--surface3:#1c2333;
  --text:#e6edf3;--text2:#8b949e;--accent:#58a6ff;--accent2:#1f6feb;
  --green:#3fb950;--red:#f85149;--gold:#d29922;--pink:#f778ba;
  --radius:16px;--font:'Space Grotesk',system-ui,sans-serif;--mono:'JetBrains Mono',monospace;
}}
body{{font-family:var(--font);background:var(--bg);color:var(--text);overflow-x:hidden}}
.grain{{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;
  background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  background-repeat:repeat;opacity:0.4}}
.glow-orb{{position:fixed;width:600px;height:600px;border-radius:50%;filter:blur(120px);opacity:0.07;pointer-events:none;z-index:0}}
.glow-1{{top:-200px;left:-100px;background:var(--accent)}}
.glow-2{{bottom:-200px;right:-100px;background:var(--pink)}}
.wrap{{max-width:1100px;margin:0 auto;padding:20px;position:relative;z-index:1;padding-bottom:240px}}
.header{{text-align:center;padding:40px 0 20px}}
.logo-text{{font-size:2.4rem;font-weight:700;letter-spacing:-1px;
  background:linear-gradient(135deg,var(--accent),var(--pink));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.logo-sub{{font-family:var(--mono);font-size:0.8rem;color:var(--text2);margin-top:4px;letter-spacing:2px;text-transform:uppercase}}

/* ── FEATURED ─────────────────────────────────────── */
.featured-section{{margin:30px 0}}
.section-title{{font-size:1.1rem;font-weight:600;color:var(--text2);margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.section-title span{{display:inline-block;width:4px;height:20px;background:linear-gradient(var(--accent),var(--pink));border-radius:2px}}
.featured-scroll{{display:flex;gap:16px;overflow-x:auto;padding-bottom:8px;scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch}}
.featured-scroll::-webkit-scrollbar{{height:4px}}
.featured-scroll::-webkit-scrollbar-track{{background:var(--surface)}}
.featured-scroll::-webkit-scrollbar-thumb{{background:var(--accent);border-radius:4px}}
.feat-card{{min-width:280px;max-width:320px;scroll-snap-align:start;background:var(--surface);border:1px solid var(--surface3);
  border-radius:var(--radius);padding:20px;position:relative;overflow:hidden;flex-shrink:0;transition:transform 0.3s,border-color 0.3s}}
.feat-card:hover{{transform:translateY(-4px);border-color:var(--accent)}}
.feat-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--accent),var(--pink))}}
.feat-card.promo-card::before{{background:linear-gradient(90deg,#ff6b35,#ffc107)}}
.feat-icon{{font-size:2rem;margin-bottom:12px}}
.feat-name{{font-size:1.05rem;font-weight:600;margin-bottom:4px}}
.feat-spec{{font-size:0.75rem;color:var(--text2);font-family:var(--mono)}}
.feat-desc{{font-size:0.8rem;color:var(--text2);margin-top:10px;line-height:1.5;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}

/* promo price in featured card */
.feat-price-wrap{{margin-top:12px}}
.feat-price-wrap.promo .feat-badge{{display:inline-block;background:linear-gradient(135deg,#ff6b35,#ffc107);color:#000;font-size:0.65rem;font-weight:700;padding:2px 8px;border-radius:20px;margin-bottom:4px}}
.feat-price-wrap.promo .feat-orig{{font-size:0.8rem;color:var(--text2);text-decoration:line-through}}
.feat-price{{font-size:1.2rem;font-weight:700;color:var(--green)}}
.feat-price-wrap.promo .feat-price{{color:#ffc107}}
.feat-price-wrap .feat-badge{{display:none}}
.feat-price-wrap .feat-orig{{display:none}}

.feat-btn{{margin-top:10px;width:100%;padding:10px;border:none;border-radius:10px;font-weight:600;font-family:var(--font);
  cursor:pointer;background:linear-gradient(135deg,var(--accent2),var(--accent));color:#fff;font-size:0.85rem;transition:opacity 0.2s}}
.feat-btn:hover{{opacity:0.85}}

/* ── PROMO BADGE in product cards ─────────────────── */
.pc-price-wrap{{display:flex;flex-direction:column;gap:2px}}
.pc-badge-promo{{display:inline-block;font-size:0.62rem;font-weight:700;background:linear-gradient(135deg,#ff6b35,#ffc107);
  color:#000;padding:2px 8px;border-radius:12px;width:fit-content}}
.pc-price-orig{{font-size:0.78rem;color:var(--text2);text-decoration:line-through}}
.promo-price{{color:#ffc107 !important}}

/* ── ALERTS ───────────────────────────────────────── */
.alert-bar{{background:var(--surface);border:1px solid var(--surface3);border-left:4px solid var(--accent);
  padding:14px 18px;border-radius:12px;margin-bottom:14px;font-size:0.85rem;line-height:1.5;color:var(--text2);position:relative}}
.alert-bar strong{{color:var(--text)}}
.alert-bar .close-x{{position:absolute;top:10px;right:14px;cursor:pointer;color:var(--text2);font-size:1.1rem}}

/* ── SEARCH & FILTERS ─────────────────────────────── */
.search-area{{margin:24px 0 16px;display:flex;gap:10px;flex-wrap:wrap}}
.search-input{{flex:1;min-width:200px;padding:12px 16px;border:1px solid var(--surface3);border-radius:12px;
  background:var(--surface);color:var(--text);font-size:0.9rem;font-family:var(--font);outline:none;transition:border-color 0.2s}}
.search-input:focus{{border-color:var(--accent)}}
.search-input::placeholder{{color:var(--text2)}}
.toggle-avail{{padding:10px 18px;border:1px solid var(--surface3);border-radius:12px;background:var(--surface);color:var(--text2);
  font-size:0.8rem;font-family:var(--font);cursor:pointer;transition:all 0.2s;white-space:nowrap}}
.toggle-avail.active{{border-color:var(--green);color:var(--green);background:rgba(63,185,80,0.1)}}
.cat-filters{{display:flex;gap:8px;overflow-x:auto;padding:4px 0 12px;-webkit-overflow-scrolling:touch}}
.cat-filters::-webkit-scrollbar{{height:0}}
.cat-btn{{padding:6px 14px;border-radius:20px;border:1px solid var(--surface3);background:var(--surface);color:var(--text2);
  font-size:0.75rem;font-family:var(--font);cursor:pointer;white-space:nowrap;transition:all 0.2s}}
.cat-btn:hover,.cat-btn.active{{border-color:var(--accent);color:var(--accent);background:rgba(88,166,255,0.08)}}

/* ── PRODUCT GRID ─────────────────────────────────── */
.product-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}}
.product-card{{background:var(--surface);border:1px solid var(--surface3);border-radius:var(--radius);padding:18px;
  transition:all 0.3s;position:relative;overflow:hidden}}
.product-card:hover{{border-color:var(--accent);transform:translateY(-2px);box-shadow:0 8px 30px rgba(88,166,255,0.06)}}
.product-card[data-available="0"]{{opacity:0.55}}
.pc-top{{display:flex;gap:14px;align-items:flex-start;margin-bottom:14px}}
.pc-icon{{font-size:1.6rem;width:44px;height:44px;display:flex;align-items:center;justify-content:center;
  background:var(--surface2);border-radius:12px;flex-shrink:0}}
.pc-info{{flex:1;min-width:0}}
.pc-name{{font-size:0.95rem;font-weight:600;line-height:1.3;margin-bottom:4px}}
.pc-spec{{font-size:0.72rem;color:var(--text2);font-family:var(--mono)}}
.pc-cat{{display:inline-block;font-size:0.65rem;padding:2px 8px;border-radius:8px;margin-top:6px;font-weight:500}}
.pc-bottom{{display:flex;justify-content:space-between;align-items:flex-end;gap:10px;flex-wrap:wrap}}
.pc-price-status{{display:flex;flex-direction:column;gap:4px}}
.pc-price{{font-size:1.1rem;font-weight:700;color:var(--green)}}
.pc-status{{font-size:0.7rem;font-family:var(--mono);text-transform:uppercase}}
.st-ok{{color:var(--green)}}
.st-out{{color:var(--red);background:rgba(248,81,73,0.1);padding:2px 8px;border-radius:6px;border:1px solid rgba(248,81,73,0.3)}}
.pc-actions{{display:flex;gap:8px}}
.btn-detail{{padding:8px 14px;border:1px solid var(--surface3);border-radius:10px;background:transparent;
  color:var(--text2);font-size:0.78rem;font-family:var(--font);cursor:pointer;transition:all 0.2s}}
.btn-detail:hover{{border-color:var(--accent);color:var(--accent)}}
.btn-cart{{padding:8px 16px;border:none;border-radius:10px;background:var(--accent2);color:#fff;
  font-size:0.78rem;font-weight:600;font-family:var(--font);cursor:pointer;transition:all 0.2s}}
.btn-cart:hover{{background:var(--accent)}}
.btn-cart:disabled{{background:var(--surface3);color:var(--text2);cursor:not-allowed}}

/* ── CEP ──────────────────────────────────────────── */
.cep-section{{background:var(--surface);border:1px solid var(--surface3);border-radius:var(--radius);padding:20px;margin:24px 0}}
.cep-section h3{{font-size:0.95rem;margin-bottom:12px}}
.cep-row{{display:flex;gap:10px}}
.cep-row input{{flex:1}}
.cep-row button{{white-space:nowrap}}
#resultado-frete{{margin-top:10px;font-size:0.85rem;color:var(--accent);font-weight:600}}

/* ── MODAL ────────────────────────────────────────── */
.modal-overlay{{display:none;position:fixed;z-index:2000;top:0;left:0;width:100%;height:100%;
  background:rgba(0,0,0,0.75);backdrop-filter:blur(8px);overflow-y:auto}}
.modal-box{{background:var(--surface);border:1px solid var(--surface3);margin:6% auto;padding:28px;
  width:92%;max-width:520px;border-radius:20px;position:relative}}
.modal-box h2{{font-size:1.2rem;margin-bottom:6px;background:linear-gradient(135deg,var(--accent),var(--pink));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.modal-body{{background:var(--surface2);padding:16px;border-radius:12px;border-left:4px solid var(--accent);
  margin:16px 0;font-size:0.9rem;line-height:1.6;color:var(--text2)}}
.modal-close{{width:100%;padding:12px;border:none;border-radius:12px;background:var(--surface3);color:var(--text);
  font-family:var(--font);font-weight:600;cursor:pointer;font-size:0.9rem;transition:background 0.2s}}
.modal-close:hover{{background:var(--surface2)}}

/* ── WHATSAPP FAB ─────────────────────────────────── */
.whatsapp-fab{{position:fixed;bottom:94px;right:24px;z-index:950;width:58px;height:58px;border-radius:50%;
  background:linear-gradient(135deg,#25D366,#128C7E);border:none;color:#fff;
  cursor:pointer;box-shadow:0 4px 24px rgba(37,211,102,0.35);display:flex;align-items:center;justify-content:center;
  transition:transform 0.2s;text-decoration:none}}
.whatsapp-fab:hover{{transform:scale(1.08)}}


/* ── CART ─────────────────────────────────────────── */
.cart-fab{{position:fixed;bottom:24px;right:24px;z-index:900;width:58px;height:58px;border-radius:50%;
  background:linear-gradient(135deg,var(--accent2),var(--accent));border:none;color:#fff;font-size:1.4rem;
  cursor:pointer;box-shadow:0 4px 24px rgba(88,166,255,0.3);display:none;align-items:center;justify-content:center;transition:transform 0.2s}}
.cart-fab:hover{{transform:scale(1.08)}}
.cart-fab .badge{{position:absolute;top:-4px;right:-4px;background:var(--red);color:#fff;font-size:0.65rem;
  width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700}}
.cart-panel{{position:fixed;bottom:0;left:0;right:0;background:var(--surface);border-top:1px solid var(--surface3);
  border-radius:20px 20px 0 0;z-index:1000;display:none;box-shadow:0 -8px 40px rgba(0,0,0,0.4);
  max-height:80vh;overflow-y:auto;padding:20px}}
@media(min-width:768px){{.cart-panel{{width:420px;left:auto;right:24px;bottom:24px;border-radius:20px}}}}
.cart-panel h3{{font-size:1rem;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center}}
.cart-panel h3 button{{background:none;border:none;color:var(--text2);font-size:1.4rem;cursor:pointer}}
.cart-list{{max-height:180px;overflow-y:auto;margin:10px 0;background:var(--surface2);border-radius:12px;padding:6px}}
.cart-list::-webkit-scrollbar{{width:4px}}
.cart-list::-webkit-scrollbar-thumb{{background:var(--surface3);border-radius:4px}}
.cart-item{{display:flex;justify-content:space-between;align-items:center;padding:10px;border-bottom:1px solid var(--surface3);font-size:0.82rem}}
.cart-item:last-child{{border:none}}
.cart-item-promo-label{{font-size:0.65rem;color:#ffc107;margin-left:4px}}
.btn-rm{{background:var(--red);border:none;color:#fff;border-radius:6px;padding:3px 8px;cursor:pointer;font-weight:700;font-size:0.75rem;margin-left:8px}}
.coupon-row{{display:flex;gap:8px;margin:12px 0}}
.coupon-row input{{flex:1;padding:10px;border:1px solid var(--surface3);border-radius:10px;background:var(--surface2);color:var(--text);font-family:var(--font);font-size:0.8rem}}
.coupon-row button{{padding:10px 16px;border:none;border-radius:10px;background:var(--gold);color:#000;font-weight:700;font-size:0.8rem;cursor:pointer}}
.coupon-note{{font-size:0.72rem;color:var(--text2);margin:-8px 0 8px;line-height:1.4}}
.ship-row{{display:flex;justify-content:space-between;align-items:center;font-size:0.82rem;color:var(--gold);font-weight:600;margin:6px 0}}
.discount-line{{display:none;justify-content:space-between;color:var(--gold);font-size:0.85rem;margin:4px 0}}
.total-row{{display:flex;justify-content:space-between;font-size:1.1rem;font-weight:700;padding-top:10px;border-top:1px solid var(--surface3);margin-top:8px}}
.btn-checkout{{width:100%;padding:14px;border:none;border-radius:14px;font-weight:700;font-size:0.95rem;
  background:linear-gradient(135deg,var(--accent2),var(--accent));color:#fff;cursor:pointer;margin-top:10px;font-family:var(--font);transition:opacity 0.2s}}
.btn-checkout:hover{{opacity:0.85}}
.form-group{{margin-bottom:12px}}
.form-group input,.form-group select{{width:100%;padding:12px;border:1px solid var(--surface3);border-radius:10px;
  background:var(--surface2);color:var(--text);font-family:var(--font);font-size:0.9rem}}
.form-group input::placeholder{{color:var(--text2)}}
.form-row{{display:flex;gap:10px;margin-bottom:12px}}
.form-row input{{flex:1}}
.no-results{{text-align:center;padding:60px 20px;color:var(--text2)}}
.no-results span{{font-size:2rem;display:block;margin-bottom:12px}}
@media(max-width:600px){{
  .product-grid{{grid-template-columns:1fr}}
  .logo-text{{font-size:1.8rem}}
  .feat-card{{min-width:240px}}
}}
</style>
</head>
<body>
<div class="grain"></div>
<div class="glow-orb glow-1"></div>
<div class="glow-orb glow-2"></div>
<div class="wrap">
  <div class="header">
    <div class="logo-text">G-LAB PEPTIDES</div>
    <div class="logo-sub">Research · Performance · Longevity</div>
  </div>
  <div class="alert-bar">
    <span class="close-x" onclick="this.parentElement.style.display='none'">&times;</span>
    <strong>📢 Aviso:</strong> Previsão de chegada de novos itens 10/07/2026. PEDIDOS ACIMA DE R$1.000 ACOMPANHAM DILUENTE.
  </div>
  <div class="alert-bar">
    <span class="close-x" onclick="this.parentElement.style.display='none'">&times;</span>
    <strong>⚗️ Importante:</strong> Os produtos são envasados em forma sólida, assim não necessitam de refrigeração para manter as propriedades. O produto deve ser diluído em solução bacteriostática (vendida à parte). Após diluição manter refrigerado!<br><strong>NOME DA SOLUÇÃO:</strong> BACTERIOSTATIC WATER.
  </div>

  <div class="featured-section">
    <div class="section-title"><span></span> Destaques do Dia</div>
    <div class="featured-scroll" id="featured-scroll"></div>
  </div>

  <div class="cep-section">
    <h3>🚚 Calcule o Frete</h3>
    <div class="cep-row">
      <input type="tel" id="cep-destino" class="search-input" placeholder="00000-000" style="min-width:auto">
      <button id="btn-calc" onclick="calcularFrete()" class="btn-cart" style="padding:12px 20px;font-size:0.85rem">Localizar</button>
    </div>
    <div id="resultado-frete"></div>
  </div>

  <div class="search-area">
    <input type="text" class="search-input" id="search-input" placeholder="Buscar produto..." oninput="filtrarProdutos()">
    <button class="toggle-avail" id="toggle-avail" onclick="toggleAvail()">Apenas Disponíveis</button>
  </div>
  <div class="cat-filters" id="cat-filters">
    {cat_buttons_html}
  </div>
  <div class="product-grid" id="product-grid">
    {table_rows}
  </div>
  <div class="no-results" id="no-results" style="display:none">
    <span>🔍</span>
    Nenhum produto encontrado.
  </div>
</div>

<!-- WHATSAPP FAB -->
<a class="whatsapp-fab" href="https://wa.me/17746222523" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp">
  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
  </svg>
</a>


<!-- FAB -->
<button class="cart-fab" id="cart-fab" onclick="toggleCartPanel()">
  🛒<span class="badge" id="fab-badge">0</span>
</button>

<!-- CART PANEL -->
<div class="cart-panel" id="cart-panel">
  <h3>🛒 Pedido (<span id="cart-count">0</span>)<button onclick="toggleCartPanel()">▾</button></h3>
  <div class="cart-list" id="cart-list"></div>
  <div class="coupon-row">
    <input type="text" id="coupon-code" placeholder="Cupom de Desconto" maxlength="30">
    <button onclick="aplicarCupom()">Aplicar</button>
  </div>
  <p class="coupon-note" id="coupon-note" style="display:none"></p>
  <div id="ship-info-container" class="ship-row" style="display:none">
    <span id="ship-info-text"></span>
    <button class="btn-rm" style="background:rgba(255,255,255,0.15)" onclick="removerFrete()">✖</button>
  </div>
  <div id="discount-row" class="discount-line">
    <span>Desconto (<span id="discount-name"></span>):</span>
    <span>- R$ <span id="discount-val">0.00</span></span>
  </div>
  <div class="total-row">
    <span>TOTAL GERAL:</span>
    <span>R$ <span id="total-val">0.00</span></span>
  </div>
  <button class="btn-checkout" onclick="abrirCheckout()">Ir para Pagamento</button>
</div>

<!-- MODAL INFO -->
<div class="modal-overlay" id="modalInfo" role="dialog" aria-modal="true" aria-labelledby="info-titulo">
  <div class="modal-box">
    <h2 id="info-titulo"></h2>
    <p id="info-spec" style="font-size:0.8rem;color:var(--text2);font-family:var(--mono);margin-bottom:0"></p>
    <div class="modal-body" id="info-texto"></div>
    <img id="info-imagem" src="" alt="Imagem do Produto"
      style="width:100%;border-radius:12px;margin:12px 0;display:none;"
      onerror="this.style.display='none'">
    <button onclick="fecharInfo()" class="modal-close">Fechar</button>
  </div>
</div>

<!-- MODAL CHECKOUT -->
<div class="modal-overlay" id="modalCheckout" role="dialog" aria-modal="true">
  <div class="modal-box" style="text-align:left">
    <h2>📦 Dados de Entrega</h2>
    <div class="form-group"><input type="text"  id="f_nome"   placeholder="Nome Completo"          maxlength="120"></div>
    <div class="form-group"><input type="text"  id="f_cpf"    placeholder="CPF"                    maxlength="14"></div>
    <div class="form-group"><input type="text"  id="f_end"    placeholder="Endereço (Rua/Av)"       maxlength="200"></div>
    <div class="form-row">
      <input type="text"  id="f_num"    placeholder="Nº"     style="max-width:100px" maxlength="10">
      <input type="text"  id="f_bairro" placeholder="Bairro"                         maxlength="100">
    </div>
    <div class="form-group"><input type="text"  id="f_comp"   placeholder="Complemento (Opcional)" maxlength="100"></div>
    <div class="form-row">
      <input type="text"  id="f_cidade" placeholder="Cidade"                         maxlength="100">
      <input type="text"  id="f_estado" placeholder="UF"    style="max-width:80px"   maxlength="2">
    </div>
    <div class="form-group"><input type="tel"   id="f_tel"    placeholder="WhatsApp"               maxlength="20"></div>
    <div class="form-group">
      <select id="f_pgto">
        <option value="Pix">Pix (Aprovação Imediata)</option>
        <option value="Cartão de crédito">Cartão de Crédito (até 12x)</option>
      </select>
    </div>
    <button onclick="enviarPedido()" class="btn-checkout" style="margin-top:0">ENVIAR PARA WHATSAPP</button>
    <button onclick="fecharCheckout()" style="background:none;border:none;width:100%;color:var(--text2);margin-top:14px;cursor:pointer;font-family:var(--font)">Cancelar</button>
  </div>
</div>

<script>
// ─── DATA (server-rendered, all values sanitized in Python before embed) ───────
const PRODUTOS = {js_produtos};

// ─── STATE ─────────────────────────────────────────────────────────────────────
let carrinho    = [];
let freteV      = 0, freteD = "";
let cupomAtivo  = null;
let catAtual    = "all";
let apenasDisp  = false;

const REGIOES = {{
  SUL:           ['PR','SC','RS'],
  SUDESTE:       ['SP','RJ','MG','ES'],
  'CENTRO-OESTE':['DF','GO','MT','MS'],
  NORTE:         ['AM','RR','AP','PA','TO','RO','AC'],
  NORDESTE:      ['BA','SE','AL','PE','PB','RN','CE','PI','MA'],
}};

// Whitelisted coupon table (codes → discount fraction, 0..1)
const CUPONS = {{
  'BRUNA10':0.10,'DANI10':0.10,'GILMARA5':0.05,'DAFNE10':0.10,'NOS5':0.05,'ROGERIO5':0.05,
  'ANDERSON5':0.05,'JAQUE5':0.05,'CABRAL5':0.05,'KARLINHA5':0.05,'LUD5':0.05,'CASSIA5':0.05,
  'THAIS5':0.05,'NATAN':0.00000000001,'LIRICY5':0.05,'ANDREAFLEURY':0.05,'ANA5':0.05,
  '10PRO':0.000000000001,'PRO5':0.05,'WEY5':0.05,'ALE5':0.05,'TRIGUEIRO':0.05,
  'RAYSSA5':0.05,'PATRICIA5':0.05,'LU5':0.05, 'RAFA5':0.05, 'WAWA':0.05, 'DUDA5':0.05, 'DUDA10': 0.10,
}};

// ─── SECURITY HELPERS ──────────────────────────────────────────────────────────
/**
 * Safely set element text (never innerHTML) to avoid stored-XSS.
 * All user-facing strings from PRODUTOS already HTML-escaped server-side;
 * here we use textContent for an extra client-side safety net.
 */
function setText(id, val) {{
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}}

function sanitizarEntrada(str, maxLen = 300) {{
  if (typeof str !== 'string') str = String(str);
  // Strip anything that looks like a tag or JS protocol
  str = str.replace(/<[^>]*>/g, '').replace(/javascript:/gi, '').replace(/on\w+=/gi, '');
  return str.slice(0, maxLen).trim();
}}

// ─── FEATURED ──────────────────────────────────────────────────────────────────
function gerarDestaques() {{
  // Only AVAILABLE items appear in featured
  const avail = PRODUTOS.filter(p => p.available);
  if (!avail.length) return;

  const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0)) / 86400000);
  const shuffled  = [...avail].sort((a, b) => {{
    const ha = ((a.id + 1) * 2654435761 + dayOfYear * 31) % 4294967296;
    const hb = ((b.id + 1) * 2654435761 + dayOfYear * 31) % 4294967296;
    return ha - hb;
  }});
  const picks     = shuffled.slice(0, 6);
  const container = document.getElementById('featured-scroll');

  picks.forEach(p => {{
    const card = document.createElement('div');
    card.className = 'feat-card' + (p.promoPct > 0 ? ' promo-card' : '');

    // Build price section safely
    let priceHTML = '';
    if (p.promoPct > 0) {{
      const pctLabel = Math.round(p.promoPct * 100) + '% OFF';
      priceHTML = `<div class="feat-price-wrap promo">
        <span class="feat-badge">${{pctLabel}}</span>
        <span class="feat-orig">R$ ${{p.precoOrig.toFixed(2)}}</span>
        <span class="feat-price">R$ ${{p.preco.toFixed(2)}}</span>
      </div>`;
    }} else {{
      priceHTML = `<div class="feat-price-wrap">
        <span class="feat-price">R$ ${{p.preco.toFixed(2)}}</span>
      </div>`;
    }}

    // Use textContent for user-data fields; only controlled strings in innerHTML
    card.innerHTML = `
      <div class="feat-icon"></div>
      <div class="feat-name"></div>
      <div class="feat-spec"></div>
      <div class="feat-desc"></div>
      ${{priceHTML}}
      <button class="feat-btn">Adicionar ao Carrinho</button>
    `;
    card.querySelector('.feat-icon').textContent = p.icon;
    card.querySelector('.feat-name').textContent = p.nome;
    card.querySelector('.feat-spec').textContent = p.espec;
    card.querySelector('.feat-desc').textContent = p.info;
    card.querySelector('.feat-btn').addEventListener('click', () => adicionar(p.id));

    container.appendChild(card);
  }});
}}

// ─── FILTERING ─────────────────────────────────────────────────────────────────
function filtrarCat(cat) {{
  catAtual = cat;
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.toggle('active', b.dataset.cat === cat));
  filtrarProdutos();
}}

function toggleAvail() {{
  apenasDisp = !apenasDisp;
  document.getElementById('toggle-avail').classList.toggle('active', apenasDisp);
  filtrarProdutos();
}}

function filtrarProdutos() {{
  const q     = document.getElementById('search-input').value.toLowerCase();
  const cards = document.querySelectorAll('.product-card');
  let visible = 0;
  cards.forEach(c => {{
    const name      = c.querySelector('.pc-name').textContent.toLowerCase();
    const cat       = c.dataset.cat;
    const avail     = c.dataset.available === '1';
    const matchSearch = !q || name.includes(q);
    const matchCat    = catAtual === 'all' || cat === catAtual;
    const matchAvail  = !apenasDisp || avail;
    const show        = matchSearch && matchCat && matchAvail;
    c.style.display   = show ? '' : 'none';
    if (show) visible++;
  }});
  document.getElementById('no-results').style.display = visible === 0 ? '' : 'none';
}}

// ─── MODAL INFO ────────────────────────────────────────────────────────────────
function abrirInfo(id) {{
  // id comes from our own rendered integer — safe, but still guard
  const pid = parseInt(id, 10);
  if (isNaN(pid)) return;
  const p = PRODUTOS.find(x => x.id === pid);
  if (!p) return;
  // Use textContent to avoid XSS even if data were malformed
  document.getElementById('info-titulo').textContent = p.nome;
  document.getElementById('info-spec').textContent   = p.espec + ' — ' + p.cat;
  document.getElementById('info-texto').textContent  = p.info;
  const img = document.getElementById('info-imagem');
  // Only allow relative paths (no javascript: or data: URIs)
  const safeSrc = p.imagem.replace(/[^a-zA-Z0-9_.\/\- ]/g, '');
  img.src = encodeURI(safeSrc);
  img.style.display = 'block';
  document.getElementById('modalInfo').style.display = 'block';
}}
function fecharInfo() {{ document.getElementById('modalInfo').style.display = 'none'; }}

// ─── CART ──────────────────────────────────────────────────────────────────────
function adicionar(id) {{
  const pid = parseInt(id, 10);
  if (isNaN(pid)) return;
  const p = PRODUTOS.find(x => x.id === pid);
  if (!p || !p.available) return;
  const ex = carrinho.find(i => i.id === pid);
  if (ex) ex.qtd += 1; else carrinho.push({{ ...p, qtd: 1 }});
  atualizarCarrinho();
}}

function remover(id) {{
  const pid = parseInt(id, 10);
  if (isNaN(pid)) return;
  const ex = carrinho.find(x => x.id === pid);
  if (ex) {{
    if (ex.qtd > 1) ex.qtd--;
    else carrinho = carrinho.filter(x => x.id !== pid);
  }}
  if (!carrinho.length) removerFrete();
  atualizarCarrinho();
}}

function toggleCartPanel() {{
  const p = document.getElementById('cart-panel');
  p.style.display = p.style.display === 'block' ? 'none' : 'block';
}}

function atualizarCarrinho() {{
  const list     = document.getElementById('cart-list');
  const panel    = document.getElementById('cart-panel');
  const fab      = document.getElementById('cart-fab');
  const totalUn  = carrinho.reduce((a, i) => a + i.qtd, 0);

  fab.style.display    = carrinho.length ? 'flex' : 'none';
  document.getElementById('fab-badge').textContent   = totalUn;
  document.getElementById('cart-count').textContent  = totalUn;
  if (!carrinho.length) panel.style.display = 'none';

  list.innerHTML = '';
  let subtotalNormal = 0;   // items without promo (coupon applies here)
  let subtotalPromo  = 0;   // items with promo   (coupon does NOT apply)

  carrinho.forEach(item => {{
    const vt = item.preco * item.qtd;
    if (item.promoPct > 0) subtotalPromo  += vt;
    else                    subtotalNormal += vt;

    const row = document.createElement('div');
    row.className = 'cart-item';

    const left  = document.createElement('span');
    const right = document.createElement('span');

    const nameSpan = document.createElement('strong');
    nameSpan.textContent = item.qtd + 'x ';
    const nameTxt = document.createTextNode(item.nome);
    left.appendChild(nameSpan);
    left.appendChild(nameTxt);

    if (item.promoPct > 0) {{
      const promoLbl = document.createElement('span');
      promoLbl.className   = 'cart-item-promo-label';
      promoLbl.textContent = '🏷️ ' + Math.round(item.promoPct * 100) + '% OFF';
      left.appendChild(promoLbl);
    }}

    const priceTxt = document.createTextNode('R$ ' + vt.toFixed(2) + ' ');
    const rmBtn    = document.createElement('button');
    rmBtn.className   = 'btn-rm';
    rmBtn.textContent = '−';
    rmBtn.addEventListener('click', () => remover(item.id));
    right.appendChild(priceTxt);
    right.appendChild(rmBtn);

    row.appendChild(left);
    row.appendChild(right);
    list.appendChild(row);
  }});

  // Coupon only affects non-promo subtotal
  let desc = 0;
  const noteEl = document.getElementById('coupon-note');
  if (cupomAtivo) {{
    desc = subtotalNormal * cupomAtivo.desc;
    const hasPromoItems = carrinho.some(i => i.promoPct > 0);
    if (hasPromoItems && subtotalNormal === 0) {{
      noteEl.textContent  = '⚠️ Cupom não aplicável: todos os itens já estão em promoção.';
      noteEl.style.display = 'block';
    }} else if (hasPromoItems) {{
      noteEl.textContent  = 'ℹ️ Cupom aplicado apenas aos itens sem promoção.';
      noteEl.style.display = 'block';
    }} else {{
      noteEl.style.display = 'none';
    }}
  }} else {{
    noteEl.style.display = 'none';
  }}

  document.getElementById('discount-row').style.display = (cupomAtivo && desc > 0) ? 'flex' : 'none';
  if (cupomAtivo) {{
    document.getElementById('discount-name').textContent = cupomAtivo.nome;
    document.getElementById('discount-val').textContent  = desc.toFixed(2);
  }}

  const sc = document.getElementById('ship-info-container');
  sc.style.display = freteV > 0 ? 'flex' : 'none';
  if (freteV > 0) document.getElementById('ship-info-text').textContent = '🚚 ' + freteD;


  const total = subtotalNormal + subtotalPromo - desc + freteV;
  document.getElementById('total-val').textContent = total.toLocaleString('pt-BR', {{minimumFractionDigits:2}});
}}

function removerFrete() {{
  freteV = 0; freteD = "";
  document.getElementById('resultado-frete').textContent = "";
  document.getElementById('cep-destino').value           = "";
  atualizarCarrinho();
}}

// ─── CUPOM ─────────────────────────────────────────────────────────────────────
function aplicarCupom() {{
  // Only accept alphanumeric codes up to 30 chars
  const raw  = document.getElementById('coupon-code').value;
  const code = raw.replace(/[^A-Za-z0-9]/g, '').toUpperCase().slice(0, 30);

  if (CUPONS[code] !== undefined) {{
    cupomAtivo = {{ nome: code, desc: CUPONS[code] }};
    alert("✅ Cupom aplicado!");
  }} else {{
    cupomAtivo = null;
    alert("❌ Cupom inválido.");
  }}
  atualizarCarrinho();
}}

// ─── FRETE ─────────────────────────────────────────────────────────────────────
async function buscarDadosCep(cep) {{
  // Only 8-digit CEPs — already validated by caller
  try {{
    const r = await fetch(`https://viacep.com.br/ws/${{encodeURIComponent(cep)}}/json/`);
    const d = await r.json();
    if (!d.erro) return {{ localidade: d.localidade, uf: d.uf.toUpperCase(), logradouro: d.logradouro, bairro: d.bairro }};
  }} catch (e) {{}}
  try {{
    const r = await fetch(`https://brasilapi.com.br/api/cep/v1/${{encodeURIComponent(cep)}}`);
    const d = await r.json();
    if (r.ok) return {{ localidade: d.city, uf: d.state.toUpperCase(), logradouro: d.street || "", bairro: d.neighborhood || "" }};
  }} catch (e) {{}}
  return null;
}}

async function calcularFrete() {{
  const raw = document.getElementById('cep-destino').value.replace(/\D/g, '');
  const btn = document.getElementById('btn-calc');
  if (raw.length !== 8) {{ alert("CEP inválido"); return; }}
  btn.disabled    = true;
  btn.textContent = "...";

  const data = await buscarDadosCep(raw);
  if (!data) {{
    alert("CEP não encontrado");
    btn.disabled    = false;
    btn.textContent = "Localizar";
    return;
  }}

  const uf = data.uf.replace(/[^A-Z]/g, '').slice(0, 2);   // hard-sanitize UF
  if      (REGIOES.SUL.includes(uf))                                          {{ freteV = 90,00;  freteD = "SUL R$ 90,00 (3-9 dias)"; }}
  else if ([...REGIOES.SUDESTE, ...REGIOES['CENTRO-OESTE']].includes(uf))     {{ freteV = 110,00; freteD = "SUDESTE/CO R$ 110,00 (5-15 dias)"; }}
  else                                                                         {{ freteV = 165,00; freteD = "N/NE R$ 165,00 (10-30 dias)"; }}

  // Populate form fields with textContent-safe values
  document.getElementById('f_cidade').value = data.localidade  || '';
  document.getElementById('f_estado').value = uf;
  document.getElementById('f_end').value    = data.logradouro  || '';
  document.getElementById('f_bairro').value = data.bairro      || '';

  document.getElementById('resultado-frete').textContent =
    '✅ ' + (data.localidade || '') + '-' + uf + ': ' + freteD;

  atualizarCarrinho();
  btn.disabled    = false;
  btn.textContent = "Localizar";
}}

// ─── CHECKOUT ──────────────────────────────────────────────────────────────────
function abrirCheckout() {{
  if (freteV <= 0) {{ alert("Calcule o frete primeiro!"); return; }}

  document.getElementById('modalCheckout').style.display = 'block';
}}
function fecharCheckout() {{ document.getElementById('modalCheckout').style.display = 'none'; }}

function enviarPedido() {{
  // Read and sanitize all form fields
  const d = {{
    n:    sanitizarEntrada(document.getElementById('f_nome').value,    120).toUpperCase(),
    cpf:  sanitizarEntrada(document.getElementById('f_cpf').value,     14),
    e:    sanitizarEntrada(document.getElementById('f_end').value,     200).toUpperCase(),
    nu:   sanitizarEntrada(document.getElementById('f_num').value,     10),
    ba:   sanitizarEntrada(document.getElementById('f_bairro').value,  100).toUpperCase(),
    co:   sanitizarEntrada(document.getElementById('f_comp').value,    100).toUpperCase(),
    ci:   sanitizarEntrada(document.getElementById('f_cidade').value,  100).toUpperCase(),
    es:   sanitizarEntrada(document.getElementById('f_estado').value,  2).toUpperCase(),
    ce:   document.getElementById('cep-destino').value.replace(/\D/g,'').replace(/(\d{{5}})(\d{{3}})/, '$1-$2'),
    t:    sanitizarEntrada(document.getElementById('f_tel').value,     20),
    p:    document.getElementById('f_pgto').value === 'Pix' ? 'PIX' : 'CARTÃO DE CRÉDITO',
  }};

  if (!d.n || !d.cpf || !d.e || !d.nu || !d.ba || !d.ci || !d.es || !d.t) {{
    alert("Preencha todos os campos obrigatórios!");
    return;
  }}

  const temSol    = carrinho.some(i => i.nome.toUpperCase().includes("BACTERIOSTATIC WATER"));
  const temBrinde = cupomAtivo && cupomAtivo.nome === "BRUNA5";
  if (!temSol && !temBrinde) {{
    if (!confirm("Pedido sem solução de diluição (Bacteriostatic Water). Continuar?")) {{
      fecharCheckout(); return;
    }}
  }}

  let subtotalNormal = 0, subtotalPromo = 0, msgI = "";
  carrinho.forEach(i => {{
    const vt = i.preco * i.qtd;
    if (i.promoPct > 0) {{
      subtotalPromo += vt;
      msgI += "• " + i.qtd + "x " + i.nome.toUpperCase() + " (" + i.espec.toUpperCase() + ")" +
              " [PROMO -" + Math.round(i.promoPct * 100) + "%] - R$ " + vt.toFixed(2) + "%0A";
    }} else {{
      subtotalNormal += vt;
      const vtFinal = cupomAtivo ? vt - vt * cupomAtivo.desc : vt;
      msgI += "• " + i.qtd + "x " + i.nome.toUpperCase() + " (" + i.espec.toUpperCase() + ")" +
              " - R$ " + vt.toFixed(2) + (cupomAtivo ? " → R$ " + vtFinal.toFixed(2) : "") + "%0A";
    }}
  }});

  const desc  = cupomAtivo ? subtotalNormal * cupomAtivo.desc : 0;
  const total = subtotalNormal + subtotalPromo - desc + freteV;

  let msg = "*NOVO PEDIDO G-LAB*%0A%0A*CLIENTE:*%0A";
  msg += "• *NOME:* "     + encodeURIComponent(d.n)   + "%0A";
  msg += "• *CPF:* "      + encodeURIComponent(d.cpf) + "%0A";
  msg += "• *WHATSAPP:* " + encodeURIComponent(d.t)   + "%0A";
  msg += "• *END:* "      + encodeURIComponent(d.e)   + ", " + encodeURIComponent(d.nu) + "%0A";
  msg += "• *BAIRRO:* "   + encodeURIComponent(d.ba)  + "%0A";
  if (d.co) msg += "• *COMPL:* " + encodeURIComponent(d.co) + "%0A";
  msg += "• *CIDADE:* "   + encodeURIComponent(d.ci)  + "-"  + encodeURIComponent(d.es) + "%0A";
  msg += "• *CEP:* "      + encodeURIComponent(d.ce)  + "%0A";
  msg += "• *PGTO:* "     + encodeURIComponent(d.p)   + "%0A%0A";
  msg += "*ITENS:*%0A"    + msgI;
  if (cupomAtivo && desc > 0)
    msg += "%0A🏷️ *CUPOM:* " + cupomAtivo.nome + " (-R$ " + desc.toFixed(2) + ") (apenas itens s/ promoção)";
  msg += "%0A🚚 *FRETE:* " + freteD.toUpperCase();
  msg += "%0A%0A*TOTAL: R$ " + total.toFixed(2) + "*";

  // Phone number — change to your actual number before deploy
  const WA_PHONE = "17746222523";
  window.open("https://wa.me/" + WA_PHONE + "?text=" + msg, '_blank');
}}

// ─── INIT ──────────────────────────────────────────────────────────────────────
gerarDestaques();

// Close modals when clicking the dark overlay (not the box)
document.getElementById('modalInfo').addEventListener('click', function(e) {{
  if (e.target === this) fecharInfo();
}});
document.getElementById('modalCheckout').addEventListener('click', function(e) {{
  if (e.target === this) fecharCheckout();
}});

// Keyboard accessibility — close modals on Escape
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') {{ fecharInfo(); fecharCheckout(); }}
}});
</script>
</body>
</html>"""

    caminho_saida = os.path.join(diretorio_atual, 'index.html')
    try:
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ Site gerado com sucesso em: {caminho_saida}")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")


if __name__ == "__main__":
    gerar_site_vendas_completo()
