#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#
#    This is stepconf, a graphical configuration editor for LinuxCNC
#    Copyright 2007 Jeff Epler <jepler@unpythonic.net>
#    stepconf 1.1 revamped by Chris Morley 2014
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#    This builds the INI file from the collected data.
#

import os
import time
import sys
import importlib
import shutil

if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf8')

class INI:
    def __init__(self,app):
        # access to:
        self.d = app.d  # collected data
        global SIG
        SIG = app._p    # private data (signals names)
        self.a = app    # The parent, stepconf

    def write_inifile(self, base):
        if self.d.axes == 2:
            maxvel = max(self.d.xmaxvel, self.d.zmaxvel)
        elif self.d.axes == 4:
            maxvel = max(self.d.xmaxvel, self.d.ymaxvel)
        else:
            maxvel = max(self.d.xmaxvel, self.d.ymaxvel, self.d.zmaxvel)
        hypotvel = (self.d.xmaxvel**2 + self.d.ymaxvel**2 + self.d.zmaxvel**2) **.5
        defvel = min(maxvel, max(.1, maxvel/10.))

        filename = os.path.join(base, self.d.machinename + ".ini")
        # make a backup copy if ini file exists
        if os.path.exists(filename):
            shutil.copy2(filename, filename.replace(".ini", "_" + str(int(time.time())) + ".ini"))
        file = open(filename, "w")
        print(_("# Generated by stepconf 1.1 at %s") % time.asctime(), file=file)
        print(_("# If you make changes to this file, they will be"), file=file)
        print(_("# overwritten when you run stepconf again"), file=file)

        print(file=file)
        print("[EMC]", file=file)
        print("MACHINE = %s" % self.d.machinename, file=file)
        print("DEBUG = 0", file=file)

        # the joints_axes conversion script named 'update_ini'
        # will try to update for joints_axes if no VERSION is set
        print("VERSION = 1.1", file=file)

        # write the qtplasmac section
        if self.d.select_qtplasmac:
            self.write_qtplasmac_section(file)

        print(file=file)
        print("[DISPLAY]", file=file)
        if self.d.select_axis:
            print("DISPLAY = axis", file=file)
        elif self.d.select_gmoccapy:
            print("DISPLAY = gmoccapy", file=file)
        elif self.d.select_qtdragon:
            print("DISPLAY = qtvcp qtdragon", file=file)
            print("PREFERENCE_FILE_PATH = WORKINGFOLDER/qtdragon.pref", file=file)
        # qtplasmac has multiple screen sizes
        elif self.d.select_qtplasmac:
            if self.d.qtplasmacscreen == 2:
                screen = "qtplasmac_9x16"
            elif self.d.qtplasmacscreen == 1:
                screen = "qtplasmac_4x3"
            else:
                screen = "qtplasmac"
            print("DISPLAY = qtvcp {}".format(screen), file=file)
        # qtplasmac has an internal editor
        if not self.d.select_qtplasmac:
            print("EDITOR = gedit", file=file)
        print("POSITION_OFFSET = RELATIVE", file=file)
        print("POSITION_FEEDBACK = ACTUAL", file=file)
        print("ARCDIVISION = 64", file=file)
        print("GRIDS = 10mm 20mm 50mm 100mm 1in 2in 5in 10in", file=file)
        print("MAX_FEED_OVERRIDE = 1.2", file=file)
        # qtplasmac doesn't use spindle override
        if not self.d.select_qtplasmac:
            print("MIN_SPINDLE_OVERRIDE = 0.5", file=file)
            print("MAX_SPINDLE_OVERRIDE = 1.2", file=file)
        print("DEFAULT_LINEAR_VELOCITY = %.2f" % defvel, file=file)
        print("MIN_LINEAR_VELOCITY = 0", file=file)
        print("MAX_LINEAR_VELOCITY = %.2f" % maxvel, file=file)
        if self.d.axes == 1:
            defvel = min(60, self.d.amaxvel/10.)
            print("DEFAULT_ANGULAR_VELOCITY = %.2f" % defvel, file=file)
            print("MIN_ANGULAR_VELOCITY = 0", file=file)
            print("MAX_ANGULAR_VELOCITY = %.2f" % self.d.amaxvel, file=file)

        print("CYCLE_TIME = 0.100", file=file)
        print("INTRO_GRAPHIC = linuxcnc.gif", file=file)
        print("INTRO_TIME = 5", file=file)
        print("PROGRAM_PREFIX = %s" % os.path.expanduser("~/linuxcnc/nc_files"), file=file)
        # qtplasmac has different increments
        if self.d.select_qtplasmac:
            if self.d.units:
                print("INCREMENTS = 10mm 1mm .1mm .01mm .001mm", file=file)
            else:
                print("INCREMENTS = 1in .1in .01in .001in .0001in", file=file)
        else:
            if self.d.units:
                print("INCREMENTS = 5mm 1mm .5mm .1mm .05mm .01mm .005mm", file=file)
            else:
                print("INCREMENTS = .1in .05in .01in .005in .001in .0005in .0001in", file=file)
        if self.d.pyvcp:
            print("PYVCP = custompanel.xml", file=file)
        if self.d.axes == 2:
            print("LATHE = 1", file=file)
        if self.d.axes == 3:
            print("FOAM = 1", file=file)
            print("GEOMETRY = XY;UZ", file=file)
            print("OPEN_FILE = ./foam.ngc", file=file)
        print(file=file)

        # self.d.axes is coded 0: X Y Z
        #                      1: X Y Z A
        #                      2: X Z
        #                      3: X Y U V
        if   self.d.axes == 0: num_joints = 3 # X Y Z
        elif self.d.axes == 1: num_joints = 4 # X Y Z A
        elif self.d.axes == 2: num_joints = 2 # X Z
        elif self.d.axes == 3: num_joints = 4 # X Y U V
        elif self.d.axes == 4: num_joints = 2 # X Y
        else:
            print("___________________unknown self.d.axes",self.d.axes)
        num_joints += len(self.d.tandemjoints)

        if   self.d.axes == 1: coords = "X Y Z A"
        elif self.d.axes == 0: coords = "X Y Z"
        elif self.d.axes == 2: coords = "X Z"
        elif self.d.axes == 3: coords = "X Y U V"
        elif self.d.axes == 4: coords = "X Y"

        for j in self.d.tandemjoints:
            if j.upper() in coords:
                coords = coords.replace(j.upper(), "{0} {0}".format(j.upper()))
        self.d.axislist = []
        for c in coords.lower().replace(" ",""):
            if c not in self.d.axislist:
                self.d.axislist.append(c)
            else:
                self.d.axislist.append("{}2".format(c))
        print("[KINS]", file=file)
        # trivial kinematics: no. of joints == no.of axes)
        # with trivkins, axes do not have to be consecutive
        print("JOINTS = %d"%num_joints, file=file)
        print("KINEMATICS = trivkins coordinates=%s"%coords.replace(" ",""), file=file)
        print(file=file)
        print("[FILTER]", file=file)
        # qtplasmac has a different filter section
        if self.d.select_qtplasmac:
            print("PROGRAM_EXTENSION = .ngc,.nc,.tap GCode File (*.ngc, *.nc, *.tap)", file=file)
            print("ngc = ./qtplasmac/qtplasmac_gcode.py", file=file)
            print("nc  = ./qtplasmac/qtplasmac_gcode.py", file=file)
            print("tap = ./qtplasmac/qtplasmac_gcode.py", file=file)
        else:
            print("PROGRAM_EXTENSION = .png,.gif,.jpg Greyscale Depth Image", file=file)
            print("PROGRAM_EXTENSION = .py Python Script", file=file)
            print("PROGRAM_EXTENSION = .nc,.tap G-Code File", file=file)
            print("png = image-to-gcode", file=file)
            print("gif = image-to-gcode", file=file)
            print("jpg = image-to-gcode", file=file)
            print("py = python", file=file)        

        print(file=file)
        print("[TASK]", file=file)
        print("TASK = milltask", file=file)
        print("CYCLE_TIME = 0.010", file=file)

        print(file=file)
        print("[RS274NGC]", file=file)
        print("PARAMETER_FILE = linuxcnc.var", file=file)
        # qtplasmac has extra rs274ngc variables
        if self.d.select_qtplasmac:
            if self.d.units:
                units = "metric"
            else:
                units = "imperial"
            print("RS274NGC_STARTUP_CODE = o<{}_startup> call".format(units), file=file)
            print("SUBROUTINE_PATH = ./:./qtplasmac:../../nc_files/subroutines", file=file)
            print("USER_M_PATH = ./:./qtplasmac", file=file)
            print("", file=file)

        base_period = self.d.ideal_period()

        print(file=file)
        print("[EMCMOT]", file=file)
        print("EMCMOT = motmod", file=file)
        print("COMM_TIMEOUT = 1.0", file=file)
        print("BASE_PERIOD = %d" % base_period, file=file)
        print("SERVO_PERIOD = 1000000", file=file)

        print(file=file)
        print("[HAL]", file=file)
        if self.d.halui or self.d.select_qtplasmac:
            print("HALUI = halui", file=file)          
        print("HALFILE = %s.hal" % self.d.machinename, file=file)
        # qtplasmac requires custom, custom_postgui and shutdown hal files
        if self.d.select_qtplasmac:
            print("HALFILE = custom.hal", file=file)
            print("POSTGUI_HALFILE = custom_postgui.hal", file=file)
            if self.d.sim_hardware:
                print("POSTGUI_HALFILE = sim_postgui.hal", file=file)
            print("SHUTDOWN = shutdown.hal", file=file)
        elif self.d.customhal:
            print("HALFILE = custom.hal", file=file)
            print("POSTGUI_HALFILE = postgui_call_list.hal", file=file)

        if self.d.halui:
           print(file=file)
           print("[HALUI]", file=file)
           print(_("# add halui MDI commands here (max 64) "), file=file)
           for mdi_command in self.d.halui_list:
               print("MDI_COMMAND = %s" % mdi_command, file=file)

        print(file=file)
        print("[TRAJ]", file=file)
        # qtplasmac requires 3 spindles
        if self.d.select_qtplasmac:
            print("SPINDLES = 3", file=file)
        # [TRAJ]AXES notused for joints_axes
        print("COORDINATES = ",coords, file=file)
        if self.d.units:
            print("LINEAR_UNITS = mm", file=file)
        else:
            print("LINEAR_UNITS = inch", file=file)
        print("ANGULAR_UNITS = degree", file=file)
        print("DEFAULT_LINEAR_VELOCITY = %.2f" % defvel, file=file)
        print("MAX_LINEAR_VELOCITY = %.2f" % maxvel, file=file)
        print(file=file)
        print("[EMCIO]", file=file)
        print("EMCIO = io", file=file)
        print("CYCLE_TIME = 0.100", file=file)
        print("TOOL_TABLE = tool.tbl", file=file)

        all_homes = "None"
        for axis in self.d.axislist:
            all_homes = all_homes and self.a.home_sig(axis)

        for axis in self.d.axislist:
            if "2" in axis:
                tandem = True
            else:
                tandem = False
            self.write_one_axis(file, self.d.axislist.index(axis), axis[0], "LINEAR", all_homes, tandem)

        file.close()
        self.d.add_md5sum(filename)

