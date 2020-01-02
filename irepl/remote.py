import zmq


def lcg(mod, a, c, seed):
    """Linear congruential generator."""
    while True:
        seed = (a * seed + c) % mod
        yield seed

#  open_port = lcg(mod=65536, a=33219, c=1, seed=5000)


class RemoteMixin(object):
    def __init__(self, **kwargs):
        super(RemoteMixin, self).__init__(**kwargs)
        self.config = kwargs['config']
        self.initialize_listener(
            self.config['lang'],
            kwargs.get('host', "tcp://localhost"),
            kwargs.get('port', 5536)
        )

    def initialize_listener(self, lang, host, port):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt_string(zmq.SUBSCRIBE, lang)
        socket.connect(f"{host}:{port}")
        self.socket = socket
        self.port = port
        self.host = host

    def get_input(self):
        print(f"\n--- waiting for input on {self.host}:{self.port}---")
        s = self.socket.recv_string()
        print(s)
        return s
