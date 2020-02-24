from engine.core.application import Application

def main(application: Application):
    while application.running:
        application.update()