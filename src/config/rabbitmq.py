from pydantic import BaseModel


class RabbitMQSettings(BaseModel):
    host: str = "rabbitmq"
    user: str = "guest"
    password: str = "guest"
    default_routing_key: str = "mindlogger"
    port: int = 5672

    @property
    def url(self):
        return f"amqps://{self.user}:{self.password}@{self.host}:{self.port}/"