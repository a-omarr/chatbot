import asyncio
from api.v1.bot import chat, ChatRequest

async def trigger_failures():
    test_queries = [
        "1234567890",
        "!!!!!!!!!!",
        "xyz abc 987",
        "asdfghjkl",
        "qwert yuiop",
        "--- --- ---",
        "zzz zzz zzz",
        "999 888 777",
        ":) :( :D",
        "poly morph ism"
    ]
    
    print(f"--- Triggering {len(test_queries)} failed interactions ---\n")
    
    for query in test_queries:
        req = ChatRequest(message=query, language="en")
        resp = await chat(req)
        print(f"Query: {query}")
        print(f"Bot Reply: {resp.reply}\n")

if __name__ == "__main__":
    asyncio.run(trigger_failures())
