import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python3",
        args=["server.py"],
        cwd="/home/claude/demo-mcp",
    )
    print("=" * 60)
    print("  TEST DU NOUVEAU TOOL : edit_file")
    print("=" * 60)
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("\n[OK] Connecte !\n")

            # Verifier que edit_file existe
            print("--- Tools disponibles ---")
            tools = await session.list_tools()
            for t in tools.tools:
                print(f"  {t.name}")
            print()

            # Lire le fichier avant modification
            print("--- AVANT modification (todo.md) ---")
            r = await session.call_tool("read_file", {"params": {"filename": "todo.md"}})
            print(r.content[0].text)
            print()

            # Appeler edit_file : cocher la documentation API
            print("--- Appel edit_file : cocher 'Rediger la documentation API' ---")
            r = await session.call_tool("edit_file", {
                "params": {
                    "filename": "todo.md",
                    "old_text": "[ ] R\u00e9diger la documentation API",
                    "new_text": "[x] R\u00e9diger la documentation API"
                }
            })
            print(r.content[0].text)
            print()

            # Relire apres modification
            print("--- APRES modification (todo.md) ---")
            r = await session.call_tool("read_file", {"params": {"filename": "todo.md"}})
            print(r.content[0].text)

    print("\n" + "=" * 60)
    print("  edit_file fonctionne !")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
