from chorus.data.prompt import Prompt
from chorus.data.prompt import StructuredPrompt
from chorus.prompters.adapters.base import PromptAdapter


class ClaudeStructuredPromptAdapter(PromptAdapter):

    def get_prompt(self, prompt: str) -> StructuredPrompt:
        prompt_dict = {
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        }
        return StructuredPrompt.from_dict(prompt_dict)
