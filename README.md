# Bitcoin Lightning Client for Agentic Workflows

GitHub: https://github.com/ehallmark/btc-lightning-client

### Motivation

This repository exists as a lightweight Python client to easily connect with a Lightning Network Daemon (`lnd`). This library is used by https://github.com/ehallmark/btc-lightning-tools for wrapping `lnd` in an MCP ([Model Context Protocol](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)) server to be used with Agentic systems. 

### Prerequisites

+ You must have a running Lightning Network Daemon (`lnd`) running on your machine. For more information on `lnd`, visit https://github.com/lightningnetwork/lnd.
+ Python >= 3.9
+ `pip`, `uv`, or similar for package management.

### Installation

```bash
# with pip
pip install lightning-client-mcp

# or with uv
uv add lightning-client-mcp
```

### Example Usage

```python
import os
from google.protobuf.json_format import MessageToJson
from lightning_client import LightningClient

# Initialize the client
client = LightningClient(
    rpc_port=10003,
    cert_path=os.path.expanduser('~/Library/Application Support/Lnd/tls.cert'),
    macaroon_path=os.path.expanduser('~/repos/lightning-ai/dev/charlie/data/chain/bitcoin/simnet/admin.macaroon')
)

# Call an RPC method
print(MessageToJson(client.ListChannels(client.ListChannelsRequest())))

# Output
{
  "channels": [
    {
      "active": true,
      "remotePubkey": "abc...",
      ...
    }
  ]
}
```

