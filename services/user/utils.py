from passlib.context import CryptContext
import aio_pika
import logging


log = logging.getLogger(__name__)

pwd_password = CryptContext(schemes=["bcrypt"])


class Hash:

    def bcrypt(password) -> str:
        return pwd_password.hash(password)

    def verify_password(hashed_password, plain_password):
        return pwd_password.verify(hashed_password, plain_password)


async def publish_message(message, queues_name, connetcion: aio_pika.RobustConnection):
    async with connetcion.channel() as channel:

        queue_name = queues_name
        await channel.declare_queue(queue_name, durable=True)

        response = message

        log.warn("Message published succsesfully %s", response)
        await channel.default_exchange.publish(
            aio_pika.Message(body=response.encode(), delivery_mode=2),
            routing_key=queue_name,
        )

        return message
