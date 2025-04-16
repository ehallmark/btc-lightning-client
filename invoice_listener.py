from lightning_client.client import LightningClient
from google.protobuf.json_format import MessageToJson
import os


alice = LightningClient(
    rpc_port=10001,
    cert_path=os.path.expanduser('~/Library/Application Support/Lnd/tls.cert'),
    macaroon_path=os.path.expanduser('~/repos/lightning-ai/dev/alice/data/chain/bitcoin/simnet/admin.macaroon')
)


for response in alice.SubscribeInvoices(alice.InvoiceSubscription()):
    print(MessageToJson(response))
