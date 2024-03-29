# Chat Portal
[![PyPI version](https://badge.fury.io/py/chat_portal.svg)](https://pypi.org/project/chat_portal)

This code automates a social media profile and makes it functions as a message exchange portal. It monitors incoming messages, pairs users based on their message content, and then relays each new message between paired users. The current implementation uses Instagram as a social platform and chatGPT to modify relayed messages in a way that makes it seem like they are comming from the automated profile.

> Python >= 3.10 is required.

## Standalone usage

Follow the below steps to set up this project:

1. Clone the repo with `git clone https://github.com/kuco23/Chat-Portal.git`.
1. Set up your virtual environment with `python -m venv .venv` then run `source .venv/bin/activate` on Linux or `.venv/Scripts/activate` on Windows.
1. Install dependencies with `pip install -r requirements.txt`.
1. Create `.env` file and fill in the fields specified in `.env.template`.
1. Run the program with `python run.py`.

Note that you can also modify the default configuration parameters inside `config.cfg`

> **WARN**
> The package ships without the `instagrapi` dependency. If using this package with it, you need to install it manually with `pip install instagrapi`.

## Use as package

To use this project as a package in your own project, you can install it with `pip install chat-portal`.

## Code architecture

The code is modular, cosisting of parts described by interfaces inside `src/interface.py`. The main code module is the `Portal` class with the `IPortal` interface, which is initialized by a `IDatabase` interfaced class and an `ISocialPlatform` interfaced class.

- The `IDatabase` interface is implemented by the `Database` class, which is a wrapper around an `SqlAlchemy` orm.
- The `ISocialPlatform` interface is implemented by the `Instagram` class, which is a wrapper around the [instagrapi](https://github.com/subzeroid/instagrapi) library. You can implement more social media platforms inside the `src/platforms` folder.
- The `IPortal` interface is implemented by the `Portal` abstract class, which is inherited by the `GptPortal` class. You can implement more portals inside the `src/portals` folder.
