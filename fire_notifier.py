import json
import logging
import os
import time
import typing
from abc import ABC, abstractmethod
from math import ceil

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

if os.environ.get("ENABLE_LOGGING", True):
    logger.addHandler(stream_handler)


class Notifier(ABC):
    @abstractmethod
    def send_message(self, message: str):
        raise NotImplementedError("Please Implement this method")


class PushoverNotifier(Notifier):
    # Docs: https://pushover.net/api
    TOKEN = os.environ.get("PUSHOVER_TOKEN")
    USER = os.environ.get("PUSHOVER_USER")
    DEVICE = os.environ.get("PUSHOVER_DEVICE", "")
    ENDPOINT = os.environ.get(
        "PUSHOVER_ENDPOINT", "https://api.pushover.net/1/messages.json"
    )

    notifier_name = "Pushover"

    def __init__(
        self,
        token: str = TOKEN,
        user: str = USER,
        device: str = DEVICE,
        endpoint: str = ENDPOINT,
    ):
        self.token = token
        self.user = user
        self.endpoint = endpoint
        self.device = device

        assert self.token, (
            "Please set Pushover Token! "
            "(Hint: Set PUSHOVER_TOKEN environment variable)"
        )
        assert self.user, (
            "Please set Pushover User! "
            "(Hint: Set PUSHOVER_USER environment variable)"
        )

        logger.debug("=" * 70)
        logger.debug("Pushover Configurations")
        logger.debug(f"Token: {self.mask_secret(self.token)}")
        logger.debug(f"User: {self.mask_secret(self.user)}")
        logger.debug(f"Device: {self.mask_secret(self.device)}")
        logger.debug(f"Endpoint: {self.endpoint}")
        logger.debug("=" * 70)

    def send_message(
        self,
        message: str,
        sound: str = "alien",
        priority: int = 2,
        retry: int = 30,
        expire: int = 3600,
        ttl: int = 60,
    ):
        url = self.endpoint
        data = {
            "token": self.token,
            "user": self.user,
            "device": self.device,
            "message": message,
            "sound": sound,
            "priority": priority,
            "retry": retry,
            "expire": expire,
            "ttl": ttl,
        }

        try:
            response = requests.post(url, data=data)
            return response
        except Exception as e:
            logger.error(f"Failed to send pushover message! {e}")
            return None

    @staticmethod
    def mask_secret(secret: str) -> str:
        secret_len = len(secret)
        mask_len = int(secret_len * 0.7)
        start_mask_len = ceil(mask_len * 0.2)
        end_mask_len = ceil(mask_len * 0.1)
        first_part_secret = secret[:start_mask_len]
        last_part_secret = secret[-end_mask_len:]
        mask = "*" * mask_len

        return f"{first_part_secret}{mask}{last_part_secret}"


class FireNotifierHelper:
    @staticmethod
    def split_and_capitalize_text(text: str) -> typing.List[str]:
        text_split = text.split(",")
        text = [term.strip().capitalize() for term in text_split]
        return text

    @staticmethod
    def capitalize_per_word(text: str) -> str:
        return " ".join([word.capitalize() for word in text.split()])

    @staticmethod
    def clean_text(text: str) -> str:
        return text.strip().replace("\n", "").replace("\t", "").replace("\r", "")


