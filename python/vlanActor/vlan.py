from datetime import datetime
import fitsio
from vlanActor.state import State
from PfsVlan import *


class Vlan:

    _HOST = {'vgw': '127.0.0.1', 'tws1': '127.0.0.1', 'tws2': '127.0.0.1'}
    _PROG = {'vgw': PfsVlanTargetProg.rpcVGW.value, 'tws1': PfsVlanTargetProg.rpcTWS.value, 'tws2': PfsVlanTargetProg.rpcTWS.value}
    
    def __init__(self, actor=None, logger=None):

        self.actor = actor
        self.logger = logger
        self.state = State()
        self.ncycles = {'vgw': 0, 'tws1': 0, 'tws2': 0}  # [0, interval)

    def receiveStatusKeys(self, key):

        self.logger.info('receiveStatusKeys: {},{},{},{},{},{}'.format(
            key.actor,
            key.name,
            key.timestamp,
            key.isCurrent,
            key.isGenuine,
            [x.__class__.baseType(x) for x in key.valueList]
        ))

        if all((key.name == 'filepath', key.isCurrent, key.isGenuine)):
            data, header = fitsio.read(key.valueList[0], header=True)
            data = data.astype('uint16').flatten()
            exposure_time = int(1e3 * float(header['EXPTIME']))  # ms
            data_type = 1  # Normal
            timestamp = datetime.fromisoformat(header['DATE-OBS'] + 'T' + header['UT'] + '+00:00').timestamp()
            tv_sec = int(timestamp)
            tv_usec = int(1000000 * (timestamp % 1))
            params = PfsVlanParam(exposure_time, data_type, tv_sec, tv_usec)
            for svc in ('vgw', 'tws1', 'tws2'):
                interval = self.state.get_output_interval(svc)
                if interval is None:
                    interval = 0
                ### send an image sooner if the interval is reduced, e.g., from 10 to 1
                if self.ncycles[svc] >= interval:
                    self.ncycles[svc] = 0
                if self.state.get_video_output_on(svc):
                    if self.ncycles[svc] == 0:
                        result = -1  # error
                        try:
                            result = SendPfsVlan(Vlan._HOST[svc], data, params, Vlan._PROG[svc])
                        except Exception as e:
                            self.logger.warn('{}'.format(e))
                        alarm = result != 0
                        self.state.set_if_alarm(svc, alarm)
                        self._sendStatusKey(self.actor.bcast, svc)
                self.ncycles[svc] += 1
                if self.ncycles[svc] >= interval:
                    self.ncycles[svc] = 0

    def _sendStatusKey(self, cmd, svc):

        output, interval, alarm = \
            self.state.get_video_output_on(svc), \
            self.state.get_output_interval(svc), \
            self.state.get_if_alarm(svc)
        cmd.inform('{}={},{},{}'.format(svc, int(output), interval, int(alarm)))

    def sendStatusKeys(self, cmd):

        for svc in ('vgw', 'tws1', 'tws2'):
            self._sendStatusKey(cmd, svc)
