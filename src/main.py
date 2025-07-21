# -----------IMPORTS-----------
from core.server import client, mcp, BOARD_ID
import asyncio
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication
import sys
from core.client import init
from gui.window import ChatWindow

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import sys
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop, QApplication
from core.client import MCPClient

async def main():
    """ Connects to MCP server, updates GUI and handles user queries.    
    """
    # Session manager
    from contextlib import AsyncExitStack

    # Creation of session scope
    async with AsyncExitStack() as exit_stack:
        
        # Initialise client and GUI
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
            # Connect to server
            
            # Collect server parameters
            server_params = StdioServerParameters(
                command='python',
                args=['core/server.py'],
                env=None
            )

            # Launch server
            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))

            # Load read and write channels
            stdio, write = stdio_transport

            # Format in MCP
            session = await exit_stack.enter_async_context(ClientSession(stdio, write))
            
            client.session = session

            # Initialise session
            await session.initialize()


            # Collect tools
            response = await session.list_tools()
            tools = response.tools
            text = "Connected to server with tools:\n"
            for tool in tools:
                if '[prompt]' not in tool.description.lower():
                    text += f'-{tool.name}\n'

            # Collect prompts
            prompts = False
            text_prompts='\nWith the following prompts:\n'
            for tool in tools:
                if '[prompt]' in tool.description.lower():
                    prompts = True
                    text_prompts += f'-{tool.name}\n'
            if prompts == False:
                text_prompts = ''
                    
            # Send message to GUI
            await window.receive_message(text+text_prompts)
            
            await quit_future  # Wait for the Qt app to quit
        finally:
            await exit_stack.aclose()
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