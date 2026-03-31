# Cluster

resource "aws_ecs_cluster" "ecs_cluster" {
    name = "${local.name}-cluster"

    setting {
        name  = "containerInsights"
        value = "enabled"
    }
}


# Task Definition

resource "aws_ecs_task_definition" "worker" {
    family                   = "${local.name}-task"
    network_mode             = "awsvpc"
    requires_compatibilities = ["FARGATE"]
    cpu                      = var.task_cpu
    memory                   = var.task_memory
    execution_role_arn       = aws_iam_role.role_ecs_task_execution.arn
    task_role_arn            = aws_iam_role.role_ecs_task.arn

    runtime_platform {
        cpu_architecture        = "X86_64" # ARM64 -> a imagem docker tem que ser buildada para ARM
        operating_system_family = "LINUX"
    }

    container_definitions = jsonencode([
        {
            name     = var.container_name
            image     = var.container_image
            essential = true

            # Opcional: defina command/entryPoint conforme seu worker
            command   = ["python", "app.py"]

            logConfiguration = {
                logDriver = "awslogs",
                options   = {
                    "awslogs-group"         = aws_cloudwatch_log_group.ecs.name,
                    "awslogs-region"        = var.region,
                    "awslogs-stream-prefix" = "ecs"
                }
            }

            environment = [
                { 
                    name = "LOG_LEVEL",
                    value = "INFO"
                },
                {
                    name = "SQS_QUEUE_URL",
                    value = aws_sqs_queue.queue.url
                },
                { 
                    name = "SQS_WAIT_TIME", 
                    value = tostring(var.long_poll_seconds) 
                },
                { 
                    name = "SQS_BATCH_SIZE", 
                    value = tostring(var.sqs_batch_size) 
                },
                { 
                    name = "WORKER_CONCURRENCY", 
                    value = tostring(var.worker_concurrency) 
                }
            ]

        }
    ])
}


# Service

resource "aws_ecs_service" "worker" {
    name                              = "${local.name}-service"
    cluster                           = aws_ecs_cluster.ecs_cluster.id
    task_definition                   = aws_ecs_task_definition.worker.arn
    desired_count                     = var.service_min_count
    launch_type                       = "FARGATE"
    # health_check_grace_period_seconds = 10

    enable_execute_command = true

    network_configuration {
        subnets          = var.subnets_id
        security_groups  = [aws_security_group.ecs_tasks.id]
        assign_public_ip = var.assign_public_ip
    }

    deployment_controller {
        type = "ECS"
    }

    deployment_circuit_breaker {
        enable   = true
        rollback = true
    }

    lifecycle {
        ignore_changes = [desired_count]
    }

    # load_balancer {
    #     target_group_arn = aws_alb_target_group.this.id
    #     container_name   = local.container_name
    #     container_port   = var.ecs.app_port
    # }

    # depends_on = [
    #     aws_alb_listener.http
    # ]

}


# CloudWatch Log Group

resource "aws_cloudwatch_log_group" "ecs" {
    name              = local.log_name
    retention_in_days = 1
}
