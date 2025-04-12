# View GRPC Docs: https://github.com/lightningnetwork/lnd/blob/master/docs/grpc/python.md
import codecs
import lightning_client.lightning_pb2 as ln
import lightning_client.lightning_pb2_grpc as lnrpc
import grpc
import os

# Due to updated ECDSA generated tls.cert we need to let gprc know that
# we need to use that cipher suite otherwise there will be a handshake
# error when we communicate with the lnd rpc server.
os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'


class LightningClient(object):
    def __init__(self, cert_path: str, macaroon_path: str, rpc_host: str = 'localhost', rpc_port: int = 10001):
        # Lnd cert is at ~/.lnd/tls.cert on Linux and
        # ~/Library/Application Support/Lnd/tls.cert on Mac
        with open(cert_path, 'rb') as f:
            self.cert = f.read()

        # Lnd admin macaroon is at ~/.lnd/data/chain/bitcoin/simnet/admin.macaroon on Linux and
        # ~/Library/Application Support/Lnd/data/chain/bitcoin/simnet/admin.macaroon on Mac
        with open(macaroon_path, 'rb') as f:
            macaroon_bytes = f.read()
            self.macaroon = codecs.encode(macaroon_bytes, 'hex')

        def metadata_callback(context, callback):
            # for more info see grpc docs
            callback([('macaroon', self.macaroon)], None)

        # build ssl credentials using the cert the same as before
        cert_creds = grpc.ssl_channel_credentials(self.cert)

        # now build meta data credentials
        auth_creds = grpc.metadata_call_credentials(metadata_callback)

        # combine the cert credentials and the macaroon auth credentials
        # such that every call is properly encrypted and authenticated
        combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)

        # finally pass in the combined credentials when creating a channel
        self.host = f'{rpc_host}:{rpc_port}'
        self.channel = grpc.secure_channel(self.host, combined_creds)
        self.stub = lnrpc.LightningStub(self.channel)
        self.available_stubs = {
            'AbandonChannel',
            'AddInvoice',
            'BakeMacaroon',
            'BatchOpenChannel',
            'ChannelAcceptor',
            'ChannelBalance',
            'CheckMacaroonPermissions',
            'CloseChannel',
            'ClosedChannels',
            'ConnectPeer',
            'DebugLevel',
            'DecodePayReq',
            'DeleteAllPayments',
            'DeleteMacaroonID',
            'DeletePayment',
            'DescribeGraph',
            'DisconnectPeer',
            'EstimateFee',
            'ExportAllChannelBackups',
            'ExportChannelBackup',
            'FeeReport',
            'ForwardingHistory',
            'FundingStateStep',
            'GetChanInfo',
            'GetDebugInfo',
            'GetInfo',
            'GetNetworkInfo',
            'GetNodeInfo',
            'GetNodeMetrics',
            'GetRecoveryInfo',
            'GetTransactions',
            'ListAliases',
            'ListChannels',
            'ListInvoices',
            'ListMacaroonIDs',
            'ListPayments',
            'ListPeers',
            'ListPermissions',
            'ListUnspent',
            'LookupHtlcResolution',
            'LookupInvoice',
            'NewAddress',
            'OpenChannelSync',
            'OpenChannel',
            'PendingChannels',
            'QueryRoutes',
            'RegisterRPCMiddleware',
            'RestoreChannelBackups',
            'SendCoins',
            'SendCustomMessage',
            'SendMany',
            'SendPaymentSync',
            'SendPayment',
            'SendToRouteSync',
            'SendToRoute',
            'SignMessage',
            'StopDaemon',
            'SubscribeChannelBackups',
            'SubscribeChannelEvents',
            'SubscribeChannelGraph',
            'SubscribeCustomMessages',
            'SubscribeInvoices',
            'SubscribePeerEvents',
            'SubscribeTransactions',
            'UpdateChannelPolicy',
            'VerifyChanBackup',
            'VerifyMessage',
            'WalletBalance'
        }

    def __getattr__(self, item):
        if item in self.available_stubs:
            return getattr(self.stub, item)
        elif item == 'stub':
            return self.stub
        elif hasattr(ln, item):
            return getattr(ln, item)
        else:
            raise AttributeError(f"{item} is not a valid method of LightningClient")
