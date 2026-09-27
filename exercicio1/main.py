"""Exercício 1 - Assistente de decisão de armazenamento."""

PERFIS = {
    "credenciais_do_SOC": {"schema_fixo":True,"precisa_acid":True,"escala_horizontal":False,"tolera_atraso_de_consistencia":False,"dado_sensivel":True},
    "telemetria_de_sensores": {"schema_fixo":False,"precisa_acid":False,"escala_horizontal":True,"tolera_atraso_de_consistencia":True,"dado_sensivel":False},
    "trilha_de_auditoria": {"schema_fixo":False,"precisa_acid":False,"escala_horizontal":True,"tolera_atraso_de_consistencia":False,"dado_sensivel":True},
    "carrinho_de_licencas": {"schema_fixo":True,"precisa_acid":True,"escala_horizontal":False,"tolera_atraso_de_consistencia":False,"dado_sensivel":False},
    "cache_de_sessoes": {"schema_fixo":True,"precisa_acid":False,"escala_horizontal":True,"tolera_atraso_de_consistencia":True,"dado_sensivel":True},
}

def recomendar(perfil):
    banco = "MySQL" if perfil["precisa_acid"] or (perfil["schema_fixo"] and not perfil["escala_horizontal"]) else "MongoDB"
    cap = "AP" if perfil["tolera_atraso_de_consistencia"] else "CP"

    # Justificativa: combina ACID + sensibilidade + tolerância a atraso
    # pra nomear o erro concreto que cada cenário não pode aceitar.
    if perfil["precisa_acid"] and perfil["dado_sensivel"]:
        justificativa = "autenticar/autorizar com base num dado errado é pior do que recusar o acesso; melhor derrubar a operação do que liberar acesso indevido"
    elif perfil["precisa_acid"] and not perfil["dado_sensivel"]:
        justificativa = "vender duas vezes a mesma licença por causa de uma transação parcial custa dinheiro; commit precisa ser tudo ou nada"
    elif not perfil["tolera_atraso_de_consistencia"] and perfil["dado_sensivel"]:
        justificativa = "uma trilha de auditoria com registros divergentes entre réplicas não serve como prova; inconsistência aqui invalida o rastro"
    elif perfil["tolera_atraso_de_consistencia"] and perfil["dado_sensivel"]:
        justificativa = "perder disponibilidade da sessão derruba o usuário na hora; aceita-se réplica levemente atrasada, mas a sessão/token não pode ficar exposta"
    else:
        justificativa = "perder alguns segundos de leitura de telemetria é aceitável; parar de aceitar novos dados por causa de uma réplica atrasada não é"

    if perfil["precisa_acid"] and perfil["dado_sensivel"]:
        risco = "A07 - Identification and Authentication Failures"
    elif not perfil["tolera_atraso_de_consistencia"] and perfil["dado_sensivel"]:
        risco = "A08 - Software or Data Integrity Failures"
    elif perfil["tolera_atraso_de_consistencia"] and perfil["dado_sensivel"]:
        risco = "A02 - Cryptographic Failures"
    else:
        risco = "A09 - Security Logging and Alerting Failures"

    return {"banco": banco, "cap": cap, "justificativa": justificativa, "risco_owasp": risco}

for nome, perfil in PERFIS.items():
    print(nome, "->", recomendar(perfil))
