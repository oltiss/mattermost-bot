import asyncio
import ollama
import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.types import CallToolResult
import json
import re

# Wczytaj zmienne środowiskowe
load_dotenv()


def parse_tool_call_from_content(content: str) -> dict | None:
    """
    Próbuje wyekstrahować tool call z treści tekstowej.
    Ollama czasami zwraca JSON jako tekst zamiast struktury tool_calls.
    """
    if not content:
        return None

    # Usuń markdown code blocks jeśli są
    content_clean = content
    if "```" in content:
        # Wyciągnij zawartość z bloków kodu
        import re as regex
        code_match = regex.search(r'```(?:json)?\s*(.*?)\s*```', content, regex.DOTALL)
        if code_match:
            content_clean = code_match.group(1)

    # Znajdź wszystkie możliwe pozycje początkowe JSON
    # Próbuj parsować od każdego '{'
    start_positions = [i for i, c in enumerate(content_clean) if c == '{']

    for start in start_positions:
        # Znajdź pasujący nawias zamykający
        depth = 0
        end = start
        for i, c in enumerate(content_clean[start:], start):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        if end > start:
            try:
                candidate = content_clean[start:end]
                data = json.loads(candidate)

                # Sprawdź czy to wygląda jak tool call
                if isinstance(data, dict) and "name" in data:
                    args = data.get("parameters") or data.get("arguments", {})
                    print(f"📋 Sparsowano tool call z tekstu: {data['name']}")
                    return {
                        "function": {
                            "name": data["name"],
                            "arguments": args if isinstance(args, dict) else {}
                        }
                    }
            except json.JSONDecodeError:
                continue

    return None

# KONFIGURACJA ADRESÓW (Domyślne)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")

async def process_query(prompt: str, ollama_host: str = OLLAMA_HOST, mcp_url: str = MCP_SERVER_URL, model: str = OLLAMA_MODEL) -> str:
    print(f"🔗 Łączenie z MCP (Narzędzia) pod: {mcp_url}...")

    ollama_client = ollama.Client(host=ollama_host)
    messages = [
        {"role": "system", "content": "You are a Database Expert Assistant. \n\nCORE PROTOCOL:\n1. When asked for data, your FIRST action MUST be `get_database_schema(table_name=...)` to see columns.\n2. DO NOT assume a table has an 'id' column. It might be 'id_abonent', 'uuid', etc.\n3. After checking schema, use `query_database(query=...)` with valid SQL to get the data.\n4. If you hit an error, use `get_database_schema` to debug.\n\nUse tools directly. Do not describe your plan."},
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

                # 3. Pętla agentic - wykonuj tool calls dopóki model nie da finalnej odpowiedzi
                MAX_ITERATIONS = 10
                iteration = 0

                while iteration < MAX_ITERATIONS:
                    iteration += 1
                    print(f"🔄 Iteracja {iteration}/{MAX_ITERATIONS}")

                    # Wysyłamy zapytanie do Ollama
                    response = ollama_client.chat(
                        model=model,
                        messages=messages,
                        tools=ollama_tools
                    )

                    message = response["message"]
                    content = message.get("content", "")

                    # Pobieramy tool calls - strukturalnie lub z treści
                    tool_calls = message.get("tool_calls", [])

                    # Fallback: jeśli brak tool_calls, sprawdź czy content zawiera JSON
                    if not tool_calls and content:
                        parsed_call = parse_tool_call_from_content(content)
                        if parsed_call:
                            print(f"⚠️ Wykryto tool call w treści tekstowej (fallback)")
                            tool_calls = [parsed_call]

                    # Jeśli brak tool calls - to jest finalna odpowiedź
                    if not tool_calls:
                        print(f"🤖 Odpowiedź finalna: {content}")
                        return content

                    # Dodajemy odpowiedź modelu do historii
                    messages.append(message)

                    # Wykonujemy wszystkie tool calls
                    for tool_call in tool_calls:
                        fn_name = tool_call["function"]["name"]
                        args = tool_call["function"]["arguments"]

                        print(f"🤖 Model prosi o: {fn_name} {args}")

                        # Wykonujemy narzędzie na serwerze MCP
                        result = await session.call_tool(fn_name, arguments=args)

                        # Pobieramy treść wyniku
                        tool_output = result.content[0].text
                        print(f"🔧 Wynik: {tool_output[:500]}..." if len(tool_output) > 500 else f"🔧 Wynik: {tool_output}")

                        # Zwracamy wynik do modelu
                        messages.append({
                            "role": "tool",
                            "content": str(tool_output),
                        })

                # Jeśli przekroczono limit iteracji
                print("⚠️ Przekroczono limit iteracji")
                return "Przekroczono maksymalną liczbę kroków. Spróbuj ponownie z prostszym zapytaniem."

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
