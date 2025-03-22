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

    def GetInfo(self):
        return self.stub.GetInfo(ln.GetInfoRequest())

    def WalletBalance(self):
        return self.stub.WalletBalance(ln.WalletBalanceRequest())
    
    def ListPeers(self):
        return self.stub.ListPeers(ln.ListPeersRequest())
    
    def ListChannels(self):
        return self.stub.ListChannels(ln.ListChannelsRequest())
    
    def ConnectPeer(self, pubkey: str, host: str):
        return self.stub.ConnectPeer(ln.ConnectPeerRequest(addr=ln.LightningAddress(pubkey=pubkey, host=host)))
    
    def AddInvoice(self, amount: int):
        return self.stub.AddInvoice(ln.Invoice(value=amount))
    
    def SendPayment(self, payment_request: str):
        return self.stub.SendPaymentSync(ln.SendRequest(payment_request=payment_request))

    def ListInvoices(self):
        return self.stub.ListInvoices(ln.ListInvoiceRequest())
    
    # Helper methods
    def get_pubkey(self):
        return self.GetInfo().identity_pubkey
    
    def get_host(self):
        return self.host
    
    def create_invoice(self, amount: int):
        invoice = self.AddInvoice(amount)
        return {
            'payment_request': invoice.payment_request,
            'r_hash_str': codecs.encode(invoice.r_hash, 'hex').decode('utf-8')
        }
    
    def pay_invoice(self, payment_request: str):
        return self.SendPayment(payment_request)
    
    def check_invoice_is_settled(self, r_hash: bytes):
        return self.stub.LookupInvoice(ln.PaymentHash(r_hash=r_hash)).settled
    
    def get_wallet_balance(self):
        return self.WalletBalance().confirmed_balance


