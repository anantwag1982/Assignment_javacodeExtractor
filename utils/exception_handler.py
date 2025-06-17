class ExceptionHandler:
    def __init__(self, logger):
        self.logger = logger

    async def handle(self, ex: Exception, context: str = ""):
        self.logger.error(f"Exception in {context}: {str(ex)}")
        # Log full stack trace in debug mode
        self.logger.debug(f"Stack trace for {context}", exc_info=ex)