#Import Modules that are needed
import telegram.ext
from telegram.ext import Updater, Filters
from slackclient import SlackClient
import json
import os.path
from multiprocessing import Pool
import sys, traceback, functools, time

class Config:
    filename = 'config/config.json'
    def generate(self):
        data = {"TELEGRAM_API_KEY": "INSERT YOUR TELEGRAM API KEY HERE", "SLACK_API_KEY": "INSERT YOUR SLACK API KEY HERE", "plugins": []}
        with open(self.filename, 'w') as config_file:
            outfile.write(json.dumps(data, indent=4))

    def get_by_path(self, keys_list):
        with open(self.filename) as config_file:
            data = json.load(config_file)
        return functools.reduce(lambda d, k: d[int(k) if isinstance(d, list) else k], keys_list, data)

    def set_by_path(self, keys_list, value):
        with open(self.filename, "r+") as config_file:
            config_data = json.load(config_file)
            config_data[keys_list[-1]] = value

            config_file.seek(0)  # rewind
            config_file.write(json.dumps(config_data))
            config_file.truncate()

    def remove(self, json_object):
        with open(self.filename) as config_file:
            config_data = json.load(config_file)
            for item in config_data:
                item.pop(config_data, None)
                with open(self.filename, mode='w') as f:
                    f.write(json.dumps(item, indent=4))

    def exists(self, keys_list):
        _exists = True

        try:
            if self.get_by_path(keys_list) is None:
                _exists = False
        except (KeyError, TypeError):
            _exists = False

        return _exists

class Memory:
    filename = 'config/memory.json'
    def generate(self):
        data = {}
        with open(self.filename, 'w') as memory_file:
            memory_file.write(json.dumps(data, indent=4))

    def get_by_path(self, keys_list):
        with open(self.filename) as memory_file:
            data = json.load(memory_file)
        return functools.reduce(lambda d, k: d[int(k) if isinstance(d, list) else k], keys_list, data)

    def set_by_path(self, keys_list, value):
        with open(self.filename, "r+") as memory_file:
            memory_data = json.load(memory_file)
            memory_data[keys_list[:-1]][keys_list[-1]] = value
            memory_file.seek(0)  # rewind
            memory_file.write(json.dumps(memory_data, indent=4))
            memory_file.truncate()

    def remove(self, json_object):
        with open(self.filename) as memory_file:
            memory_data = json.load(memory_file)
            for item in memory_data:
                item.pop(json_object, None)
                with open(self.filename, mode='w') as f:
                    f.write(json.dumps(item, indent=4))

    def exists(self, keys_list):
        _exists = True

        try:
            if self.get_by_path(keys_list) is None:
                _exists = False
        except (KeyError, TypeError):
            _exists = False

        return _exists

class Core:
    def slack_init(self):
        api_key = Config().get_by_path(['SLACK_API_KEY'])
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

            if Memory().exists(['tg_sl-sync']['tg2sl']):
                if Memory().exists(['tg_sl-sync']['sl2tg']):
                    tg2sl = Memory().get_by_path(['tg_sl-sync']['tg2sl'])
                    sl2tg = Memory().get_by_path(['tg_sl-sync']['sl2tg'])

                    if update.message.chat_id in tg2sl:
                        print("tretre")
                    else:
                        try:
                            tg2sl[str(update.message.chat_id)] = params[1]
                            sl2tg[str(params[1])] = str(update.message.chat_id)
                            new_memory = {'tg2sl': tg2sl, 'sl2tg': sl2tg}
                            Memory().set_by_path(['tg_sl-sync'], new_memory)
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
        api_key = Config().get_by_path(['TELEGRAM_API_KEY'])
        if not Memory().exists(['tg_sl-sync']):
            print('tg_sl-sync missing...')
            Memory().set_by_path(['tg_sl-sync'], {})
        # if not Memory().exists(['tg_sl-sync']['sl2tg']):
        #     print("sl2tg missing...")
        #     Memory().set_by_path(['tg_sl-sync']['sl2tg'], {})
        # if not Memory().exists(['tg_sl-sync']['tg2sl']):
        #     print("tg2sl missing...")
        #     Memory().set_by_path(['tg_sl-sync']['tg2sl'], {})
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

    check_pass = 0

    if os.path.isdir("config"):
        if os.path.isfile("config/config.json"):
            check_pass = check_pass+1
        else:
            check_pass = check_pass-1
            Config().generate()

        if os.path.isfile("config/memory.json"):
            check_pass = check_pass+1
        else:
            check_pass = check_pass-1
            Memory().generate()

        if check_pass == 2:
            Core().init()
        else:
            print("Configs are regenrated. Please check the API Keys and restart the Bot.")
    else:
        os.mkdir("config")
        Config().generate()
        Memory().generate()
        print("First run... Configs are genrated. Please add the API Keys and restart the Bot.")
