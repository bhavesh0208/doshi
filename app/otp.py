import pyotp
import datetime
from dataclasses import dataclass


@dataclass
class OtpVerification:
    key: str = pyotp.random_base32()
    number_of_digits: int = 6
    token_validity_period: int = 60
    verified: bool = False

    def __post_init__(self) -> None:
        self.totp = pyotp.TOTP(
            s=self.key,
            digits=self.number_of_digits,
            interval=self.token_validity_period,
        )

    def set_token_validity_period(self, seconds=30):
        if isinstance(seconds, int) and seconds > 0:
            self.token_validity_period = seconds
        else:
            raise Exception("Seconds must be a positive integer value.")

    def generate_token(self):
        token = self.totp.now()
        return token

    def get_remaining_time(self):
        return (
            self.totp.interval
            - datetime.datetime.now().timestamp() % self.totp.interval
        )

    def verify_otp(self, otp):
        return self.totp.verify(otp)
