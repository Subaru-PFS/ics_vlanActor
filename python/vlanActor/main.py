#!/usr/bin/env python

import argparse
from actorcore.Actor import Actor
from vlanActor.ag import Ag
from vlanActor.agcc import Agcc
from vlanActor.vlan import Vlan


class VlanActor(Actor):

    # Keyword arguments for this class
    _kwargs = {
    }

    def __init__(self, name, **kwargs):

        # Consume keyword arguments for this class
        for k in VlanActor._kwargs:
            if k in kwargs:
                setattr(self, '_' + k, kwargs[k])
                del kwargs[k]
            else:
                setattr(self, '_' + k, VlanActor._kwargs[k])

        super().__init__(name, **kwargs)

        self._everConnected = False

    def reloadConfiguration(self, cmd):

        pass

    # override
    def connectionMade(self):

        if not self._everConnected:

            self._everConnected = True

            self.ag = Ag(actor=self, logger=self.logger)
            self.agcc = Agcc(actor=self, logger=self.logger)
            self.vlan = Vlan(actor=self, logger=self.logger)

            _models = ('ag', 'agcc',)
            self.addModels(_models)
            for key in ('guideObjects', 'detectedObjects', 'identifiedObjects',):
                self.models['ag'].keyVarDict[key].addCallback(self.ag.receiveStatusKeys, callNow=False)
            self.models['agcc'].keyVarDict['agc_fitsfile'].addCallback(self.agcc.receiveStatusKeys, callNow=False)

    # override
    def connectionLost(self, reason):

        pass

    # override
    def commandFailed(self, cmd):

        pass


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--configFile', default=None)
    args = parser.parse_args()

    actor = VlanActor(
        'vlan',
        productName='vlanActor',
        configFile=args.configFile
    )
    actor.run()


if __name__ == '__main__':

    main()
