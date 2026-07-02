import streamlit as st
import google.generativeai as genai
import json

def get_gemini_client():
    """
    Inicializa e configura o cliente do Gemini usando a chave nos secrets do Streamlit.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        return genai
    except Exception:
        return None

def generate_route_explanation(route_data: dict) -> str:
    """
    Recebe os dados brutos de uma rota e gera um briefing explicativo
    em linguagem natural para o motorista, utilizando o modelo Gemini.
    """
    client = get_gemini_client()
    if client is None:
        return (
            "⚠️ Não foi possível obter o briefing do motorista porque a chave "
            "'GEMINI_API_KEY' não está configurada corretamente nos Secrets do Streamlit."
        )

    # 1. Instruções do Sistema (Template)
    system_instruction = (
        "Você é o \"Co-Piloto Médico\". Sua tarefa é ler a rota gerada pelo nosso algoritmo genético "
        "e traduzi-la em um briefing de rota direto e sucinto para o motorista.\n\n"
        "Regras de Negócio:\n"
        "1. Comece com uma saudação curta e direta identificando o veículo.\n"
        "2. Informe o total de quilômetros e peso da carga.\n"
        "3. Liste os pontos de parada na ordem exata como uma lista de marcadores do markdown (usando '-').\n"
        "4. Destaque entregas com prioridade especial (como \"CRÍTICO\" ou \"URGENTE\") em negrito e caixa alta.\n"
        "5. IMPORTANTE: Use quebras de linha duplas para separar cada item da rota, garantindo que não fiquem na mesma linha."
    )

    # 2. Exemplares para In-Context Learning (ICL)
    exemplar_input = {
        "veiculo": "Veículo 2",
        "total_entregas_kg": 15.2,
        "distancia_total_km": 42.1,
        "rota": [
            {"nome": "Depósito Central", "prioridade": "N/A"},
            {"nome": "Hospital 4", "demanda": "5.2kg", "prioridade": "REGULAR"},
            {"nome": "Hospital 1", "demanda": "10.0kg", "prioridade": "URGENT"},
            {"nome": "Depósito Central", "prioridade": "N/A"}
        ]
    }

    exemplar_output = (
        "Rota para o Veículo 2. Distância total: 42.1 km | Carga total: 15.2 kg.\n\n"
        "- **Início:** Depósito Central (Carregamento)\n\n"
        "- **Parada 1:** Hospital 4 - Entregar 5.2 kg [Prioridade: Regular]\n\n"
        "- **Parada 2:** Hospital 1 - Entregar 10.0 kg [**ATENÇÃO: Prioridade URGENTE**]\n\n"
        "- **Retorno:** Depósito Central.\n\n"
        "Tenha uma boa viagem."
    )

    # 3. Montagem do prompt final (com a entrada na cauda)
    prompt = (
        f"{system_instruction}\n\n"
        f"---\n"
        f"EXEMPLO 1 (Entrada de dados):\n"
        f"{json.dumps(exemplar_input, indent=2, ensure_ascii=False)}\n\n"
        f"EXEMPLO 1 (Saída esperada):\n"
        f"{exemplar_output}\n"
        f"---\n\n"
        f"[ENTRADA DA ROTA REAL A SER PROCESSADA]:\n"
        f"{json.dumps(route_data, indent=2, ensure_ascii=False)}\n\n"
        f"[RESPOSTA GERADA PELA IA]:\n"
    )

    try:
        # Executando com gemini-2.5-flash (modelo estável disponível)
        model = client.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Erro ao chamar a API do Gemini: {str(e)}"