class FireNotifier:
    USER_AGENT = "https://github.com/nulldot0/fire-notifier"

    # Website: https://txtfire.net
    # Source Data URL
    TARGET_URL = "https://id.txtfire.net/qqq3"

    # Alert Types
    FIRST_ALARM = "1ST ALARM"
    SECOND_ALARM = "2ND ALARM"
    THIRD_ALARM = "3RD ALARM"
    FOURTH_ALARM = "4TH ALARM"
    FIFTH_ALARM = "5TH ALARM"
    POSSITIVE_ALARM = "POSSITIVE ALARM"
    GAS_STOVE_FIRE = "GAS STOVE FIRE"
    ELECTRICAL_FIRE = "ELECTRICAL FIRE"
    VEHICULAR_FIRE = "VEHICULAR FIRE"
    FIRE_UNDER_CONTROL = "FIRE UNDER CONTROL"
    RUBBISH_FIRE = "RUBBISH FIRE"
    CEILING_FIRE = "CEILING FIRE"
    FOR_VERIFICATION = "FOR VERIFICATION"
    VISIBLE_SMOKE = "VISIBLE SMOKE"
    FALSE_ALARM = "FALSE ALARM"
    FIRE_OUT = "FIRE OUT"
    POSITIVE_ALARM = "POSITIVE ALARM"
    NEGATIVE_ALARM = "NEGATIVE ALARM"
    POST_FIRE = "POST FIRE"
    KITCHEN_FIRE = "KITCHEN FIRE"
    MATRESS_FIRE = "MATRESS FIRE"

    # Alarm Types that are considered dangerous
    WARN_ALARMS = [
        FIRST_ALARM,
        SECOND_ALARM,
        THIRD_ALARM,
        FOURTH_ALARM,
        FIFTH_ALARM,
        POSSITIVE_ALARM,
        GAS_STOVE_FIRE,
        ELECTRICAL_FIRE,
        VEHICULAR_FIRE,
        RUBBISH_FIRE,
        CEILING_FIRE,
        VISIBLE_SMOKE,
        POSITIVE_ALARM,
        POST_FIRE,
        KITCHEN_FIRE,
        MATRESS_FIRE,
        FOR_VERIFICATION,  # Consider as dangerous
    ]

    def __init__(
        self,
        search_term: str,
        delay: int,
        json_db_filename: str = "fire_alerts.json",
        json_db_path: str = "db",
        notifier_type: str = "pushover",
        notifier: Notifier = None,
    ):
        self.search_term = search_term
        self.delay = delay
        self.json_db_filename = json_db_filename
        self.json_db_path = os.path.join(json_db_path, json_db_filename)

        if not os.path.exists(json_db_path):
            os.makedirs(json_db_path)

        if not os.path.exists(self.json_db_path):
            with open(self.json_db_path, "w") as f:
                json.dump([], f, indent=4)

        if notifier and notifier_type:
            logger.warning(
                "Notifier and Notifier Type both provided! "
                "Overriding to use Notifier!"
            )

        if notifier:
            self.notifier = notifier
        else:
            self.set_default_notifier(notifier_type)

        logger.debug("=" * 70)
        logger.debug("Configurations")
        logger.debug(f"Search Term/s: {search_term}")
        logger.debug(f"Delay: {delay} seconds")
        logger.debug(f"JSON DB Filename: {json_db_filename}")
        logger.debug(f"JSON DB Path: {self.json_db_path}")
        logger.debug(f"Notifier Type: {self.notifier.notifier_name}")
        logger.debug("=" * 70)

    def set_default_notifier(self, notifier_type: str):
        if notifier_type == "pushover":
            self.notifier = PushoverNotifier()
        else:
            raise ValueError(f"Notifier type {notifier_type} not supported!")

    def start(self):
        while True:
            time.sleep(self.delay)
            fire_alerts = self.get_fire_alerts()
            if not fire_alerts:
                logger.warning("No fire alerts found!")
                continue

            recent_fire_alert = fire_alerts[0]
            alert_type = recent_fire_alert["alert_type"]
            alert_info = recent_fire_alert["alert_info"]
            alert_time = recent_fire_alert["alert_time"]

            alert_type_clean = FireNotifierHelper.capitalize_per_word(alert_type)
            alert_info_clean = FireNotifierHelper.capitalize_per_word(alert_info)

            logger.info(
                f"Recent Fire Alert: {alert_type_clean} "
                f"from {alert_info_clean} on {alert_time}"
            )

            if not self.is_match_found_in_alert_info(alert_info):
                search_terms = FireNotifierHelper.split_and_capitalize_text(
                    self.search_term
                )
                search_terms_readable = ", ".join(search_terms)
                if len(search_terms) > 1:
                    logger.info(
                        f"Search terms `{search_terms_readable}` not found in {alert_info}!"
                    )
                    continue

                search_term = search_terms[0].capitalize()
                logger.info(f"Search term '{search_term}' not found in {alert_info}!")
                continue

            if alert_type not in self.WARN_ALARMS:
                logger.info(f"Alert type {alert_type_clean} is not dangerous!")
                continue

            if self.check_fire_alert_in_db(recent_fire_alert):
                logger.info(
                    f"Alert {alert_type_clean} "
                    f"from {alert_info_clean} on {alert_time} already sent!"
                )
                continue

            notification_message = (
                f"{alert_type_clean}\n{alert_info_clean}\n{alert_time}"
            )
            response = self.notifier.send_message(notification_message)

            if response and response.ok:
                logger.info(
                    f"Notified! {alert_type_clean} "
                    f"from {alert_info_clean} on {alert_time}"
                )
                self.add_fire_alert_to_db(recent_fire_alert)
            else:
                logger.warning(f"Failed to send notification! {response.text}")

    def get_fire_alerts(self) -> typing.List[dict]:
        try:
            response = requests.get(
                self.TARGET_URL, headers={"User-Agent": self.USER_AGENT}
            )
        except Exception as e:
            logger.warning(f"Failed to get response from {self.TARGET_URL}! {e}")
            return []

        if not response.ok:
            logger.warning(
                f"Failed to get response from {self.TARGET_URL}! {response.text}"
            )
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        fire_alerts = soup.find_all("div", class_="cardfire")

        data = []
        for fire_alert in fire_alerts:
            fire_alert_info = FireNotifierHelper.clean_text(
                fire_alert.find_all("p")[0].text
            )
            fire_alert_info = fire_alert_info.replace("->", "")
            fire_alert_parts = fire_alert_info.split(":")
            alert_info = fire_alert_parts[0].strip()

            alert_type = "UNKNOWN"
            if len(fire_alert_parts) == 2:
                alert_info = fire_alert_parts[0].split("!")[1]
                alert_type = fire_alert_parts[1]

            fire_alert_time = FireNotifierHelper.clean_text(
                fire_alert.find_all("p")[1].text
            )
            fire_alert_time = fire_alert_time.split("As of ")[1]

            alert_info = alert_info.strip()
            alert_info = alert_info.replace("FIRE ALERT!", "")
            alert_type = alert_type.strip()
            alert_time = fire_alert_time.strip()

            data.append(
                {
                    "alert_info": alert_info.upper(),
                    "alert_type": alert_type.upper(),
                    "alert_time": alert_time.upper(),
                }
            )

        return data

    def is_match_found_in_alert_info(self, alert_info: str) -> bool:
        search_terms = FireNotifierHelper.split_and_capitalize_text(self.search_term)

        for term in search_terms:
            if term.lower() in alert_info.strip().lower():
                return True

        return False

    def check_fire_alert_in_db(self, alert_data: dict) -> bool:
        with open(self.json_db_path, "r") as f:
            data = json.load(f)

        for alert in data:
            if alert["alert_time"] == alert_data["alert_time"]:
                return True

        return False

    def add_fire_alert_to_db(self, alert_data: dict) -> None:
        with open(self.json_db_path, "r") as f:
            data = json.load(f)

        data.append(alert_data)

        with open(self.json_db_path, "w") as f:
            json.dump(data, f, indent=4)


def main():
    SEARCH_TERM = os.environ.get("SEARCH_TERM", "")
    DELAY = int(os.environ.get("DELAY", 30))
    JSON_DB_FILENAME = os.environ.get("JSON_DB_FILENAME", "fire_alerts.json")
    fire_notifier = FireNotifier(
        search_term=SEARCH_TERM,
        delay=DELAY,
        json_db_filename=JSON_DB_FILENAME,
    )
    fire_notifier.start()


if __name__ == "__main__":
    main()
