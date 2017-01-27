#Import external Modules that are needed
import telegram.ext
from telegram.ext import Updater, Filters
from slackclient import SlackClient
import json, os.path, sys, traceback, functools, time, shutil
from multiprocessing import Pool

#Import internal Modules that are needed
import config

class Core:
    def __init__(self):
        try:
            self.config = config.Config("config/config.json")
        except ValueError:
            logging.exception("failed to load config, malformed json")
            sys.exit()

        try:
            self.memory = config.Memory("config/memory.json")
        except ValueError:
            logging.exception("failed to load config, malformed json")
            sys.exit()
    def slack_init(self):
        api_key = self.config.get_by_path(['SLACK_API_KEY'])
        sc = SlackClient(api_key)

        print("slack starting...")
        if sc.rtm_connect():
            last_ping = int(time.time())
            while True:
                rtm_flow = sc.rtm_read()
                if rtm_flow:
                    type = rtm_flow[0]['type']
                    if type == "message":
                        if "subtype" in rtm_flow[0]:
                            subtype = rtm_flow[0]['subtype']
                            if subtype == "message_deleted":
                                print("something deleted")
                        else:
                            print(rtm_flow)
                    else:
                        print(rtm_flow)
                now = int(time.time())
                if now > last_ping + 30:
                    sc.server.ping()
                    last_ping = now
                time.sleep(.1)
        else:
            print("Connection Failed, invalid token?")

    def telegram_init(self):
        def sync_handler(bot, update):
            print(update.message.text)

        def slacksync(bot, update):
            params = update.message.text.split()
            print(params[1])

            try:
                tg2sl = self.memory.get_by_path(['tg_sl-sync'])['tg2sl']
                sl2tg = self.memory.get_by_path(['tg_sl-sync'])['sl2tg']
            except Exception as e:
                #print(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                traceback.print_exc()
                update.message.reply_text('Failed to get memory. Please contact Admin!')

            if tg2sl:
                print("works")

            if update.message.chat_id in tg2sl:
                print("tretre")
            else:
                print("got sync request...")
                try:
                    tg2sl[str(update.message.chat_id)] = params[1]
                    sl2tg[str(params[1])] = str(update.message.chat_id)
                    new_memory = {'tg2sl': tg2sl, 'sl2tg': sl2tg}
                    self.memory.set_by_path(['tg_sl-sync'], new_memory)
                    self.memory.save()
                    update.message.reply_text('Saved sync!')
                except Exception as e:
                    #print(e)
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    traceback.print_exc()
                    update.message.reply_text('Failed to save sync!')
                print("sync saved")

        print("Telegram starting...")
        api_key = self.config.get_by_path(['TELEGRAM_API_KEY'])
        if not self.memory.exists(['tg_sl-sync']):
            print('tg_sl-sync missing...')
            self.memory.set_by_path(['tg_sl-sync'], {'sl2tg':{}, 'tg2sl': {}})
            self.memory.save()
        updater = Updater(api_key)
        updater.dispatcher.add_handler(telegram.ext.MessageHandler(Filters.text, sync_handler))
        updater.dispatcher.add_handler(telegram.ext.CommandHandler('slacksync', slacksync))


        updater.start_polling()
        # updater.idle()

    def stop(self):
        print("Caught keyboard interrupt. Canceling tasks...")

    def init(self):
        pool = Pool()
        telegram = pool.apply_async(self.telegram_init(), [])    # evaluate "solve1(A)" asynchronously
        slack = pool.apply_async(self.slack_init(), [])    # evaluate "solve2(B)" asynchronously

if __name__ == "__main__":
    if os.path.isdir("config"):
        if not os.path.isfile('config/config.json'):
            try:
                shutil.copy('defaults/config.json', "config/config.json")
                sys.exit('Please set Api Keys')
            except (OSError, IOError) as e:
                sys.exit('Failed to copy default config file: {}'.format(e))
        if not os.path.isfile('config/memory.json'):
            try:
                shutil.copy('defaults/memory.json', "config/memory.json")
            except (OSError, IOError) as e:
                sys.exit('Failed to copy default memory file: {}'.format(e))
    else:
        os.mkdir("config")
        if not os.path.isfile('config/config.json'):
            try:
                shutil.copy('defaults/config.json', "config/config.json")
                sys.exit('Please set Api Keys')
            except (OSError, IOError) as e:
                sys.exit('Failed to copy default config file: {}'.format(e))

    core = Core()
    core.init()
