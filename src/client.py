# -----------IMPORTS-----------
import os
from openai import AzureOpenAI
from typing import Optional
import json
import asyncio
from loguru import logger

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

from dotenv import load_dotenv

from gui import ChatBubble, ChatWindow
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton, QLineEdit
from PyQt6.QtCore import QTimer, Qt, QCoreApplication
from qasync import asyncSlot, QEventLoop, QApplication

#----------INITIALIZATION-----------
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
"""


class MCPClient():
    def __init__(self,exit_stack):
        self.session: Optional[ClientSession] = None
        # Session manager
        self.exit_stack = exit_stack
        # gpt-4o model
        self.azure = AzureOpenAI(
            api_version='2024-12-01-preview',
            azure_endpoint='https://light-rag-models.openai.azure.com/',
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
        # GUI window
        self.window: Optional[ChatWindow] = None

    @asyncSlot()
    async def connect_to_server(self, server_path: str) -> None:

        # Collect server parameters
        server_params = StdioServerParameters(
            command='python',
            args=[server_path],
            env=None
        )

        # Launch servers
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))

        # Load read and write channels
        self.stdio, self.write = stdio_transport

        # Format in MCP
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        # Initialise session
        await self.session.initialize()

        logger.info("Session initialised. Collecting tools")

        # Collect tools and prompts
        response = await self.session.list_tools()
        tools = response.tools
        text = "Connected to server with tools:\n"
        for tool in tools:
            if '[prompt]' not in tool.description.lower():
                text += f'-{tool.name}\n'

        # text+='\nWith the following prompts:\n'
        # print('\nWith the following prompts:\n')
        for tool in tools:
            if '[prompt]' in tool.description.lower():
                text += f'-{tool.name}\n'
                # print(f'-{tool.name}\n')

        await self.window.receive_message(text)
        return None

    @asyncSlot()
    async def process_query(self, query: str) -> str:
        logger.info("Launched process_query function.")
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        messages.append({'role': 'user', 'content': query})
        # await asyncio.sleep(0.001)
        # Format tools
        response = await self.session.list_tools()
        logger.info("Got tools")
        available_tools = [{
            'type': 'function',
            'function': {
                'name': tool.name,
                'description': tool.description,
                'parameters': tool.inputSchema
            }
        } for tool in response.tools]

        # Feed query and tools to LLM
        response = self.azure.chat.completions.create(
            messages=messages,
            tool_choice='auto',
            tools=available_tools,
            max_tokens=1000,
            model='gpt-4o'
        )
        # await asyncio.sleep(0.1)
        logger.info("Query and tools fed to model.")

        tool_results = []
        final_text = []

        # While LLM still calls tools
        while True:
            # Collect latest message
            message = response.choices[0].message

            # Process tool
            if message.tool_calls:
                for call in message.tool_calls:
                    tool_name = call.function.name
                    tool_args = json.loads(call.function.arguments)

                    tool_desc = ''.join(
                        [t['function']['description']
                            for t in available_tools if t['function']['name'] == tool_name]
                    )
                    needs_consent = '[consent]' in tool_desc.lower()

                    is_prompt = '[prompt]' in tool_desc.lower()

                    text = f"Dave wants to launch {'prompt' if is_prompt else ''} {tool_name} with arguments: {tool_args}.\nThis tool has the following description: {tool_desc}.\n"
                    text += "Do you consent to the execution? [Y/N]: "
                    logger.info("Launching receive message")
                    if needs_consent == False:
                        consent = "OK"
                    else:
                        consent = await self.window.ask_user_consent(text)

                    if consent.upper() == "Y" or consent.upper() == "OK":

                        # Collect tool call response
                        logger.info("Launching tool call.")
                        result = await self.session.call_tool(tool_name, tool_args)
                        logger.info("Received tool call response.")

                        tool_results.append(
                            {'call': tool_name, 'result': result})
                        final_text.append(
                            f"[Called {'prompt' if is_prompt else 'tool'} {tool_name} with arguments: {tool_args}].")

                        # Update messages
                        messages.append({
                            'role': 'assistant',
                            'tool_calls': [{
                                'id': call.id,
                                'type': 'function',
                                'function': {
                                    'name': tool_name,
                                    'arguments': json.dumps(tool_args)
                                }
                            }]
                        })

                        messages.append({
                            'role': 'tool',
                            'tool_call_id': call.id,
                            'content': result.content
                        })

                        # Feed LLM tool call results
                        response = self.azure.chat.completions.create(
                            model='gpt-4o',
                            max_tokens=1000,
                            messages=messages,
                            tools=available_tools,
                            tool_choice='auto'
                        )
                        logger.info("Fed LLM tool call results.")

                    # No consent obtained
                    else:
                        final_text.append(
                            "Dave did not obtain the necessary consent for execution.")
                        return '\n'.join(final_text)

            elif message.content:
                final_text.append(message.content)
                break

        return '\n'.join(final_text)

    '''
    async def chat_loop(self):
        while True:
            try:
                
                query = input('\nQuery: ').strip()
                if query.lower() == 'quit':
                    break
                
                response = await self.process_query(query)
                self.window.receive_message(response)
                
                print("\n" + response)
            except Exception as e:
                print(f"Error: {e}")
    '''

    async def shutdown_tasks(self):
        # Set a flag or cancel internal task group
        self._stop = True
        # Await all those background tasks to finish
        await asyncio.gather(*self._background_tasks, return_exceptions=True)

    async def cleanup(self):
        # Closes server connections
        logger.info("Cleaning up client session...")
        # await self.shutdown_tasks()
        await self.exit_stack.aclose()


async def main():
    import sys
    from contextlib import AsyncExitStack

    async with AsyncExitStack() as exit_stack:
        client = MCPClient(exit_stack)
        window = ChatWindow(client)
        window.show()
        client.window = window

        quit_future = asyncio.get_event_loop().create_future()

        def on_quit():
            if not quit_future.done():
                quit_future.set_result(None)
        app.aboutToQuit.connect(on_quit)

        try:
                # Collect server parameters
            server_params = StdioServerParameters(
                command='python',
                args=['server.py'],
                env=None
            )

            # Launch servers
            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))

            # Load read and write channels
            stdio, write = stdio_transport

            # Format in MCP
            session = await exit_stack.enter_async_context(ClientSession(stdio, write))
            client.session = session

            # Initialise session
            await session.initialize()

            logger.info("Session initialised. Collecting tools")

            # Collect tools and prompts
            response = await session.list_tools()
            tools = response.tools
            text = "\nConnected to server with tools:\n"
            for tool in tools:
                if '[prompt]' not in tool.description.lower():
                    text += f'-{tool.name}\n'

            # text+='\nWith the following prompts:\n'
            # print('\nWith the following prompts:\n')
            for tool in tools:
                if '[prompt]' in tool.description.lower():
                    text += f'-{tool.name}\n'
                    # print(f'-{tool.name}\n')

            await window.receive_message(text)
            
            
            logger.info("Connected to server.")
            await quit_future  # Wait for the Qt app to quit
        finally:
            await exit_stack.aclose()
            logger.info("Client session closed.")
            # Do not call app.quit() here

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        main_task = loop.create_task(main())
        try:
            loop.run_forever()
        finally:
            # Wait for main() to finish before cancelling other tasks
            loop.run_until_complete(main_task)
            # Now cancel all other running tasks
            tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
            for task in tasks:
                task.cancel()
            loop.run_until_complete(asyncio.gather(
                *tasks, return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
            logger.info("Exiting application...")
