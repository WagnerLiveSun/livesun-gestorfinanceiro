def montar_balancete_estruturado(contas_models, lancamentos_models, usar_valor_pago=True, incluir_zeradas=False):
    """
    Gera uma lista de dicionários estruturados para balancete hierárquico.
    Cada item: {'codigo': str, 'descricao': str, 'valor': float, 'nivel': int}
    """
    # Monta um dicionário de contas por id para lookup rápido
    contas_dict = {c.id: c for c in contas_models}
    # Calcula valores por conta
    valores = {c.id: 0.0 for c in contas_models}
    for lanc in lancamentos_models:
        conta_id = getattr(lanc, 'fluxo_conta_id', None)
        if conta_id in valores:
            valor = lanc.valor_pago if usar_valor_pago and hasattr(lanc, 'valor_pago') else lanc.valor_real
            valores[conta_id] += float(valor)
    # Função para determinar nível de hierarquia pela máscara/código
    def get_nivel(conta):
        if hasattr(conta, 'mascara') and conta.mascara:
            return conta.mascara.count('.')
        if hasattr(conta, 'codigo') and conta.codigo:
            return str(conta.codigo).count('.')
        return 0
    # Ordena contas por código
    contas_ordenadas = sorted(contas_models, key=lambda c: c.codigo)
    linhas = []
    total = 0.0
    for conta in contas_ordenadas:
        soma = valores[conta.id]
        if soma != 0 or incluir_zeradas:
            nivel = get_nivel(conta)
            linhas.append({
                'codigo': conta.codigo,
                'descricao': conta.descricao,
                'valor': soma,
                'nivel': nivel
            })
            total += soma
    return linhas, total
def montar_balancete_financeiro(contas_models, lancamentos_models, usar_valor_pago=True, incluir_zeradas=False):
    """
    Gera um balancete financeiro simples em texto.
    contas_models: lista de contas (objetos ou dicts)
    lancamentos_models: lista de lançamentos (objetos ou dicts)
    usar_valor_pago: se True, usa valor pago; senão, valor real
    incluir_zeradas: se True, inclui contas zeradas
    """
    linhas = []
    linhas.append("BALANCETE FINANCEIRO")
    linhas.append("")
    total = 0
    for conta in contas_models:
        soma = 0
        for lanc in lancamentos_models:
            if hasattr(lanc, 'fluxo_conta_id') and hasattr(conta, 'id') and lanc.fluxo_conta_id == conta.id:
                valor = lanc.valor_pago if usar_valor_pago and hasattr(lanc, 'valor_pago') else lanc.valor_real
                soma += float(valor)
        if soma != 0 or incluir_zeradas:
            linhas.append(f"{getattr(conta, 'descricao', getattr(conta, 'codigo', 'Conta'))}: R$ {soma:,.2f}")
        total += soma
    linhas.append("")
    linhas.append(f"TOTAL: R$ {total:,.2f}")
    return '\n'.join(linhas)
