from typing import Optional, List
from openai import OpenAI
from .._entities import User, ReceivedMessage, ModifiedMessage
from .._portal import Portal
from ..interface import ISocialPlatform, IDatabase

MAX_CONTEXT_MESSAGE_NUMBER = 5


class GptPortal(Portal):
    openai_client: OpenAI
    openai_model_name: str
    system_prompt_template: str

    def __init__(
        self: "GptPortal",
        database: IDatabase,
        social_platform: ISocialPlatform,
        openai_model_name: str,
        system_prompt_template: str
    ):
        super().__init__(database, social_platform)
        self.openai_client = OpenAI() # takes OPENAI_API_KEY from os.environ
        self.openai_model_name = openai_model_name
        self.system_prompt_template = system_prompt_template

    def _modifyUnsentMessages(self, received_messages: List[ReceivedMessage], from_user: User, to_user: User):
        if len(received_messages) == 0: return []
        sys_prompt = self._getSysPrompt(from_user, to_user)
        user_prompt = self._messagesToGptPrompt(received_messages)
        gpt_response = self._getGptPromptResponse(sys_prompt, user_prompt)
        if gpt_response is None:
            raise Exception("GptPortal: GPT API call returned None")
        gpt_messages = self._gptResponseToRawMessages(gpt_response)
        return self._toModifiedMessageList(gpt_messages, received_messages, to_user)

    def _messagesToGptPrompt(self, received_messages: List[ReceivedMessage]) -> str:
        thread_id = received_messages[0].thread_id
        first_timestamp = min(map(lambda msg: msg.timestamp, received_messages))
        conversation = self.database.conversationHistory(thread_id, first_timestamp, MAX_CONTEXT_MESSAGE_NUMBER)
        context = filter(lambda msg: msg.timestamp < first_timestamp, conversation)
        return "\n\n".join([msg.content for msg in context]) + "\n---\n" + "\n\n".join([msg.content for msg in received_messages])

    def _getGptPromptResponse(self, prompt_sys: str, prompt_usr: str) -> Optional[str]:
        completion = self.openai_client.chat.completions.create(
            model=self.openai_model_name,
            messages=[
                { "role": "system", "content": prompt_sys },
                { "role": "user", "content": prompt_usr }
            ]
        )
        return completion.choices[0].message.content

    def _toModifiedMessageList(self, gpt_messages: List[str], received_messages: List[ReceivedMessage], to_user: User):
        if len(gpt_messages) != len(received_messages):
            last_message = max(received_messages, key=lambda msg: msg.timestamp)
            return [
                ModifiedMessage(last_message.id, to_user.thread_id, processed_message, last_message.timestamp + i)
                for i, processed_message in enumerate(gpt_messages)
            ]
        return [
            ModifiedMessage(received_message.id, to_user.thread_id, processed_message, received_message.timestamp)
            for received_message, processed_message in zip(received_messages, gpt_messages)
        ]

    def _getSysPrompt(self, from_user: User, to_user: User) -> str:
        return self.system_prompt_template.format(
            from_name=GptPortal._determineName(from_user),
            to_name=GptPortal._determineName(to_user)
        )

    @staticmethod
    def _determineName(user: User) -> str:
        return user.full_name or user.username

    @staticmethod
    def _gptResponseToRawMessages(gpt_response: str) -> List[str]:
        return gpt_response.split("\n\n")