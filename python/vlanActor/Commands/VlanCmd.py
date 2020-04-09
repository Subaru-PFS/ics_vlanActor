#!/usr/bin/env python

from twisted.internet import reactor
import opscore.protocols.keys as keys
import opscore.protocols.types as types


class VlanCmd(object):

    def __init__(self, actor):

        self.actor = actor
        self.vocab = [
            ('ping', '', self.ping),
            ('status', '', self.status),
            ('show', '', self.show),
            ('vgw', '[(on|off)] [<interval>]', self.control),
            ('tws1', '[(on|off)] [<interval>]', self.control),
            ('tws2', '[(on|off)] [<interval>]', self.control),
        ]
        self.keys = keys.KeysDictionary(
            'vlan_vlan',
            (1, 1),
            keys.Key('interval', types.Int(), help=''),
        )

    def ping(self, cmd):
        """Return a product name."""

        cmd.inform('text="{}"'.format(self.actor.productName))
        cmd.finish()

    def status(self, cmd):
        """Return status keywords."""

        self.actor.sendVersionKey(cmd)
        self.actor.vlan.sendStatusKeys(cmd)
        cmd.finish()

    def show(self, cmd):
        """Show status keywords from all models."""

        for n in self.actor.models:
            try:
                d = self.actor.models[n].keyVarDict
                for k, v in d.items():
                    cmd.inform('text="{}"'.format(repr(v)))
            except Exception as e:
                cmd.warn('text="VlanCmd.show: {}: {}"'.format(n, e))
        cmd.finish()

    def control(self, cmd):
        """Set video output parameters."""

        try:
            output, interval, alarm = \
                self.actor.vlan.state.get_video_output_on(cmd.cmd.name), \
                self.actor.vlan.state.get_output_interval(cmd.cmd.name), \
                self.actor.vlan.state.get_if_alarm(cmd.cmd.name)
            if 'interval' in cmd.cmd.keywords:
                interval = int(cmd.cmd.keywords['interval'].values[0])
                if interval < 0 or 255 < interval:
                    raise RuntimeError('interval={}"'.format(interval))
                self.actor.vlan.state.set_output_interval(cmd.cmd.name, interval)
            if any(x in cmd.cmd.keywords for x in ('on', 'off')):
                output = 'on' in cmd.cmd.keywords
                self.actor.vlan.state.set_video_output_on(cmd.cmd.name, output)
            cmd.inform('{}={},{},{}'.format(cmd.cmd.name, int(output), interval, int(alarm)))
        except Exception as e:
            cmd.fail('text="VlanCmd.control: {}"'.format(e))
            return
        cmd.finish()
