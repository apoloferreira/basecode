
Perfeito 👍
Abaixo está o **BRD / PRD em formato Markdown**, **100% preenchível**, já **adaptado ao seu projeto de ingestão de imagens de satélite**, pronto para usar em **Git, Confluence, Notion ou Wiki corporativa**.

Você pode **copiar/colar direto** e usar como documento vivo durante os workshops.

---

# 📄 BRD / PRD — Plataforma de Ingestão e Análise de Imagens de Satélite

> **Documento vivo** — deve ser preenchido e evoluído em conjunto com o negócio
> **Status:** *Em discovery*
> **Tech Lead:** `[Seu nome]`
> **Data:** `[DD/MM/AAAA]`

---

## 1. Visão e Objetivo de Negócio

### 1.1 Contexto

Atualmente não existe uma solução estruturada para ingestão, processamento e análise de imagens de satélite associadas a geometrias específicas, limitando a capacidade de tomada de decisão baseada em evidências espaciais e temporais.

---

### 1.2 Objetivo do Projeto

Disponibilizar informações derivadas de imagens de satélite que permitam **análises espaciais e temporais** para suportar decisões de negócio relacionadas a:

* `[ ] Monitoramento`
* `[ ] Comparação entre áreas`
* `[ ] Detecção de mudanças`
* `[ ] Avaliação de risco`
* `[ ] Outro: ______________________`

---

### 1.3 Resultados Esperados (Negócio)

* Melhorar a capacidade de `[ ]`
* Reduzir `[tempo / incerteza / risco / esforço manual]`
* Aumentar `[confiabilidade / escala / automação]`

---

### 1.4 Métricas de Sucesso (KPIs)

* Tempo entre aquisição da imagem e disponibilidade da informação: `[ ]`
* Frequência de uso das informações: `[ ]`
* Decisões suportadas pelo sistema: `[ ]`

---

## 2. Stakeholders e Usuários

| Papel                | Nome / Área | Responsabilidade |
| -------------------- | ----------- | ---------------- |
| Dono do Negócio      |             |                  |
| Usuário Final        |             |                  |
| Consumidor Técnico   |             |                  |
| Auditor / Compliance |             |                  |

---

## 3. Decisões de Negócio Suportadas (Seção Crítica)

> ❗ **Se esta seção estiver fraca, a arquitetura será fraca**

| Decisão                        | Quem Decide | Frequência | Impacto |
| ------------------------------ | ----------- | ---------- | ------- |
| Identificar degradação da área | Analista    | Mensal     | Alto    |
| Comparar evolução entre áreas  |             |            |         |
| Detectar anomalias             |             |            |         |
| `[Nova decisão]`               |             |            |         |

**Pergunta validada:**

> *“O que muda no negócio quando essa informação existir?”*

---

## 4. Escopo do Projeto

### 4.1 IN SCOPE

* Ingestão de imagens de satélite
* Associação imagem ↔ geometria
* Cálculo de índices espectrais
* Persistência histórica
* Disponibilização para análise

### 4.2 OUT OF SCOPE

* Visualização avançada
* Modelagem preditiva
* Ações automáticas de campo
* `[Outro]`

---

## 5. Requisitos Funcionais (RF)

> **O que o sistema deve fazer**

| ID    | Requisito                                                                   |
| ----- | --------------------------------------------------------------------------- |
| RF-01 | Ingerir imagens de satélite associadas a um conjunto definido de geometrias |
| RF-02 | Recortar imagens espacialmente por geometria                                |
| RF-03 | Calcular índices espectrais por geometria e período                         |
| RF-04 | Armazenar histórico temporal dos índices                                    |
| RF-05 | Disponibilizar dados para consumo analítico                                 |
| RF-XX | `[Novo requisito]`                                                          |

---

## 6. Regras de Negócio (RN)

> **Critérios e políticas do domínio — não técnicas**

| ID    | Regra                                                                    |
| ----- | ------------------------------------------------------------------------ |
| RN-01 | Uma geometria pode possuir múltiplas imagens associadas no mesmo período |
| RN-02 | Índices só são válidos se cobertura útil ≥ `[ ]%`                        |
| RN-03 | Geometrias podem ser versionadas ao longo do tempo                       |
| RN-04 | Dados reprocessados devem manter histórico                               |
| RN-XX | `[Nova regra]`                                                           |

---

## 7. Requisitos Não Funcionais (NFR)

### 7.1 Latência

* Disponibilidade dos dados em: `[D+1 / semanal / mensal]`

---

### 7.2 Escala

* Quantidade estimada de geometrias: `[ ]`
* Imagens por período: `[ ]`
* Crescimento anual estimado: `[ ]%`

---

### 7.3 Histórico e Retenção

* Retenção mínima: `[ ] anos`
* Reprocessamento histórico permitido: `[Sim / Não]`

---

### 7.4 Qualidade e Confiabilidade

* Tolerância a dados ausentes: `[ ]`
* Percentual máximo de nuvem aceitável: `[ ]%`
* Critérios mínimos de qualidade: `[ ]`

---

### 7.5 Auditabilidade e Governança

* Rastreabilidade de:

  * Imagem original
  * Versão da geometria
  * Regra aplicada
  * Versão do cálculo

---

## 8. Modelo Conceitual de Dados (Alto Nível)

* **Imagem**
* **Geometria (com versionamento temporal)**
* **Tabela Transacional**

  * imagem × geometria × data
* **Tabela Informacional**

  * agregações temporais e espaciais

> ⚠️ **Sem definição tecnológica nesta etapa**

---

## 9. Consumo e Integrações

### 9.1 Consumidores

* `[ ] Analistas`
* `[ ] Sistemas downstream`
* `[ ] Processos automatizados`

### 9.2 Forma de Consumo

* `[ ] Consulta`
* `[ ] Exportação`
* `[ ] Integração via serviço`

---

## 10. Premissas, Riscos e Restrições

### Premissas

* Disponibilidade contínua das imagens
* Estabilidade das regras de negócio

### Riscos

* Crescimento de volume acima do esperado
* Mudança futura de escopo
* Dependência de fonte externa

---

## 11. Roadmap Inicial

| Fase   | Entrega                    |
| ------ | -------------------------- |
| MVP    | Ingestão + índices básicos |
| Fase 2 | Histórico + agregações     |
| Fase 3 | Automatizações / alertas   |

---

## 12. Observações Finais

* Este documento **não define arquitetura**
* Todas as decisões técnicas devem derivar dos requisitos aqui descritos
* Mudanças relevantes devem atualizar este documento

---

# ✅ Como usar esse template na prática (dica final)

* **Abra o documento durante a reunião**
* Preencha **ao vivo** com o negócio
* Não discuta tecnologia
* Sempre feche respostas com:

  > “Isso vira uma decisão de negócio, correto?”

Se quiser, no próximo passo eu posso:

* gerar a **agenda + slides de condução do workshop**
* derivar **NFRs → arquitetura alvo (C4)**
* adaptar o template para **Data Mesh / ML / Feature Store**

É só me dizer.

