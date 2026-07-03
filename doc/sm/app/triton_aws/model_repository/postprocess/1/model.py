import logging
import time

import numpy as np

import triton_python_backend_utils as pb_utils

logger = logging.getLogger(__name__)

CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]


class TritonPythonModel:

    def initialize(self, args):
        pass

    def execute(self, requests):
        responses = []
        for request in requests:
            try:
                t0 = time.perf_counter()
                record_ids = pb_utils.get_input_tensor_by_name(request, "record_id").as_numpy()
                scores = pb_utils.get_input_tensor_by_name(request, "scores").as_numpy()
                # record_ids shape: (batch_size, 1), dtype object (bytes)
                # scores shape: (batch_size, 6)
                indices = np.argmax(scores, axis=1)                          # (B,)
                top_scores = scores[np.arange(len(scores)), indices]         # (B,)
                elapsed = time.perf_counter() - t0

                out_record_id = np.array(
                    [[record_ids[i, 0]] for i in range(len(record_ids))], dtype=object
                )                                                            # (B, 1)
                out_class_name = np.array(
                    [[CLASSES[idx].encode()] for idx in indices], dtype=object
                )                                                            # (B, 1)
                out_score = np.array(
                    [[f"{top_scores[i]:.6f}".encode()] for i in range(len(top_scores))], dtype=object
                )                                                            # (B, 1)

                for i in range(len(record_ids)):
                    rid = record_ids[i, 0].decode() if isinstance(record_ids[i, 0], bytes) else str(record_ids[i, 0])
                    logger.info("postprocess record_id=%s elapsed=%.4fs", rid, elapsed)

                responses.append(pb_utils.InferenceResponse(output_tensors=[
                    pb_utils.Tensor("record_id",  out_record_id),
                    pb_utils.Tensor("class_name", out_class_name),
                    pb_utils.Tensor("score",      out_score),
                ]))
            except Exception as e:
                responses.append(pb_utils.InferenceResponse(output_tensors=[], error=pb_utils.TritonError(str(e))))
        return responses

    def finalize(self):
        pass
