import logging, time

logger = logging.getLogger(__name__)

class Slack:
    def __init__(self, sc, tg_bot, memory):
        self.sc = sc
        self.tg_bot = tg_bot
        self.memory = memory

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
                                        response = self.tg_bot.sendMessage(parse_mode='HTML', chat_id=sl2tg['#{}'.format(channel_name)], text='<b>{user_name} ({channel}):</b> {text}'.format(user_name=user_name, channel=channel_name, text=text))
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
