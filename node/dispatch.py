from .data import Data
import time

async def echo(node: 'DataInterface', data: Data) -> bool:
    await node.send(data)
    return True

async def ping(node: 'DataInterface', data: Data) -> bool:
    await node.send(time.time() - float(data.data), "ping")
    return True
