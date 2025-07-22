# -----------IMPORTS-----------
import os
from openai import AzureOpenAI
import json
from mcp import ClientSession

from dotenv import load_dotenv

from gui.window import ChatWindow


# ----------INITIALIZATION-----------
load_dotenv()

SYSTEM_PROMPT = """
You are a Trello Assistant AI that helps users manage their Trello boards using natural language commands. You have access to tools that let you list boards, view cards, create new cards, move cards between lists, rename items, assign members, set due dates, and mark cards as done.

Your tone is concise, helpful, and professional. When responding:
- Summarize actions taken or explain what information was retrieved.
- If more detail is needed, do not ask follow-up questions. Instead, ask the user to send their query again with the information that is needed.
- Always prioritize clarity and brevity.

Examples of tasks you handle:
- “Create a card called 'Write report' in the 'To Do' list of my 'Work' board.”
- “Move the 'Fix login bug' card from 'In Progress' to 'Done'.”
- “List all cards in the 'Bugs' list.”
- "Add the 'Data Viz' label to the 'seaborn' card."

Assume the user knows how Trello works but prefers speaking naturally instead of using the UI. Interpret vague or partial input sensibly and confirm unclear intents before acting.
The name of the Trello board is Dave's Corner.
If the user does not give precisions on the value of a parameter and a default value is given for the parameter, use the default value and do not ask for more information.
If you have links in your response, format them as "Description of link (link)".
"""


# ----------CLIENT CLASS-----------
class MCPClient:
    """Client class for processing queries"""

    def __init__(self, exit_stack):
        """Initialise MCP client

        Args:
            exit_stack (ASyncStack): session manager for async context
        """
        self.session: ClientSession | None = None
        # Session manager
        self.exit_stack = exit_stack
        # gpt-4o model
        self.azure = AzureOpenAI(
            api_version="2024-12-01-preview",
            azure_endpoint="https://light-rag-models.openai.azure.com/",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
        # GUI window
        self.window: ChatWindow | None = None

    async def process_query(self, query: str) -> str:
        """Processes a query (one turn)

        Args:
            query (str): user query to process

        Returns:
            str: result reprocessed by LLM
        """

        # Initialise message history with system prompt and user query
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.append({"role": "user", "content": query})

        # Format tools
        response = await self.session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in response.tools
        ]

        # Feed system prompt, query and tools to LLM
        response = self.azure.chat.completions.create(
            messages=messages,
            tool_choice="auto",
            tools=available_tools,
            max_tokens=1000,
            model="gpt-4o",
        )

        tool_results = []
        final_text = []

        # While LLM calls tools
        while True:
            # Collect latest message
            message = response.choices[0].message

            # Process potential tool call
            if message.tool_calls:
                for call in message.tool_calls:
                    # Load tool
                    tool_name = call.function.name
                    tool_args = json.loads(call.function.arguments)
                    tool_desc = "".join(
                        [
                            t["function"]["description"]
                            for t in available_tools
                            if t["function"]["name"] == tool_name
                        ]
                    )
                    # Does the tool need consent?
                    needs_consent = "[consent]" in tool_desc.lower()

                    # Is the tool a prompt?
                    is_prompt = "[prompt]" in tool_desc.lower()

                    # Ask user for consent
                    if not needs_consent:
                        consent = "OK"
                    else:
                        text = f"Dave wants to launch {'prompt' if is_prompt else ''} {tool_name} with arguments: {tool_args}.\nThis tool has the following description: {tool_desc}.\n"
                        text += "Do you consent to the execution? [Y/N]: "
                        consent = await self.window.ask_user_consent(text)

                    # User consents
                    if consent.upper() == "Y" or consent.upper() == "OK":
                        # Collect tool call response
                        result = await self.session.call_tool(tool_name, tool_args)

                        # Collect logs and tool results
                        tool_results.append({"call": tool_name, "result": result})
                        final_text.append(
                            f"[Called {'prompt' if is_prompt else 'tool'} {tool_name} with arguments: {tool_args}].\n"
                        )

                        # Update messages
                        messages.append(
                            {
                                "role": "assistant",
                                "tool_calls": [
                                    {
                                        "id": call.id,
                                        "type": "function",
                                        "function": {
                                            "name": tool_name,
                                            "arguments": json.dumps(tool_args),
                                        },
                                    }
                                ],
                            }
                        )

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call.id,
                                "content": result.content,
                            }
                        )

                        # Feed LLM tool call results
                        response = self.azure.chat.completions.create(
                            model="gpt-4o",
                            max_tokens=1000,
                            messages=messages,
                            tools=available_tools,
                            tool_choice="auto",
                        )

                    # No consent obtained
                    else:
                        final_text.append(
                            "Dave did not obtain the necessary consent for execution."
                        )
                        return "\n".join(final_text)

            # No tool call (end of turn)
            elif message.content:
                final_text.append(message.content)
                break
        result_text = "\n".join(final_text)
        result_text = result_text.rstrip("\n")
        return result_text
