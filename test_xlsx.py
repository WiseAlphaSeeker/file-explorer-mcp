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
    print("  TEST DU TOOL : edit_xlsx")
    print("=" * 60)
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("\n[OK] Connecte ! 7 tools disponibles.\n")

            # Test 1 : Modifier un nom (cellule B8)
            print("-" * 60)
            print("TEST 1 : Changer le nom en B8")
            print("  -> 'Renomme Hugo Moreau en Hugo Martin'")
            print("-" * 60)
            r = await session.call_tool("edit_xlsx", {
                "params": {
                    "filename": "equipe.xlsx",
                    "cell": "B8",
                    "value": "Hugo Martin"
                }
            })
            print(r.content[0].text)
            print()

            # Test 2 : Modifier un statut (cellule E8)
            print("-" * 60)
            print("TEST 2 : Changer le statut en E8")
            print("  -> 'Passe Hugo en termine'")
            print("-" * 60)
            r = await session.call_tool("edit_xlsx", {
                "params": {
                    "filename": "equipe.xlsx",
                    "cell": "E8",
                    "value": "termine"
                }
            })
            print(r.content[0].text)
            print()

            # Test 3 : Modifier des heures (cellule F8)
            print("-" * 60)
            print("TEST 3 : Mettre 185 heures en F8")
            print("  -> 'Hugo a fait 185 heures'")
            print("-" * 60)
            r = await session.call_tool("edit_xlsx", {
                "params": {
                    "filename": "equipe.xlsx",
                    "cell": "F8",
                    "value": "185"
                }
            })
            print(r.content[0].text)
            print()

            # Test 4 : Erreur - cellule invalide
            print("-" * 60)
            print("TEST 4 : Fichier inexistant")
            print("-" * 60)
            r = await session.call_tool("edit_xlsx", {
                "params": {
                    "filename": "inexistant.xlsx",
                    "cell": "A1",
                    "value": "test"
                }
            })
            print(r.content[0].text)

    print("\n" + "=" * 60)
    print("  edit_xlsx fonctionne !")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
