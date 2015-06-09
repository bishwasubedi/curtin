#   Copyright (C) 2013 Canonical Ltd.
#
#   Author: Scott Moser <scott.moser@canonical.com>
#
#   Curtin is free software: you can redistribute it and/or modify it under
#   the terms of the GNU Affero General Public License as published by the
#   Free Software Foundation, either version 3 of the License, or (at your
#   option) any later version.
#
#   Curtin is distributed in the hope that it will be useful, but WITHOUT ANY
#   WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#   FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
#   more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with Curtin.  If not, see <http://www.gnu.org/licenses/>.

import errno
import os
import stat
import shlex
import tempfile

from curtin import util
from curtin.log import LOG


def get_dev_name_entry(devname):
    bname = devname.split('/dev/')[-1]
    return (bname, "/dev/" + bname)


def is_valid_device(devname):
    devent = get_dev_name_entry(devname)[1]
    try:
        return stat.S_ISBLK(os.stat(devent).st_mode)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
    return False


def _lsblock_pairs_to_dict(lines):
    ret = {}
    for line in lines.splitlines():
        toks = shlex.split(line)
        cur = {}
        for tok in toks:
            k, v = tok.split("=", 1)
            cur[k] = v
        cur['device_path'] = get_dev_name_entry(cur['NAME'])[1]
        ret[cur['NAME']] = cur
    return ret


def _lsblock(args=None):
    # lsblk  --help | sed -n '/Available/,/^$/p' |
    #     sed -e 1d -e '$d' -e 's,^[ ]\+,,' -e 's, .*,,' | sort
    keys = ['ALIGNMENT', 'DISC-ALN', 'DISC-GRAN', 'DISC-MAX', 'DISC-ZERO',
            'FSTYPE', 'GROUP', 'KNAME', 'LABEL', 'LOG-SEC', 'MAJ:MIN',
            'MIN-IO', 'MODE', 'MODEL', 'MOUNTPOINT', 'NAME', 'OPT-IO', 'OWNER',
            'PHY-SEC', 'RM', 'RO', 'ROTA', 'RQ-SIZE', 'SCHED', 'SIZE', 'STATE',
            'TYPE', 'UUID']
    if args is None:
        args = []
    args = [x.replace('!', '/') for x in args]

    # in order to avoid a very odd error with '-o' and all output fields above
    # we just drop one.  doesn't really matter which one.
    keys.remove('SCHED')
    basecmd = ['lsblk', '--noheadings', '--bytes', '--pairs',
               '--output=' + ','.join(keys)]
    (out, _err) = util.subp(basecmd + list(args), capture=True)
    out = out.replace('!', '/')
    return _lsblock_pairs_to_dict(out)


def get_unused_blockdev_info():
    # return a list of unused block devices. These are devices that
    # do not have anything mounted on them.

    # get a list of top level block devices, then iterate over it to get
    # devices dependent on those.  If the lsblk call for that specific
    # call has nothing 'MOUNTED", then this is an unused block device
    bdinfo = _lsblock(['--nodeps'])
    unused = {}
    for devname, data in bdinfo.items():
        cur = _lsblock([data['device_path']])
        mountpoints = [x for x in cur if cur[x].get('MOUNTPOINT')]
        if len(mountpoints) == 0:
            unused[devname] = data
    return unused


def get_devices_for_mp(mountpoint):
    # return a list of devices (full paths) used by the provided mountpoint
    bdinfo = _lsblock()
    found = set()
    for devname, data in bdinfo.items():
        if data['MOUNTPOINT'] == mountpoint:
            found.add(data['device_path'])

    if found:
        return list(found)

    # for some reason, on some systems, lsblk does not list mountpoint
    # for devices that are mounted.  This happens on /dev/vdc1 during a run
    # using tools/launch.
    with open("/proc/mounts", "r") as fp:
        for line in fp:
            try:
                (dev, mp, vfs, opts, freq, passno) = line.split(None, 5)
                if mp == mountpoint:
                    return [os.path.realpath(dev)]
            except ValueError:
                continue
    return []


def get_installable_blockdevs(include_removable=False, min_size=1024**3):
    good = []
    unused = get_unused_blockdev_info()
    for devname, data in unused.items():
        if not include_removable and data.get('RM') == "1":
            continue
        if data.get('RO') != "0" or data.get('TYPE') != "disk":
            continue
        if min_size is not None and int(data.get('SIZE', '0')) < min_size:
            continue
        good.append(devname)
    return good


