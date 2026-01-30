import pandas as pd
import os
import json

def gerar_site_vendas_completo():
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    # Busca o arquivo de dados
    arquivo_dados = None
    for nome in ['stock_2901.xlsx', 'stock_2901.xlsx - Plan1.csv']:
        caminho = os.path.join(diretorio_atual, nome)
        if os.path.exists(caminho):
            arquivo_dados = caminho
            break

    if not arquivo_dados:
        print(f"Erro: Arquivo não encontrado em: {diretorio_atual}")
        return

    try:
        if arquivo_dados.endswith('.xlsx'):
            df = pd.read_excel(arquivo_dados)
        else:
            df = pd.read_csv(arquivo_dados)
        df.columns = [str(col).strip() for col in df.columns]
        
        # Prepara base de dados para o JavaScript
        produtos_base = []
        for idx, row in df.iterrows():
            produtos_base.append({
                "id": idx,
                "nome": str(row.get('PRODUTO', 'N/A')),
                "espec": f"{row.get('VOLUME', '')} {row.get('MEDIDA', '')}".strip(),
                "preco": float(row.get('Preço (R$)', 0))
            })
        js_produtos = json.dumps(produtos_base)
        
    except Exception as e:
        print(f"Erro ao ler os dados: {e}")
        return

    # Início do HTML com CSS Completo Restaurado
    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>G-LAB PEPTIDES - Pedidos</title>
        <style>
            :root {{ --primary: #004a99; --secondary: #28a745; --danger: #dc3545; --bg: #f4f7f9; }}
            body {{ font-family: 'Segoe UI', Roboto, sans-serif; background: var(--bg); margin: 0; padding: 0; color: #333; }}
            
            .container {{ max-width: 900px; margin: auto; background: white; min-height: 100vh; padding: 15px; box-sizing: border-box; padding-bottom: 220px; }}
            
            h1 {{ color: var(--primary); text-align: center; font-size: 1.6rem; margin-bottom: 5px; }}
            .subtitle {{ text-align: center; color: #666; font-size: 0.9rem; margin-bottom: 20px; }}

            .frete-card {{ background: #fff; border: 2px solid var(--primary); padding: 15px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
            
            .table-container {{ overflow-x: auto; border-radius: 8px; border: 1px solid #eee; }}
            table {{ width: 100%; border-collapse: collapse; background: white; min-width: 400px; }}
            th {{ background: var(--primary); color: white; padding: 12px 8px; text-align: left; font-size: 0.85rem; }}
            td {{ padding: 12px 8px; border-bottom: 1px solid #f0f0f0; font-size: 0.9rem; }}
            
            .status-disponivel {{ color: var(--secondary); font-weight: bold; }}
            .status-espera {{ color: var(--danger); font-weight: bold; background: #fff5f5; padding: 4px 8px; border-radius: 4px; border: 1px solid var(--danger); display: inline-block; }}

            .input-style {{ padding: 12px; border: 1px solid #ccc; border-radius: 8px; width: 100%; box-sizing: border-box; font-size: 16px; }}
            .btn-add {{ background: var(--secondary); color: white; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; }}
            .btn-add:disabled {{ background: #eee; color: #999; cursor: not-allowed; }}

            /* Painel Carrinho */
            .cart-panel {{ position: fixed; bottom: 0; left: 0; right: 0; background: var(--primary); color: white; padding: 15px; border-radius: 20px 20px 0 0; z-index: 1000; display: none; box-shadow: 0 -5px 20px rgba(0,0,0,0.3); max-height: 80vh; overflow-y: auto; }}
            @media (min-width: 768px) {{ .cart-panel {{ width: 400px; left: auto; right: 20px; bottom: 20px; border-radius: 20px; }} }}
            
            .cart-list {{ margin: 10px 0; max-height: 150px; overflow-y: auto; background: rgba(255,255,255,0.1); border-radius: 8px; padding: 5px; }}
            .cart-item {{ display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 0.85rem; align-items: center; }}
            .btn-remove {{ background: #ff4444; border: none; color: white; cursor: pointer; font-weight: bold; border-radius: 4px; padding: 2px 8px; margin-left: 10px; }}

            .coupon-section {{ display: flex; gap: 5px; margin: 10px 0; }}
            .coupon-input {{ flex: 1; padding: 8px; border-radius: 5px; border: none; font-size: 0.8rem; }}
            .btn-coupon {{ background: #ffeb3b; color: #333; border: none; padding: 8px 12px; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 0.8rem; }}

            .ship-row {{ display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: #ffeb3b; margin-top: 5px; font-weight: bold; }}
            .total-row {{ display: flex; justify-content: space-between; font-size: 1.1rem; font-weight: bold; margin: 5px 0; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 10px; }}
            .discount-line {{ display: none; justify-content: space-between; color: #ffeb3b; font-size: 0.9rem; margin-bottom: 5px; }}
            
            .btn-checkout-final {{ background: white; color: var(--primary); border: none; width: 100%; padding: 14px; border-radius: 12px; font-weight: bold; font-size: 1rem; cursor: pointer; margin-top: 5px; }}

            .modal {{ display: none; position: fixed; z-index: 2000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); overflow-y: auto; }}
            .modal-content {{ background: white; margin: 5% auto; padding: 20px; width: 90%; max-width: 500px; border-radius: 15px; box-sizing: border-box; }}
            .form-group {{ margin-bottom: 12px; }}
        </style>
    </head>
    <body>

    <div class="container">
        <h1>🧪 G-LAB PEPTIDES</h1>
        <p class="subtitle">Estoque Atualizado e Pedidos Online</p>
        
        <div class="frete-card">
            <strong>🚚 1. Informe seu CEP para o Frete</strong>
            <div style="display: flex; gap: 8px;">
                <input type="tel" id="cep-destino" class="input-style" style="flex: 1;" placeholder="00000-000">
                <button onclick="calcularFrete()" class="btn-add" style="width: auto; padding: 0 15px;">Calcular</button>
            </div>
            <div id="resultado-frete" style="margin-top:12px; font-size: 0.95rem; line-height: 1.4; color: var(--primary); font-weight: bold;"></div>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="width: 45%;">Produto</th>
                        <th>Status</th>
                        <th>Preço</th>
                        <th>Ação</th>
                    </tr>
                </thead>
                <tbody>
    """

    for idx, row in df.iterrows():
        produto = row.get('PRODUTO', 'N/A')
        espec = f"{row.get('VOLUME', '')} {row.get('MEDIDA', '')}".strip()
        preco = row.get('Preço (R$)', 0)
        estoque_status = str(row.get('ESTOQUE', row.get('STATUS', ''))).strip().upper()
        
        is_available = "DISPONÍVEL" in estoque_status
        status_class = "status-disponivel" if is_available else "status-espera"
        btn_disabled = "" if is_available else "disabled"
        
        html_template += f"""
                    <tr>
                        <td><strong>{produto}</strong><br><small style="color:#666">{espec}</small></td>
                        <td><span class="{status_class}">{estoque_status}</span></td>
                        <td style="white-space: nowrap;">R$ {preco:,.2f}</td>
                        <td>
                            <button onclick="adicionar({idx})" {btn_disabled} class="btn-add">
                                { "+" if is_available else "✖" }
                            </button>
                        </td>
                    </tr>
        """

    html_template += f"""
                </tbody>
            </table>
        </div>
    </div>

    <div id="cart-panel" class="cart-panel">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3 style="margin:0">🛒 Seu Pedido (<span id="cart-count">0</span>)</h3>
            <button onclick="document.getElementById('cart-panel').style.display='none'" style="background:none; border:none; color:white; font-size:1.5rem;">▾</button>
        </div>
        
        <div id="cart-list" class="cart-list"></div>

        <div class="coupon-section">
            <input type="text" id="coupon-code" class="coupon-input" placeholder="Cupom de Desconto">
            <button onclick="aplicarCupom()" class="btn-coupon">Aplicar</button>
        </div>

        <div id="ship-info-container" class="ship-row" style="display:none;">
            <span id="ship-info-text"></span>
            <button onclick="removerFrete()" class="btn-remove" style="background:rgba(255,255,255,0.2); margin:0;">✖</button>
        </div>
        
        <div id="discount-row" class="discount-line">
            <span>Desconto (BRUNA5 -5%):</span>
            <span>- R$ <span id="discount-val">0.00</span></span>
        </div>

        <div class="total-row">
            <span>TOTAL GERAL:</span>
            <span>R$ <span id="total-val">0.00</span></span>
        </div>
        <button class="btn-checkout-final" onclick="abrirCheckout()">Ir para Pagamento</button>
    </div>

    <div id="modalCheckout" class="modal">
        <div class="modal-content">
            <h2 style="color: var(--primary); margin-top: 0;">📦 Dados de Entrega</h2>
            <div class="form-group"><input type="text" id="f_nome" class="input-style" placeholder="Nome Completo"></div>
            <div class="form-group"><input type="text" id="f_end" class="input-style" placeholder="Endereço (Rua/Av)"></div>
            <div style="display:flex; gap:10px; margin-bottom:12px;">
                <input type="text" id="f_num" class="input-style" style="width:30%" placeholder="Nº">
                <input type="text" id="f_comp" class="input-style" style="width:70%" placeholder="Compl.">
            </div>
            <div style="display:flex; gap:10px; margin-bottom:12px;">
                <input type="text" id="f_cidade" class="input-style" placeholder="Cidade">
                <input type="text" id="f_estado" class="input-style" style="width:30%" placeholder="UF">
            </div>
            <div class="form-group"><input type="tel" id="f_tel" class="input-style" placeholder="WhatsApp"></div>
            <div class="form-group">
                <label style="font-size:12px; font-weight:bold;">Forma de Pagamento:</label>
                <select id="f_pgto" class="input-style">
                    <option value="Pix">Pix (Aprovação Imediata)</option>
                    <option value="Cartão de crédito">Cartão de Crédito</option>
                </select>
            </div>
            <button onclick="enviarPedido()" class="btn-add" style="padding:15px; font-size:1.1rem; background:var(--primary);">ENVIAR PARA WHATSAPP</button>
            <button onclick="fecharCheckout()" style="background:none; border:none; width:100%; color:#666; margin-top:15px;">Cancelar / Voltar</button>
        </div>
    </div>

    <script>
        const PRODUTOS = {js_produtos};
        let carrinho = [];
        let freteV = 0;
        let freteD = "";
        let descontoAtivo = false;

        function adicionar(id) {{
            const p = PRODUTOS.find(x => x.id === id);
            if(p) {{
                carrinho.push({{...p, uid: Date.now() + Math.random()}});
                atualizarInterface();
            }}
        }}

        function remover(uid) {{
            carrinho = carrinho.filter(x => x.uid !== uid);
            atualizarInterface();
        }}

        function removerFrete() {{
            freteV = 0;
            freteD = "";
            document.getElementById('resultado-frete').innerText = "";
            document.getElementById('cep-destino').value = "";
            atualizarInterface();
        }}

        function aplicarCupom() {{
            const code = document.getElementById('coupon-code').value.trim().toUpperCase();
            if(code === 'BRUNA5') {{
                descontoAtivo = true;
                alert("Cupom BRUNA5 aplicado! 5% de desconto nos itens.");
            }} else {{
                descontoAtivo = false;
                alert("Cupom inválido.");
            }}
            atualizarInterface();
        }}

        function atualizarInterface() {{
            const list = document.getElementById('cart-list');
            const panel = document.getElementById('cart-panel');
            panel.style.display = carrinho.length > 0 ? 'block' : 'none';
            document.getElementById('cart-count').innerText = carrinho.length;
            
            list.innerHTML = '';
            let sub = 0;
            carrinho.forEach(item => {{
                sub += item.preco;
                list.innerHTML += `<div class="cart-item"><span>${{item.nome}}</span><span>R$ ${{item.preco.toFixed(2)}} <button class="btn-remove" onclick="remover(${{item.uid}})">×</button></span></div>`;
            }});
            
            let valorDesconto = 0;
            if(descontoAtivo) {{
                valorDesconto = sub * 0.05;
                document.getElementById('discount-row').style.display = 'flex';
                document.getElementById('discount-val').innerText = valorDesconto.toFixed(2);
            }} else {{
                document.getElementById('discount-row').style.display = 'none';
            }}

            const shipContainer = document.getElementById('ship-info-container');
            if(freteV > 0) {{
                shipContainer.style.display = 'flex';
                document.getElementById('ship-info-text').innerText = "🚚 Frete: " + freteD;
            }} else {{
                shipContainer.style.display = 'none';
            }}

            const totalFinal = (sub - valorDesconto) + freteV;
            document.getElementById('total-val').innerText = totalFinal.toLocaleString('pt-BR', {{minimumFractionDigits: 2}});
        }}

        function calcularFrete() {{
            const cep = document.getElementById('cep-destino').value.replace(/\D/g, '');
            if(cep.length !== 8) {{ alert("CEP Inválido"); return; }}
            const r = parseInt(cep.substring(0,1));
            if(r === 8) {{ freteV = 90.00; freteD = "SUL R$ 90,00 (5 DIAS)"; }}
            else if([0,1,2,3].includes(r)) {{ freteV = 115.00; freteD = "SUDESTE R$ 115,00 (5 DIAS)"; }}
            else if([4,5,6].includes(r)) {{ freteV = 145.00; freteD = "NORDESTE R$ 145,00 (8 DIAS)"; }}
            else if(r === 7) {{ freteV = 125.00; freteD = "CENTRO OESTE R$ 125,00 (5 DIAS)"; }}
            else if(r === 9) {{ freteV = 145.00; freteD = "NORTE R$ 145,00 (8 DIAS)"; }}
            document.getElementById('resultado-frete').innerText = "✅ " + freteD;
            atualizarInterface();
        }}

        function abrirCheckout() {{ 
            document.getElementById('modalCheckout').style.display = 'block'; 
        }}
        function fecharCheckout() {{ document.getElementById('modalCheckout').style.display = 'none'; }}

        function enviarPedido() {{
            const n = document.getElementById('f_nome').value;
            const e = document.getElementById('f_end').value;
            const t = document.getElementById('f_tel').value;
            const p = document.getElementById('f_pgto').value;
            if(!n || !e || !t) {{ alert("Preencha os campos obrigatórios!"); return; }}

            let sub = 0;
            carrinho.forEach(i => sub += i.preco);
            let desc = descontoAtivo ? sub * 0.05 : 0;

            let msg = "*NOVO PEDIDO G-LAB*%0A%0A*CLIENTE:* " + n + "%0A*WhatsApp:* " + t + "%0A*PAGAMENTO:* " + p + "%0A%0A*ITENS:*%0A";
            carrinho.forEach(i => {{ msg += "• " + i.nome + " (" + i.espec + ") - R$ " + i.preco.toFixed(2) + "%0A"; }});
            
            if(descontoAtivo) msg += "%0A🏷️ *CUPOM APLICADO:* BRUNA5 (-R$ " + desc.toFixed(2) + ")";
            if(freteV > 0) msg += "%0A🚚 *FRETE:* " + freteD;
            else msg += "%0A🚚 *FRETE:* Não calculado/Retirada";
            
            msg += "%0A*TOTAL GERAL: R$ " + (sub - desc + freteV).toFixed(2) + "*";
            window.open("https://wa.me/554188643910?text=" + msg, '_blank');
        }}
    </script>
    </body>
    </html>
    """

    caminho_saida = os.path.join(diretorio_atual, 'index.html')
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"Sucesso! Código com opção de remover frete e forma de pagamento no WhatsApp gerado.")

if __name__ == "__main__":
    gerar_site_vendas_completo()