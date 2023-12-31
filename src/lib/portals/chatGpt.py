from typing import List
from openai import OpenAI
from ...interface import ISocialPlatform, IDatabase
from .._models import MessageBatch
from .._entities import ProcessedMessage
from .._portal import Portal
from .._logger import logger


SYS_PROMPT_TEMPLATE = """\
You are a 13 year old girl named Laila and have been given a message from a person named "{from_full_name}". \
Make that message look like it is comming from you and is addressed to a person named "{to_full_name}". \
Respect that messages are seperated by two blank lines, and that for each given message you should produce exactly one message. \
If you cannot determine genders from the names, then assume they are both male.\
"""

class GptPortal(Portal):
    openai_client: OpenAI
    openai_model_name: str

    def __init__(
        self: "GptPortal",
        database: IDatabase,
        social_platform: ISocialPlatform,
        openai_client: OpenAI,
        openai_model_name: str
    ):
        super().__init__(database, social_platform)
        self.openai_client = openai_client
        self.openai_model_name = openai_model_name

    def _processMessageBatch(self, batch: MessageBatch, to_user_id: str) -> List[ProcessedMessage] | None:
        from_user = self.database.fetchUser(batch.from_user_id)
        to_user = self.database.fetchUser(to_user_id)
        if from_user is None:
            return logger.error(f"GptPortal: could not find user {batch.from_user_id}")
        if to_user is None:
            return logger.error(f"GptPortal: could not find user {to_user_id}")
        sys_prompt = SYS_PROMPT_TEMPLATE.format(
            from_full_name=from_user.full_name,
            to_full_name=to_user.full_name
        )
        usr_prompt = self._messageBatchToPrompt(batch)
        response = self._callGptApi(sys_prompt, usr_prompt)
        if response is None: return
        last_message_id = batch.messages[-1].id
        return [
            ProcessedMessage(last_message_id, message)
            for message in response.split("\n\n")
        ]

    def _messageBatchToPrompt(self, message_batch: MessageBatch) -> str:
        prompt = ""
        for message in message_batch.messages:
            prompt += f"{message.content}\n\n"
        return prompt

    def _callGptApi(self, prompt_sys: str, prompt_usr: str) -> str | None:
        completion = self.openai_client.chat.completions.create(
            model=self.openai_model_name,
            messages=[
                { "role": "system", "content": prompt_sys },
                { "role": "user", "content": prompt_usr }
            ]
        )
        return completion.choices[0].message.content