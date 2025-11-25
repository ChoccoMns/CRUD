# CRUD de Solicitações de Viagem

Aplicação web em Streamlit integrada ao PostgreSQL para registrar e gerenciar solicitações de serviços (transporte, hospedagem, passagens aéreas, etc.). O projeto permite criar, consultar, atualizar e remover registros com todos os campos solicitados.

## Pré-requisitos

- Python 3.10+
- PostgreSQL 13+ já configurado e acessível
- Virtualenv (opcional, mas recomendado)

## Configuração

1. Clone ou copie este repositório e acesse a pasta `CRUD TEST`.
2. Crie e ative um ambiente virtual:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Instale as dependências:
   ```powershell
   pip install -r requirements.txt
   ```
4. Configure as credenciais do banco copiando `env.example` para `.env` e ajustando o valor de `DATABASE_URL`:
   ```
   DATABASE_URL=postgresql+psycopg2://usuario:senha@host:5432/nome_do_banco
   ```
   > Exemplo local: `postgresql+psycopg2://postgres:postgres@localhost:5432/crud_viagens`

5. Garanta que o usuário do banco possui permissão de criação de tabelas. A aplicação cria a tabela `travel_services` automaticamente se ela ainda não existir.

## Execução

Com o ambiente configurado e o `.env` preenchido:

```powershell
streamlit run app.py
```

Acesse o link exibido no terminal (por padrão `http://localhost:8501`).

## Estrutura principal

- `app.py`: aplicação Streamlit com formulários de criação, atualização, visualização e exclusão.
- `requirements.txt`: dependências do Python.
- `.env.example`: modelo de configuração do banco.

## Campos contemplados

- Tipo de serviço
- Controle
- Data de emissão
- Emissor
- Companhia aérea
- Data de partida/check-in
- Mês (número ↔ nome)
- Origem / destino
- Usuário
- Motivo
- Centro de custo
- Custo do serviço, taxa e cálculo automático do custo total
- Status
- Fornecedor
- Emissão de NF e número da NF

## Próximos passos sugeridos

- Publicar o app usando Streamlit Cloud ou outra infraestrutura.
- Adicionar autenticação de usuários.
- Exportar relatórios (CSV/Excel) diretamente da interface.

