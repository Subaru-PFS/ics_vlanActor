#!/usr/bin/env python

from twisted.internet import reactor
import opscore.protocols.keys as keys
import opscore.protocols.types as types
from vlanActor.composite_simple import IMAGE


class VlanCmd:

    def __init__(self, actor):

        self.actor = actor
        self.vocab = [
            ('ping', '', self.ping),
            ('status', '', self.status),
            ('show', '', self.show),
            ('vgw', '[(on|off)] [<interval>]', self.control),
            ('tws1', '[(on|off)] [<interval>]', self.control),
            ('tws2', '[(on|off)] [<interval>]', self.control),
            ('format', '@simple [<center>] [<orientation>]', self.format_simple),
            ('format', '@focused', self.format_focused),
        ]
        self.keys = keys.KeysDictionary(
            'vlan_vlan',
            (1, 2),
            keys.Key('interval', types.Int(), help=''),
            keys.Key('center', types.Float() * 2, help=''),
            keys.Key('orientation', types.Bool('landscape', 'portrait'), help=''),
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

    def format_simple(self, cmd):
        """Set output video format to simple."""

        center = (float(cmd.cmd.keywords['center'].values[0]), float(cmd.cmd.keywords['center'].values[1])) if 'center' in cmd.cmd.keywords else IMAGE.CENTER
        orientation = int(cmd.cmd.keywords['orientation'].values[0]) if 'orientation' in cmd.cmd.keywords else IMAGE.ORIENTATION.LANDSCAPE
        #self.actor.ag.send_image = False
        self.actor.agcc.image_center = (center, ) * 6
        self.actor.agcc.image_orientation = orientation
        #self.actor.agcc.send_image = True
        cmd.finish()

    def format_focused(self, cmd):
        """Set output video format to focused."""

        #self.actor.agcc.send_image = False
        #self.actor.ag.send_image = True
        cmd.finish()
