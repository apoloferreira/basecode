Em condições equivalentes, a troca de GPU por CPU **não deve gerar grandes diferenças visuais nos segmentos do SAM/SamGeo**. Porém, não existe garantia de que as máscaras sejam idênticas pixel a pixel.

A diferença normalmente aparece por causa da precisão numérica e da implementação das operações:

* CPU e GPU podem executar as mesmas operações em ordens diferentes.
* A GPU pode usar TF32, FP16 ou mixed precision, enquanto a CPU geralmente executa em FP32.
* Pequenas diferenças nos logits podem fazer alguns pixels cruzarem o limiar de binarização.
* No gerador automático do SAM, uma pequena mudança pode afetar filtros como `pred_iou_thresh`, `stability_score_thresh` e NMS, fazendo uma máscara ser mantida ou descartada.

O próprio PyTorch informa que resultados em CPU e GPU podem diferir mesmo com entradas idênticas e controle de aleatoriedade. Isso é esperado em computação numérica, não necessariamente um defeito. [PyTorch — Numerical Accuracy](https://docs.pytorch.org/docs/stable/notes/numerical_accuracy.html) e [PyTorch — Reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html).

### Quando a diferença tende a ser pequena

O resultado deve ser praticamente equivalente quando vocês mantêm:

* o mesmo checkpoint do SAM;
* o mesmo `model_type`, como `vit_h`, `vit_l` ou `vit_b`;
* a mesma versão de PyTorch, SamGeo, Segment Anything, NumPy e OpenCV;
* exatamente a mesma imagem e o mesmo pré-processamento;
* os mesmos prompts ou a mesma grade de pontos;
* os mesmos parâmetros do gerador automático;
* inferência em FP32 nos dois ambientes;
* modelo em modo de avaliação.

```python
model.eval()

with torch.inference_mode():
    resultado = model(entrada)
```

Nesse cenário, eu esperaria diferenças restritas principalmente às bordas das máscaras ou a objetos muito próximos dos limiares de aceitação.

### Quando pode haver diferença relevante

Eu investigaria com mais cuidado se no ambiente analítico vocês usaram algo como:

```python
with torch.autocast(device_type="cuda", dtype=torch.float16):
    resultado = model(entrada)
```

ou:

```python
torch.set_float32_matmul_precision("high")
```

Também podem ocorrer diferenças maiores se houver:

* versões diferentes das bibliotecas;
* resize, normalização ou conversão de bandas diferentes;
* imagens GeoTIFF convertidas para `uint8` de maneiras diferentes;
* parâmetros diferentes do `SamAutomaticMaskGenerator`;
* pós-processamento diferente para remover regiões pequenas e buracos;
* tiling, tamanho dos recortes ou sobreposição diferentes.

No gerador automático, estes parâmetros merecem atenção especial:

```python
sam_kwargs = {
    "points_per_side": 32,
    "pred_iou_thresh": 0.88,
    "stability_score_thresh": 0.95,
    "box_nms_thresh": 0.7,
    "crop_n_layers": 0,
    "min_mask_region_area": 0,
}
```

Esses limiares controlam quais máscaras são aceitas ou eliminadas. Portanto, diferenças numéricas pequenas podem causar diferenças discretas no número final de segmentos. [Implementação oficial do gerador automático do SAM](https://github.com/facebookresearch/segment-anything/blob/main/segment_anything/automatic_mask_generator.py).

### Como eu faria a homologação

Não compararia os arquivos usando hash nem exigiria igualdade absoluta dos pixels. Usaria um conjunto representativo de imagens e compararia:

| Métrica                          | O que identifica                       |
| -------------------------------- | -------------------------------------- |
| IoU ou Dice                      | Similaridade espacial das máscaras     |
| Percentual de pixels divergentes | Alteração global entre CPU e GPU       |
| Número de segmentos              | Máscaras criadas ou eliminadas         |
| Área total segmentada            | Mudança na cobertura                   |
| Distribuição das áreas           | Mudança em objetos pequenos ou grandes |
| Diferença nas bordas             | Pequenos deslocamentos do contorno     |
| Tempo e memória                  | Viabilidade operacional da CPU         |

Para uma máscara binária consolidada:

```python
import numpy as np

def comparar_mascaras(gpu_mask, cpu_mask):
    gpu = gpu_mask.astype(bool)
    cpu = cpu_mask.astype(bool)

    intersection = np.logical_and(gpu, cpu).sum()
    union = np.logical_or(gpu, cpu).sum()

    iou = intersection / union if union else 1.0
    pixel_disagreement = np.not_equal(gpu, cpu).mean()

    return {
        "iou": float(iou),
        "pixel_disagreement": float(pixel_disagreement),
    }
```

Uma regra inicial razoável, que depois deve ser ajustada ao negócio, seria:

* IoU CPU × GPU acima de `0,98` para a máscara consolidada;
* divergência de pixels abaixo de `1%` ou `2%`;
* diferenças concentradas nas bordas;
* número e área dos segmentos dentro de uma tolerância definida.

Para segmentação por instâncias, cuidado: os valores `1`, `2`, `3` etc. do raster podem representar os mesmos objetos, mas com IDs ou ordenação diferentes. Nesse caso, é necessário associar os segmentos por sobreposição espacial antes de calcular IoU.

### Minha recomendação

A troca de dispositivo provavelmente afetará **muito mais o tempo de execução do que a qualidade da segmentação**. O SAM, principalmente `vit_h`, pode ficar bastante lento em CPU, e a própria documentação do SamGeo recomenda GPU nos exemplos de geração automática. [SamGeo — Automatic Mask Generator](https://samgeo.gishub.org/examples/automatic_mask_generator/).

Ainda assim, a homologação deveria reproduzir o ambiente que será usado em produção. Se produção será GPU, homologar apenas em CPU valida o código e o contrato da aplicação, mas não valida integralmente:

* o runtime CUDA;
* a precisão usada na GPU;
* o desempenho;
* o consumo de memória;
* o comportamento numérico real de produção.

Portanto: **não esperaria uma diferença grande nos segmentos somente por trocar GPU por CPU, desde que ambos usem FP32 e todo o restante seja idêntico**. Mas validaria por tolerância métrica, porque igualdade pixel a pixel entre dispositivos não é uma garantia do PyTorch.

---

Sim. Se os testes de desenvolvimento foram executados com seed e modo determinístico, a homologação deve usar a mesma configuração, principalmente para eliminar aleatoriedade como causa de divergência.

Porém, isso não garante que CPU e GPU produzam resultados idênticos. O determinismo garante principalmente que:

CPU → CPU seja reproduzível no mesmo ambiente;
GPU → GPU seja reproduzível no mesmo ambiente;
execuções repetidas não introduzam variação aleatória.

Ainda podem existir pequenas diferenças entre CPU e GPU devido às implementações e à precisão numérica das operações. O próprio PyTorch não garante reprodutibilidade exata entre plataformas. PyTorch — Reproducibility.

Uma configuração adequada seria:

import os
import random


import numpy as np
import torch




def configure_determinism(seed: int = 42) -> None:
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"


    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


    torch.use_deterministic_algorithms(True)


    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

Ela deve ser chamada no início do processo, antes de carregar e executar o modelo:

configure_determinism(seed=42)


model.eval()


with torch.inference_mode():
    resultado = model(entrada)

Algumas observações:

torch.backends.cudnn.* e CUBLAS_WORKSPACE_CONFIG só têm efeito relevante na GPU.
torch.use_deterministic_algorithms(True) pode gerar erro se alguma operação utilizada não possuir implementação determinística. Isso é útil na homologação porque expõe o problema.
model.eval() é indispensável, mas não substitui o modo determinístico. Ele desativa comportamentos de treinamento, como dropout.
torch.inference_mode() melhora a eficiência e evita a construção do grafo de gradientes.
As versões de PyTorch, SamGeo, Segment Anything, NumPy e OpenCV também devem ser fixadas.

Minha recomendação seria manter a configuração determinística em homologação e produção, caso o impacto de desempenho seja aceitável. Se produção for executada sem determinismo para ganhar desempenho, então é importante fazer uma segunda etapa da homologação usando exatamente a configuração real de produção.

Em resumo: use a mesma seed e o mesmo modo determinístico na homologação, mas compare CPU e GPU por métricas e tolerâncias — não por igualdade exata dos arquivos ou dos pixels.
