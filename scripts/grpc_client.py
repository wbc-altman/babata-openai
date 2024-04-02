import asyncio

from client.babata_openai import ping

if __name__ == "__main__":
    asyncio.run(ping())
