import json
import google.generativeai as genai

def configure_llm(api_key: str):
    """Configura a chave de API do Gemini."""
    genai.configure(api_key=api_key)

def get_model():
    """Retorna a instância do modelo Gemini."""
    # Utilizando o gemini-flash-latest que está disponível na sua conta
    return genai.GenerativeModel('gemini-flash-latest')

def generate_driver_instructions(routes, city_map, vehicles):
    """
    Gera instruções em linguagem natural para os motoristas
    baseado nas rotas otimizadas.
    """
    model = get_model()
    
    context = "Você é um coordenador logístico experiente especializado em logística hospitalar de urgência.\n\n"
    context += "Sua tarefa é gerar um 'Roteiro de Viagem' claro, direto e empático para os motoristas da nossa frota.\n"
    context += "Abaixo estão as rotas matemáticas calculadas pelo nosso Algoritmo Genético:\n"
    
    for idx, route in enumerate(routes):
        vehicle = vehicles[idx]
        if len(route) > 2:
            context += f"\n--- {vehicle.name} (Capacidade total: {vehicle.capacity}kg, Autonomia: {vehicle.autonomy}km) ---\n"
            for i, loc in enumerate(route):
                if loc in city_map:
                    hospital = city_map[loc]
                    context += f"  - Parada {i}: Entregar {hospital.demand}kg no {hospital.name} [Prioridade: {hospital.priority.name}]\n"
                else:
                    status = "Saída do Depósito" if i == 0 else "Retorno ao Depósito"
                    context += f"  - Parada {i}: {status}\n"
    
    prompt = context + "\n\nInstruções: Escreva de forma profissional, orientando os motoristas sobre a ordem das paradas e pedindo atenção redobrada aos hospitais com prioridade CRITICAL e URGENT. Crie um texto estruturado e amigável."
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Erro ao gerar instruções: {e}"

def generate_efficiency_report(report_data, unvisited_names):
    """
    Cria um relatório analítico sobre a eficiência das rotas geradas.
    """
    model = get_model()
    
    context = "Você é um consultor sênior de dados e logística em saúde.\n\n"
    context += "Analise os dados de desempenho abaixo referentes ao roteamento de hoje (calculado via VRP com Algoritmos Genéticos):\n\n"
    context += json.dumps(report_data, indent=2, ensure_ascii=False)
    
    if unvisited_names:
        context += f"\n\n🚨 ALERTA: Os seguintes hospitais NÃO puderam ser atendidos por falta de capacidade na frota: {', '.join(unvisited_names)}\n"
    else:
        context += "\n\n✅ SUCESSO: Todos os hospitais cadastrados foram atendidos com sucesso.\n"
        
    prompt = context + "\n\nEscreva um Relatório de Eficiência Executivo. O relatório deve conter:\n" \
                       "1. Um resumo executivo da operação.\n" \
                       "2. Análise da ocupação dos veículos (espaço ocioso x usado).\n" \
                       "3. Identificação de gargalos (ex: hospitais ignorados ou veículos no limite).\n" \
                       "4. Sugestões de melhorias táticas e padrões identificados para as próximas rotadas."
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Erro ao gerar relatório: {e}"

def chat_with_data(context_data, user_question):
    """
    Permite que o usuário tire dúvidas em linguagem natural sobre o contexto atual da frota.
    """
    model = get_model()
    
    prompt = f"""Você é um assistente virtual integrado a um sistema logístico hospitalar. 
Use EXCLUSIVAMENTE o contexto de dados estruturados abaixo para responder à pergunta do usuário de forma clara e direta.
Se a resposta exigida não estiver contida nos dados do contexto, seja honesto e diga que não possui essa informação.

=== CONTEXTO DE DADOS DA OPERAÇÃO DE HOJE ===
{context_data}
=============================================

Pergunta do usuário: {user_question}
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Erro na comunicação com a IA: {e}"
