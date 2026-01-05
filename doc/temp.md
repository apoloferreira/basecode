
O caminho “certo” é transformar **necessidades de negócio** em **requisitos verificáveis**, depois em **decisões de arquitetura** (com trade-offs explícitos). Em projetos grandes, isso vira um funil:

1. **Descobrir** (entender o problema e o contexto)
2. **Definir** (formalizar requisitos + prioridades + métricas)
3. **Validar** (alinhamento com stakeholders + critérios de aceite)
4. **Traduzir** (requisitos → atributos de qualidade → arquitetura)
5. **Evoluir** (governança de mudanças e rastreabilidade)

Abaixo vai um playbook prático com melhores práticas, metodologias e templates.

---

## 1) Levantamento de requisitos de negócio: como é feito na prática

### A. Preparação (antes das entrevistas)

**Objetivo:** evitar “workshop sem direção”.

* **Mapa de stakeholders (RACI)**: quem decide, quem aprova, quem opera, quem sofre o problema.
* **Entendimento do domínio**: documentos existentes, KPIs, relatórios, processos atuais (AS-IS).
* **Hipóteses iniciais**: “o que achamos que é o problema” (para validar/derrubar rápido).
* **Plano de discovery**:

  * agenda de entrevistas (1:1) e workshops (grupo),
  * artefatos que você vai produzir (BRD/PRD, backlog, C4, NFRs),
  * definição de “pronto para arquitetar”.

**Saída:** agenda, lista de perguntas, stakeholders e “objetivo do discovery” aprovado.

---

### B. Discovery (entrevistas + observação + dados)

Você coleta informação em **três camadas**:

1. **Por quê (objetivos)**

   * Qual resultado de negócio precisa melhorar? (reduzir custo, aumentar receita, reduzir risco, tempo, erro)
   * Como mediremos sucesso? (KPIs / SLAs / OKRs)

2. **O quê (capabilidades e regras)**

   * Quais decisões e regras do negócio existem?
   * Quais entidades, eventos, documentos, exceções?
   * O que entra e sai do processo (inputs/outputs)?

3. **Como hoje (processo atual e restrições)**

   * Sistemas envolvidos, integrações, dados, pessoas, gargalos
   * Restrições regulatórias e de segurança
   * Picos de uso, sazonalidade, volumetria

**Técnicas que funcionam muito bem:**

* **Entrevistas estruturadas** (roteiro fixo) + **5 Whys** (chegar na causa raiz)
* **Event storming** (muito bom p/ domínios complexos)
* **User story mapping** (jornada e priorização visual)
* **Shadowing** (observar operação real: “o que dizem” ≠ “o que fazem”)
* **Análise de dados** (volumes, latência, retrabalho, erros)

**Saída:** mapa do problema, objetivos, jornada/capabilidades, inventário de dados/sistemas.

---

### C. Formalização (transformar em requisitos claros)

Aqui você converte “dor” em itens **testáveis**:

* **Requisitos funcionais**: o sistema deve fazer X.
* **Requisitos não funcionais (NFRs)**: desempenho, disponibilidade, segurança, auditabilidade, custo, observabilidade.
* **Regras de negócio**: validações, cálculos, exceções, políticas.
* **Requisitos de dados**: fontes, qualidade, linhagem, retenção, LGPD, dicionário.
* **Requisitos operacionais**: deploy, rollback, suporte, SRE, runbooks.
* **Restrições**: cloud/provider, tecnologias obrigatórias, budgets, prazos, compliance.

**Dica-chave:** todo requisito bom tem:

* **clareza** (sem ambiguidade),
* **criticidade/prioridade**,
* **critério de aceite** (como validar),
* **rastreabilidade** (de onde veio e por quê).

---

### D. Validação e priorização (com negócio)

* Revisão com stakeholders (workshop de validação)
* **Priorizar**:

  * **MoSCoW** (Must/Should/Could/Won’t)
  * ou **WSJF** (muito bom em ambientes ágeis/SAFe)
* Definir **MVP** + fases
* Fechar **Definition of Ready** (o que precisa estar pronto para arquitetar/desenvolver)

**Saída:** backlog priorizado + NFRs acordados + escopo do MVP.

---

## 2) Como requisitos viram arquitetura (o “pulo do gato”)

Arquitetura não nasce de features; nasce de **atributos de qualidade** (NFRs) e restrições.

**Mapeamento típico:**

