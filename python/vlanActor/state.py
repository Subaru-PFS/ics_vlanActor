class State(object):

    def __init__(self):

        self.vgw_video_output_on = False
        self.tws1_video_output_on = False
        self.tws2_video_output_on = False
        self.vgw_output_interval = 1
        self.tws1_output_interval = 1
        self.tws2_output_interval = 1
        self.vgw_if_alarm = False
        self.tws1_if_alarm = False
        self.tws2_if_alarm = False

    def get_video_output_on(self, svc):

        attribute = svc.lower() + '_video_output_on'
        return getattr(self, attribute)

    def set_video_output_on(self, svc, value):

        attribute = svc.lower() + '_video_output_on'
        _value = getattr(self, attribute)
        setattr(self, attribute, value)
        return _value

    def get_output_interval(self, svc):

        attribute = svc.lower() + '_output_interval'
        return getattr(self, attribute)

    def set_output_interval(self, svc, value):

        attribute = svc.lower() + '_output_interval'
        _value = getattr(self, attribute)
        setattr(self, attribute, value)
        return _value

    def get_if_alarm(self, svc):

        attribute = svc.lower() + '_if_alarm'
        return getattr(self, attribute)

    def set_if_alarm(self, svc, value):

        attribute = svc.lower() + '_if_alarm'
        _value = getattr(self, attribute)
        setattr(self, attribute, value)
        return _value
