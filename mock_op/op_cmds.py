class GetCommand:

    def __init__(self, config):
        self.sub_command = config.get_subcmd
        fields = config.fields
        self.fields = fields.split(",") if fields else []

        print("get {}".format(self.sub_command))
