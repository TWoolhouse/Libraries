from .data import Data

async def echo(node: 'DataInterface', data: Data) -> bool:
    await node.send(data)
    return True

import time

async def ping(node: 'DataInterface', data: Data) -> bool:
    await node.send(time.time() - float(data.data), "ping")
    return True