def get_blockdev_for_partition(devpath):
    # convert an entry in /dev/ to parent disk and partition number
    # if devpath is a block device and not a partition, return (devpath, None)

    # input of /dev/vdb or /dev/disk/by-label/foo
    # rpath is hopefully a real-ish path in /dev (vda, sdb..)
    rpath = os.path.realpath(devpath)

    bname = os.path.basename(rpath)
    syspath = "/sys/class/block/%s" % bname

    if not os.path.exists(syspath):
        syspath2 = "/sys/class/block/cciss!%s" % bname
        if not os.path.exists(syspath2):
            raise ValueError("%s had no syspath (%s)" % (devpath, syspath))
        syspath = syspath2

    ptpath = os.path.join(syspath, "partition")
    if not os.path.exists(ptpath):
        return (rpath, None)

    ptnum = util.load_file(ptpath).rstrip()

    # for a partition, real syspath is something like:
    # /sys/devices/pci0000:00/0000:00:04.0/virtio1/block/vda/vda1
    rsyspath = os.path.realpath(syspath)
    disksyspath = os.path.dirname(rsyspath)

    diskmajmin = util.load_file(os.path.join(disksyspath, "dev")).rstrip()
    diskdevpath = os.path.realpath("/dev/block/%s" % diskmajmin)

    # diskdevpath has something like 253:0
    # and udev has put links in /dev/block/253:0 to the device name in /dev/
    return (diskdevpath, ptnum)


def get_pardevs_on_blockdevs(devs):
    # return a dict of partitions with their info that are on provided devs
    if devs is None:
        devs = []
    devs = [get_dev_name_entry(d)[1] for d in devs]
    found = _lsblock(devs)
    ret = {}
    for short in found:
        if found[short]['device_path'] not in devs:
            ret[short] = found[short]
    return ret


def stop_all_unused_multipath_devices():
    """
    Stop all unused multipath devices.
    """
    multipath = util.which('multipath')

    # Command multipath is not available only when multipath-tools package
    # is not installed. Nothing needs to be done in this case because system
    # doesn't create multipath devices without this package installed and we
    # have nothing to stop.
    if not multipath:
        return

    # Command multipath -F flushes all unused multipath device maps
    cmd = [multipath, '-F']
    try:
        util.subp(cmd)
    except util.ProcessExecutionError as e:
        LOG.warn("Failed to stop multipath devices: %s", e)


def blkid(devs=None, cache=True):
    if devs is None:
        devs = []
    cachefile = "/run/blkid/blkid.tab"
    if not cache and os.path.exists(cachefile):
        os.unlink(cachefile)

    # blkid output is <device_path>: KEY=VALUE
    # where KEY is TYPE, UUID, PARTUUID, LABEL
    out, err = util.subp(['blkid', '-o', 'full'] + devs, capture=True)
    data = {}
    for line in out.splitlines():
        curdev, curdata = line.split(":", 1)
        data[curdev] = dict(tok.split('=', 1) for tok in shlex.split(curdata))
    return data


def detect_multipath(target_mountpoint):
    """
    Detect if the operating system has been installed to a multipath device.
    """
    # The obvious way to detect multipath is to use multipath utility which is
    # provided by the multipath-tools package. Unfortunately, multipath-tools
    # package is not available in trusty ephemeral image hence we can't use it.
    # Another reasonable way to detect multipath is to look for two (or more)
    # devices with the same World Wide Name (WWN) which can be fetched using
    # scsi_id utility. This way doesn't work as well because WWNs are not
    # unique in some cases which leads to false positives which may prevent
    # system from booting (see LP:1463046 for details).
    # Taking into account all the issues mentioned above, curent implementation
    # detects multipath by looking for a device (partition) with the same UUID
    # as the target device. It relies on the fact that all alternative routes
    # to the same disk observe identical partition information including UUID.
    binfo = blkid(cache=False)
    # This function may return multiple devices by design. It is not yet
    # implemented but it should return multiple devices when installer creates
    # separate disk partitions for / and /boot. We need to do UUID-based
    # multipath detection against each of target devices.
    target_devs = get_devices_for_mp(target_mountpoint)
    LOG.debug("target_devs: %s" % target_devs)
    for devpath, data in binfo.items():
        # We need to figure out UUID of the target device first
        if devpath not in target_devs:
            continue
        # This entry contains information about one of target devices
        target_uuid = data.get('UUID')
        # UUID-based multipath detection won't work if target partition
        # doesn't have UUID assigned
        if not target_uuid:
            LOG.warn("Target partition %s doesn't have UUID assigned",
                     devpath)
            continue
        LOG.debug("%s: %s" % (devpath, data.get('UUID', "")))
        # Iterating over available devices to see if any other device
        # has the same UUID as the target device. If such device exists
        # we probably installed the system to the multipath device.
        for other_devpath, other_data in binfo.items():
            if ((other_data.get('UUID') == target_uuid) and
                (other_devpath != devpath)):
                   return True
    # No other devices have the same UUID as the target devices.
    # We probably installed the system to the non-multipath device.
    return False


def get_root_device(dev, fpath="curtin"):
    """
    Get root partition for specified device, based on presence of /curtin.
    """
    partitions = get_pardevs_on_blockdevs(dev)
    target = None
    tmp_mount = tempfile.mkdtemp()
    for i in partitions:
        dev_path = partitions[i]['device_path']
        mp = None
        try:
            util.do_mount(dev_path, tmp_mount)
            mp = tmp_mount
            curtin_dir = os.path.join(tmp_mount, fpath)
            if os.path.isdir(curtin_dir):
                target = dev_path
                break
        except:
            pass
        finally:
            if mp:
                util.do_umount(mp)

    os.rmdir(tmp_mount)

    if target is None:
        raise ValueError("Could not find root device")
    return target


# vi: ts=4 expandtab syntax=python
