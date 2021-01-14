from vlanActor.composite_simple import composite, IMAGE


class Agcc:

    def __init__(self, actor=None, logger=None):

        self.actor = actor
        self.logger = logger

        self.send_image = False
        self.image_center = (IMAGE.CENTER, ) * 6
        self.image_orientation = IMAGE.ORIENTATION.LANDSCAPE

    def receiveStatusKeys(self, key):

        self.logger.info('receiveStatusKeys: {},{},{},{},{},{}'.format(
            key.actor,
            key.name,
            key.timestamp,
            key.isCurrent,
            key.isGenuine,
            [x.__class__.baseType(x) for x in key.valueList]
        ))

        if all((key.name == 'agc_fitsfile', key.isCurrent, key.isGenuine)):
            if self.send_image:
                filepath = str(key.valueList[0])
                self.actor.vlan.sendImage(filepath, composite=composite, center=self.image_center, orientation=self.image_orientation)

    def _getValues(self, key):

        valueList = self.actor.models['agcc'].keyVarDict[key].valueList
        return {x.name: x.__class__.baseType(x) for x in valueList} if len(valueList) > 1 else valueList[0].__class__.baseType(valueList[0])

    @property
    def filepath(self):

        return self._getValues('agc_fitsfile')['filename']

    @property
    def frameId(self):

        return self._getValues('agc_frameid')

    @property
    def dataTime(self):

        return self._getValues('agc_fitsfile')['timestamp']
