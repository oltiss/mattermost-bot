import asyncio
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.types import CallToolResult

# KONFIGURACJA ADRESÓW (Domyślne)
OLLAMA_HOST = "http://localhost:11434"
MCP_SERVER_URL = "http://localhost:8000/sse"
MODEL_NAME = "llama3.1:latest"

async def process_query(prompt: str, ollama_host: str = OLLAMA_HOST, mcp_url: str = MCP_SERVER_URL, model: str = MODEL_NAME) -> str:
    print(f"🔗 Łączenie z MCP (Narzędzia) pod: {mcp_url}...")

    ollama_client = ollama.Client(host=ollama_host)
    messages = [
        {"role": "system", "content": "You are a helpful assistant. You have access to tools for querying a database, but you should ONLY use them when the user explicitly asks for data or performs an action that requires them. For greetings (like 'hi', 'hello'), general questions, or small talk, respond naturally as a chat assistant without using or mentioning tools."},
        {"role": "user", "content": prompt}
    ]

    try:
        # Łączymy się z serwerem MCP
        async with sse_client(mcp_url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()

                # 1. Pobieramy listę dostępnych narzędzi
                tools_list = await session.list_tools()
                print(f"✅ Pobrano {len(tools_list.tools)} narzędzi.")

                # 2. Konwertujemy format MCP na format Ollama
                ollama_tools = []
                for tool in tools_list.tools:
                    ollama_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    })

                # 3. Wysyłamy zapytanie do Ollama
                response = ollama_client.chat(
                    model=model,
                    messages=messages,
                    tools=ollama_tools
                )

                messages.append(response["message"])

                # 4. Jeśli Ollama chce użyć narzędzia...
                if response["message"].get("tool_calls"):
                    for tool_call in response["message"]["tool_calls"]:
                        fn_name = tool_call["function"]["name"]
                        args = tool_call["function"]["arguments"]

                        print(f"🤖 Model prosi o: {fn_name} {args}")

                        # 5. Wykonujemy narzędzie na serwerze MCP
                        result = await session.call_tool(fn_name, arguments=args)

                        # Pobieramy treść wyniku
                        tool_output = result.content[0].text
                        print(f"🔧 Wynik: {tool_output}")

                        # 6. Zwracamy wynik do modelu
                        messages.append({
                            "role": "tool",
                            "content": str(tool_output),
                        })

                    # Finalna odpowiedź modelu
                    final_response = ollama_client.chat(
                        model=model,
                        messages=messages
                    )
                    final_content = final_response['message']['content']
                    print(f"🤖 Odpowiedź: {final_content}")
                    return final_content
                else:
                    content = response['message']['content']
                    print(f"🤖 Odpowiedź: {content}")
                    return content

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Błąd: {e}")
        error_details = str(e)
        if hasattr(e, 'exceptions'):
            error_details += f" ({'; '.join(str(sub) for sub in e.exceptions)})"
        return f"Wystąpił błąd podczas przetwarzania: {error_details}"

if __name__ == "__main__":
    # Test lokalny
    response = asyncio.run(process_query("Jaka jest pogoda w Warszawie?"))
    print(f"Final response: {response}")
