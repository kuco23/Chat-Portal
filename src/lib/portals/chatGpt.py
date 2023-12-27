from typing import List
from openai import OpenAI
from ...interface import ISocialPlatform, IDatabase
from .._models import MessageBatch
from .._entities import ProcessedMessage
from .._portal import Portal

class GptPortal(Portal):
    openai_client: OpenAI
    openai_assistant_config: str
    openai_model_name: str

    def __init__(self,
        database: IDatabase,
        social_platform: ISocialPlatform,
        openai_client: OpenAI,
        openai_assistant_config: str,
        openai_model_name: str
    ):
        super().__init__(database, social_platform)
        self.openai_client = openai_client
        self.openai_assistant_config = openai_assistant_config
        self.openai_model_name = openai_model_name

    def _getGptResponse(self, prompt_sys: str, prompt_usr: str) -> str | None:
        completion = self.openai_client.chat.completions.create(
            model=self.openai_model_name,
            messages=[
                { "role": "system", "content": prompt_sys },
                { "role": "user", "content": prompt_usr }
            ]
        )
        return completion.choices[0].message.content