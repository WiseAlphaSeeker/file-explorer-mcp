"""Client MCP de demonstration."""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python3",
        args=["server.py"],
        cwd="/home/claude/demo-mcp",
    )

    print("=" * 60)
    print("  DEMO CLIENT MCP")
    print("=" * 60)

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("\n[OK] Connecte au serveur MCP !\n")

            # ETAPE 1 : Decouvrir les tools
            print("-" * 60)
            print("ETAPE 1 : Decouverte des tools")
            print("-" * 60)
            tools_result = await session.list_tools()
            for tool in tools_result.tools:
                desc = (tool.description or "")[:80]
                print(f"  Tool: {tool.name}")
                print(f"    Desc: {desc}")
                print()

            # ETAPE 2 : Appeler list_files
            print("-" * 60)
            print("ETAPE 2 : Appel list_files")
            print("  -> 'Quels fichiers sont disponibles ?'")
            print("-" * 60)
            result = await session.call_tool("list_files", {})
            print(f"\n{result.content[0].text}\n")

            # ETAPE 3 : Appeler read_file
            print("-" * 60)
            print("ETAPE 3 : Appel read_file(notes.txt)")
            print("  -> 'Montre-moi notes.txt'")
            print("-" * 60)
            result = await session.call_tool("read_file", {"params": {"filename": "notes.txt"}})
            print(f"\n{result.content[0].text}\n")

            # ETAPE 4 : Appeler search_in_files
            print("-" * 60)
            print("ETAPE 4 : Appel search_in_files(Marie)")
            print("  -> 'Cherche Marie dans mes fichiers'")
            print("-" * 60)
            result = await session.call_tool("search_in_files", {"params": {"query": "Marie", "case_sensitive": False}})
            print(f"\n{result.content[0].text}\n")

            # ETAPE 5 : Appeler file_stats
            print("-" * 60)
            print("ETAPE 5 : Appel file_stats(todo.md)")
            print("  -> 'Stats du fichier todo.md ?'")
            print("-" * 60)
            result = await session.call_tool("file_stats", {"params": {"filename": "todo.md"}})
            print(f"\n{result.content[0].text}\n")

            # ETAPE 6 : Lire une resource
            print("-" * 60)
            print("ETAPE 6 : Lecture resource file://config.json")
            print("  -> L'appli injecte du contexte")
            print("-" * 60)
            resource = await session.read_resource("file://config.json")
            print(f"\n{resource.contents[0].text}\n")

    print("=" * 60)
    print("  DEMO TERMINEE !")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
