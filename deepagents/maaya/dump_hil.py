import inspect
from langchain.agents.middleware import HumanInTheLoopMiddleware
with open("hil_source.py", "w") as f:
    f.write(inspect.getsource(HumanInTheLoopMiddleware))
