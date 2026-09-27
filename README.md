# Check Point 02 — Coding for Security (FIAP)

Resolução dos exercícios do Check Point 02 da disciplina Coding for Security,
cobrindo SQL vs NoSQL, MongoDB, MySQL, Machine Learning, APIs Flask e OWASP Top 10 (2025).

## Estrutura

- `exercicio1/` — Assistente de decisão de armazenamento (SQL vs NoSQL, CAP)
- `exercicio2/` — Migração relacional → documentos (MySQL → MongoDB)
- `exercicio3/` — Retenção e janela temporal (TTL, agregação por hora)
- `exercicio4/` — Transação com trilha de auditoria (commit/rollback + Mongo)
- `exercicio5/` — API com ORDER BY seguro via whitelist (SQL Injection)
- `exercicio6/` — Controle de acesso quebrado / IDOR (autenticação por API Key)
- `exercicio7/` — XSS em atributo HTML (Jinja2 + Content-Security-Policy)
- `exercicio8/` — Modelo de ML servido por API, com métricas auditáveis

## Como rodar

1. Suba os bancos localmente (MySQL e MongoDB, ex: via Docker).
2. Copie `.env.example` para `.env` e preencha as credenciais.
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Rode o exercício desejado, por exemplo:
   ```
   python exercicio1/main.py
   ```
