import numpy
from vlanActor.composite import composite


class Ag:

    def __init__(self, actor=None, logger=None):

        self.actor = actor
        self.logger = logger

        self.send_image = True

        self.guide_objects = None
        self.detected_objects = None
        self.identified_objects = None

    def receiveStatusKeys(self, key):

        self.logger.info('receiveStatusKeys: {},{},{},{},{},{}'.format(
            key.actor,
            key.name,
            key.timestamp,
            key.isCurrent,
            key.isGenuine,
            [x.__class__.baseType(x) for x in key.valueList]
        ))

        if all((key.name == 'guideObjects', key.isCurrent, key.isGenuine)):
            self.guide_objects = numpy.load(key.valueList[0])
        elif all((key.name == 'detectedObjects', key.isCurrent, key.isGenuine)):
            self.detected_objects = numpy.load(key.valueList[0])
        elif all((key.name == 'identifiedObjects', key.isCurrent, key.isGenuine)):
            self.identified_objects = numpy.load(key.valueList[0])
            if self.send_image:
                filepath = self.actor.agcc.filepath
                self.actor.vlan.sendImage(filepath, composite=composite, detected_objects=self.detected_objects, identified_objects=self.identified_objects)

    def _getValues(self, key):

        valueList = self.actor.models['ag'].keyVarDict[key].valueList
        return {x.name: x.__class__.baseType(x) for x in valueList} if len(valueList) > 1 else valueList[0].__class__.baseType(valueList[0])

    @property
    def guideReady(self):

        return self._getValues('guideReady')

    @property
    def detectionState(self):

        return self._getValues('detectionState')
