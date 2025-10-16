import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("./logs/main.log", mode="a", encoding="utf-8", delay=False))

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(funcName)s - %(process)d - %(thread)d - %(threadName)s - %(message)s')
logger.handlers[0].setFormatter(formatter)
logger.handlers[1].setFormatter(formatter)


def main():
    logger.info("Hello from bookclub-local-poc!")


if __name__ == "__main__":
    main()