* Baixa latência / alto throughput → cache, filas, particionamento, escalabilidade horizontal
* Alta disponibilidade → multi-AZ, failover, desenho stateless, DR
* Auditabilidade / rastreabilidade → event log, trilha de auditoria, imutabilidade, versionamento
* Segurança / LGPD → classificação de dados, criptografia, IAM least privilege, masking
* Integrações numerosas → API gateway, eventos, CDC, contratos (schema registry)
* Custo como driver → autoscaling, spot, cold storage, right-sizing

**Boa prática:** registrar decisões em **ADRs (Architecture Decision Records)**:

* Contexto → decisão → alternativas → trade-offs → consequências.

---

## 3) Melhores práticas (as que mais evitam retrabalho)

* **Comece por objetivos e métricas**, não por telas e features.
* **Separar “necessidade” de “solução”**: usuário pede “um dashboard”; necessidade pode ser “reduzir tempo de decisão”.
* **Requisitos não funcionais desde o dia 1** (90% dos problemas de produção vêm daqui).
* **Volumetria e picos são requisitos** (tamanho de dados, RPS, concorrência, crescimento).
* **Glossário do domínio** (um termo = um significado).
* **Critérios de aceite** sempre (Gherkin ajuda: Given/When/Then).
* **Rastreabilidade**: requisito → épico/story → componente → teste → métrica.
* **Prototipar riscos cedo** (spikes): performance, integrações, permissões, custos.
* **Change control leve**: toda mudança relevante revisa NFRs e decisões (ADR).

---

## 4) Metodologias úteis (quando usar cada uma)

* **Design Thinking / Discovery**: fase inicial, problemas mal definidos.
* **Lean Inception**: 1 semana para alinhar visão, personas, jornadas, MVP.
* **Agile (Scrum/Kanban)**: delivery contínuo com backlog.
* **BDD**: requisitos como comportamento testável (Given/When/Then).
* **Domain-Driven Design (DDD)**: domínios complexos; define bounded contexts e linguagem ubíqua.
* **Event Storming**: excelente para levantar eventos, regras, exceções, integrações.
* **C4 Model**: comunicar arquitetura em níveis (Context/Container/Component/Code).
* **TOGAF** (mais “enterprise”): quando precisa governança pesada e portfólio corporativo.

---

## 5) Templates prontos (copiar/colar)

### Template 1 — One-page “Problem & Outcome”

**Problema:**
**Contexto atual (AS-IS):**
**Impacto (custo/risco/tempo/erro):**
**Objetivo (TO-BE):**
**Métrica de sucesso (KPI/OKR):**
**Não-objetivos:**
**Premissas e restrições:**
**Stakeholders (decisor/aprovador/usuário/operação):**

---

### Template 2 — BRD/PRD (resumo)

1. Visão e objetivos
2. Escopo (in/out)
3. Personas e jornadas
4. Requisitos funcionais (lista)
5. Regras de negócio
6. Requisitos não funcionais (NFRs)
7. Dados e integrações
8. Segurança e compliance (LGPD)
9. Observabilidade e operação (SLO/SLI, suporte)
10. Critérios de aceite / Definition of Done
11. Riscos e dependências
12. Roadmap (MVP + fases)

---

### Template 3 — User Story (com critério de aceite)

**Como** [persona]
**Quero** [capabilidade]
**Para** [benefício mensurável]

**Critérios de aceite (Given/When/Then):**

* Given … When … Then …

**Notas:** regras, exceções, dados necessários
**Prioridade:** Must/Should/Could
**Métrica ligada:** KPI X

---

### Template 4 — NFRs (tabela)

* **Performance:** p95 ≤ X ms, throughput ≥ Y rps, batch ≤ Z min
* **Disponibilidade:** 99.9%, RTO/RPO
* **Escalabilidade:** até N usuários / M registros/dia
* **Segurança:** IAM, criptografia em trânsito/repouso, segregação, auditoria
* **Observabilidade:** logs estruturados, métricas, tracing, alarmes
* **Manutenibilidade:** padrões, versionamento, testes
* **Compliance:** LGPD, retenção, consentimento, data lineage
* **Custo:** teto mensal, custo por transação

---

### Template 5 — ADR (Architecture Decision Record)

**Título:**
**Contexto:**
**Decisão:**
**Alternativas consideradas:**
**Trade-offs:**
**Consequências:**
**Data / Autor:**

