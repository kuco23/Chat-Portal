from .._entities import User, Thread, ReceivedMessage, ModifiedMessage
from .. import Database

database = Database("sqlite+pysqlite:///:memory:")

# storing / fetching users
for user_id in ["user1", "user2", "user3"]:
    database.addEntities([User(user_id)])
    user = database.fetchUser(user_id)
    assert user is not None
    assert user.id == user_id

# storing / fetching threads
for user_id in ["user1", "user2", "user3"]:
    database.addEntities([Thread(user_id + "_thread", user_id)])
    thread = database.fetchThread(user_id + "_thread")
    assert thread is not None
    assert thread.id == user_id + "_thread"
    assert thread.user_id == user_id
    assert thread.pair_id is None

# storing / fetching received messages
for i, user_id in enumerate(["user1", "user2", "user3"]):
    message = ReceivedMessage(str(i), user_id + "_thread", "hello", i)
    database.addEntities([message])
    message = database.fetchReceivedMessage(str(i))
    assert message is not None
    assert message.id == str(i)
    assert message.content == "hello"
    assert message.timestamp == i

for i, user_id in enumerate(["user1", "user2", "user3"]):
    thread = database.fetchThread(user_id + "_thread")
    assert thread is not None
    unprocessed_messages = database.unprocessedMessagesOnThread(thread)
    assert len(unprocessed_messages) == 1
    assert unprocessed_messages[0].id == str(i)

# storing / fetching modified messages
for i, user_id in enumerate(["user1", "user2", "user3"]):
    modified_message = ModifiedMessage(str(i), user_id + "_thread", "modified hello", i)
    database.addEntities([modified_message])
    # check modified message
    thread = database.fetchThread(user_id + "_thread")
    assert thread is not None
    modified_message = database.unsentMessagesOnThread(thread)
    assert len(modified_message) == 1
    assert modified_message[0].original_id == str(i)
    # mark original message was processed
    received_message = database.fetchReceivedMessage(str(i))
    assert received_message is not None
    database.markMessageProcessed(received_message)

for user_id in ["user1", "user2", "user3"]:
    thread = database.fetchThread(user_id + "_thread")
    assert thread is not None
    unprocessed_messages = database.unprocessedMessagesOnThread(thread)
    assert len(unprocessed_messages) == 0

# pairing threads
assert (thread1 := database.fetchThread("user1_thread")) is not None
assert (thread2 := database.fetchThread("user2_thread")) is not None
database.pairThreads(thread1, thread2)
thread1 = database.fetchThread("user1_thread")
assert thread1 is not None
assert thread1.id == "user1_thread"
assert thread1.pair_id == "user2_thread"
thread2 = database.fetchThread("user2_thread")
assert thread2 is not None
assert thread2.id == "user2_thread"
assert thread2.pair_id == "user1_thread"
thread3 = database.fetchThread("user3_thread")
assert thread3 is not None
assert thread3.id == "user3_thread"
assert thread3.pair_id is None

print("All tests for _database_basic_test.py passed")