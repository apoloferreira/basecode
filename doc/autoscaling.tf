# Alvo de escalonamento: DesiredCount do Service
resource "aws_appautoscaling_target" "ecs" {
    service_namespace  = "ecs"
    scalable_dimension = "ecs:service:DesiredCount"
    max_capacity       = var.service_max_count
    min_capacity       = var.service_min_count
    resource_id        = "service/${aws_ecs_cluster.ecs_cluster.name}/${aws_ecs_service.worker.name}"
}


# Target tracking por backlog por task = mensagens visíveis / desiredCount
resource "aws_appautoscaling_policy" "ecs_sqs_backlog_tgt" {
    name               = "${local.name}-tt-backlog-policy"
    policy_type        = "TargetTrackingScaling"
    resource_id        = aws_appautoscaling_target.ecs.resource_id
    scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
    service_namespace  = aws_appautoscaling_target.ecs.service_namespace

    # Policy de Prateleira
    # target_tracking_scaling_policy_configuration {
    #     target_value       = var.target_backlog_per_task # manter ~X msgs por task
    #     scale_in_cooldown  = 60
    #     scale_out_cooldown = 60

    #     predefined_metric_specification {
    #         predefined_metric_type = "ECSServiceAverageCPUUtilization"
    #     }
    # }

    # Policy Customizada
    # target_tracking_scaling_policy_configuration {
    #     # target_value       = var.target_backlog_per_task # manter ~X msgs por task
    #     target_value       = 2
    #     scale_in_cooldown  = 60
    #     scale_out_cooldown = 60

    #     customized_metric_specification {
    #         metrics {
    #             label = "Get the queue size (the number of messages waiting to be processed)"
    #             id    = "m1"
    #             metric_stat {
    #                 metric {
    #                     namespace   = "AWS/SQS"
    #                     metric_name = "ApproximateNumberOfMessagesVisible"
    #                     dimensions  {
    #                         name = "QueueName"
    #                         value = aws_sqs_queue.queue.name
    #                     }
    #                 }
    #                 stat = "Sum"
    #             }
    #             return_data = false
    #         }
    #         metrics {
    #             label = "Get the ECS running task count (the number of currently running tasks)"
    #             id    = "m2"
    #             metric_stat {
    #                 metric {
    #                     namespace   = "ECS/ContainerInsights"
    #                     metric_name = "RunningTaskCount"
    #                     dimensions {
    #                         name  = "ClusterName"
    #                         value = aws_ecs_cluster.ecs_cluster.name
    #                     }
    #                     dimensions {
    #                         name  = "ServiceName"
    #                         value = aws_ecs_service.worker.name
    #                     }

    #                 }
    #                 stat = "Average"
    #             }
    #             return_data = false
    #         }
    #         metrics {
    #             label       = "Calculate the backlog per instance"
    #             id          = "e1"
    #             expression  = "m1 / m2"
    #             return_data = true
    #         }
    #     }
    # }


    target_tracking_scaling_policy_configuration {
        # Quantas mensagens em média você aceita por task
        # Para jobs pesados (~4 min), começaria baixo, tipo 5–10
        target_value       = 2

        # Segurar um pouco pra evitar “pula-pula”
        scale_in_cooldown  = 120
        scale_out_cooldown = 60

        # Métrica customizada = backlog por task (SQS / ECS)
        customized_metric_specification {
            # Métrica 1: tamanho da fila SQS
            metrics {
                id    = "m1"
                label = "SQS queue depth"
                metric_stat {
                    metric {
                        namespace   = "AWS/SQS"
                        metric_name = "ApproximateNumberOfMessagesVisible"
                        dimensions {
                            name  = "QueueName"
                            value = aws_sqs_queue.jobs.name
                        }
                    }
                    stat = "Sum"
                }
                return_data = false
            }

            # Métrica 2: quantidade de tasks rodando no service (Container Insights)
            metrics {
                id    = "m2"
                label = "ECS running task count"
                metric_stat {
                    metric {
                        namespace   = "ECS/ContainerInsights"
                        metric_name = "RunningTaskCount"
                        dimensions {
                            name  = "ClusterName"
                            value = aws_ecs_cluster.main.name
                        }
                        dimensions {
                            name  = "ServiceName"
                            value = aws_ecs_service.worker.name
                        }
                    }
                    stat = "Average"
                }
                return_data = false
            }

            # Métrica 3: expressão = backlog por task (m1 / m2)
            metrics {
                id          = "e1"
                label       = "Backlog per task"
                expression  = "m1 / m2"
                return_data = true
            }
        }
    }

}

# # Escalar para 10 tasks às 07:55 (UTC-3 => ajuste fuso; use UTC na regra)
# resource "aws_appautoscaling_scheduled_action" "scale_out_morning" {
#     name               = "warm-up-cluster"
#     service_namespace  = aws_appautoscaling_target.ecs.service_namespace
#     resource_id        = aws_appautoscaling_target.ecs.resource_id
#     scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
#     schedule           = "cron(55 10 ? * MON-FRI *)" # 07:55 BRT ~ 10:55 UTC; ajuste seu caso

#     scalable_target_action {
#         min_capacity = 1
#         max_capacity = var.service_max_count
#     }
# }

# # Escalar para 0 tasks ao meio-dia
# resource "aws_appautoscaling_scheduled_action" "scale_in_noon" {
#     name               = "cool-cluster"
#     service_namespace  = aws_appautoscaling_target.ecs.service_namespace
#     resource_id        = aws_appautoscaling_target.ecs.resource_id
#     scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
#     schedule           = "cron(0 15 ? * MON-FRI *)"  # 12:00 BRT ~ 15:00 UTC

#     scalable_target_action {
#         min_capacity = 0
#         max_capacity = var.service_max_count
#     }
# }
