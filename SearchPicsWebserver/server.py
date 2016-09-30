from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

import logging
import json


logging.basicConfig(level=logging.DEBUG)
SPIDERS = ['google', 'yandex', 'instagram']
START_STATUS = "IN_PROGRESS"
FINISHED = "FINISHED"
CLIENTS = {}


class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        """
        When client connects this method updates saves.

        @param request: 
        @return: 
        """
        logging.info("Client connecting: {0}".format(request.peer))
       # self.user_id = request.params['user_id'][0]
        logging.info("Client user id: {0}".format(request.params['user_id'][0]))

    def onMessage(self, payload, isBinary):
        """
        When client sends the task_number that was requested, function appends class instance to global CLIENTS dict by
        task_number as key.

        :param payload: input message - requested task number
        :param isBinary:
        :return:
        """
        logging.info("NEW MESSAGE "+repr(payload.decode('utf8')))
        task_number = payload.decode('utf8')
        if task_number in CLIENTS.keys():
            CLIENTS[task_number].append(self)
        else:
            CLIENTS[task_number] = [self, ]
        logging.info("MESSAGES" + repr(CLIENTS))


    def onOpen(self):
        logging.info("WebSocket connection open.")


    def onClose(self, wasClean, code, reason):
        logging.info("WebSocket connection closed: {0}".format(reason))
        self.connection_is_open = False


def main():
    try:
        import asyncio
    except ImportError:
        # Trollius >= 0.3 was renamed
        import trollius as asyncio

    factory = WebSocketServerFactory(u"ws://127.0.0.1:9000")
    factory.protocol = MyServerProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '0.0.0.0', 9000)

    import asyncio_redis

    @asyncio.coroutine
    def redis_subscriber():
        """
        The function that subscribes to redis channel and waits for messages. Once one appears the function checks the
        task_number, stored in it and sends right search_phrase to each Web client that waits for it.
        @return:
        """
        # Create connection
        connection = yield from asyncio_redis.Connection.create(host='127.0.0.1', port=6379)

        # Create subscriber.
        subscriber = yield from connection.start_subscribe()

        # Subscribe to channel.
        yield from subscriber.subscribe(['our-channel'])

        # Inside a while loop, wait for incoming events.
        while True:
            reply = yield from subscriber.next_published()
            logging.info('Received: {} on channel {}'.format(repr(reply.value), repr(reply.channel)))
            reply = json.loads(reply.value)
            user_id = str(reply['user_id'])
            value = repr(reply['search_phrase'])
            task_number = str(reply['task_number'])
            res_message = json.dumps({'search_phrase':value}).encode('utf8')
            logging.info('clients[task_number]:{}'.format(CLIENTS[task_number]))
            for client in CLIENTS[task_number]:
                client.sendMessage(res_message)
            logging.info('Sent message to client')

        # When finished, close the connection.
        connection.close()

    loop = asyncio.get_event_loop()
    server = asyncio.async(coro)
    subscriber = asyncio.async(redis_subscriber())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()


if __name__ == '__main__':
    main()