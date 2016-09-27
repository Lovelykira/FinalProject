from autobahn.asyncio.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory

import logging
import json

user_messages = {}
logging.basicConfig(level=logging.DEBUG)


class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        """
        When client connects this method updates global user_messages and sets connection_is_open to True
        @param request: 
        @return: 
        """
        logging.info("Client connecting: {0}".format(request.peer))
        self.connection_is_open = True
        self.user_id = request.params['user_id'][0]
        logging.info("Client user id: {0}".format(self.user_id))
        global user_messages
        user_messages[str(self.user_id)] = []
        logging.info("user messages: {0}".format(user_messages))



    def onOpen(self):
        """
        When connection is open this method checks if there are new messages from redis-server and if so sends it to
        the client.
        @return:
        """
        logging.info("WebSocket connection open.")

        def send():
            global messages
            while len(user_messages[self.user_id]):
                if not self.connection_is_open:
                    return
                #result_mes = {'phrase_info':user_messages[self.user_id][0]}
                self.sendMessage(json.dumps(user_messages[self.user_id][0]).encode('utf8'))
                user_messages[self.user_id] = user_messages[self.user_id][1:]
                logging.info('Sent message to client')
            self.factory.loop.call_later(5, send)

        send()

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
        The function that subscribes to redis channel and waits for messages. Once one appear the function stores it in
        global messages.
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
            num_spiders = repr(reply['num_spiders'])
            logging.info('user_id: {} value: {}'.format(str(user_id), repr(value)))
            logging.info('type [user_id]: {}'.format(type(user_id)))

            res_message = {'search_phrase':value, 'num_spiders':num_spiders}
            user_messages[user_id].append(res_message)
            logging.info('user_messages[user_id]: {}'.format(user_messages[user_id]))

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