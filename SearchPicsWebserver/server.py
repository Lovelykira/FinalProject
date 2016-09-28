from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

import logging
import json

users = {}
logging.basicConfig(level=logging.DEBUG)


class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        """
        When client connects this method updates global users
        @param request: 
        @return: 
        """
        logging.info("Client connecting: {0}".format(request.peer))
        self.user_id = request.params['user_id'][0]
        logging.info("Client user id: {0}".format(self.user_id))
        global users
        users[str(self.user_id)] = self
        logging.info("user messages: {0}".format(users))


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
        The function that subscribes to redis channel and waits for messages. Once one appear the function stores sends it to Web client
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
            was_searched_before = reply['was_searched_before']
            logging.info('user_id: {} value: {}'.format(str(user_id), repr(value)))

            res_message = {'search_phrase':value, 'was_searched_before':was_searched_before}
            users[user_id].sendMessage(json.dumps(res_message).encode('utf8'))
            logging.info('Sent message to client')
           # users[user_id].append(res_message)
            logging.info('users[user_id]: {}'.format(users[user_id]))

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