---

## 6) Roteiro de workshops (bem direto)

**Workshop 1 (1–2h): Visão e sucesso**

* Problema, objetivos, métricas, não-objetivos

**Workshop 2 (2–4h): Jornada / Stories**

* User story mapping + MVP

**Workshop 3 (2–4h): Domínio e regras**

* Event storming + glossário

**Workshop 4 (1–2h): NFRs e restrições**

* SLOs, segurança, compliance, volumetria, custos

**Workshop 5 (1–2h): Validação final**

* backlog priorizado + Definition of Ready + riscos

---

Se você me disser **o tipo de projeto** (ex.: “pipeline de dados”, “sistema transacional”, “ML scoring”, “app interno”, etc.), eu adapto esses templates para o seu caso e já te devolvo um **kit preenchível** (ex.: BRD + NFRs + ADR + roteiro de perguntas) com exemplos bem próximos da realidade do seu domínio (dados/ML/risco/AWS).

===============================================================================================================
Explique mais sobre o template 2 - BRD/PRD. O que são os requisitos funcionários e não funcionais, exemplifique

Ótima pergunta — **BRD/PRD** é onde muita arquitetura boa *nasce ou morre*. Vou explicar de forma **estruturada, com exemplos reais**, e mostrando **como isso vira decisão técnica depois**.

---

# 1) O que é BRD e PRD (e por que às vezes viram um só)

### **BRD — Business Requirements Document**

Foco: **o negócio**

* *Por que* o projeto existe
* *Qual valor* ele gera
* *Quais regras* precisam ser respeitadas
* *Como medir sucesso*

Normalmente escrito em linguagem mais próxima do negócio.

---

### **PRD — Product Requirements Document**

Foco: **o produto/sistema**

* *O que o sistema faz*
* *Como o usuário interage*
* *Quais comportamentos são esperados*
* *Quais restrições técnicas e operacionais existem*

Mais técnico, mas ainda **não é arquitetura nem código**.

👉 Em projetos modernos, **BRD + PRD viram um único documento**, com seções bem separadas.

---

# 2) Estrutura detalhada do Template 2 — BRD/PRD

Vou percorrer seção por seção e aprofundar onde entram **requisitos funcionais e não funcionais**.

---

## 1. Visão e objetivos

**Pergunta-chave:** *Qual problema de negócio estamos resolvendo?*

Exemplo:

> Reduzir o tempo médio de aprovação de crédito de **48h para menos de 5 minutos**, mantendo aderência às regras regulatórias.

Inclui:

* Contexto atual (AS-IS)
* Objetivo futuro (TO-BE)
* KPIs / OKRs

📌 **Aqui ainda não existe requisito funcional**, só *intenção*.

---

## 2. Escopo (In / Out)

Define o **perímetro** do projeto.

Exemplo:
**IN**

* Avaliação automática de crédito pessoa física
* Integração com bureaus externos
* Geração de decisão e justificativa

**OUT**

* Gestão de contratos
* Cobrança
* Atendimento ao cliente

📌 Evita “scope creep”.

---

## 3. Personas e jornadas

Define **quem usa** e **como usa**.

Exemplo:

* Analista de crédito
* Sistema parceiro (API)
* Auditor/regulador

Aqui já começamos a enxergar **onde surgirão requisitos funcionais**.

---

## 4. Requisitos Funcionais (RF)

### O que são?

São **comportamentos e capacidades que o sistema deve oferecer**.

📌 Regra simples:

> Se você consegue demonstrar em uma *demo*, provavelmente é funcional.

---

### Exemplos de Requisitos Funcionais

#### RF-01 — Cálculo de score

> O sistema deve calcular o score de crédito de um cliente a partir dos dados cadastrais, financeiros e comportamentais.

---

#### RF-02 — Classificação de risco

> O sistema deve classificar o cliente em uma faixa de risco (A, B, C, D ou E).

---

#### RF-03 — Decisão automática

> O sistema deve gerar automaticamente uma decisão de **aprovação**, **recusa** ou **análise manual**.

---

#### RF-04 — Justificativa da decisão

> O sistema deve apresentar os principais fatores que influenciaram a decisão de crédito.

---

#### RF-05 — Integração externa

> O sistema deve consultar bureaus de crédito externos via API REST.

---

### Forma recomendada (boa prática)

