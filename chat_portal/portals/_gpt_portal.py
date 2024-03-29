from typing import Optional, List, Iterable
from openai import OpenAI
from .._entities import User, Thread, Message, ReceivedMessage, ModifiedMessage
from .._portal import Portal
from ..interface import ISocialPlatform, IDatabase


MAX_CONTEXT_MESSAGES = 5
MAX_PROMPT_RETRY = 3
CONTEXT_SEPARATOR = "---"

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

    def _modifyUnsentMessages(self, received_messages: List[ReceivedMessage], from_thread: Thread, to_thread: Thread):
        if len(received_messages) == 0: return []
        from_user = self.database.fetchUser(from_thread.user_id)
        to_user = self.database.fetchUser(to_thread.user_id)
        assert from_user is not None and to_user is not None
        sys_prompt = self._sysPrompt(from_user, to_user)
        user_prompt = self._messagesToGptPrompt(received_messages, to_thread, from_user, to_user)
        gpt_messages = self._messagesToModified(received_messages, sys_prompt, user_prompt)
        return self._toModifiedMessageList(gpt_messages, received_messages, to_thread)

    def _messagesToGptPrompt(self, received_messages: List[ReceivedMessage], to_thread: Thread, from_user: User, to_user: User) -> str:
        first_timestamp = min(map(lambda msg: msg.timestamp, received_messages))
        conversation = self.database.conversationHistory(to_thread.id, first_timestamp, MAX_CONTEXT_MESSAGES)
        context_messages = filter(lambda msg: msg.timestamp < first_timestamp, conversation)
        context = self._formatContextConversation(context_messages, from_user, to_user)
        return context + f"\n\n{CONTEXT_SEPARATOR}\n\n" + "\n\n".join([msg.content for msg in received_messages])

    def _messagesToModified(self, prompt_messages: List[ReceivedMessage], sys_prompt: str, user_prompt: str) -> List[str]:
        gpt_messages: List[str]
        for _ in range(MAX_PROMPT_RETRY):
            gpt_response = self._promptGpt(sys_prompt, user_prompt)
            if gpt_response is None: continue
            gpt_messages = self._gptResponseToRawMessages(gpt_response)
            if len(gpt_messages) == len(prompt_messages): break
        else:
            gpt_messages = [msg.content for msg in prompt_messages]
        return gpt_messages

    def _promptGpt(self, prompt_sys: str, prompt_usr: str) -> Optional[str]:
        completion = self.openai_client.chat.completions.create(
            model=self.openai_model_name,
            messages=[
                { "role": "system", "content": prompt_sys },
                { "role": "user", "content": prompt_usr }
            ]
        )
        return completion.choices[0].message.content

    def _toModifiedMessageList(self, gpt_messages: List[str], received_messages: List[ReceivedMessage], to_thread: Thread):
        if len(gpt_messages) != len(received_messages):
            last_message = max(received_messages, key=lambda msg: msg.timestamp)
            return [
                ModifiedMessage(last_message.id, to_thread.id, processed_message, last_message.timestamp + i)
                for i, processed_message in enumerate(gpt_messages)
            ]
        return [
            ModifiedMessage(received_message.id, to_thread.id, processed_message, received_message.timestamp)
            for received_message, processed_message in zip(received_messages, gpt_messages)
        ]

    def _sysPrompt(self, from_user: User, to_user: User) -> str:
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

    @staticmethod
    def _formatContextConversation(messages: Iterable[Message], from_user: User, to_user: User) -> str:
        context = []
        for message in messages:
            # TODO: think if it makes sense that from_user is the artificial entity instead
            message_owner = from_user if message.modified else to_user
            message_owner_name = GptPortal._determineName(message_owner)
            context.append(f"{message_owner_name}: {message.content}")
        return "\n\n".join(context)