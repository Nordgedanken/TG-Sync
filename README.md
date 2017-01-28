# TG-Slack-Syncbot

This Bot is aiming to replace th hangoutbot in terms of Sync between Telegram and Slack. It also aims to be as modifyable as the hangoutsbot.
Currently it is still Work in Progress

# How to Install

## Preparing your Environment

**install python 3.4 from source**
```
wget https://www.python.org/ftp/python/3.4.2/Python-3.4.2.tgz
tar xvf Python-3.4.2.tgz
cd Python-3.4.2
./configure
make
make test
sudo make install
```

**git clone the repository**
```
git clone <repository url>
```

**install dependencies**
```
pip3 install -r requirements.txt
```

## First-Run

You need to **run the bot for the first time**. You will need at least
  a TG Bot API Key and a Slack Bot API Key.

The basic syntax for running the bot (assuming you are in the root
  of the cloned repository) is:
```
python3 bot.py
```

If you are having problems starting the bot, appending a `-d` at the
  end will dump more details into the bot logs e.g.
  `python3 bot.py -d` - more configuration
  directives can be found at the end of the README file.

To quit the bot from the console, press CTRL-C  <--- BROKEN just kill it

## Initial Configuration

DO NOT EDIT the `config.json` supplied with the bot. It is the
  reference file used to generate the actual config file, which
  is located elsewhere. Please see the next section on
  **Additional Configuration** to get the location of the
  actual configuration file if you need to edit it manually.

You will need to add your actual Telegram and Slack User as a bot administrator.

This will be accomplished using the supplied **starter** plugin with
  the default supplied configuration.

WORK IN PROGRESS

## Additional Configuration

After the first successful run of the bot, it should generate a
  `config.json` inside the `config` directory.

You can edit this file and restart the bot to load any new configs.

For further information, please see the wiki.

## Troubleshooting

* For console output when the bot is starting, errors messages always
  start in ALLCAPS e.g. "EXCEPTION in ..."
* Additional logs can be found in:
  `config/TG-SL_bot.log` -
  note: this file is more useful for developers and may be quite verbose
* You can verify the location of your active `config.json` by sending
  the following command to the bot via hangouts: `/bot files` (with
  the **starter** plugin active)
