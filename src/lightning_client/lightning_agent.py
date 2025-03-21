from dotenv import load_dotenv
from typing import Literal
import getpass
import os
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_anthropic import ChatAnthropic
from lightning_client.client import LightningClient
from langchain_core.messages import ToolMessage
import codecs
import json


load_dotenv()  # take environment variables from .env.


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


_set_env("ANTHROPIC_API_KEY")


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


#invoice = charlie.AddInvoice(100)
#print(f"Settled: {charlie.check_invoice_is_settled(invoice.r_hash)}")
#client.pay_invoice(invoice.payment_request)
#print(f"Settled: {charlie.check_invoice_is_settled(invoice.r_hash)}")



@tool
def pay_invoice(payment_request: str):
    """Pay a payment request."""
    alice.pay_invoice(payment_request)
    return "Payment sent."


@tool
def create_invoice(amount: int):
    """Create an invoice for the given amount and return the invoice payment request."""
    return charlie.create_invoice(amount)


@tool
def check_invoice_is_settled(r_hash_str: str):
    """Check if an invoice is settled."""
    r_hash = codecs.decode(r_hash_str, 'hex')
    return charlie.check_invoice_is_settled(r_hash)


tools = [pay_invoice, create_invoice, check_invoice_is_settled]
tool_node = ToolNode(tools)

model_with_tools = ChatAnthropic(
    model="claude-3-haiku-20240307", temperature=0
).bind_tools(tools)


def should_continue(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


def call_model(state: MessagesState):
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}


workflow = StateGraph(MessagesState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

app = workflow.compile()

invoice = None

# example with a multiple tool calls in succession
for chunk in app.stream(
    {"messages": [("human", "create an invoice with amount 100")]},
    stream_mode="values",
):
    if chunk["messages"][-1].name == 'create_invoice':
        invoice = chunk["messages"][-1].content
        print(f'found payment request: {invoice}')
    chunk["messages"][-1].pretty_print()

if invoice:
    invoice = json.loads(invoice)
    
    for chunk in app.stream(
        {"messages": [("human", f"check the status of payment request {invoice['r_hash_str']}")]},
        stream_mode="values",
    ):
        chunk["messages"][-1].pretty_print()

    for chunk in app.stream(
        {"messages": [("human", f"pay the invoice with payment request {invoice['payment_request']}")]},
        stream_mode="values",
    ):
        chunk["messages"][-1].pretty_print()

    for chunk in app.stream(
        {"messages": [("human", f"check the status of payment request {invoice['r_hash_str']}")]},
        stream_mode="values",
    ):
        chunk["messages"][-1].pretty_print()