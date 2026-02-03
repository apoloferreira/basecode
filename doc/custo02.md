
# Fargate

https://aws.amazon.com/pt/fargate/pricing/

Sao Paulo (us-east-1)

### Preço do Fargate

|  Unidade  |   ARM   |   x86  |
|-----------|---------|--------|
| vCPU-hour	| 0,0557  | 0,0696 |
| GB-hour   | 0,00612 | 0,0076 |

|   Unidade   |     ARM     |     x86     |
|-------------|-------------|-------------|
| vCPU-minute | 0,000928333 | 0,00116     |
| GB-minute   | 0,000102    | 0,000126667 |


### Preço do Fargate Spot para o Amazon ECS

|  Unidade  |     ARM    |    x86     |
|-----------|------------|------------|
| vCPU-hour	| 0,01870297 | 0,02337032 |
| GB-hour   | 0,00205498 | 0,00255193 |


========================================================================

-> 1.000 tasks

- Cobranças mensais de CPU
Total de cobranças de vCPU = (n.º de tarefas) x (n.º de vCPUs) x (preço por CPU-minuto) x (duração da CPU por dia por minuto) x (n.º de dias)
Total de cobranças de vCPU = 1.000 x 4 x 0,000928333 x 7 x 30 = 780,00 USD

- Cobranças mensais de memória
Total de cobranças de memória = (n.º de tarefas) x (memória em GB) x (preço por GB-minuto) x (duração da memória por dia por minuto) x (n.º de dias)
Total de cobranças de memória = 1.000 x 8 x 0,000102 x 7 x 30 = 172,00 USD

- Cobranças mensais de computação do Fargate
Cobranças mensais de computação do Fargate = (cobranças mensais de CPU) + (cobranças mensais de memória) + (cobranças mensais de armazenamento temporário)
Cobranças mensais de computação do Fargate = 780,00 USD + 172,00 USD = 952,00 USD

--------------------------------------------------------------------------

Fórmula base:
(Fargate cobra por vCPU-hora e GB-hora, por segundo, com mínimo de 1 min)

vCPU-h/dia = 1.000 × (7/60) × 4 = 466,67 vCPU-h/dia
GB-h/dia   = 1.000 × (7/60) × 8 = 933,33 GB-h/dia

Regiao: sa-east-1 (São Paulo, Linux/x86)
-> vCPU $0.0557/h
-> Mem  $0.00612/GB-h


CPU:           $ 780,00/mês
Memória:       $ 170,00/mês
-----------------------------
Fargate total: $ 950,00/mês

========================================================================

-> 100.000 tasks

- Cobranças mensais de CPU
Total de cobranças de vCPU = (n.º de tarefas) x (n.º de vCPUs) x (preço por CPU-minuto) x (duração da CPU por dia por minuto) x (n.º de dias)
Total de cobranças de vCPU = 100.000 x 4 x 0,000928333 x 7 x 30 = 77.980,00 USD

- Cobranças mensais de memória
Total de cobranças de memória = (n.º de tarefas) x (memória em GB) x (preço por GB-minuto) x (duração da memória por dia por minuto) x (n.º de dias)
Total de cobranças de memória = 100.000 x 8 x 0,000102 x 7 x 30 = 17.136,00 USD

- Cobranças mensais de computação do Fargate
Cobranças mensais de computação do Fargate = (cobranças mensais de CPU) + (cobranças mensais de memória) + (cobranças mensais de armazenamento temporário)
Cobranças mensais de computação do Fargate = 77.980,00 USD + 17.136,00 USD = 95.116,00 USD

========================================================================

1.000     =     950,00
100.000   =  95.000,00 
1.000.000 = 950.000,00 

========================================================================

# Lambda

https://aws.amazon.com/pt/lambda/pricing

Sao Paulo (us-east-1)

### Preço da Lambda

#### x86

| Memória (MB) | Preço por 1 milissegundo |
|--------------|--------------------------|
| 128	       | USD 0,0000000021         |
| 512	       | USD 0,0000000083         |
| 1.024	       | USD 0,0000000167         |
| 1536	       | USD 0,0000000250         |
| 2048	       | USD 0,0000000333         |
| 3072	       | USD 0,0000000500         |
| 4096	       | USD 0,0000000667         |
| 5120	       | USD 0,0000000833         |
| 6144	       | USD 0,0000001000         |
| 7168	       | USD 0,0000001167         |
| 8192	       | USD 0,0000001333         |
| 9216	       | USD 0,0000001500         |
| 10.240       | USD 0,0000001667         |

#### ARM

| Memória (MB) | Preço por 1 milissegundo |
|--------------|--------------------------|
| 128	       | USD 0,0000000017         |
| 512	       | USD 0,0000000067         |
| 1024	       | USD 0,0000000133         |
| 1536	       | USD 0,0000000200         |
| 2048	       | USD 0,0000000267         |
| 3072	       | USD 0,0000000400         |
| 4096	       | USD 0,0000000533         |
| 5120	       | USD 0,0000000667         |
| 6144	       | USD 0,0000000800         |
| 7168	       | USD 0,0000000933         |
| 8192	       | USD 0,0000001067         |
| 9216	       | USD 0,0000001200         |
| 10.240	   | USD 0,0000001333         |





|  Unidade  |   ARM   |   x86  |
|-----------|---------|--------|
| vCPU-hour	| 0,0557  | 0,0696 |
| GB-hour   | 0,00612 | 0,0076 |

|   Unidade   |     ARM     |     x86     |
|-------------|-------------|-------------|
| vCPU-minute | 0,000928333 | 0,00116     |
| GB-minute   | 0,000102    | 0,000126667 |






















