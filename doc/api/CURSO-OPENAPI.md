# Mini-curso: OpenAPI 3.1 do zero

> **Para quem:** quem nunca escreveu um contrato de API.
> **Duração:** ~3h no total, em 9 módulos de 15-30 min. Dá para fazer em 3 sessões.
> **Formato:** cada módulo tem **Conceito → Prática → Exercício → Gabarito**. Digite o YAML, não copie. O erro é onde se aprende.
> **Domínio usado:** uma API de talhões de propriedades rurais. Domínio escolhido de propósito: você já o conhece, então toda a carga cognitiva vai para o OpenAPI e não para as regras de negócio.

---

## Índice

| # | Módulo | Tempo | O que você sai sabendo |
|---|---|---|---|
| 0 | [Por que OpenAPI](#módulo-0--por-que-openapi) | 10 min | O que o formato resolve e o que ele **não** resolve |
| 1 | [Setup](#módulo-1--setup) | 10 min | Ambiente rodando, lint + preview |
| 2 | [O menor documento válido](#módulo-2--o-menor-documento-válido) | 15 min | `openapi`, `info`, `paths` |
| 3 | [Paths e operações](#módulo-3--paths-e-operações) | 20 min | Recursos, métodos, `operationId`, `tags` |
| 4 | [Parâmetros e obrigatoriedade](#módulo-4--parâmetros-e-obrigatoriedade) | 25 min | `path`/`query`/`header`, `required`, `default` |
| 5 | [Schemas — o coração](#módulo-5--schemas--o-coração) | 30 min | JSON Schema, `required`, `enum`, `null` |
| 6 | [Responses e exemplos](#módulo-6--responses-e-exemplos) | 20 min | `content`, `example` vs `examples` |
| 7 | [`$ref` e `components`](#módulo-7--ref-e-components) | 20 min | Parar de repetir, reuso, SDK |
| 8 | [Security](#módulo-8--security) | 15 min | `securitySchemes`, Bearer/JWT |
| 9 | [O ecossistema](#módulo-9--o-ecossistema-onde-o-roi-aparece) | 25 min | Mock, lint, docs, codegen, API Gateway |
| 10 | [As 8 armadilhas](#módulo-10--as-8-armadilhas-que-pegam-todo-mundo) | 15 min | O que quebra na vida real |
| — | [Projeto final](#projeto-final) | 30 min | Um contrato seu, do zero |

---

## Módulo 0 — Por que OpenAPI

### Conceito

OpenAPI é **um arquivo YAML (ou JSON) que descreve uma API HTTP de forma que máquina consegue ler**. Só isso. Não é framework, não é biblioteca, não roda nada.

O nome antigo era **Swagger**. Em 2015 a spec foi doada para a OpenAPI Initiative e virou "OpenAPI". Hoje:
- **OpenAPI** = o formato/spec.
- **Swagger** = nome de um conjunto de ferramentas (Swagger UI, Swagger Editor) da SmartBear.

Quando alguém diz "manda o swagger da API", quer dizer o arquivo OpenAPI.

### O ponto que muda tudo

O valor não está em "ter documentação bonita". Está em ser **legível por máquina**. Do mesmo arquivo você extrai:

```
                       ┌─→ Documentação HTML (Redoc/Swagger UI)  ← negócio lê
                       ├─→ Mock server (Prism)                   ← front integra antes do back existir
openapi.yaml ─────────→├─→ Linter (Spectral)                     ← governança no CI
  (fonte da verdade)   ├─→ SDK cliente (Python/TS/Java)          ← consumidor não escreve HTTP na mão
                       ├─→ Testes de contrato                    ← quebrou o contrato? build falha
                       └─→ Infra (API Gateway importa o arquivo) ← contrato VIRA a infra
```

Documentação escrita em Confluence apodrece porque ninguém consegue testá-la. Um `openapi.yaml` no repo, validado no CI, **não pode** divergir do código sem alguém perceber.

### Design-first vs. code-first

| | Design-first | Code-first |
|---|---|---|
| Como funciona | Escreve o YAML → gera/implementa o código | Escreve o código com annotations → gera o YAML |
| Bom para | APIs com consumidor externo, refinamento com negócio | APIs internas, protótipos |
| Ruim porque | Exige disciplina | O contrato só existe depois do código; negócio não participa |

**Na fase de refinamento, design-first é o único que funciona.** O contrato é o artefato da conversa com o PO.

### O que OpenAPI NÃO resolve

Isto é importante para não frustrar depois:

- ❌ **Não diz se sua API é boa.** OpenAPI valida a *sintaxe*, não o *design*. Você pode escrever um `POST /v1/fazerTudo` perfeitamente válido. Para o *estilo*, existe o Spectral (módulo 9).
- ❌ **Não valida regra de negócio.** "A data final deve ser maior que a inicial" não cabe no schema (JSON Schema até faz coisas assim, mas o API Gateway ignora). Isso é código.
- ❌ **Não gera implementação pronta.** Gera *stub*, esqueleto. Você preenche.
- ❌ **Não descreve APIs assíncronas** (Kafka, SNS/SQS, WebSocket). Para isso existe o **AsyncAPI**, formato irmão.

### Versões — qual usar

| Versão | Ano | Situação |
|---|---|---|
| Swagger 2.0 | 2014 | Legado. Só se herdar. |
| OpenAPI 3.0.x | 2017 | Muito comum. Usa um *subset divergente* de JSON Schema. |
| **OpenAPI 3.1.x** | 2021 | **Use esta.** 100% JSON Schema 2020-12. |
| OpenAPI 3.2 | recente | Ainda pouco suportada pelo ferramental. |

**Por que 3.1 e não 3.0:** o 3.0 inventou um dialeto próprio "parecido com JSON Schema, mas não igual". Isso significa que schema de OpenAPI 3.0 não valida com validador de JSON Schema. O 3.1 acabou com essa esquizofrenia — é JSON Schema de verdade. Além disso ganhou `webhooks`, `summary` no `info` e `type` com múltiplos valores.

**A pegadinha:** algumas ferramentas ainda só falam 3.0. O **API Gateway da AWS importa 3.0 nativamente e tem suporte parcial a 3.1** — na dúvida, valide sua importação cedo. Se der problema, o `redocly bundle` converte 3.1 → 3.0.

> ✅ **Checkpoint do módulo 0**
> - OpenAPI é um arquivo, não um framework.
> - O valor está em ser legível por máquina, não em ser bonito.
> - Use 3.1.

---

## Módulo 1 — Setup

### Prática

Você precisa só de Node. Nada de instalar global — use `npx`.

```bash
mkdir curso-openapi && cd curso-openapi
```

As 3 ferramentas que vamos usar o curso inteiro:

```bash
# 1. Validar o arquivo (o compilador do OpenAPI)
npx @stoplight/spectral-cli@6 lint openapi.yaml

# 2. Ver a doc renderizada (abre no browser, recarrega ao salvar)
npx @redocly/cli@latest preview-docs openapi.yaml

# 3. Subir um mock server a partir do contrato
npx @stoplight/prism-cli@5 mock openapi.yaml
```

**Editor:** VS Code + extensão **OpenAPI (Swagger) Editor** (42Crunch) ou **Redocly OpenAPI**. Dão autocomplete e validação enquanto você digita. Sem isso, escrever OpenAPI é sofrido.

### Dica de fluxo

Deixe **3 terminais abertos** durante o curso:

```bash
# terminal 1 — validação contínua
watch -n 2 'npx @stoplight/spectral-cli@6 lint openapi.yaml'

# terminal 2 — preview da doc
npx @redocly/cli@latest preview-docs openapi.yaml

# terminal 3 — mock
npx @stoplight/prism-cli@5 mock openapi.yaml
```

Você escreve YAML e vê o resultado nos três em tempo real. É esse loop que faz o aprendizado grudar.

---

## Módulo 2 — O menor documento válido

### Conceito

Um documento OpenAPI tem **3 campos obrigatórios no topo**:

| Campo | O que é |
|---|---|
| `openapi` | A versão da *spec* (não da sua API). String, tipo `3.1.0`. |
| `info` | Metadados da API. Dentro, `title` e `version` são obrigatórios. |
| `paths` | Os endpoints. Pode estar vazio (`{}`), mas precisa existir. |

> ⚠️ Primeira confusão clássica: **`openapi: 3.1.0` é a versão da especificação. `info.version: 1.0.0` é a versão da SUA API.** São coisas diferentes e independentes.

### Prática

Crie `openapi.yaml`:

```yaml
openapi: 3.1.0

info:
  title: API de Talhões
  version: 1.0.0

paths: {}
```

Valide:

```bash
npx @stoplight/spectral-cli@6 lint openapi.yaml
```

Você vai ver warnings (falta `description`, falta `servers`...), mas **não erros**. Este documento é válido.

### O `info` completo

```yaml
info:
  title: API de Talhões
  version: 1.0.0
  summary: Consulta de talhões por propriedade rural.      # 3.1+, uma linha
  description: |                                           # aceita Markdown
    Retorna os talhões de uma propriedade a partir do código CAR.

    ## Autenticação
    Bearer token com scope `talhoes:read`.
  contact:
    name: Squad Modelagem
    email: squad@empresa.com.br
  license:
    name: Proprietário — uso interno
```

O `description` **aceita Markdown completo** e é renderizado no topo do Redoc. É aqui que boa parte da narrativa para o time de negócio mora — tabelas, listas, links, tudo funciona.

### `servers`

```yaml
servers:
  - url: https://api-dev.empresa.com.br
    description: Desenvolvimento
  - url: https://api.empresa.com.br
    description: Produção
```

O Swagger UI usa isso no dropdown do "Try it out". O Prism usa para saber o base path.

Dá para parametrizar:

```yaml
servers:
  - url: https://api-{ambiente}.empresa.com.br
    variables:
      ambiente:
        enum: [dev, hml, prod]
        default: dev
```

### Exercício 2

Escreva um `openapi.yaml` com:
1. Versão da spec 3.1.0, versão da API 0.1.0
2. Título "API de Talhões", um `summary` de uma linha e um `description` com um cabeçalho Markdown
3. Contato da sua squad
4. Dois servers (dev e prod), ambos HTTPS
5. `paths` vazio

Rode o lint. Deve passar sem erros.

<details>
<summary><b>Gabarito</b></summary>

```yaml
openapi: 3.1.0

info:
  title: API de Talhões
  version: 0.1.0
  summary: Consulta de talhões por propriedade rural.
  description: |
    ## Visão geral

    Retorna os talhões de uma propriedade rural a partir do código CAR.
  contact:
    name: Squad Modelagem
    email: squad-modelagem@empresa.com.br

servers:
  - url: https://api-dev.empresa.com.br
    description: Desenvolvimento
  - url: https://api.empresa.com.br
    description: Produção

paths: {}
```
</details>

> ✅ **Checkpoint do módulo 2**
> `openapi` + `info` + `paths` = documento válido. `openapi` ≠ `info.version`.

---

## Módulo 3 — Paths e operações

### Conceito

```yaml
paths:                          # ← objeto: chave = path, valor = Path Item
  /v1/talhoes:                  # ← Path Item
    get:                        # ← Operation (o método HTTP, minúsculo)
      summary: Lista talhões
      responses:                # ← obrigatório dentro de uma Operation
        '200':
          description: OK
```

Três níveis: **`paths` → Path Item → Operation**.

Regras:
- A chave do path **começa com `/`**.
- Métodos em **minúsculo**: `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `trace`.
- Todo Operation **precisa** de `responses` com pelo menos uma resposta.
- Os códigos HTTP vão **entre aspas**: `'200'`, não `200`. Em YAML, `200:` sem aspas vira o *inteiro* 200 e a spec exige string. Muita ferramenta perdoa; algumas não. Sempre use aspas.

### Path templating

Variável no path vai entre chaves:

```yaml
paths:
  /v1/propriedades/{codigoCar}/talhoes:
    get: ...
```

**Toda variável no path exige um `parameter` correspondente com `in: path` e `required: true`.** Se declarar `{codigoCar}` e não declarar o parâmetro, o documento é inválido.

### Modelando recursos, não ações

Esta é a parte de *design* que o OpenAPI não valida para você, mas define a qualidade da API:

| ❌ Ruim | ✅ Bom |
|---|---|
| `GET /v1/getTalhoes` | `GET /v1/talhoes` |
| `POST /v1/criarTalhao` | `POST /v1/talhoes` |
| `GET /v1/talhao/deletar/{id}` | `DELETE /v1/talhoes/{id}` |
| `GET /v1/talhao` (lista) | `GET /v1/talhoes` (plural para coleção) |

O **verbo é o método HTTP**. O path é **substantivo, plural, kebab-case**.

O par canônico de leitura:

```
GET /v1/talhoes            → coleção (lista paginada)
GET /v1/talhoes/{talhaoId} → item individual
```

### `operationId`

```yaml
    get:
      operationId: listTalhoes
```

Identificador **único no documento inteiro**. Parece burocracia, mas:
- vira **nome de método no SDK gerado** (`client.listTalhoes()`);
- vira nome de teste de contrato;
- é como o Spectral e o oasdiff referenciam a operação.

Convenção: **camelCase**, verbo + recurso. `listTalhoes`, `getTalhaoById`, `createTalhao`.

### `tags`

```yaml
    get:
      tags: [Talhões]
```

Agrupa operações no menu lateral do Redoc. Com 3 endpoints não faz diferença; com 40, é o que torna a doc navegável. Declare as tags no topo para dar descrição a elas:

```yaml
tags:
  - name: Talhões
    description: Operações de consulta de talhões.
  - name: Propriedades
    description: Operações de consulta de propriedades rurais.
```

A **ordem** que você declara aqui é a ordem do menu no Redoc.

### Prática

```yaml
openapi: 3.1.0

info:
  title: API de Talhões
  version: 0.1.0

tags:
  - name: Talhões
    description: Operações de consulta de talhões.

paths:
  /v1/talhoes:
    get:
      tags: [Talhões]
      summary: Lista talhões
      description: Retorna a lista paginada de talhões visíveis para o usuário.
      operationId: listTalhoes
      responses:
        '200':
          description: Lista de talhões.
```

Rode o preview e veja o menu aparecer:

```bash
npx @redocly/cli@latest preview-docs openapi.yaml
```

### Exercício 3

Adicione ao documento acima um segundo endpoint: **detalhe de um talhão por ID**.
- Path com templating
- `tags`, `summary`, `description`, `operationId`
- Responses `'200'` e `'404'`

(Ainda vai faltar declarar o parâmetro — o lint vai reclamar. É de propósito, resolvemos no módulo 4.)

<details>
<summary><b>Gabarito</b></summary>

```yaml
paths:
  /v1/talhoes:
    get:
      tags: [Talhões]
      summary: Lista talhões
      description: Retorna a lista paginada de talhões visíveis para o usuário.
      operationId: listTalhoes
      responses:
        '200':
          description: Lista de talhões.

  /v1/talhoes/{talhaoId}:
    get:
      tags: [Talhões]
      summary: Detalha um talhão
      description: Retorna um talhão pelo identificador único.
      operationId: getTalhaoById
      responses:
        '200':
          description: Talhão encontrado.
        '404':
          description: Talhão não encontrado.
```

O lint acusa `path-params` — falta declarar `talhaoId`. Próximo módulo.
</details>

> ✅ **Checkpoint do módulo 3**
> Path = substantivo plural. Verbo = método HTTP. `operationId` vira nome de método no SDK. Códigos HTTP entre aspas.

---

## Módulo 4 — Parâmetros e obrigatoriedade

Este é **o módulo que mais importa para o seu refinamento**. É aqui que "campo obrigatório vs. opcional" vira contrato.

### Conceito

Um Parameter Object tem 4 campos que importam:

```yaml
parameters:
  - name: talhaoId          # nome exato que vai na URL
    in: path                # onde vive: path | query | header | cookie
    required: true          # obrigatório?
    description: ...        # o que o negócio lê
    schema:                 # o TIPO vive aqui dentro
      type: string
```

### `in` — os 4 lugares

| `in` | Onde aparece | `required` |
|---|---|---|
| `path` | `/v1/talhoes/{talhaoId}` | **Sempre `true`.** Obrigatório e a spec exige. |
| `query` | `/v1/talhoes?status=ATIVO` | `true` ou `false`. Default: `false`. |
| `header` | `X-Request-Id: abc` | `true` ou `false`. |
| `cookie` | Raro em API. | — |

> ⚠️ **Nunca** declare `Authorization`, `Content-Type` ou `Accept` como `header` parameter. Eles são tratados por `securitySchemes` e por `content`. Declarar na mão é erro e o Spectral acusa.

### A confusão nº 1 do OpenAPI: dois `required` diferentes

Isto pega **todo mundo**. Existem dois `required` que não têm nada a ver um com o outro:

```yaml
# 1) Em PARAMETER → é um BOOLEANO. "este parâmetro é obrigatório?"
parameters:
  - name: status
    in: query
    required: false        # ← boolean

# 2) Em SCHEMA → é uma LISTA DE NOMES. "quais propriedades deste objeto são obrigatórias?"
schemas:
  Talhao:
    type: object
    required: [id, areaHa]   # ← array de strings
    properties:
      id: { type: string }
      areaHa: { type: number }
      cultura: { type: string }   # não está no required → opcional
```

**Regra mental:**
- `required` em **entrada** (parameter) = booleano, campo a campo.
- `required` em **saída** (schema) = lista, no objeto pai.

Uma propriedade **não** tem `required: true` dentro dela. Quem declara é o objeto pai, na lista.

### `required` explícito — a disciplina que salva o refinamento

A spec diz que `required` em query param, se omitido, é `false`. **Mas escreva sempre.** Motivo:

```yaml
# Isto é ambíguo para quem lê no refinamento:
- name: status
  in: query
  # ...o PO omitiu porque é opcional, ou porque esqueceu de decidir?

# Isto é uma decisão registrada:
- name: status
  in: query
  required: false
```

No ruleset Spectral que você já tem, a regra `parameter-required-explicit` transforma isso em erro de CI.

### `default` — e a pegadinha

```yaml
- name: limit
  in: query
  required: false
  description: Itens por página.
  schema:
    type: integer
    minimum: 1
    maximum: 100
    default: 20        # ← dentro do SCHEMA, não do parameter
```

⚠️ **`default` vive dentro de `schema`**, junto com `type`. Não no nível do parameter. E `default` **é documentação, não comportamento** — nenhuma ferramenta preenche o valor por você. Sua Lambda precisa implementar o default. O OpenAPI só *declara* qual é.

⚠️ **`default` + `required: true` é contraditório.** Se é obrigatório, não tem default. Algumas ferramentas dão erro; todas dão confusão.

### Validação no schema do parâmetro

É aqui que o contrato ganha dentes:

```yaml
- name: codigoCar
  in: path
  required: true
  description: Código CAR da propriedade, formato SICAR.
  schema:
    type: string
    pattern: '^[A-Z]{2}-\d{7}-[A-F0-9]{32}$'
  example: MG-3106200-A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6

- name: areaMinHa
  in: query
  required: false
  description: Área mínima do talhão, em hectares.
  schema:
    type: number
    minimum: 0
    exclusiveMaximum: 100000

- name: status
  in: query
  required: false
  description: Situação do talhão.
  schema:
    type: string
    enum: [ATIVO, INATIVO, EM_ANALISE]
```

Ferramentas de validação: `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`, `minLength`, `maxLength`, `pattern` (regex), `enum`, `format`.

**Isso não é enfeite.** Com `x-amazon-apigateway-request-validator: params-only`, o **API Gateway valida antes de invocar a Lambda** — requisição inválida nem chega no seu código, e você não paga a invocação.

### Parâmetro que aceita lista

```yaml
- name: status
  in: query
  required: false
  description: Filtra por uma ou mais situações.
  schema:
    type: array
    items:
      type: string
      enum: [ATIVO, INATIVO, EM_ANALISE]
  style: form
  explode: true     # → ?status=ATIVO&status=INATIVO
  # explode: false  → ?status=ATIVO,INATIVO
```

`style` + `explode` definem a serialização. O default para query é `form` + `explode: true`. Se seu backend só entende `?status=ATIVO,INATIVO`, precisa de `explode: false`.

### Prática

```yaml
paths:
  /v1/talhoes:
    get:
      tags: [Talhões]
      summary: Lista talhões
      description: Retorna a lista paginada de talhões visíveis para o usuário.
      operationId: listTalhoes
      parameters:
        - name: status
          in: query
          required: false
          description: Filtra pela situação do talhão. Se omitido, retorna todas.
          schema:
            type: string
            enum: [ATIVO, INATIVO, EM_ANALISE]
          example: ATIVO
        - name: limit
          in: query
          required: false
          description: Quantidade de itens por página.
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
          example: 50
      responses:
        '200':
          description: Lista de talhões.

  /v1/talhoes/{talhaoId}:
    get:
      tags: [Talhões]
      summary: Detalha um talhão
      description: Retorna um talhão pelo identificador único.
      operationId: getTalhaoById
      parameters:
        - name: talhaoId
          in: path
          required: true
          description: Identificador único do talhão.
          schema:
            type: string
            format: uuid
          example: f47ac10b-58cc-4372-a567-0e02b2c3d479
      responses:
        '200':
          description: Talhão encontrado.
        '404':
          description: Talhão não encontrado.
```

Agora o lint para de reclamar de `path-params`.

### Exercício 4

Adicione ao `listTalhoes`:
1. `codigoCar` — query, **obrigatório**, string com `pattern` de CAR
2. `areaMinHa` — query, opcional, number, mínimo 0
3. `nextToken` — query, opcional, string, máximo 2048 caracteres

Depois responda sem olhar: **por que `default: 20` está dentro de `schema` e `required: false` está fora?**

<details>
<summary><b>Gabarito</b></summary>

```yaml
      parameters:
        - name: codigoCar
          in: query
          required: true
          description: Código CAR da propriedade, formato SICAR.
          schema:
            type: string
            pattern: '^[A-Z]{2}-\d{7}-[A-F0-9]{32}$'
          example: MG-3106200-A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6

        - name: areaMinHa
          in: query
          required: false
          description: Área mínima do talhão, em hectares.
          schema:
            type: number
            minimum: 0
          example: 10.5

        - name: nextToken
          in: query
          required: false
          description: Cursor opaco devolvido em `pagination.nextToken` da chamada anterior.
          schema:
            type: string
            maxLength: 2048
```

**Por quê:** `required` é uma propriedade **do parâmetro** — fala sobre a requisição HTTP. `default`, `type`, `minimum`, `enum` são propriedades **do valor** — falam sobre o dado. `schema` é a fronteira entre "o que o HTTP transporta" e "o que o dado é".
</details>

> ✅ **Checkpoint do módulo 4**
> `required` em parameter = boolean. `required` em schema = lista de nomes. `default` vive no `schema` e é só declaração — você implementa. Sempre escreva `required` explicitamente.

---

## Módulo 5 — Schemas — o coração

**90% do OpenAPI 3.1 é JSON Schema.** Aprendeu Schema, aprendeu OpenAPI. E o conhecimento é transferível: o mesmo JSON Schema você usa em validação de config, em structured output de LLM, em Pydantic.

### Tipos

```yaml
type: string    # texto
type: number    # decimal
type: integer   # inteiro
type: boolean   # true/false
type: array     # lista → exige `items`
type: object    # objeto → normalmente com `properties`
type: 'null'    # nulo (entre aspas! `null` puro em YAML vira nil)
```

### `format` — anotação, não validação

```yaml
type: string
format: uuid          # date, date-time, email, uri, hostname, ipv4, byte, binary, password
```

⚠️ **`format` é, por padrão, apenas anotação.** A maioria dos validadores JSON Schema **não valida** `format` a menos que configurados para isso. Se você precisa de garantia, use `pattern`:

```yaml
type: string
format: date          # documenta a intenção
pattern: '^\d{4}-\d{2}-\d{2}$'   # garante o formato
```

Na prática: `format` é ótimo para gerador de SDK (vira `UUID` em Python, `Date` em TS) e para documentação. Para validação real, `pattern`.

### Objetos e a lista `required`

```yaml
Talhao:
  type: object
  title: Talhão
  description: Representação de um talhão de uma propriedade rural.
  required: [id, areaHa, status]     # ← quais propriedades SEMPRE vêm
  additionalProperties: false        # ← proíbe campos não declarados
  properties:
    id:
      type: string
      format: uuid
      description: Identificador único do talhão.
    areaHa:
      type: number
      description: Área em hectares, projeção SIRGAS 2000 (EPSG:4674).
      minimum: 0
    status:
      type: string
      enum: [ATIVO, INATIVO, EM_ANALISE]
      description: Situação do talhão.
    cultura:
      type: string
      description: Cultura plantada. Ausente quando não informada.
```

`cultura` **não** está em `required` → é opcional → pode não vir no JSON.

### `additionalProperties` — a decisão estratégica

```yaml
additionalProperties: false   # JSON com campo não declarado → INVÁLIDO
additionalProperties: true    # (default) qualquer campo extra é aceito
```

**Trade-off real, e você precisa decidir consciente:**

| | `false` | `true` (default) |
|---|---|---|
| Contrato | Fechado, previsível | Aberto |
| Validação de **request** | ✅ Use. Pega typo do cliente (`{"limite": 20}` em vez de `{"limit": 20}`) | Aceita lixo silenciosamente |
| Validação de **response** | ⚠️ Cuidado. **Adicionar campo novo vira breaking change** para clientes com validação estrita | Você evolui sem quebrar ninguém |

**Recomendação:** `false` em request, e em response só se a API for interna (`x-audience: internal`). Para API pública, deixe o response aberto.

### `null` — a diferença 3.0 vs 3.1

```yaml
# OpenAPI 3.0 (dialeto próprio):
dataColheita:
  type: string
  format: date
  nullable: true          # ← palavra que só existe no 3.0

# OpenAPI 3.1 (JSON Schema puro):
dataColheita:
  type: [string, 'null']  # ← union type
  format: date
```

`nullable` **não existe** no 3.1. Se você copiar exemplo de blog antigo, vai levar erro aqui.

⚠️ **Aspas em `'null'` são obrigatórias.** Em YAML, `null` sem aspas vira o valor nulo, e `type: [string, null]` vira `type: ["string", None]` — inválido.

### Ausente ≠ `null` — a distinção que vira bug

Esta é a fonte clássica de bug de contrato, e é decisão de refinamento:

```json
// A) campo AUSENTE  → "não se aplica / não foi retornado"
{ "id": "abc", "areaHa": 42.7 }

// B) campo NULL     → "se aplica, mas não tem valor conhecido"
{ "id": "abc", "areaHa": 42.7, "dataColheita": null }
```

Como declarar cada um:

```yaml
required: [id, areaHa]     # dataColheita fora da lista → pode ser AUSENTE

properties:
  dataColheita:
    type: [string, 'null'] # e quando vier, pode ser NULL
    format: date
```

Combinando:

| Comportamento | `required`? | `type` |
|---|---|---|
| Sempre vem, nunca null | ✅ na lista | `string` |
| Sempre vem, pode ser null | ✅ na lista | `[string, 'null']` |
| Pode não vir, nunca null | ❌ fora | `string` |
| Pode não vir, e pode ser null | ❌ fora | `[string, 'null']` |

**Decida isso campo a campo no refinamento.** Escreva na tabela do dicionário de dados. É a diferença entre o front fazer `if (x)` e `if (x !== undefined)`.

### `enum` — e como documentar

```yaml
StatusTalhao:
  type: string
  title: Situação do talhão
  description: |
    - `ATIVO`      — talhão em uso na safra corrente
    - `INATIVO`    — talhão desativado pelo produtor
    - `EM_ANALISE` — aguardando validação do CAR
  enum: [ATIVO, INATIVO, EM_ANALISE]
```

O `description` com a lista Markdown é **o que o negócio lê no Redoc**. Enum sem descrição de cada valor é enum inútil — ninguém sabe o que `EM_ANALISE` significa.

⚠️ **Adicionar valor a enum de response é breaking change** para clientes que validam estritamente. Combine isso com o consumidor antes.

### Composição: `allOf`, `oneOf`, `anyOf`

```yaml
# allOf = E (herança / mixin). Mescla todos os schemas.
TalhaoDetalhado:
  allOf:
    - $ref: '#/components/schemas/Talhao'
    - type: object
      properties:
        geometria:
          type: string
          description: Geometria do talhão em WKT.

# oneOf = XOR. Casa com EXATAMENTE um.
- oneOf:
    - $ref: '#/components/schemas/TalhaoSoja'
    - $ref: '#/components/schemas/TalhaoCafe'
  discriminator:
    propertyName: cultura     # ajuda o gerador de SDK a escolher a classe

# anyOf = OU. Casa com um ou mais.
```

Na prática: **`allOf` é 90% do uso** (composição/herança). `oneOf` aparece em resposta polimórfica. `anyOf` é raro.

### Exercício 5

Modele o schema `Talhao` com:
1. `id` — uuid, sempre presente
2. `nome` — string 1–120 chars, sempre presente
3. `areaHa` — number ≥ 0, sempre presente
4. `status` — enum `ATIVO`/`INATIVO`/`EM_ANALISE`, sempre presente, com cada valor descrito
5. `cultura` — string, **pode não vir**
6. `dataColheita` — date, **sempre vem, mas pode ser null**
7. Contrato fechado

<details>
<summary><b>Gabarito</b></summary>

```yaml
components:
  schemas:
    StatusTalhao:
      type: string
      title: Situação do talhão
      description: |
        - `ATIVO`      — talhão em uso na safra corrente
        - `INATIVO`    — talhão desativado pelo produtor
        - `EM_ANALISE` — aguardando validação do CAR
      enum: [ATIVO, INATIVO, EM_ANALISE]

    Talhao:
      type: object
      title: Talhão
      description: Representação de um talhão de uma propriedade rural.
      required: [id, nome, areaHa, status, dataColheita]
      additionalProperties: false
      properties:
        id:
          type: string
          format: uuid
          description: Identificador único do talhão.
        nome:
          type: string
          description: Nome do talhão dado pelo produtor.
          minLength: 1
          maxLength: 120
        areaHa:
          type: number
          description: Área em hectares (SIRGAS 2000 / EPSG:4674).
          minimum: 0
        status:
          $ref: '#/components/schemas/StatusTalhao'
        cultura:
          type: string
          description: Cultura plantada. Campo ausente quando não informada.
        dataColheita:
          type: [string, 'null']
          format: date
          description: Data prevista de colheita. `null` quando ainda não definida.
```

**Sacadas:** `dataColheita` está em `required` (sempre vem) **e** aceita `'null'` (pode não ter valor) — os dois ao mesmo tempo. `cultura` está fora de `required` (pode não vir). `status` virou schema próprio para poder ser reutilizado.
</details>

> ✅ **Checkpoint do módulo 5**
> OpenAPI 3.1 = JSON Schema. `nullable` não existe → use `type: [string, 'null']`. Ausente ≠ null, e isso se decide no refinamento. `format` documenta; `pattern` valida.

---

## Módulo 6 — Responses e exemplos

### Conceito

```yaml
responses:
  '200':                             # ← código HTTP entre aspas
    description: Lista de talhões.   # ← OBRIGATÓRIO
    headers:
      X-Trace-Id:
        description: Identificador de rastreio.
        schema: { type: string }
    content:                         # ← opcional (204 não tem)
      application/json:              # ← media type
        schema:
          $ref: '#/components/schemas/TalhaoList'
        examples:
          primeiraPagina:
            summary: Primeira página, há mais resultados
            value:
              data: [...]
```

`description` é o **único campo obrigatório** de um Response. Ele aparece no Redoc — escreva algo útil, não "OK".

### A confusão nº 2: `example` vs `examples`

Isto confunde **todo mundo**, porque a resposta depende de **onde** você está. Decore esta tabela:

| Onde | `example` (singular) | `examples` (plural) |
|---|---|---|
| **Media Type** (dentro de `content`) | um valor solto | **mapa** de nome → Example Object (com `summary`/`value`) |
| **Parameter** | um valor solto | **mapa** de nome → Example Object |
| **Schema** (3.1) | ⚠️ *deprecated* | **array** de valores (veio do JSON Schema) |

Ou seja: `examples` é **mapa** em Media Type/Parameter, mas **array** dentro de Schema. Não é você que está confuso — a spec é assim mesmo.

```yaml
# Em MEDIA TYPE → mapa, com summary. Vira dropdown no Swagger UI.
content:
  application/json:
    schema:
      $ref: '#/components/schemas/Talhao'
    examples:
      ativo:
        summary: Talhão ativo com cultura definida
        value:
          id: f47ac10b-58cc-4372-a567-0e02b2c3d479
          nome: Talhão Norte
          areaHa: 42.7
          status: ATIVO
          cultura: SOJA
          dataColheita: '2026-03-15'
      semColheita:
        summary: Talhão sem data de colheita definida
        value:
          id: 9c8b7a65-4321-4def-8abc-1234567890ab
          nome: Talhão Sul
          areaHa: 18.2
          status: EM_ANALISE
          dataColheita: null

# Em SCHEMA (3.1) → array, sem summary
properties:
  areaHa:
    type: number
    examples: [42.7]      # ← array!
```

**Regra prática:** ponha exemplos no **Media Type**. É lá que rende — vira dropdown na doc e vira resposta do mock server.

### Por que exemplos são o item mais subestimado

Exemplo não é enfeite. Exemplo é:

1. **O que o negócio realmente lê.** Ninguém do time de negócio lê `type: string, format: date-time`. Todo mundo entende `"2026-03-15T10:30:00Z"`.
2. **O que o mock server devolve.** Sem exemplo, o Prism inventa valores aleatórios e o front testa com lixo.
3. **Onde o bug aparece no refinamento.** Você escreve o exemplo, mostra pro PO, e ele diz "espera, area vem em hectare ou alqueire?". Esse é o momento que o exemplo se paga.

**Escreva pelo menos 3 exemplos por endpoint de coleção:** caso feliz, caso vazio, caso de borda.

```yaml
        examples:
          primeiraPagina:
            summary: Primeira página, há mais resultados
            value:
              data:
                - { id: f47ac10b-58cc-4372-a567-0e02b2c3d479, nome: Talhão Norte, areaHa: 42.7, status: ATIVO, dataColheita: '2026-03-15' }
              pagination: { nextToken: 'eyJrIjoiZjQ3In0=', total: 137 }
          vazio:
            summary: Nenhum talhão para o filtro
            value:
              data: []
              pagination: { nextToken: null, total: 0 }
```

O caso **vazio** é o que mais quebra front na produção. Documente-o.

### Envelope: nunca retorne array na raiz

```yaml
# ❌ Array na raiz — você fica preso
TalhaoList:
  type: array
  items: { $ref: '#/components/schemas/Talhao' }

# ✅ Envelope — dá para evoluir
TalhaoList:
  type: object
  required: [data, pagination]
  properties:
    data:
      type: array
      description: Itens da página atual. Array vazio quando não há resultados.
      items:
        $ref: '#/components/schemas/Talhao'
    pagination:
      $ref: '#/components/schemas/Pagination'
```

**Por quê:** com array na raiz, no dia que você precisar devolver `total` ou `nextToken`, **não tem onde colocar** sem breaking change. Com envelope, você adiciona um campo e ninguém quebra.

### Erros: padronize com RFC 9457

Não invente formato de erro. Use **Problem Details for HTTP APIs (RFC 9457)** — media type `application/problem+json`:

```yaml
Problem:
  type: object
  title: Erro (RFC 9457)
  required: [type, title, status]
  properties:
    type:
      type: string
      format: uri
      description: URI que identifica o tipo do erro.
    title:
      type: string
      description: Resumo legível e estável do tipo do erro.
    status:
      type: integer
      description: Código HTTP, repetido no corpo.
    detail:
      type: string
      description: Explicação específica desta ocorrência.
    instance:
      type: string
      description: Path da requisição que gerou o erro.
    traceId:
      type: string
      description: ID de rastreio (X-Ray). Informe ao acionar o suporte.
```

Diferença entre `title` e `detail`: `title` é **estável** (o cliente pode fazer `switch` nele), `detail` é **específico da ocorrência** (para humano ler). Não faça o cliente parsear `detail`.

### Exercício 6

Complete o `listTalhoes` com:
1. Response `'200'` com schema `TalhaoList` (envelope) e **3 exemplos**: primeira página, última página, vazio
2. Response `'400'` com `application/problem+json`
3. Header `X-Trace-Id` no 200

<details>
<summary><b>Gabarito</b></summary>

```yaml
      responses:
        '200':
          description: Lista paginada de talhões.
          headers:
            X-Trace-Id:
              description: Identificador de rastreio da requisição.
              schema: { type: string }
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TalhaoList'
              examples:
                primeiraPagina:
                  summary: Primeira página, há mais resultados
                  value:
                    data:
                      - id: f47ac10b-58cc-4372-a567-0e02b2c3d479
                        nome: Talhão Norte
                        areaHa: 42.7
                        status: ATIVO
                        cultura: SOJA
                        dataColheita: '2026-03-15'
                    pagination:
                      nextToken: eyJrIjoiZjQ3YWMxMGIifQ==
                      total: 137
                ultimaPagina:
                  summary: Última página
                  value:
                    data:
                      - id: 9c8b7a65-4321-4def-8abc-1234567890ab
                        nome: Talhão Sul
                        areaHa: 18.2
                        status: INATIVO
                        dataColheita: null
                    pagination:
                      nextToken: null
                      total: 137
                vazio:
                  summary: Nenhum talhão para o filtro
                  value:
                    data: []
                    pagination:
                      nextToken: null
                      total: 0
        '400':
          description: Requisição inválida — parâmetro ausente ou fora da faixa.
          content:
            application/problem+json:
              schema:
                $ref: '#/components/schemas/Problem'
              example:
                type: https://api.empresa.com.br/errors/validation-error
                title: Parâmetro inválido
                status: 400
                detail: "O campo 'limit' deve estar entre 1 e 100."
                instance: /v1/talhoes
                traceId: 1-67ab-c123def456
```
</details>

> ✅ **Checkpoint do módulo 6**
> `description` é obrigatório no response. `examples` é mapa em Media Type e array em Schema. Sempre envelope, nunca array na raiz. Documente o caso vazio.

---

## Módulo 7 — `$ref` e `components`

### Conceito

Repare que no módulo 6 você repetiu o schema de erro em cada operação. Com 10 endpoints × 6 códigos de erro = 60 blocos duplicados. `$ref` resolve.

```yaml
$ref: '#/components/schemas/Talhao'
#      ↑ ↑          ↑       ↑
#      | |          |       └─ nome
#      | |          └───────── seção
#      | └──────────────────── raiz do bloco reutilizável
#      └────────────────────── "este documento"
```

`$ref` é **JSON Reference**: um ponteiro. Onde tem `$ref`, a ferramenta substitui pelo conteúdo apontado.

### As seções de `components`

```yaml
components:
  schemas: {}          # modelos de dados
  parameters: {}       # parâmetros reutilizáveis
  responses: {}        # respostas inteiras (ótimo para erros)
  requestBodies: {}    # corpos de request
  headers: {}          # headers de response
  examples: {}         # exemplos nomeados
  securitySchemes: {}  # esquemas de auth
```

Nada em `components` é exposto sozinho — só existe quando referenciado. Chaves devem casar `^[a-zA-Z0-9._-]+$`.

### Antes e depois

```yaml
# ANTES — 60 linhas duplicadas por operação
responses:
  '400':
    description: Requisição inválida
    content:
      application/problem+json:
        schema:
          type: object
          properties:
            type: { type: string }
            title: { type: string }
            # ... repetido em cada endpoint

# DEPOIS — 1 linha
responses:
  '400': { $ref: '#/components/responses/BadRequest' }
  '401': { $ref: '#/components/responses/Unauthorized' }
  '500': { $ref: '#/components/responses/InternalError' }
```

E lá embaixo, uma vez só:

```yaml
components:
  responses:
    BadRequest:
      description: Requisição inválida — parâmetro ausente, mal formatado ou fora da faixa.
      content:
        application/problem+json:
          schema: { $ref: '#/components/schemas/Problem' }
          example:
            type: https://api.empresa.com.br/errors/validation-error
            title: Parâmetro inválido
            status: 400
```

### Parâmetros reutilizáveis

`limit` e `nextToken` aparecem em **toda** coleção. Declare uma vez:

```yaml
components:
  parameters:
    Limit:
      name: limit
      in: query
      required: false
      description: Quantidade de itens por página.
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20
      example: 50
```

E use:

```yaml
      parameters:
        - $ref: '#/components/parameters/Limit'
        - $ref: '#/components/parameters/NextToken'
```

> ⚠️ A **chave** em `components.parameters` (`Limit`, PascalCase) não é o **nome** do parâmetro (`limit`, camelCase). São coisas diferentes: a chave é o "endereço" do `$ref`, o `name` é o que vai na URL.

### `$ref` com irmãos — mudou no 3.1

```yaml
# OpenAPI 3.0: irmãos de $ref são IGNORADOS silenciosamente
status:
  $ref: '#/components/schemas/StatusTalhao'
  description: Isto some no 3.0!   # ← ignorado

# OpenAPI 3.1: irmãos funcionam (é JSON Schema 2020-12)
status:
  $ref: '#/components/schemas/StatusTalhao'
  description: Isto funciona no 3.1
```

Ainda assim, **muita ferramenta implementa isso mal**. Se precisa sobrescrever, o caminho seguro é `allOf`:

```yaml
status:
  allOf:
    - $ref: '#/components/schemas/StatusTalhao'
  description: Situação atual do talhão nesta safra.
```

### `$ref` para arquivo externo

```yaml
schema:
  $ref: './schemas/talhao.yaml'
  # ou
  $ref: './common.yaml#/components/schemas/Problem'
```

Útil para compartilhar `Problem` e `Pagination` entre APIs da empresa. **Mas:** nem toda ferramenta resolve ref externo, e o API Gateway **não** resolve. Antes de importar, faça bundle:

```bash
npx @redocly/cli@latest bundle openapi.yaml -o openapi-bundled.yaml
```

O `bundle` inlineia os refs externos e mantém os internos. É o formato que você entrega para o API Gateway.

### Quando NÃO usar `$ref`

Não crie `components/schemas/String120`. `$ref` serve para **conceito de negócio reutilizável** (`Talhao`, `Problem`, `Pagination`), não para economizar 2 linhas. Indireção demais deixa o contrato ilegível.

### Exercício 7

Refatore seu documento:
1. `Limit` e `NextToken` → `components/parameters`
2. `Problem` → `components/schemas`
3. `BadRequest`, `NotFound`, `InternalError` → `components/responses`
4. Aplique nos dois endpoints

Compare o tamanho do arquivo antes e depois.

<details>
<summary><b>Gabarito</b></summary>

Estrutura final:

```yaml
paths:
  /v1/talhoes:
    get:
      operationId: listTalhoes
      parameters:
        - $ref: '#/components/parameters/Status'
        - $ref: '#/components/parameters/Limit'
        - $ref: '#/components/parameters/NextToken'
      responses:
        '200':
          description: Lista paginada de talhões.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/TalhaoList' }
              examples: { ... }
        '400': { $ref: '#/components/responses/BadRequest' }
        '500': { $ref: '#/components/responses/InternalError' }

  /v1/talhoes/{talhaoId}:
    get:
      operationId: getTalhaoById
      parameters:
        - $ref: '#/components/parameters/TalhaoId'
      responses:
        '200':
          description: Talhão encontrado.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Talhao' }
        '404': { $ref: '#/components/responses/NotFound' }
        '500': { $ref: '#/components/responses/InternalError' }

components:
  parameters:
    TalhaoId: { ... }
    Status:   { ... }
    Limit:    { ... }
    NextToken:{ ... }
  schemas:
    StatusTalhao: { ... }
    Talhao:       { ... }
    Pagination:   { ... }
    TalhaoList:   { ... }
    Problem:      { ... }
  responses:
    BadRequest:    { ... }
    NotFound:      { ... }
    InternalError: { ... }
```

O arquivo completo está em [`exemplo-final.yaml`](./exemplo-final.yaml).
</details>

> ✅ **Checkpoint do módulo 7**
> `$ref: '#/components/<seção>/<Nome>'`. Reuse conceitos, não linhas. Ref externo precisa de `bundle` antes do API Gateway.

---

## Módulo 8 — Security

### Conceito

Auth tem duas partes: **declarar** o esquema (uma vez) e **aplicar** (global ou por operação).

```yaml
# 1. Declarar
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT emitido pelo Cognito User Pool.

# 2. Aplicar globalmente (vale para TODAS as operações)
security:
  - bearerAuth: []
```

O `[]` é a lista de **scopes**. Vazio para `http`/`apiKey`; preenchido para OAuth2/OIDC.

### Os tipos

```yaml
# Bearer / JWT — o mais comum
bearerAuth:
  type: http
  scheme: bearer
  bearerFormat: JWT

# API Key
apiKeyAuth:
  type: apiKey
  in: header          # header | query | cookie
  name: X-Api-Key     # ⚠️ NUNCA in: query — vaza em access log

# Basic
basicAuth:
  type: http
  scheme: basic

# OAuth2 com scopes
oauth2:
  type: oauth2
  flows:
    clientCredentials:
      tokenUrl: https://auth.empresa.com.br/oauth2/token
      scopes:
        'talhoes:read':  Leitura de talhões
        'talhoes:write': Escrita de talhões

# IAM SigV4 (AWS)
sigv4:
  type: apiKey
  in: header
  name: Authorization
  x-amazon-apigateway-authtype: awsSigv4
```

### Aplicando

```yaml
security:
  - bearerAuth: []          # global: todas as operações

paths:
  /v1/health:
    get:
      security: []          # ← sobrescreve: este endpoint é PÚBLICO
      summary: Health check
```

A lista `security` é um **OU**: qualquer um dos esquemas serve.

```yaml
security:
  - bearerAuth: []   #  OU
  - apiKeyAuth: []
```

Para exigir **E** (os dois juntos), ponha no mesmo item:

```yaml
security:
  - bearerAuth: []
    apiKeyAuth: []   # E — precisa dos dois
```

### Amarrando no API Gateway

Aqui o contrato vira infra:

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      x-amazon-apigateway-authtype: cognito_user_pools
      x-amazon-apigateway-authorizer:
        type: jwt
        jwtConfiguration:
          issuer: https://cognito-idp.sa-east-1.amazonaws.com/sa-east-1_EXEMPLO
          audience:
            - 1exemplo23client45id67
        identitySource: $request.header.Authorization
```

Com isso, o `openapi.yaml` importado no API Gateway **já sobe com o authorizer configurado**. Você escreveu documentação e ganhou infra.

### O par 401/403 — semântica que quase todo mundo erra

| | Significado |
|---|---|
| `401 Unauthorized` | "Não sei **quem** você é." Token ausente, expirado, inválido. |
| `403 Forbidden` | "Sei quem você é, mas **você não pode**." Token válido, sem permissão. |

Os nomes na RFC são péssimos (401 deveria se chamar "Unauthenticated"), mas a semântica é essa.

**A decisão de segurança:** quando o recurso existe mas não é do usuário, retorne **404, não 403**. `403` confirma que o recurso existe — é vazamento de informação. Documente essa escolha:

```yaml
        '404':
          description: |
            Talhão inexistente **ou** fora do escopo de visibilidade do usuário.
            Retornamos 404 (e não 403) para não revelar a existência do recurso.
```

### Exercício 8

1. Declare `bearerAuth` (JWT) e aplique globalmente
2. Adicione `GET /v1/health` público (sem auth)
3. Adicione `'401'` e `'403'` no `listTalhoes`, com descrições que expliquem a diferença

<details>
<summary><b>Gabarito</b></summary>

```yaml
security:
  - bearerAuth: []

paths:
  /v1/health:
    get:
      tags: [Health]
      summary: Health check
      description: Verifica se a API está no ar. Endpoint público.
      operationId: getHealth
      security: []
      responses:
        '200':
          description: API operacional.
          content:
            application/json:
              schema:
                type: object
                required: [status]
                properties:
                  status:
                    type: string
                    enum: [ok]
                    description: Situação da API.
              example: { status: ok }

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT emitido pelo Cognito User Pool.

  responses:
    Unauthorized:
      description: Token ausente, expirado ou inválido. Renove a credencial.
      content:
        application/problem+json:
          schema: { $ref: '#/components/schemas/Problem' }
    Forbidden:
      description: Autenticado, mas o token não possui o scope `talhoes:read`.
      content:
        application/problem+json:
          schema: { $ref: '#/components/schemas/Problem' }
```
</details>

> ✅ **Checkpoint do módulo 8**
> Declare em `securitySchemes`, aplique em `security`. `security: []` na operação = público. 401 = quem é você; 403 = você não pode; 404 = escondendo que existe.

---

## Módulo 9 — O ecossistema (onde o ROI aparece)

Você já sabe escrever OpenAPI. Este módulo é **por que valeu a pena**.

### 1. Mock server — o mais valioso no refinamento

```bash
npx @stoplight/prism-cli@5 mock openapi.yaml
```

```bash
curl "http://localhost:4010/v1/talhoes?limit=10" -H "Authorization: Bearer x"
```

O Prism lê o contrato e devolve **os exemplos que você escreveu**. Consequências:

- O **front integra antes do backend existir**. Paralelismo real.
- Você leva o mock rodando **para a reunião de refinamento**. O PO vê o JSON de verdade e diz "faltou o município" ali, não três sprints depois.
- Dá para forçar cenários:

```bash
# devolver o exemplo "vazio"
curl "http://localhost:4010/v1/talhoes" -H "Prefer: example=vazio"

# devolver um 400
curl "http://localhost:4010/v1/talhoes" -H "Prefer: code=400"
```

Modo **proxy** valida a API real contra o contrato:

```bash
npx @stoplight/prism-cli@5 proxy openapi.yaml https://api-dev.empresa.com.br
```

Toda divergência entre implementação e contrato vira log. É teste de contrato quase de graça.

### 2. Spectral — governança automática

Lint é o **compilador do OpenAPI**. O ruleset é o guia de estilo da guilda executável:

```bash
npx @stoplight/spectral-cli@6 lint openapi.yaml --ruleset .spectral.yaml
```

```yaml
extends: [[spectral:oas, recommended]]

rules:
  no-verbs-in-path:
    description: 'Paths representam recursos, não ações.'
    severity: error
    given: $.paths[*]~              # ← `~` = pega a CHAVE, não o valor
    then:
      function: pattern
      functionOptions:
        notMatch: '\/(get|create|update|delete|list)[A-Za-z-]*(\/|$)'
```

Anatomia de uma regra:
- **`given`** — JSONPath: onde aplicar. O `~` no fim pega a chave.
- **`then.function`** — `truthy`, `defined`, `pattern`, `schema`, `casing`, `length`, `enumeration`, `alphabetical`.
- **`severity`** — `error` quebra o CI; `warn` só avisa.

**A jogada de adoção:** regra nova entra como `warn`, você zera o passivo, depois promove para `error`. Ninguém trava.

Isso resolve o problema real de guilda: **você para de discutir camelCase em code review**. O CI discute.

### 3. Documentação

```bash
npx @redocly/cli@latest preview-docs openapi.yaml           # dev
npx @redocly/cli@latest build-docs openapi.yaml -o index.html   # publica
```

| | Redoc | Swagger UI |
|---|---|---|
| Leitura | ✅ Excelente, 3 colunas | Razoável |
| "Try it out" | ❌ (só na versão paga) | ✅ |
| Público | Negócio | Dev |

**Sirva os dois.** Redoc para o PO ler, Swagger UI para o dev testar.

### 4. Geração de código

```bash
# SDK Python para o consumidor
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml -g python -o ./sdk-python

# Tipos TypeScript para o front
npx openapi-typescript openapi.yaml -o ./types/api.ts

# Modelos Pydantic (útil para validar na Lambda)
pip install datamodel-code-generator
datamodel-codegen --input openapi.yaml --output models.py --output-model-type pydantic_v2.BaseModel
```

O `datamodel-codegen` é o que mais rende no seu contexto: os schemas do contrato viram modelos Pydantic que a Lambda usa para validar. **Contrato e implementação não podem divergir porque saíram do mesmo arquivo.**

### 5. Detecção de breaking change

```bash
docker run --rm -v $(pwd):/specs tufin/oasdiff breaking \
  /specs/openapi-main.yaml /specs/openapi-pr.yaml
```

Compara duas versões e falha se você quebrou o contrato. No CI, isso é a rede de segurança que permite mexer no contrato sem medo.

### 6. API Gateway — o contrato vira infra

```yaml
paths:
  /v1/talhoes:
    get:
      x-amazon-apigateway-request-validator: params-only
      x-amazon-apigateway-integration:
        type: aws_proxy
        httpMethod: POST          # ← SEMPRE POST para Lambda, mesmo em GET
        payloadFormatVersion: '2.0'
        uri:
          Fn::Sub: arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ListTalhoesFunction.Arn}/invocations

x-amazon-apigateway-request-validators:
  params-only:
    validateRequestParameters: true
    validateRequestBody: false
```

> ⚠️ **`httpMethod: POST` em integração Lambda é sempre POST**, mesmo que sua operação seja `GET`. Não é typo: é o método da chamada *do API Gateway para o Lambda*, não do cliente para o gateway. Pega todo mundo na primeira vez.

Importando via SAM:

```yaml
Resources:
  ApiTalhoes:
    Type: AWS::Serverless::Api
    Properties:
      StageName: dev
      DefinitionBody:
        Fn::Transform:
          Name: AWS::Include
          Parameters:
            Location: s3://meu-bucket/openapi.yaml
```

**Consequência:** o `openapi.yaml` deixa de ser documentação e vira **a definição da infra**. Não tem como divergir — é o mesmo arquivo. O validador do gateway rejeita `limit=500` antes de invocar a Lambda: você não paga a invocação e não escreve validação na mão.

Antes de importar, sempre:

```bash
npx @redocly/cli@latest bundle openapi.yaml -o openapi-bundled.yaml
```

### O pipeline completo

```
   openapi.yaml (PR)
        │
        ├─→ spectral lint          → estilo da guilda ok?
        ├─→ oasdiff breaking       → quebrou consumidor?
        ├─→ prism proxy + testes   → implementação bate com o contrato?
        │
     merge em main
        │
        ├─→ redocly build-docs → S3/CloudFront    (negócio lê)
        ├─→ openapi-generator  → SDK publicado    (consumidor usa)
        └─→ bundle → SAM deploy → API Gateway     (vira infra)
```

Um arquivo. Seis saídas. **Esse é o ROI do OpenAPI** — não a documentação bonita.

---

## Módulo 10 — As 8 armadilhas que pegam todo mundo

**1. `nullable: true` no 3.1**
Não existe. É sintaxe 3.0. Use `type: [string, 'null']`.

**2. `null` sem aspas em YAML**
`type: [string, null]` → YAML interpreta como nil → inválido. Sempre `'null'`.

**3. Os dois `required`**
Parameter → booleano. Schema → array de nomes de propriedade. Não são a mesma coisa.

**4. `default` fora do `schema`**
```yaml
- name: limit
  default: 20        # ❌ ignorado silenciosamente
  schema:
    type: integer
    default: 20      # ✅
```
E lembre: `default` é declaração. Sua Lambda implementa.

**5. Código HTTP sem aspas**
`200:` vira inteiro em YAML; a spec quer string. Use `'200'`.

**6. `example` vs `examples`**
Mapa em Media Type/Parameter. Array em Schema (3.1). Se o exemplo não aparece na doc, é quase sempre isto.

**7. `$ref` com irmãos**
No 3.0 os irmãos somem **sem aviso**. Se seu `description` não aparece, é isto. Use `allOf` para sobrescrever com segurança.

**8. Array na raiz do response**
```yaml
schema:
  type: array          # ❌
  items: {...}
```
No dia que precisar de `nextToken`, não tem onde colocar. Sempre `{ data, pagination }`.

### Bônus — as 3 que só aparecem em produção

**9. Ref externo no API Gateway**
Não resolve. `redocly bundle` antes de importar.

**10. `additionalProperties: false` em response de API pública**
Adicionar campo vira breaking change para cliente com validação estrita.

**11. Adicionar valor a enum**
Também é breaking change no response. Cliente com `switch` exaustivo quebra.

---

## Projeto final

Escreva do zero, sem copiar dos módulos, um contrato para **`GET /v1/propriedades/{codigoCar}/talhoes`**:

**Requisitos**
1. OpenAPI 3.1, `info` completo com `contact`, 2 servers HTTPS
2. `codigoCar` — path, obrigatório, com `pattern` de CAR
3. Filtros opcionais: `status` (enum), `culturaAtual` (string), `areaMinHa` (number ≥ 0)
4. Paginação: `limit` (1–100, default 20) e `nextToken`
5. Schema `Talhao` com pelo menos um campo opcional (ausente) e um nullable
6. Response 200 com envelope `{ data, pagination }` e **3 exemplos** (cheio, vazio, última página)
7. Erros 400, 401, 404, 500 com `Problem` (RFC 9457), via `components/responses`
8. `bearerAuth` global
9. Tudo reutilizável em `components`

**Critérios de aceite**

```bash
# 1. passa no lint sem erros
npx @stoplight/spectral-cli@6 lint openapi.yaml --ruleset .spectral.yaml

# 2. o mock devolve seus exemplos
npx @stoplight/prism-cli@5 mock openapi.yaml
curl "http://localhost:4010/v1/propriedades/MG-3106200-A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6/talhoes" \
  -H "Authorization: Bearer x"

# 3. a doc renderiza e um não-técnico entende
npx @redocly/cli@latest build-docs openapi.yaml -o docs.html
```

**O teste final que vale mais que os três:** mostre o Redoc para alguém de negócio e peça para explicar o que o endpoint faz. Se conseguir, seu contrato está bom. Se não, faltou `description` e exemplo — não faltou schema.

Referência completa em [`exemplo-final.yaml`](./exemplo-final.yaml) — mas escreva o seu antes de abrir.

---

## Colinha

```yaml
openapi: 3.1.0                        # versão da SPEC
info:
  title: ...                          # obrigatório
  version: 1.0.0                      # versão da SUA API
servers: [{ url: https://... }]
tags: [{ name: X, description: ... }]
security: [{ bearerAuth: [] }]        # global
paths:
  /v1/recursos:                       # substantivo, plural, kebab-case
    get:                              # método em minúsculo
      tags: [X]
      summary: ...                    # aparece no índice
      description: ...                # aceita Markdown
      operationId: listRecursos       # camelCase, único → nome no SDK
      parameters:
        - name: limit
          in: query                   # path | query | header | cookie
          required: false             # BOOLEANO — sempre explícito
          description: ...
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20               # dentro do SCHEMA
          example: 50
      responses:                      # obrigatório
        '200':                        # ENTRE ASPAS
          description: ...            # obrigatório
          content:
            application/json:
              schema: { $ref: '#/components/schemas/RecursoList' }
              examples:               # MAPA aqui
                caso1: { summary: ..., value: {...} }
        '400': { $ref: '#/components/responses/BadRequest' }
components:
  parameters: {}
  schemas:
    Recurso:
      type: object
      required: [id]                  # ARRAY de nomes
      additionalProperties: false
      properties:
        id:
          type: string
          description: ...
        opcional:
          type: [string, 'null']      # 'null' COM ASPAS (3.1)
  responses: {}
  securitySchemes:
    bearerAuth: { type: http, scheme: bearer, bearerFormat: JWT }
```

| Preciso de... | Uso |
|---|---|
| Validar | `spectral lint openapi.yaml` |
| Ver a doc | `redocly preview-docs openapi.yaml` |
| Mockar | `prism mock openapi.yaml` |
| Testar contra a API real | `prism proxy openapi.yaml https://api...` |
| Achatar refs | `redocly bundle openapi.yaml -o out.yaml` |
| Breaking change | `oasdiff breaking a.yaml b.yaml` |
| SDK Python | `openapi-generator-cli generate -g python` |
| Pydantic | `datamodel-codegen --input openapi.yaml` |
| Tipos TS | `openapi-typescript openapi.yaml -o api.ts` |

---

## Para continuar

| Recurso | Por quê |
|---|---|
| [spec.openapis.org/oas/v3.1.0](https://spec.openapis.org/oas/v3.1.0) | A spec. Densa, mas é a fonte. |
| [json-schema.org/understanding-json-schema](https://json-schema.org/understanding-json-schema) | **O melhor investimento.** 90% do OpenAPI 3.1 é isto. |
| [learn.openapis.org](https://learn.openapis.org) | Tutorial oficial da OpenAPI Initiative. |
| Zalando RESTful API Guidelines | Guia de estilo pragmático, com ruleset Spectral pronto. |
| Google AIP (aip.dev) | Mais opinativo. Bom se houver gRPC no horizonte. |
| RFC 9457 | Problem Details. Curta, leia inteira. |
| AsyncAPI | O irmão para SNS/SQS/Kafka. A sintaxe é quase a mesma. |

**Se for dar isso na guilda:** o módulo 9 é o que converte. Comece por ele — mostre o `prism mock` respondendo, depois volte para a sintaxe. Ninguém se anima com `type: string`; todo mundo se anima quando vê o front integrando contra uma API que ainda não existe.
