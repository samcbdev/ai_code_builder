class LLMClient:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

class DummyLLM(LLMClient):
    def generate(self, prompt: str) -> str:
        return "// TODO: real code will be generated here\n"