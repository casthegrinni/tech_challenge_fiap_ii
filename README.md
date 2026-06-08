# TSP Tech Challenge II

Otimização de Rotas Médicas (Vehicle Routing Problem) usando Algoritmos Genéticos e LLMs para o Tech Challenge Fase 2.

## Como Executar o Projeto

Este projeto utiliza o **Poetry** para gerenciamento de dependências e ambientes virtuais, garantindo um setup determinístico.

### Pré-requisitos
- Python 3.9 (Recomendado, pois o Streamlit versão 1.29.0 é utilizado para manter compatibilidade com este ambiente).
- [Poetry](https://python-poetry.org/docs/#installation) instalado na máquina.

### Passos para Instalação

1. Clone o repositório e navegue até a pasta do projeto:

2. (Opcional, mas recomendado se tiver múltiplas versões do Python) Diga ao Poetry para usar o Python 3.9:
   ```bash
   poetry env use python3.9
   ```

3. Instale as dependências isoladamente:
   ```bash
   poetry install
   ```

### Iniciando a Aplicação

Para abrir a interface gráfica interativa (Streamlit) no seu navegador, execute:

```bash
poetry run streamlit run app.py
```
