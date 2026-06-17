import asyncio

from app.analyzer import analyze_comment


async def main():
    resultado = await analyze_comment(
        "The professor explains very clearly and is always punctual."
    )

    print(resultado)


asyncio.run(main())
