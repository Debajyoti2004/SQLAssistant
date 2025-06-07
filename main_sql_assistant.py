import threading
from sql_assistant_gui import SQLAssistantGUI
from assistant_cli import SQLAssistant

def main_sql_assistant():
    gui = SQLAssistantGUI()
    assistant = SQLAssistant(gui=gui)

    logic_thread = threading.Thread(target=assistant.run, daemon=True)
    logic_thread.start()

    gui.run()

if __name__ == "__main__":
    main_sql_assistant()