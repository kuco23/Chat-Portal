# Run chat portal as a systemd service

To set up the `chat-portal-bot` service, follow these steps:

1. Clone the repo and install dependencies inside `.venv` virtual environment.

1. Replace `/path/to/repo` with the absolute path to the `Chat Portal`'s repository directory.

1. Copy the `chat-portal-bot.service` file to `/etc/systemd/system`.

1. Make the system detect new services by running:
     ```
     sudo systemctl daemon-reload
     ```

1. Start the service by running
    ```
    sudo systemctl start chat-portal-bot
    ```

5. To make services start automatically at boot time, execute
    ```
    sudo systemctl enable chat-portal-bot
    ```

6. To view the console output use command
    ```
    sudo journalctl -fu chat-portal-bot.service
    ```
    This will follow the output. To show the past output in `less`, call instead
    ```
    sudo journalctl -eu chat-portal-bot.service
    ```
