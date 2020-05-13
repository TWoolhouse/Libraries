__all__ = ["Session"]

class Session:

    def __init__(self, session: str):
        self.session = session

        self.variables = {
            "SESSION": self.session,
        }
        self.cookies = Cookies()