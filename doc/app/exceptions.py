from typing import Optional


class SQSConsumerException(Exception):
    """Exceção base para o consumidor SQS."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        message_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        Args:
            message: Descrição do erro
            error_code: Código de erro (ex: "VISIBILITY_TIMEOUT_INVALID")
            message_id: ID da mensagem envolvida (se aplicável)
            cause: Exceção underlying
        """
        self.message = message
        self.error_code = error_code
        self.message_id = message_id
        self.cause = cause
        super().__init__(message)


class SQSConfigurationError(SQSConsumerException):
    """Erro na validação de configuração."""
    pass
