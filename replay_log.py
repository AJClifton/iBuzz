import os

class ReplayLog:

    def __init__(self, replay_log_folder="replay_logs/"):
        self.replay_log_folder = replay_log_folder
        if not os.path.isdir(replay_log_folder):
            os.mkdir(replay_log_folder)

    def add_to_log(self, log_name, text):
        """Write a string to a log with the given name.
        
        :param str log_name: Name of the log file that will be written to. Doesn't need to end in '.txt'."""
        try:
            path = self.replay_log_folder + ("" if self.replay_log_folder.endswith("/") else "/") + str(log_name) + ("" if log_name.endswith(".txt") else ".txt")
            print(path)
            with open(path, "a+") as log:
                log.write(text)
        except Exception as e:
            print(e)