| Campo              | Exemplo                                                                                                  |
| ------------------ | -------------------------------------------------------------------------------------------------------- |
| ID                 | RF-04                                                                                                    |
| Descrição          | Exibir justificativa da decisão                                                                          |
| Prioridade         | Must                                                                                                     |
| Origem             | Compliance / Negócio                                                                                     |
| Critério de aceite | Dado um cliente recusado, quando a decisão é retornada, então devem ser exibidos os 5 principais fatores |

---

## 5. Regras de Negócio (RN)

📌 **Não confundir com requisito funcional**

* Requisito funcional: *o sistema faz*
* Regra de negócio: *como e sob quais condições*

Exemplo:

> RN-03: Clientes com renda comprovada inferior a R$ 1.500 não podem ser aprovados.

O **sistema implementa**, mas **não define** a regra.

---

## 6. Requisitos Não Funcionais (NFRs)

### O que são?

São **qualidades, restrições e garantias** do sistema.

📌 Regra de ouro:

> Funcional diz *o que*
> Não funcional diz *como bem*, *quão rápido*, *quão seguro*, *quão confiável*

---

## 7. Tipos de Requisitos Não Funcionais (com exemplos)

### 1️⃣ Performance

> O sistema deve retornar a decisão de crédito em até **500 ms (p95)**.

Impacto arquitetural:

* cache
* paralelismo
* serviços assíncronos

---

### 2️⃣ Escalabilidade

> O sistema deve suportar **2.000 requisições por segundo** em horários de pico.

Impacto:

* stateless services
* auto scaling
* filas

---

### 3️⃣ Disponibilidade

> O sistema deve ter disponibilidade mínima de **99,9% mensal**.

Impacto:

* multi-AZ
* health checks
* retry / circuit breaker

---

### 4️⃣ Segurança

> Dados pessoais devem ser criptografados em repouso e em trânsito.

Impacto:

* KMS
* TLS
* IAM

---

### 5️⃣ Auditabilidade / Compliance

> Todas as decisões de crédito devem ser auditáveis por até **5 anos**.

Impacto:

* event logs
* versionamento de modelos
* trilha de decisão

---

### 6️⃣ Observabilidade

> O sistema deve expor métricas de latência, erro e throughput.

Impacto:

* logs estruturados
* métricas
* tracing

---

### 7️⃣ Qualidade de dados

> Campos críticos não podem ter taxa de nulos superior a **0,1%**.

Impacto:

* validação
* DQ rules
* pipelines de saneamento

---

### 8️⃣ Custo

> O custo mensal do sistema não pode ultrapassar **R$ 30.000**.

Impacto:

* escolha de tecnologia
* escalabilidade sob demanda
* storage tiering

---

## 8. Dados e Integrações

Aqui você descreve:

* fontes
* formatos
* volumetria
* frequência
* retenção

Exemplo:

> Ingestão diária de 50 milhões de registros, retenção de 5 anos.

📌 Isso é **requisito não funcional de dados**.

---

## 9. Operação e suporte

Define **como o sistema vive em produção**:

* deploy
* rollback
* monitoramento
* suporte

Exemplo:

> Rollback automático em caso de erro acima de 5% por 5 minutos.

---

## 10. Critérios de aceite

Conecta requisitos → testes → validação.

Exemplo:

> Dado um cliente válido, quando submeto uma solicitação, então recebo decisão e justificativa em até 500 ms.

---

## 11. Riscos e dependências

Exemplo:

* Dependência de bureau externo
* Qualidade dos dados históricos
* Mudança regulatória

---

## 12. Roadmap

MVP → Fase 2 → Fase 3

---

# 3) Resumo rápido: Funcional vs Não Funcional

| Aspecto      | Funcional            | Não Funcional         |
| ------------ | -------------------- | --------------------- |
| Pergunta     | O que o sistema faz? | Com que qualidade?    |
| Visibilidade | Usuário vê           | Usuário sente         |
| Exemplo      | Calcular score       | Responder em 500 ms   |
| Impacto      | Lógica de negócio    | Arquitetura inteira   |
| Erros comuns | Muito detalhado cedo | Ignorado até produção |

---

# 4) Erros clássicos em BRD/PRD

❌ “O sistema deve ser rápido”
✅ “p95 ≤ 500 ms”

❌ “Alta disponibilidade”
✅ “99,9% mensal, RTO 15 min, RPO 5 min”

❌ Misturar regra de negócio com tecnologia
❌ Escrever NFRs vagos e não mensuráveis

