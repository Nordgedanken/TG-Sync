import logging
import telegram.ext
from telegram.ext import Updater, Filters

logger = logging.getLogger(__name__)

from bot.helper import sc, updater, memory_class

class Telegram:
    def __init__(self):
        self.sc = sc
        self.updater = updater
        self.memory = memory_class

    def Hsyc(self, bot, update):
        try:
            tg2sl = self.memory.get_by_path(['tg_sl-sync'])['tg2sl']
        except Exception as e:
            traceback.print_exc()
            update.message.reply_text('Failed to get memory. Please contact Admin!')
        try:
            if str(update.message.chat_id) in tg2sl:
                response = self.sc.api_call(
                  "chat.postMessage",
                  channel=tg2sl[str(update.message.chat_id)],
                  text=update.message.text,
                  username="{firstname} {lastname} ({synced_chat})".format(firstname=update.message.from_user['first_name'], lastname=update.message.from_user['last_name'], synced_chat=update.message['chat']['title']),
                  icon_url=str(bot.getFile(file_id=update.message.from_user.get_profile_photos(limit=1)['photos'][0][0]['file_id'])['file_path'])
                )
                print("response: {}".format(response))
        except Exception as e:
            traceback.print_exc()
            update.message.reply_text('Failed to sync to chat. Please contact Admin!')
        print(update.message.text)

    def Cslacksync(self, bot, update):
        params = update.message.text.split()
        logger.debug(params[1])

        try:
            tg2sl = self.memory.get_by_path(['tg_sl-sync'])['tg2sl']
            sl2tg = self.memory.get_by_path(['tg_sl-sync'])['sl2tg']
        except Exception as e:
            traceback.print_exc()
            update.message.reply_text('Failed to get memory. Please contact Admin!')

            update.message.reply_text(tg2sl)

        if update.message.chat_id in tg2sl:
            update.message.reply_text('This channel is already synced!')
        else:
            logger.debug("got sync request...")
            try:
                tg2sl[str(update.message.chat_id)] = params[1]
                sl2tg[str(params[1])] = str(update.message.chat_id)
                new_memory = {'tg2sl': tg2sl, 'sl2tg': sl2tg}
                self.memory.set_by_path(['tg_sl-sync'], new_memory)
                self.memory.save()
                update.message.reply_text('Saved sync!')
                logger.debug("sync saved")
            except Exception as e:
                traceback.print_exc()
                update.message.reply_text('Failed to save sync!')

    def telegram_init(self):
        try:
            logger.info("Telegram starting...")
            self.updater.dispatcher.add_handler(telegram.ext.MessageHandler(Filters.text, self.Hsyc))
            self.updater.dispatcher.add_handler(telegram.ext.CommandHandler('slacksync', self.Cslacksync))
            self.updater.start_polling()
        except KeyboardInterrupt:
            sys.exit()
