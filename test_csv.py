import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python3",
        args=["server.py"],
        cwd="/home/claude/demo-mcp",
    )
    print("=" * 70)
    print("  TEST DU TOOL : read_csv")
    print("=" * 70)
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("\n[OK] Connecte !\n")

            # Test 1 : Lire tout le CSV
            print("-" * 70)
            print("TEST 1 : Lire tout le CSV")
            print("  -> 'Montre-moi le fichier equipe.csv'")
            print("-" * 70)
            r = await session.call_tool("read_csv", {
                "params": {"filename": "equipe.csv"}
            })
            print(r.content[0].text)
            print()

            # Test 2 : Filtrer par statut
            print("-" * 70)
            print("TEST 2 : Filtrer par statut = 'en cours'")
            print("  -> 'Qui travaille sur des projets en cours ?'")
            print("-" * 70)
            r = await session.call_tool("read_csv", {
                "params": {
                    "filename": "equipe.csv",
                    "filter_column": "statut",
                    "filter_value": "en cours"
                }
            })
            print(r.content[0].text)
            print()

            # Test 3 : Filtrer par personne + colonnes specifiques
            print("-" * 70)
            print("TEST 3 : Projets de Marie (colonnes: nom, projet, statut)")
            print("  -> 'Sur quels projets travaille Marie ?'")
            print("-" * 70)
            r = await session.call_tool("read_csv", {
                "params": {
                    "filename": "equipe.csv",
                    "filter_column": "nom",
                    "filter_value": "Marie",
                    "columns": ["nom", "projet", "statut", "heures"]
                }
            })
            print(r.content[0].text)
            print()

            # Test 4 : Projets termines, 3 premiers
            print("-" * 70)
            print("TEST 4 : Projets termines (limit 3)")
            print("  -> 'Quels projets sont termines ?'")
            print("-" * 70)
            r = await session.call_tool("read_csv", {
                "params": {
                    "filename": "equipe.csv",
                    "filter_column": "statut",
                    "filter_value": "termine",
                    "limit": 3
                }
            })
            print(r.content[0].text)

    print("\n" + "=" * 70)
    print("  read_csv fonctionne !")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
