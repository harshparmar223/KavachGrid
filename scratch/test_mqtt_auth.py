import asyncio
import aiomqtt

async def test():
    try:
        async with aiomqtt.Client(hostname="localhost", port=1883, username="kavachgrid", password="change_me_in_production") as c:
            print("Connected WITH auth!")
    except Exception as e:
        print("Failed WITH auth:", e)

    try:
        async with aiomqtt.Client(hostname="localhost", port=1883) as c:
            print("Connected WITHOUT auth!")
    except Exception as e:
        print("Failed WITHOUT auth:", e)

asyncio.run(test())
