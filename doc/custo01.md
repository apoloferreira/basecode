
# Lambda

https://aws.amazon.com/pt/lambda/pricing/

-----------------------------------------------------------------
## Tempo de execucao

5 min = 300 seg = 300.000 milisegundos

1 milisegundos com 2048 memoria = 0,0000000267 USD


300.000 x 0,0000000267 = 0,00801 USD


0,00801 x 22.000 = 176,22 USD por dia

30/5 = 6 cargas por mes


176,22 x 6 = 1057,32 USD (6.132 R$)

-----------------------------------------------------------------
## Armazenamento temporario

custo: 0,0000000586 USD por cada GB/segundo

22.000 x 1 GB = 22.000 GB total por execucao

300 seg x 22.000 = 6.600.000 GB/seg total


6.600.000 GB/seg x 0,0000000586 USD GB/seg = 0,38676 USD

0,38676 USD x 6 = 2,32056 USD (13,46 R$)

-----------------------------------------------------------------
## Total

7.000   R$ para 22.000
31.818  R$ para 100.000
318.181 R$ para 1.000.000

========================================================================

# Fargate

https://aws.amazon.com/pt/fargate/pricing/
ARM vCPU per hour	USD 0,01016828
ARM GB per hour   	USD 0,00111795

-----------------------------------------------------------------
## Tempo de execucao

4 vCPU
2 GB

vCPU    -> 0,01016828 x 4 = 0,04067312
memoria -> 0,00111795 x 2 = 0,0022359
--------------------------------------
total   ->                  0,04290902 USD/hora

5 min x 22.000 = 110.000 min
110.000 min    = 1.834 horas

1834 horas x 0,04290902 USD/hora = 80 USD

80 USD x 5,8 = 458 R$

-----------------------------------------------------------------
## Tempo de execucao

4 vCPU
8 GB

vCPU    -> 0,01016828 x 4 = 0,04067312
memoria -> 0,00111795 x 8 = 0,0089436
--------------------------------------
total   ->                  0,04961672 USD/hora

7 min x 1.000 = 7.000 min
7.000 min     = 116 horas

116 horas x 0,04961672 USD/hora = 6 USD

6 USD x 30 dias = 180 R$

R$ 180 * 5,7 = R$ 1030,00


