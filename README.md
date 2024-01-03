# Social Media Profile Portal

This code automates a social media profile, currently Instagram, that functions as a message exchange portal. It monitors incoming messages, pairs users based on their message content, and then relays each new message between matched users. The current implementation uses chatGPT to make it look like the messages are coming from the automated profile and are addressed to the matched user.

> Python >= 3.10 is required.

## Setup

Follow the below (basic) steps to set up this project:

1. Clone the repo with `git clone https://github.com/kuco23/Chat-Portal.git`.
1. Set up your virtual environment with `python -m venv .venv` then run `source .venv/bin/activate` on Linux or `.venv/Scripts/activate` on Windows.
1. Install dependencies with `pip install -r requirements.txt`.
1. Create `.env` file and fill in the fields specified in `.env.template`.
1. Run the program with `python run.py`.

Note that you can also modify the default configuration parameters inside `config.cfg`

## Code architecture

The code is modular, cosisting of parts described by interfaces inside `src/interface.py`. The main code module is the `Portal` class with the `IPortal` interface, which is initialized by a `IDatabase` interfaced class and an `ISocialPlatform` interfaced class.

- The `IDatabase` interface is implemented by the `Database` class, which is a wrapper around an `SqlAlchemy` orm.
- The `ISocialPlatform` interface is implemented by the `Instagram` class, which is a wrapper around the [instagrapi](https://github.com/subzeroid/instagrapi) library. You can implement more social media platforms inside the `src/platforms/` folder.
- The `IPortal` interface is implemented by the `Portal` abstract class, which is inherited by the `ChatGpt` class. You can implement more portals inside the `src/portals/` folder.

## Notes about implementation

Note that ideally the social media platform api used would stream newly received messages (e.g. as implemented in [fbchat](https://github.com/fbchat-dev/fbchat)), but that is usually not the case (e.g. as with [instagrapi](https://github.com/subzeroid/instagrapi)), so our interface is adjusted to messages being fetched from the social media server in batches. If your social platform implementation can stream messages, you should store them in a buffer and return them in the `getNewMessages` method.