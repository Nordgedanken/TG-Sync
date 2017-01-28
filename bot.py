#Import external Modules that are needed
import telegram.ext
from telegram.ext import Updater, Filters
from slackclient import SlackClient
import os.path, sys, traceback, shutil, logging, logging.config, argparse
from multiprocessing import Pool

logger = logging.getLogger(__name__)

#Import internal Modules that are needed
from bot import config
from bot import Htelegram
from bot import Hslack

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
        telegram_class = Htelegram.Telegram(self.sc, self.updater, self.memory)
        slack_class = Hslack.Slack(self.sc, self.tg_bot, self.memory)
        try:
            Ttelegram = pool.apply_async(telegram_class.telegram_init(), [])
            Tslack = pool.apply_async(slack_class.slack_init(), [])
            pool.close()
            Ttelegram.join()
            Tslack.join()
        except KeyboardInterrupt:
            logger.info("Caught KeyboardInterrupt, terminating workers")
            pool.terminate()

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
    default_log_path = os.path.join('config', 'TG-SL_bot.log')

    parser = argparse.ArgumentParser(prog='TG-SL_bot',
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