---

Se quiser, no próximo passo eu posso:

* adaptar esse BRD/PRD para **data platform / ML / scoring / ingestão em larga escala**, ou
* te entregar um **template em Markdown ou Confluence** pronto para uso em time corporativo.

===============================================================================================================

Esse cenário é **muito comum** em projetos *data-first / ML-first* e você está certo:
👉 quando **não existe produto anterior**, **não existe “dor explícita”** — então **você não pode perguntar “qual é o problema?”**.
Você precisa **criar o problema junto com o negócio**.

Vou te passar um **framework prático**, pensado **exatamente para o seu tipo de projeto** (ingestão de imagens de satélite + índices espectrais + tabelas analíticas), cobrindo:

1. **Mudança de mentalidade** (por que o approach tradicional falha)
2. **Estratégia correta de discovery quando tudo é novo**
3. **Agenda de workshops (passo a passo)**
4. **Perguntas certas para pessoas de negócio (sem falar de tecnologia)**
5. **Como documentar isso em BRD/PRD**
6. **Como isso vira arquitetura depois (ponte direta)**

---

## 1️⃣ Por que “levantar dores” não funciona nesse caso

Quando tudo é novo, o negócio:

* ❌ **não sabe o que é possível**
* ❌ **não sabe quais decisões poderiam ser melhores**
* ❌ **não consegue imaginar o produto final**
* ❌ **não fala em requisitos — fala em desejos vagos**

Se você perguntar:

> “Qual dor vocês têm hoje?”

A resposta típica será:

* “Não sabemos ainda”
* “Queremos explorar dados”
* “Queremos algo flexível”
* “Queremos indicadores”

📌 **Conclusão**
Você não levanta *dor*.
Você levanta **DECISÕES DE NEGÓCIO FUTURAS**.

---

## 2️⃣ O framework correto: Decision-Driven Discovery

Troque a pergunta:

❌ *“Qual funcionalidade você quer?”*
❌ *“Qual sistema você imagina?”*

Por perguntas como:

✅ **“Que decisões vocês querem tomar com esses dados?”**
✅ **“O que muda no negócio se essa informação existir?”**
✅ **“Quem usa, quando usa e o que faz depois?”**

Esse tipo de projeto se estrutura em 4 pilares:

| Pilar          | Você levanta                       |
| -------------- | ---------------------------------- |
| Decisões       | O que será decidido                |
| Informações    | O que precisa existir para decidir |
| Frequência     | Quando e com qual latência         |
| Confiabilidade | O quão errado pode estar           |

---

## 3️⃣ Agenda recomendada de workshops (prática e realista)

### 🧭 Workshop 1 — Visão, objetivos e decisões (2h)

**Participantes:** negócio + você
**Objetivo:** criar o *porquê* do sistema

**Saídas:**

* Objetivo de negócio
* Decisões que o sistema habilita
* Métricas de sucesso

---

### 🗺️ Workshop 2 — Domínio geoespacial e regras (3h)

**Objetivo:** entender *o mundo real* que vocês estão modelando

**Saídas:**

* Tipos de geometria
* Eventos relevantes
* Regras temporais e espaciais
* Ciclo de vida dos dados

---

### ⏱️ Workshop 3 — Uso da informação (latência, escala, custo) (2h)

**Objetivo:** levantar NFRs sem chamar de NFR

**Saídas:**

* Frequência de ingestão
* SLA implícito
* Escala e crescimento
* Tolerância a atraso/erro

---

### 🧪 Workshop 4 — Qualidade, confiança e governança (2h)

**Objetivo:** evitar retrabalho e refactor caro depois

**Saídas:**

* Qualidade mínima aceitável
* Auditoria
* Retenção
* Versionamento

---

## 4️⃣ Perguntas certas (adaptadas ao seu projeto)

### 🔹 Bloco 1 — Decisões de negócio (o mais importante)

Pergunte **sempre nesse formato**:

* “Quando vocês tiverem essas imagens processadas, **o que muda na prática**?”
* “Que decisão vocês tomariam se soubessem o NDVI médio dessa área?”
* “Quem consome essa informação: humano ou sistema?”
* “O que acontece se essa informação chegar atrasada?”
* “Existe alguma decisão automática que pode ser tomada?”

📌 Aqui você descobre:

