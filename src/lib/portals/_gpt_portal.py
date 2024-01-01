from typing import List
from openai import OpenAI
from ...interface import ISocialPlatform, IDatabase
from .._models import MessageBatch
from .._entities import ProcessedMessage
from .._portal import Portal


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
        openai_model_name: str
    ):
        super().__init__(database, social_platform)
        self.openai_client = OpenAI() # takes OPENAI_API_KEY from os.environ
        self.openai_model_name = openai_model_name

    def _processMessageBatch(self, batch: MessageBatch, to_user_id: str) -> List[ProcessedMessage] | None:
        from_user = self.database.fetchUser(batch.from_user_id)
        to_user = self.database.fetchUser(to_user_id)
        if from_user is None:
            raise Exception("GptPortal: could not find user {batch.from_user_id}")
        if to_user is None:
            raise Exception("GptPortal: could not find user {to_user_id}")
        sys_prompt = SYS_PROMPT_TEMPLATE.format(
            from_full_name=from_user.full_name,
            to_full_name=to_user.full_name
        )
        user_prompt = self._messageBatchToGptPrompt(batch)
        gpt_response = self._getGptPromptResponse(sys_prompt, user_prompt)
        if gpt_response is None:
            raise Exception("GptPortal: GPT API call returned None")
        return self._gptResponseToProcessedMessages(gpt_response, batch)

    def _messageBatchToGptPrompt(self, batch: MessageBatch) -> str:
        return "\n\n".join([msg.content for msg in batch.messages])

    def _gptResponseToProcessedMessages(self, gpt_response: str, batch: MessageBatch) -> List[ProcessedMessage]:
        processed_messages = gpt_response.split("\n\n")
        if len(processed_messages) != len(batch.messages):
            last_message_id = max(batch.messages, key=lambda msg: msg.timestamp).id
            return [
                ProcessedMessage(last_message_id, processed_message)
                for processed_message in processed_messages
            ]
        return [
            ProcessedMessage(original_message.id, processed_message)
            for original_message, processed_message in zip(batch.messages, processed_messages)
        ]

    def _getGptPromptResponse(self, prompt_sys: str, prompt_usr: str) -> str | None:
        completion = self.openai_client.chat.completions.create(
            model=self.openai_model_name,
            messages=[
                { "role": "system", "content": prompt_sys },
                { "role": "user", "content": prompt_usr }
            ]
        )
        return completion.choices[0].message.content