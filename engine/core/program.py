__all__ = ["Program"]

class Program:
    """Subclassed by the User to Control start-up and shutdown"""

    def __init__(self):
        pass

    def initialize(self, app: 'Application'):
        """Run when the Application starts"""
        pass

    def terminate(self, app: 'Application'):
        """Run when the Application stops"""
        pass