* se o sistema é **analítico, operacional ou híbrido**
* se precisa ser **near-real-time ou batch**
* se haverá **integração downstream**

---

### 🔹 Bloco 2 — Geometrias e tempo (muito crítico)

Perguntas:

* As geometrias são:

  * fixas?
  * versionadas?
  * mutáveis ao longo do tempo?
* Existe histórico de geometria?
* A análise é:

  * pontual?
  * por período?
  * comparativa (antes/depois)?

Isso define:

* modelagem temporal
* versionamento
* estratégia de storage

---

### 🔹 Bloco 3 — Índices espectrais (sem falar de bandas)

Não pergunte:
❌ “Quer NDVI, EVI, SAVI?”

Pergunte:

* “O que vocês querem detectar?”

  * vigor vegetal?
  * estresse?
  * mudança?
* “Vocês comparam áreas entre si ou uma área ao longo do tempo?”
* “Qual erro é aceitável?”

📌 Depois você traduz isso para índices.

---

### 🔹 Bloco 4 — Latência (NFR disfarçado)

Perguntas que o negócio entende:

* “Isso é usado no mesmo dia ou pode esperar?”
* “Se chegar 24h depois, perde valor?”
* “Existe evento crítico (ex: seca, quebra de safra)?”

---

### 🔹 Bloco 5 — Confiabilidade e governança

Pergunte:

* “Vocês precisam explicar esse dado para alguém externo?”
* “Existe auditoria, regulação ou disputa?”
* “Se o dado mudar, precisamos saber que mudou?”

---

## 5️⃣ Como documentar isso no BRD/PRD (template adaptado)

### 📄 Seção 1 — Objetivo de negócio

> Habilitar análise temporal e espacial de indicadores espectrais para suportar decisões relacionadas a X.

---

### 📄 Seção 2 — Decisões suportadas

| Decisão                | Quem     | Frequência |
| ---------------------- | -------- | ---------- |
| Identificar degradação | Analista | Semanal    |
| Comparar áreas         | Sistema  | Mensal     |
| Detectar anomalias     | Sistema  | Diário     |

---

### 📄 Seção 3 — Requisitos Funcionais (exemplo)

* RF-01: Ingerir imagens de satélite associadas a geometrias definidas
* RF-02: Calcular índices espectrais por geometria e período
* RF-03: Persistir histórico temporal dos índices
* RF-04: Disponibilizar dados agregados para consumo analítico

---

### 📄 Seção 4 — Requisitos Não Funcionais (derivados do negócio)

| Categoria      | Requisito                                     |
| -------------- | --------------------------------------------- |
| Latência       | Processamento diário até D+1                  |
| Escala         | Até X geometrias / Y imagens                  |
| Retenção       | Histórico mínimo de 5 anos                    |
| Auditabilidade | Reprocessamento rastreável                    |
| Qualidade      | Índices calculados somente com cobertura ≥ Z% |

---

### 📄 Seção 5 — Dados e tabelas (alto nível)

* Metadados de imagem
* Tabela transacional por geometria e data
* Tabela informacional agregada

(Sem falar ainda em Athena, Iceberg, Spark, etc.)

---

## 6️⃣ Como isso vira arquitetura (sem retrabalho)

Quando você fecha esses workshops, você **automaticamente sabe**:

| Decisão de negócio  | Impacto arquitetural            |
| ------------------- | ------------------------------- |
| D+1 é ok            | Batch processing                |
| Histórico longo     | Storage particionado            |
| Reprocessamento     | Dados imutáveis + versionamento |
| Comparação temporal | Modelo temporal consistente     |
| Escala alta         | Paralelismo e chunking          |

Ou seja:
👉 **a arquitetura deixa de ser “opinião técnica” e vira consequência do negócio**.

---

## 7️⃣ Dica final de Tech Lead (importante)

Nunca apresente arquitetura primeiro.
Apresente **decisões de negócio habilitadas**.

Frase poderosa para abrir o workshop:

> “Não vamos falar de tecnologia hoje. Vamos falar de decisões que vocês gostariam de tomar e hoje não conseguem.”

Se quiser, no próximo passo eu posso:

* montar **um roteiro de reunião pronto (slide por slide)**
* gerar **um BRD/PRD preenchível específico para ingestão de imagens de satélite**
* ou simular **perguntas/respostas típicas do negócio** para você treinar a condução.

===============================================================================================================

Perfeito. Vou te entregar **dois artefatos prontos para uso** — no formato que um **tech lead realmente usa**:

