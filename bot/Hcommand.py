from functools import wraps
import traceback

from bot.helper import sc, updater
import telegram.ext
from telegram.ext import Filters

def register_command(filter):
    def wrap(f):
        #r = f()
        updater.dispatcher.add_handler(telegram.ext.CommandHandler(filter, f))
    return wrap
