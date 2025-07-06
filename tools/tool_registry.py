
import os
import importlib
import inspect

REGISTERED_TOOLS = {}

def discover_tools(tools_folder="tools"):
    for filename in os.listdir(tools_folder):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            module_path = f"{tools_folder}.{module_name}"
            try:
                module = importlib.import_module(module_path)
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    full_name = f"{module_name}.{name}"
                    REGISTERED_TOOLS[full_name] = func
            except Exception as e:
                print(f"❌ Error loading {module_path}: {e}")

def get_tool(name: str):
    return REGISTERED_TOOLS.get(name)

# Call it once at import
discover_tools()