1. **BRD/PRD preenchível**, específico para **ingestão de imagens de satélite + índices espectrais + tabelas analíticas**
2. **Simulação realista de perguntas e respostas com o negócio**, para você **conduzir a agenda com segurança**, mesmo quando eles “não sabem o que querem”

Nada de buzzword, nada de tecnologia ainda — foco **100% em negócio → requisito → arquitetura depois**.

---

# PARTE 1 — BRD / PRD PREENCHÍVEL (ESPECÍFICO PARA SEU CASO)

> 📌 **Como usar**
>
> * Use este documento como **guia de condução** das reuniões
> * Preencha **junto com o negócio** (não sozinho)
> * Onde estiver `[ ]`, é campo preenchível

---

## 1. Visão e Objetivo de Negócio

**Problema / Oportunidade**

> Atualmente, não existe uma base estruturada que permita analisar imagens de satélite associadas a geometrias específicas para suportar decisões relacionadas a [uso do solo / agricultura / risco / monitoramento / outro].

**Objetivo do Projeto**

> Disponibilizar informações derivadas de imagens de satélite que permitam **análises espaciais e temporais** para apoiar decisões de negócio relacionadas a [ ].

**Resultado Esperado (em termos de negócio)**

* Melhorar a capacidade de: [monitorar / comparar / detectar mudanças / automatizar decisões]
* Reduzir: [tempo de análise / risco / incerteza / dependência manual]

**Métricas de Sucesso (KPIs)**

* [ ] Decisões tomadas com base nos dados
* [ ] Frequência de uso das informações
* [ ] Tempo entre aquisição da imagem e disponibilidade do dado

---

## 2. Stakeholders e Usuários

| Papel              | Responsabilidade                   |
| ------------------ | ---------------------------------- |
| Usuário final      | [ex: analista, cientista, sistema] |
| Dono do dado       | [ ]                                |
| Decisor de negócio | [ ]                                |
| Consumidor externo | [se houver]                        |

---

## 3. Decisões de Negócio Suportadas (SEÇÃO MAIS IMPORTANTE)

> 📌 **Se essa seção estiver fraca, a arquitetura vai nascer errada**

| Decisão                            | Quem decide | Frequência | Impacto |
| ---------------------------------- | ----------- | ---------- | ------- |
| Ex: Identificar degradação da área | Analista    | Mensal     | Alto    |
| [ ]                                | [ ]         | [ ]        | [ ]     |

Pergunta-chave validada:

> “O que muda no negócio quando essa informação existir?”

---

## 4. Escopo do Projeto

### IN SCOPE

* Ingestão de imagens de satélite
* Associação imagem ↔ geometria
* Cálculo de índices espectrais
* Persistência histórica
* Disponibilização para análise

### OUT OF SCOPE

* [ex: visualização avançada]
* [ex: ações operacionais automáticas]
* [ex: modelagem preditiva]

---

## 5. Requisitos Funcionais (RF)

> 📌 **O que o sistema deve fazer**

| ID    | Requisito                                                                   |
| ----- | --------------------------------------------------------------------------- |
| RF-01 | Ingerir imagens de satélite associadas a um conjunto definido de geometrias |
| RF-02 | Processar imagens considerando recortes espaciais por geometria             |
| RF-03 | Calcular índices espectrais por geometria e período                         |
| RF-04 | Armazenar histórico temporal dos índices                                    |
| RF-05 | Disponibilizar dados para consumo analítico                                 |
| RF-XX | [Novo requisito identificado]                                               |

---

## 6. Regras de Negócio (RN)

> 📌 **Não são técnicas — são políticas e critérios do domínio**

| ID    | Regra                                                                    |
| ----- | ------------------------------------------------------------------------ |
| RN-01 | Uma geometria pode possuir múltiplas imagens associadas no mesmo período |
| RN-02 | Índices só são válidos se cobertura útil ≥ [ ]%                          |
| RN-03 | Geometrias podem ser versionadas ao longo do tempo                       |
| RN-XX | [ ]                                                                      |

---

## 7. Requisitos Não Funcionais (NFR)

> 📌 **Aqui nasce a arquitetura**

### Latência

* Os dados devem estar disponíveis em até: `[D+1 / semanal / mensal]`

### Escala

* Volume estimado:

  * Geometrias: `[ ]`
  * Imagens por período: `[ ]`
  * Crescimento anual: `[ ]%`

