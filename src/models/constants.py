from typing import Dict

# --- BASE DE DADOS DE PROFISSIONAIS ---
PROFISSIONAIS: Dict[str, Dict[str, str]] = {
    "FRANCISCO DAVID MENESES DOS SANTOS": {
        "empresa": "FRANCISCO DAVID MENESES DOS SANTOS - F. D. MENESES DOS SANTOS",
        "cnpj": "54.801.096/0001-16",
        "cpf_emp": "058.756.003-73",
        "nome_resp": "FRANCISCO DAVID MENESES DOS SANTOS",
        "cpf_resp": "058.756.003-73",
        "registro": "336241CE",
    },
    "PALLOMA TEIXEIRA DA SILVA": {
        "empresa": "PALLOMA TEIXEIRA DA SILVA - PALLOMA TEIXEIRA ARQUITETURA LTDA",
        "cnpj": "54.862.474/0001-71",
        "cpf_emp": "064.943.593-10",
        "nome_resp": "PALLOMA TEIXEIRA DA SILVA",
        "cpf_resp": "064.943.593-10",
        "registro": "A184355-9",
    },
    "SANDY PEREIRA CORDEIRO": {
        "empresa": "SANDY PEREIRA CORDEIRO - CS ENGENHARIA",
        "cnpj": "54.794.898/0001-46",
        "cpf_emp": "071.222.553-60",
        "nome_resp": "SANDY PEREIRA CORDEIRO",
        "cpf_resp": "071.222.553-60",
        "registro": "356882CE",
    },
    "TIAGO VICTOR DE SOUSA": {
        "empresa": "TIAGO VICTOR DE SOUSA - T V S ENGENHARIA E ASSESSORIA",
        "cnpj": "54.806.521/0001-60",
        "cpf_emp": "068.594.803-00",
        "nome_resp": "TIAGO VICTOR DE SOUSA",
        "cpf_resp": "068.594.803-00",
        "registro": "346856CE",
    },
    "DAVID ARRUDA VIANA": {
        "empresa": "DAVID ARRUDA VIANA - DAV ENGENHARIA LTDA",
        "cnpj": "51.508.674/0001-32",
        "cpf_emp": "033.467.853-60",
        "nome_resp": "DAVID ARRUDA VIANA",
        "cpf_resp": "033.467.853-60",
        "registro": "061931352-8",
    },
    "MIKAELL GUSTAVO FARIAS GOMES": {
        "empresa": "MIKAELL GUSTAVO FARIAS GOMES",
        "cnpj": "51.899.957/0001-52",
        "cpf_emp": "057.953.393-00",
        "nome_resp": "MIKAELL GUSTAVO FARIAS GOMES",
        "cpf_resp": "057.953.393-00",
        "registro": "367577CE",
    },
    "YAN LUCAS E SILVA VASCONCELOS": {
        "empresa": "YAN LUCAS E SILVA VASCONCELOS",
        "cnpj": "54.732.603/0001-07",
        "cpf_emp": "038.621.633-93",
        "nome_resp": "YAN LUCAS E SILVA VASCONCELOS",
        "cpf_resp": "038.621.633-93",
        "registro": "365506",
    },
}

# --- SCHEMA GEMINI ---
GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "proponente": {"type": "string"},
        "cpf_cnpj": {"type": "string"},
        "ddd": {"type": "string"},
        "telefone": {"type": "string"},
        "endereco_literal": {"type": "string"},
        "bairro": {"type": "string"},
        "cep": {"type": "string"},
        "municipio": {"type": "string"},
        "uf": {"type": "string"},
        "coordenada_s": {"type": "string"},
        "coordenada_w": {"type": "string"},
        "valor_terreno": {"type": "number"},
        "valor_imovel": {"type": "number"},
        "valor_unitario": {"type": "number"},
        "testada": {"type": "number"},
        "matricula": {"type": "string"},
        "oficio": {"type": "string"},
        "comarca": {"type": "string"},
        "uf_matricula": {"type": "string"},
        "incidencias": {"type": "array", "items": {"type": "number"}},
        "numero_etapas": {"type": "number"},
        "acumulado_proposto": {"type": "array", "items": {"type": "number"}},
        "idade_estimada": {"type": "string"},
        "area_terreno": {"type": "number"},
        "area_construida": {"type": "number"},
        "quartos": {"type": "number"},
        "banheiros": {"type": "number"},
        "suites": {"type": "number"},
        "vagas": {"type": "number"},
        "padrao_acabamento": {"type": "string"},
        "estado_conservacao": {"type": "string"},
        "infraestrutura": {"type": "string"},
        "servicos_publicos": {"type": "string"},
        "usos_predominantes": {"type": "string"},
        "via_acesso": {"type": "string"},
        "regiao_contexto": {"type": "string"},
        "data_referencia": {"type": "string"},
        "empresa_responsavel": {"type": "string"},
    },
    "required": [
        "proponente",
        "ddd",
        "telefone",
        "endereco_literal",
        "incidencias",
        "empresa_responsavel",
    ],
}

