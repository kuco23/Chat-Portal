# Social Media Profile Portal

This code implements a social media profile that works as a message portal. For a given social media platform (currently only instagram supported) it listens to new messages and matches the users based on what they have written. Then it forwards each new message to the matched user and vice-versa.

> **IMPORTANT**
> This project is currently a work in progress.

## Code architecture

All the interfaces start with the capital `I` and are defined in the `src/interface.py` file. The main code module is the `Portal` class with the `IPortal` interface, which is initialized by a `IDatabase` interfaced class and an `ISocialPlatform` interfaced class.

- The `IDatabase` interface is implemented by the `Database` class, which is a wrapper around an `SqlAlchemy` orm.
- The `ISocialPlatform` interface is implemented by the `Instagram` class, which is a wrapper around the [instagrapi](https://github.com/subzeroid/instagrapi) library. You can implement more social media platforms inside the `src/lib/platforms/` folder.

To implement a message processor and a user matcher, you have to subclass the `Portal` class and implement the `_processMessageBatch`, `_bestMatchOf` methods. The current implementation inside `src/lib/portals/chatGpt.py` connects to ChatGPT and asks it to process messages and score user pair compatibility.

## Setup

Run `pip install -r requirements.txt` to install the required packages, then create `.env` file and fill in the fields specified in `.env.template`. To run, execute `python run.py`. You can also change the default settings defined in `config.cfg`.

## Note

We abstract the message processing of the social platforms by implementing a common interface class `SocialPlatform`. It includes two methods related to the message processing, `getNewUsers` and `getNewMessages`. The first one should implement a platform-based decision of when to register new users. This should be a precursor to the second method, which should fetch new messages.

Note that ideally the social media platform api used would stream newly received messages (e.g. as implemented in [fbchat](https://github.com/fbchat-dev/fbchat)), but that is usually not the case (e.g. as with [instagrapi](https://github.com/subzeroid/instagrapi)), so our interface is adjusted to messages being fetched from the social media server in batches. If your social platform implementation can stream messages, you should store them in a buffer and return them in the `getNewMessages` method.

## Note

The social platform implementation should only bother with supplying new messages. The users are considered senders of those messages and are registered when new messages are processed by the `Platform` class.