### Histórico e Retenção

* Retenção mínima: `[ ] anos`
* Reprocessamento histórico: `[Sim / Não]`

### Qualidade e Confiabilidade

* Tolerância a dados faltantes: `[ ]`
* Detecção de erro ou inconsistência: `[ ]`

### Auditabilidade

* Capacidade de rastrear:

  * Imagem original
  * Versão da geometria
  * Regra aplicada
  * Versão do cálculo

---

## 8. Modelo Conceitual de Dados (alto nível)

* **Metadados de Imagem**
* **Geometria (com versionamento temporal)**
* **Tabela Transacional** (imagem × geometria × data)
* **Tabela Informacional** (agregações por período)

📌 *Sem tecnologia ainda.*

---

## 9. Consumo e Integrações

* Quem consome:

  * [Analista]
  * [Sistema]
* Forma de consumo:

  * [Consulta]
  * [Exportação]
  * [Integração downstream]

---

## 10. Riscos e Premissas

* Disponibilidade das imagens
* Qualidade dos dados
* Mudança futura de escopo
* Crescimento não previsto

---

## 11. Roadmap

| Fase   | Entrega                    |
| ------ | -------------------------- |
| MVP    | Ingestão + índices básicos |
| Fase 2 | Histórico + agregações     |
| Fase 3 | Automatizações / alertas   |

---

# PARTE 2 — SIMULAÇÃO DE PERGUNTAS E RESPOSTAS (CONDUÇÃO REAL)

Abaixo está um **diálogo realista**, exatamente como acontece com negócio.

---

### 🎯 Abertura (você)

> “Hoje não vamos falar de tecnologia. Quero entender **que decisões vocês gostariam de tomar no futuro usando imagens de satélite**.”

---

### ❓ Pergunta 1 — “O que vocês querem ver?”

**Negócio (típico):**

> “Queremos analisar imagens.”

❌ **Não pare aqui.**

✅ **Follow-up correto (você):**

> “Quando vocês analisarem essas imagens, **o que muda na prática?**”

**Negócio:**

> “Queremos saber se uma área está piorando ou melhorando.”

👉 **Anote como decisão**

> *Detectar mudança temporal por geometria*

---

### ❓ Pergunta 2 — Frequência

**Você:**

> “Isso precisa ser visto em tempo real?”

**Negócio:**

> “Não, pode ser periódico.”

**Você (fecha NFR):**

> “Periódico é diário, semanal ou mensal?”

**Negócio:**

> “Semanal já resolve.”

👉 **Latência definida sem falar em arquitetura**

---

### ❓ Pergunta 3 — Geometrias

**Você:**

> “Essas áreas mudam com o tempo?”

**Negócio:**

> “Sim, às vezes ajustamos limites.”

👉 **Descoberta crítica:**
Versionamento de geometria → impacto direto em storage e modelagem.

---

### ❓ Pergunta 4 — Qualidade

**Você:**

> “Se uma imagem vier com nuvem, o dado ainda serve?”

**Negócio:**

> “Depende, se for pouca nuvem sim.”

**Você:**

> “O que é pouca?”

**Negócio:**

> “Até uns 20%.”

👉 **Regra de negócio explícita**

---

### ❓ Pergunta 5 — Confiança e explicação

**Você:**

> “Alguém pode questionar esse dado no futuro?”

**Negócio:**

> “Sim, pode virar disputa.”

👉 **Auditabilidade obrigatória**

---

### ❓ Pergunta 6 — Consumo

**Você:**

> “Isso será usado por pessoas ou sistemas?”

**Negócio:**

> “Por ambos.”

👉 **Sistema híbrido → analítico + operacional**

---

## 3️⃣ O que você ganha com isso (como Tech Lead)

Após essas sessões, você terá:

* Decisões claras
* Requisitos funcionais objetivos
* NFRs **definidos pelo negócio**
* Um BRD/PRD defendível
* Arquitetura que **não é opinião técnica**

---

## Próximo passo (se quiser)

Posso:

* Converter isso em **slides de workshop (1–4)**
* Transformar em **template Markdown / Confluence / Notion**
* Ou pegar esse BRD e **derivar a arquitetura-alvo (C4 + decisões)**

Se quiser, me diga **onde você vai documentar (Confluence, Git, Notion, Markdown)** e **quem participa das reuniões**.