# --- PROMPT TEMPLATE ---
GEMINI_PROMPT_TEMPLATE = """
    Você é um ENGENHEIRO REVISOR ESPECIALISTA EM LAUDOS DE AVALIAÇÃO DA CAIXA ECONÔMICA FEDERAL.

    Sua tarefa é extrair informações técnicas do laudo abaixo e retornar EXCLUSIVAMENTE um JSON
    válido, rigorosamente conforme o schema fornecido. NÃO explique nada fora do JSON.

    ────────────────────────────────────────
    EXTRAÇÃO DE COORDENADAS GEOGRÁFICAS

    O texto abaixo não é Markdown! Ele é um RETRATO ESPACIAL do PDF. As colunas estão devidamente alinhadas
    com espaços em branco reproduzindo a posição exata da tabela original.

    Olhe o visual do texto perto da palavra "Latitude" e "Longitude Oeste":

    REGRA MATEMÁTICA DEFINITIVA NO BRASIL:
    1. Mapeie visualmente as colunas de [Graus], [Min] e [Seg].
    2. Extraia o primeiro conjunto que encontrar na mesma linha lida horizontalmente.
    3. Extraia o segundo conjunto na mesma linha.
    4. Classifique-os estritamente pelo GRAU:
       - Se o Grau for entre 00º e 33º -> Este grupo inteiro (Grau+Min+Seg) é a LATITUDE (coordenada_s).
       - Se o Grau for entre 34º e 74º -> Este grupo inteiro (Grau+Min+Seg) é a LONGITUDE (coordenada_w).

    FORMATO FINAL EXIGIDO NAS CHAVES JSON:
    coordenada_s: "XXºYY'ZZ,ZZZ\\""
    coordenada_w: "XXºYY'ZZ,ZZZ\\""
    ────────────────────────────────────────

    REGRAS DE CRONOGRAMA:
    1. Localize a tabela de "Cronograma" ou "Parcelas".
    2. **acumulado_proposto**:
       - O primeiro valor da lista DEVE ser o da linha "Pré-executado".
       - É OBRIGATÓRIO incluir o valor do "Pré-executado" mesmo que seja 0.00.
       - NÃO pule a etapa 0. Se ela for 0%, retorne 0.0 como primeiro item da lista.
       - Em seguida, extraia os valores da coluna "% Acumulado" para as parcelas 1, 2, 3...

    REGRAS DE EXTRAÇÃO DO CRONOGRAMA (INCIDÊNCIAS):

    1. Localize a tabela:
       - "Cronograma Físico-Financeiro"
       - "Discriminação dos Serviços"
       - ou "Orçamento Proposto"

    2. Extraia a coluna de INCIDÊNCIA (ou PESOS).
       - Retorne EXATAMENTE 20 valores percentuais.
       - Preserve a ordem original das etapas.
       - NÃO normalize, NÃO ajuste, NÃO redistribua valores.

    3. Se houver menos de 20 etapas:
       - Complete a lista com 0.0 até atingir 20 itens.

    ────────────────────────────────────────
    REGRAS PARA CAMPOS CLASSIFICÁVEIS:

    - VIA_ACESSO: Retorne SOMENTE se estiver explícito no laudo.
      Valores aceitos: LOCAL, COLETORA ou ARTERIAL.
      Se não estiver explícito, retorne string vazia.

    - PADRAO_ACABAMENTO, ESTADO_CONSERVACAO, REGIAO_CONTEXTO:
      - NÃO infira.
      - NÃO classifique por suposição.
      - Se não estiver textual e claramente descrito, retorne string vazia.

    ────────────────────────────────────────
    OUTRAS REGRAS CRÍTICAS:

    1. ENDERECO_LITERAL:
       - Copie EXATAMENTE como consta na identificação do imóvel.
       - Preserve abreviações, números e ordem.

    2. MATRÍCULA:
       - Extraia número da matrícula.
       - OFÍCIO = número do cartório.
       - COMARCA = município do registro.
       - UF_MATRICULA = estado do cartório.

    3. IDADE_ESTIMADA:
       - Capture o TEXTO LITERAL COMPLETO.
       - Exemplos válidos: "5 anos", "Novo", "Na Planta".

    4. DATA_REFERENCIA:
       - Utilize EXCLUSIVAMENTE a data da AVALIAÇÃO DO IMÓVEL.
       - Ignore datas de ART, vistoria, assinatura ou emissão.
       - Formato obrigatório: DD/MM/AAAA.

    5. EMPRESA_RESPONSAVEL:
       - Vá para a seção final 'SIGNATÁRIOS'.
       - Localize o campo 'Representante legal' associado ao Responsável Técnico.
       - Extraia o nome literal completo do representante legal (Ex: MIKAELL GUSTAVO FARIAS GOMES).

    6. CAMPOS AUSENTES:
       - Se a informação não existir no laudo, retorne:
         - string vazia para textos
         - 0 para números
         - lista vazia quando aplicável

    ERRO GRAVE:
    - Misturar dados entre campos invalida a extração.
    - Inferir informações técnicas não explícitas é proibido.

    ────────────────────────────────────────
    TEXTO DO LAUDO:

    {texto_laudo}
    """
