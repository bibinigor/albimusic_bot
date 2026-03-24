import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import logging
from vk_config import VK_TOKEN, VK_GROUP_ID, DEBUG

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VKBot:
    def __init__(self):
        self.vk_session = vk_api.VkApi(token=VK_TOKEN)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkLongPoll(self.vk_session, group_id=VK_GROUP_ID)
        logger.info("VK Bot initialized successfully")

    def send_message(self, user_id, message, keyboard=None):
        """Send message to user with optional keyboard"""
        try:
            params = {
                'user_id': user_id,
                'message': message,
                'random_id': get_random_id()
            }
            if keyboard:
                params['keyboard'] = keyboard.get_keyboard()
            
            self.vk.messages.send(**params)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def handle_message(self, event):
        """Handle incoming message event"""
        try:
            # Basic echo response for testing
            self.send_message(
                user_id=event.user_id,
                message=f"Received your message: {event.text}"
            )
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def run(self):
        """Start the bot's event loop"""
        logger.info("Starting VK bot...")
        try:
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    logger.debug(f"New message from user {event.user_id}: {event.text}")
                    self.handle_message(event)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise

def main():
    bot = VKBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise

if __name__ == "__main__":
    main()