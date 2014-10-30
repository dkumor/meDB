def run(pipe,logger,config):
    logger.info("Running server process")

    pipe.send({"cmd": "create","id": "hi"})
    pipe.send("EOF")
    logger.info(str(pipe.recv()))
    logger.info("runner done")
