#Import external Modules that are needed
import telegram.ext
from telegram.ext import Updater, Filters
from slackclient import SlackClient
import json, os.path, sys, traceback, functools, time, shutil, logging, logging.config, argparse, signal
from multiprocessing import Pool

logger = logging.getLogger(__name__)

#Import internal Modules that are needed
import config

class Core:
    def __init__(self):
        try:
            self.config = config.Config(os.path.join('config', 'config.json'))
        except ValueError:
            logging.exception("failed to load config, malformed json")
            sys.exit()

        try:
            self.memory = config.Memory(os.path.join('config', 'memory.json'))
        except ValueError:
            logging.exception("failed to load config, malformed json")
            sys.exit()

        try:
            self.sl_api_key = self.config.get_by_path(['SLACK_API_KEY'])
            self.sc = SlackClient(self.sl_api_key)
        except Exception as e:
            traceback.print_exc()

        try:
            self.tg_api_key = self.config.get_by_path(['TELEGRAM_API_KEY'])
            if not self.memory.exists(['tg_sl-sync']):
                logger.warn('tg_sl-sync missing...')
                self.memory.set_by_path(['tg_sl-sync'], {'sl2tg':{}, 'tg2sl': {}})
                self.memory.save()
            self.tg_bot = telegram.Bot(self.tg_api_key)
            self.updater = Updater(self.tg_api_key)
        except Exception as e:
            traceback.print_exc()

    def run(self):
        pool = Pool(2)
        try:
            telegram = pool.apply_async(self.telegram_init(), [])
            slack = pool.apply_async(self.slack_init(), [])
            pool.close()
            telegram.join()
            slack.join()
        except KeyboardInterrupt:
            logger.info("Caught KeyboardInterrupt, terminating workers")
            pool.terminate()

    def slack_init(self):
        try:
            sl2tg = self.memory.get_by_path(['tg_sl-sync'])['sl2tg']
            logger.info("Slack Bot starting...")
            if self.sc.rtm_connect():
                last_ping = int(time.time())
                while True:
                    rtm_flow = self.sc.rtm_read()
                    if rtm_flow:
                        print(rtm_flow)
                        type = rtm_flow[0]['type']
                        if 'text' in rtm_flow[0]:
                            if type == "message":
                                    if "subtype" in rtm_flow[0]:
                                        subtype = rtm_flow[0]['subtype']
                                        if "message_deleted" in subtype:
                                            logger.debug("something got deleted at slack")
                                    else:
                                        text = rtm_flow[0]['text']
                                        user_profile = self.sc.api_call("users.info", user=rtm_flow[0]['user'])
                                        channel_info = self.sc.api_call("channels.info", channel=rtm_flow[0]['channel'])
                                        channel_name = channel_info['channel']['name']
                                        user_name = user_profile['user']['profile']['real_name']
                                        response = self.tg_bot.sendMessage(chat_id=sl2tg['#{}'.format(channel_name)], text='{user_name} ({channel}): {text}'.format(user_name=user_name, channel=channel_name, text=text))
                                        print('TG RESPONSE: {}'.format(response))
                            else:
                                logger.debug(rtm_flow)
                    now = int(time.time())
                    if now > last_ping + 30:
                        self.sc.server.ping()
                        last_ping = now
                    time.sleep(.1)
            else:
                logger.critical("Connection Failed, invalid token?")
        except KeyboardInterrupt:
            sys.exit()

    def Hsyc(self, bot, update):
        try:
            tg2sl = self.memory.get_by_path(['tg_sl-sync'])['tg2sl']
        except Exception as e:
            traceback.print_exc()
            update.message.reply_text('Failed to get memory. Please contact Admin!')
        try:
            if str(update.message.chat_id) in tg2sl:
                print("USER: {}".format(bot.getFile(file_id=update.message.from_user.get_profile_photos(limit=1)['photos'][0][0]['file_id'])['file_path']))
                response = self.sc.api_call(
                  "chat.postMessage",
                  channel=tg2sl[str(update.message.chat_id)],
                  text=update.message.text,
                  username="{firstname} {lastname}".format(firstname=update.message.from_user['first_name'], lastname=update.message.from_user['last_name']),
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
            print("in it")
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

def configure_logging(args):
    """Configure Logging
    If the user specified a logging config file, open it, and
    fail if unable to open. If not, attempt to open the default
    logging config file. If that fails, move on to basic
    log configuration.
    """

    log_level = 'DEBUG' if args.debug else 'INFO'

    default_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'console': {
                'format': '%(asctime)s %(levelname)s %(name)s: %(message)s',
                'datefmt': '%H:%M:%S'
                },
            'default': {
                'format': '%(asctime)s %(levelname)s %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
                }
            },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'level': 'INFO',
                'formatter': 'console'
                },
            'file': {
                'class': 'logging.FileHandler',
                'filename': args.log,
                'level': log_level,
                'formatter': 'default',
                }
            },
        'loggers': {
            # root logger
            '': {
                'handlers': ['file', 'console'],
                'level': log_level
                },

            # asyncio's debugging logs are VERY noisy, so adjust the log level
            'asyncio': {'level': 'WARNING'},
            'irde_bot': {'level': 'ERROR'}
            }
        }

    logging_config = default_config

    # Temporarily bring in the configuration file, just so we can configure
    # logging before bringing anything else up. There is no race internally,
    # if logging() is called before configured, it outputs to stderr, and
    # we will configure it soon enough
    bootcfg = config.Config(os.path.join('config', 'config.json'))
    if bootcfg.exists(["logging.system"]):
        logging_config = bootcfg["logging.system"]

    if "extras.setattr" in logging_config:
        for class_attr, value in logging_config["extras.setattr"].items():
            try:
                [modulepath, classname, attribute] = class_attr.rsplit(".", maxsplit=2)
                try:
                    setattr(class_from_name(modulepath, classname), attribute, value)
                except ImportError:
                    logging.error("module {} not found".format(modulepath))
                except AttributeError:
                    logging.error("{} in {} not found".format(classname, modulepath))
            except ValueError:
                logging.error("format should be <module>.<class>.<attribute>")

    logging.config.dictConfig(logging_config)

    logger = logging.getLogger()
    if args.debug:
        logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    default_log_path = os.path.join('config', 'irde_bot.log')

    parser = argparse.ArgumentParser(prog='irde_bot',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--log', default=default_log_path,
                            help='log file path')
    parser.add_argument('-d', '--debug', action='store_true',
                    help='log detailed debugging messages')
    args = parser.parse_args()

    if os.path.isdir("config"):
        if not os.path.isfile(os.path.join('config', 'config.json')):
            try:
                shutil.copy(os.path.join('config', 'config.json'), os.path.join('config', 'config.json'))
                sys.exit('Please set Api Keys')
            except (OSError, IOError) as e:
                sys.exit('Failed to copy default config file: {}'.format(e))
        if not os.path.isfile(os.path.join('config', 'config.json')):
            try:
                shutil.copy(os.path.join('defaults', 'memory.json'), os.path.join('config', 'memory.json'))
            except (OSError, IOError) as e:
                sys.exit('Failed to copy default memory file: {}'.format(e))
    else:
        os.mkdir("config")
        if not os.path.isfile(os.path.join('config', 'config.json')):
            try:
                shutil.copy(os.path.join('defaults', 'config.json'), os.path.join('config', 'config.json'))
                sys.exit('Please set Api Keys')
            except (OSError, IOError) as e:
                sys.exit('Failed to copy default config file: {}'.format(e))

    configure_logging(args)
    core = Core()
    core.run()