#******************
# HELPER FUNCTIONS
#******************
    def write_one_axis(self, file, num, letter, type, all_homes, tandem):
        order = "1203"
        def get(s): return self.d[letter + s]
        scale = get("scale")
        vel = min(get("maxvel"), self.ideal_maxvel(scale))
        # linuxcnc doesn't like having home right on an end of travel,
        # so extend the travel limit by up to .001in or .01mm
        minlim = get("minlim")
        maxlim = get("maxlim")
        home = get("homepos")
        if self.d.units: extend = .001
        else: extend = .01
        minlim = min(minlim, home) - extend
        maxlim = max(maxlim, home) + extend
        axis_letter = letter.upper()
        if not tandem:
            print(file=file)
            print("#*** AXIS_%s *******************************" % axis_letter, file=file)
            print("[AXIS_%s]" % axis_letter, file=file)
            # qtplasmac requires double vel & acc to use eoffsets correctly
            if self.d.select_qtplasmac:
                print("# MAX_VEL & MAX_ACC need to be twice the corresponding joint value", file=file)
                print("MAX_VELOCITY = %s" % (vel * 2), file=file)
                print("MAX_ACCELERATION = %s" % (get("maxacc") * 2), file=file)
                print("OFFSET_AV_RATIO = 0.5", file=file)
            else:
                print("MAX_VELOCITY = %s" % vel, file=file)
                print("MAX_ACCELERATION = %s" % get("maxacc"), file=file)
            print("MIN_LIMIT = %s" % minlim, file=file)
            print("MAX_LIMIT = %s" % maxlim, file=file)

        print(file=file)
        print("[JOINT_%d]" % num, file=file)
        print("TYPE = %s" % type, file=file)
        print("HOME = %s" % get("homepos"), file=file)
        print("MIN_LIMIT = %s" % minlim, file=file)
        print("MAX_LIMIT = %s" % maxlim, file=file)
        print("MAX_VELOCITY = %s" % vel, file=file)
        print("MAX_ACCELERATION = %s" % get("maxacc"), file=file)
        print("STEPGEN_MAXACCEL = %s" % (1.25 * get("maxacc")), file=file)
        print("SCALE = %s" % scale, file=file)
        if num == 3:
            print("FERROR = 1", file=file)
            print("MIN_FERROR = .25", file=file)
        elif self.d.units:
            print("FERROR = 1", file=file)
            print("MIN_FERROR = .25", file=file)
        else:
            print("FERROR = 0.05", file=file)
            print("MIN_FERROR = 0.01", file=file)

        inputs = self.a.build_input_set()
        thisaxishome = set((SIG.ALL_HOME, SIG.ALL_LIMIT_HOME, "home-" + letter, "min-home-" + letter,
                            "max-home-" + letter, "both-home-" + letter))
        # no need to set HOME_IGNORE_LIMITS when ALL_LIMIT_HOME, HAL logic will do the trick
        ignore = set(("min-home-" + letter, "max-home-" + letter,
                            "both-home-" + letter))
        homes = bool(inputs & thisaxishome)
    
        if homes:
            print("HOME_OFFSET = %f" % get("homesw"), file=file)
            print("HOME_SEARCH_VEL = %f" % get("homevel"), file=file)
            latchvel = get("homevel") / abs(get("homevel"))
            if get("latchdir"): latchvel = -latchvel
            # set latch velocity to one step every two servo periods
            # to ensure that we can capture the position to within one step
            latchvel = latchvel * 500 / get("scale")
            # don't do the latch move faster than the search move
            if abs(latchvel) > abs(get("homevel")):
                latchvel = latchvel * (abs(get("homevel"))/abs(latchvel))
            print("HOME_LATCH_VEL = %f" % latchvel, file=file)
            if inputs & ignore:
                print("HOME_IGNORE_LIMITS = YES", file=file)
            if all_homes:
                if self.d.axes == 3: # XYUV
                    if letter in('y','v'): hs = 1
                    else: hs = 0
                    if letter in self.d.tandemjoints:
                        print("HOME_SEQUENCE = -%d"% hs, file=file)
                    else:
                        print("HOME_SEQUENCE = %d"% hs, file=file)
                else:
                    if letter in self.d.tandemjoints:
                        print("HOME_SEQUENCE = -%s" % order["xyza".index(letter)], file=file)
                    else:
                        print("HOME_SEQUENCE = %s" % order["xyza".index(letter)], file=file)
        else:
            print("HOME_OFFSET = %s" % get("homepos"), file=file)
        if letter not in self.d.tandemjoints or tandem:
            print("#******************************************", file=file)

    def hz(self, axname):
        steprev = self.d[axname+"steprev"]
        microstep = self.d[axname+"microstep"]
        pulleynum = self.d[axname+"pulleynum"]
        pulleyden = self.d[axname+"pulleyden"]
        leadscrew = self.d[axname+"leadscrew"]
        maxvel = self.d[axname+"maxvel"]
        if self.d.units or axname == 'a': leadscrew = 1./leadscrew
        pps = leadscrew * steprev * microstep * (pulleynum/pulleyden) * maxvel
        return abs(pps)

    def minperiod(self, steptime=None, stepspace=None, latency=None):
        if steptime is None: steptime = self.d.steptime
        if stepspace is None: stepspace = self.d.stepspace
        if latency is None: latency = self.d.latency
        if self.a.doublestep(steptime):
            return max(latency + steptime + stepspace + 5000, 4*steptime)
        else:
            return latency + max(steptime, stepspace)

    def maxhz(self):
        return 1e9 / self.minperiod()

    def ideal_maxvel(self, scale):
        if self.a.doublestep():
            return abs(.95 * 1e9 / self.d.ideal_period() / scale)
        else:
            return abs(.95 * .5 * 1e9 / self.d.ideal_period() / scale)

    # write the qtplasmac section
    def write_qtplasmac_section(self, file):
        print(file=file)
        print("[QTPLASMAC]", file=file)
        print("# set the operating mode (default is 0)", file=file)
        print("MODE = {}".format(self.d.qtplasmacmode), file=file)
        print("# set the estop type (0=indicator, 1=hidden, 2=button)", file=file)
        print("ESTOP_TYPE = {}".format(self.d.qtplasmacestop), file=file)
        print("# laser touchoff", file=file)
        if self.d.qtplasmacxlaser or self.d.qtplasmacylaser:
            print("LASER_TOUCHOFF = X{:0.4f} Y{:0.4f}".format(self.d.qtplasmacxlaser, self.d.qtplasmacylaser), file=file)
        else:
            print("#LASER_TOUCHOFF = X0.0 Y0.0", file=file)
        print("# camera touchoff", file=file)
        if self.d.qtplasmacxcam or self.d.qtplasmacycam:
            print("CAMERA_TOUCHOFF = X{:0.4f} Y{:0.4f}".format(self.d.qtplasmacxcam, self.d.qtplasmacycam), file=file)
        else:
            print("#CAMERA_TOUCHOFF = X0.0 Y0.0 ", file=file)
        print("# powermax communications", file=file)
        if self.d.qtplasmacpmx:
            print("PM_PORT = {}".format(self.d.qtplasmacpmx), file=file)
        else:
            print("#PM_PORT = /dev/ttyUSB0", file=file)
        print("# user buttons", file=file)
        for ub in range(1, 21):
            if self.d.qtplasmac_bnames[ub-1]:
                print("BUTTON_{}_NAME = {}".format(ub ,self.d.qtplasmac_bnames[ub-1]), file=file)
                print("BUTTON_{}_CODE = {}".format(ub ,self.d.qtplasmac_bcodes[ub-1]), file=file)

    # Boiler code
    def __getitem__(self, item):
        return getattr(self, item)
    def __setitem__(self, item, value):
        return setattr(self, item, value)
