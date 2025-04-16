from lightning_client.client import LightningClient
from google.protobuf.json_format import MessageToJson
import codecs
import json
import os


alice = LightningClient(
    rpc_port=10001,
    cert_path=os.path.expanduser('~/Library/Application Support/Lnd/tls.cert'),
    macaroon_path=os.path.expanduser('~/repos/lightning-ai/dev/alice/data/chain/bitcoin/simnet/admin.macaroon')
)

charlie = LightningClient(
    rpc_port=10003,
    cert_path=os.path.expanduser('~/Library/Application Support/Lnd/tls.cert'),
    macaroon_path=os.path.expanduser('~/repos/lightning-ai/dev/charlie/data/chain/bitcoin/simnet/admin.macaroon')
)

alice_pubkey = alice.GetInfo(alice.GetInfoRequest()).identity_pubkey
print(f'Alice: {alice_pubkey}')
alice_pubkey_bytes = codecs.decode(alice_pubkey, 'hex')

#print(MessageToJson(charlie.ListChannels(charlie.ListChannelsRequest())))
#print(MessageToJson(charlie.ListPeers(charlie.ListPeersRequest())))

#invoice = alice.AddInvoice(alice.Invoice(
#    memo='invoice from alice to charlie',
#    is_amp=True,
#))

#print(f'Invoice: {MessageToJson(invoice)}')

for response in charlie.RouterSendPaymentV2(charlie.RouterSendPaymentRequest(
    dest=alice_pubkey_bytes,
    fee_limit_sat=10,
    #payment_request=invoice.payment_request,
    amt=100,
    amp=True,
    timeout_seconds=60,
)):
    print(response)