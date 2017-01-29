import logging, os.path, traceback
import telegram.ext
from telegram.ext import Updater, Filters
from slackclient import SlackClient

logger = logging.getLogger(__name__)

from bot import config

try:
    config_class = config.Config(os.path.join('config', 'config.json'))
except ValueError:
    logging.exception("failed to load config, malformed json")
    sys.exit()

try:
    memory_class = config.Memory(os.path.join('config', 'memory.json'))
except ValueError:
    logging.exception("failed to load config, malformed json")
    sys.exit()

try:
    sl_api_key = config_class.get_by_path(['SLACK_API_KEY'])
    sc = SlackClient(sl_api_key)
except Exception as e:
    traceback.print_exc()

try:
    tg_api_key = config_class.get_by_path(['TELEGRAM_API_KEY'])
    if not memory_class.exists(['tg_sl-sync']):
        logger.warn('tg_sl-sync missing...')
        memory_class.set_by_path(['tg_sl-sync'], {'sl2tg':{}, 'tg2sl': {}})
        memory_class.save()
    tg_bot = telegram.Bot(tg_api_key)
    updater = Updater(tg_api_key)
except Exception as e:
    traceback.print_exc()
