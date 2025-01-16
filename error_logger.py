def log_error(error):
    print("error received by error logger: ", error)
    ErrorLogger.write(error)


class ErrorLogger:

    def write(error):
        with open("errors.txt", "a+") as log:
            log.write(error + "\n")
