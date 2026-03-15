from mcp.server.fastmcp import FastMCP

# Créer un serveur
mcp = FastMCP("Mon Premier Serveur")

# Ajouter un outil simple
@mcp.tool()
def dire_bonjour(nom: str) -> str:
    """Dit bonjour à quelqu'un"""
    return f"Bonjour, {nom} !"

if __name__ == "__main__":
    mcp.run()