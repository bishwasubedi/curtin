====================
Curtin Configuration
====================

Curtin exposes a number of configuration options for controlling Curtin
behavior during installation.


Configuration options
---------------------
Curtin's top level config keys are as follows:


- apt_mirrors (``apt_mirrors``)
- apt_proxy (``apt_proxy``)
- block-meta (``block``)
- curthooks (``curthooks``)
- debconf_selections (``debconf_selections``)
- disable_overlayroot (``disable_overlayroot``)
- grub (``grub``)
- http_proxy (``http_proxy``)
- install (``install``)
- kernel (``kernel``)
- kexec (``kexec``)
- multipath (``multipath``)
- network (``network``)
- pollinate (``pollinate``)
- power_state (``power_state``)
- proxy (``proxy``)
- reporting (``reporting``)
- restore_dist_interfaces: (``restore_dist_interfaces``)
- sources (``sources``)
- stages (``stages``)
- storage (``storage``)
- swap (``swap``)
- system_upgrade (``system_upgrade``)
- write_files (``write_files``)


apt_mirrors
~~~~~~~~~~~
Configure APT mirrors for ``ubuntu_archive`` and ``ubuntu_security``

**ubuntu_archive**: *<http://local.archive/ubuntu>*

**ubuntu_security**: *<http://local.archive/ubuntu>*

If the target OS includes /etc/apt/sources.list, Curtin will replace
the default values for each key set with the supplied mirror URL.

**Example**::

  apt_mirrors:
    ubuntu_archive: http://local.archive/ubuntu
    ubuntu_security: http://local.archive/ubuntu


apt_proxy
~~~~~~~~~
Curtin will configure an APT HTTP proxy in the target OS

**apt_proxy**: *<URL to APT proxy>*

**Example**::

  apt_proxy: http://squid.mirror:3267/


block-meta
~~~~~~~~~~
Configure how Curtin selects and configures disks on the target
system without providing a custom configuration (mode=simple).

**devices**: *<List of block devices for use>*

The ``devices`` parameter is a list of block device paths that Curtin may
select from with choosing where to install the OS.

**boot-partition**: *<dictionary of configuration>*

The ``boot-partition`` parameter controls how to configure the boot partition
with the following parameters:

**enabled**: *<boolean>*

Enabled will forcibly setup a partition on the target device for booting.

**format**: *<['uefi', 'gpt', 'prep', 'mbr']>*

Specify the partition format.  Some formats, like ``uefi`` and ``prep``
are restricted by platform characteristics.

**fstype**: *<filesystem type: one of ['ext3', 'ext4'], defaults to 'ext4'>*

Specify the filesystem format on the boot partition.

**label**: *<filesystem label: defaults to 'boot'>*

Specify the filesystem label on the boot partition.

**Example**::

  block-meta:
      devices:
        - /dev/sda
        - /dev/sdb
      boot-partition:
        - enabled: True
          format: gpt
          fstype: ext4
          label: my-boot-partition


curthooks
~~~~~~~~~
Configure how Curtin determines what :ref:`curthooks` to run during the installation
process.

**mode**: *<['auto', 'builtin', 'target']>*

The default mode is ``auto``.

In ``auto`` mode, curtin will execute curthooks within the image if present.
For images without curthooks inside, curtin will execute its built-in hooks.

Currently the built-in curthooks support the following OS families:

- Ubuntu
- Centos

When specifying ``builtin``, curtin will only run the curthooks present in
Curtin ignoring any curthooks that may be present in the target operating
system.

When specifying ``target``, curtin will attempt run the curthooks in the target
operating system.  If the target does NOT contain any curthooks, then the
built-in curthooks will be run instead.

Any errors during execution of curthooks (built-in or target) will fail the
installation.

**Example**::

  # ignore any target curthooks
  curthooks:
    mode: builtin

  # Only run target curthooks, fall back to built-in
  curthooks:
    mode: target


debconf_selections
~~~~~~~~~~~~~~~~~~
Curtin will update the target with debconf set-selection values.  Users will
need to be familiar with the package debconf options.  Users can probe a
packages' debconf settings by using ``debconf-get-selections``.

**selection_name**: *<debconf-set-selections input>*

``debconf-set-selections`` is in the form::

  <packagename> <packagename/option-name> <type> <value>

**Example**::

  debconf_selections:
    set1: |
      cloud-init cloud-init/datasources multiselect MAAS
      lxd lxd/bridge-name string lxdbr0
    set2: lxd lxd/setup-bridge boolean true



disable_overlayroot
~~~~~~~~~~~~~~~~~~~
Curtin disables overlayroot in the target by default.

**disable_overlayroot**: *<boolean: default True>*

**Example**::

  disable_overlayroot: False


grub
~~~~
Curtin configures grub as the target machine's boot loader.  Users
can control a few options to tailor how the system will boot after
installation.

**install_devices**: *<list of block device names to install grub>*

Specify a list of devices onto which grub will attempt to install.

**replace_linux_default**: *<boolean: default True>*

Controls whether grub-install will update the Linux Default target
value during installation.

**update_nvram**: *<boolean: default False>*

Certain platforms, like ``uefi`` and ``prep`` systems utilize
NVRAM to hold boot configuration settings which control the order in
which devices are booted.  Curtin by default will not attempt to
update the NVRAM settings to preserve the system configuration.
Users may want to force NVRAM to be updated such that the next boot
of the system will boot from the installed device.

**probe_additional_os**: *<boolean: default False>*

This setting controls grub's os-prober functionality and Curtin will
disable this feature by default to prevent grub from searching for other
operating systems and adding them to the grub menu.

When False, curtin writes "GRUB_DISABLE_OS_PROBER=true" to target system in
/etc/default/grub.d/50-curtin-settings.cfg.  If True, curtin won't modify the
grub configuration value in the target system.

**terminal**: *<['unmodified', 'console', ...]>*

Configure target system grub option GRUB_TERMINAL ``terminal`` value
which is written to /etc/default/grub.d/50-curtin-settings.cfg.  Curtin
does not attempt to validate this string, grub2 has many values that
it accepts and the list is platform dependent.  If ``terminal`` is
not provided, Curtin will set the value to 'console'.  If the ``terminal``
value is 'unmodified' then Curtin will not set any value at all and will
use Grub defaults.


**Example**::

  grub:
     install_devices:
       - /dev/sda1
     replace_linux_default: False
     update_nvram: True
     terminal: serial

**Default terminal value, GRUB_TERMINAL=console**::

  grub:
     install_devices:
       - /dev/sda1

**Don't set GRUB_TERMINAL in target**::

  grub:
     install_devices:
       - /dev/sda1
     terminal: unmodified

**Allow grub to probe for additional OSes**::

  grub:
    install_devices:
      - /dev/sda1
     probe_additional_os: True

**Avoid writting any settings to etc/default/grub.d/50-curtin-settings.cfg**::

  grub:
    install_devices:
      - /dev/sda1
     probe_additional_os: True
     terminal: unmodified


http_proxy
~~~~~~~~~~
Curtin will export ``http_proxy`` value into the installer environment.
**Deprecated**: This setting is deprecated in favor of ``proxy`` below.

**http_proxy**: *<HTTP Proxy URL>*

**Example**::

  http_proxy: http://squid.proxy:3728/



install
~~~~~~~
Configure Curtin's install options.

**log_file**: *<path to write Curtin's install.log data>*

Curtin logs install progress by default to /var/log/curtin/install.log

**error_tarfile**: *<path to write a tar of Curtin's log and configuration
data in the event of an error>*

If error_tarfile is not None and curtin encounters an error, this tarfile will
be created. It includes logs, configuration and system info to aid triage and
bug filing. When unset, error_tarfile defaults to
/var/log/curtin/curtin-logs.tar.

**post_files**: *<List of files to read from host to include in reporting data>*

Curtin by default will post the ``log_file`` value to any configured reporter.

**save_install_config**: *<Path to save merged curtin configuration file>*

Curtin will save the merged configuration data into the target OS at
the path of ``save_install_config``.  This defaults to /root/curtin-install-cfg.yaml

**save_install_logs**: *<Path to save curtin install log>*

Curtin will copy the install log to a specific path in the target
filesystem.  This defaults to /root/install.log

**target**: *<path to mount install target>*

Control where curtin mounts the target device for installing the OS.  If this
value is unset, curtin picks a suitable path under a temporary directory. If
a value is set, then curtin will utilize the ``target`` value instead.

**unmount**: *disabled*

If this key is set to the string 'disabled' then curtin will not
unmount the target filesystem when install is complete.  This
skips unmounting in all cases of install success or failure.

**Example**::

  install:
     log_file: /tmp/install.log
     error_tarfile: /var/log/curtin/curtin-error-logs.tar
     post_files:
       - /tmp/install.log
       - /var/log/syslog
     save_install_config: /root/myconf.yaml
     save_install_log: /var/log/curtin-install.log
     target: /my_mount_point
     unmount: disabled


kernel
~~~~~~
Configure how Curtin selects which kernel to install into the target image.
If ``kernel`` is not configured, Curtin will use the default mapping below
and determine which ``package`` value by looking up the current release
and current kernel version running.


**fallback-package**: *<kernel package-name to be used as fallback>*

Specify a kernel package name to be used if the default package is not
available.

**mapping**: *<Dictionary mapping Ubuntu release to HWE kernel names>*

Default mapping for Releases to package names is as follows::

 precise:
    3.2.0: 
    3.5.0: -lts-quantal
    3.8.0: -lts-raring
    3.11.0: -lts-saucy
    3.13.0: -lts-trusty
  trusty:
    3.13.0: 
    3.16.0: -lts-utopic
    3.19.0: -lts-vivid
    4.2.0: -lts-wily
    4.4.0: -lts-xenial
  xenial:
    4.3.0:
    4.4.0:
 

**package**: *<Linux kernel package name>*

Specify the exact package to install in the target OS.

**Example**::

  kernel:
    fallback-package: linux-image-generic
    package: linux-image-generic-lts-xenial
    mapping:
      - xenial:
        - 4.4.0: -my-custom-kernel    


kexec
~~~~~
Curtin can use kexec to "reboot" into the target OS.

**mode**: *<on>*

Enable rebooting with kexec.

**Example**::

  kexec: on


multipath
~~~~~~~~~
Curtin will detect and autoconfigure multipath by default to enable
boot for systems with multipath.  Curtin does not apply any advanced
configuration or tuning, rather it uses distro defaults and provides
enough configuration to enable booting.

**mode**: *<['auto', ['disabled']>*

Defaults to auto which will configure enough to enable booting on multipath
devices.  Disabled will prevent curtin from installing or configuring
multipath.

**overwrite_bindings**: *<boolean>*

If ``overwrite_bindings`` is True then Curtin will generate new bindings
file for multipath, overriding any existing binding in the target image.

**Example**::

  multipath:
      mode: auto
      overwrite_bindings: True


network
~~~~~~~
Configure networking (see Networking section for details).

**network_option_1**: *<option value>*

**Example**::

  network:
     version: 1
     config:
       - type: physical
         name: eth0
         mac_address: "c0:d6:9f:2c:e8:80"
         subnets:
           - type: dhcp4


pollinate
~~~~~~~~~
Configure pollinate user-agent

Curtin will automatically include Curtin's version in the pollinate user-agent.
If a MAAS server is being used, Curtin will query the MAAS version and include
this value as well.

**user_agent**: [*<mapping>* | *<boolean>*]

Mapping is a dictionary of key value pairs which will result in the string
'key/value' being present in the pollinate user-agent string sent to the
pollen server.

Setting the ``user_agent`` value to false will disable writting of the
user-agent string.

**Example**::

  pollinate:
     user_agent:
         curtin: 17.1-33-g92fbc491
         maas: 2.1.5+bzr5596-0ubuntu1
         machine: bob27
         app: 63.12

  pollinate:
     user_agent: false


power_state
~~~~~~~~~~~
Curtin can configure the target machine into a specific power state after
completing an installation.  Default is to do nothing.

**delay**: *<Integer seconds to delay change in state>*

Curtin will wait ``delay`` seconds before changing the power state.

**mode**: *<New power state is one of: [halt, poweroff, reboot]>*

Curtin will transition the node into one of the new states listed.

``halt`` will stop a machine, but may not cut the power to the system.
``poweroff`` will stop a machine and request it shut off the power.
``reboot`` will perform a platform reset.

**message**:  *<message string>*

The ``message`` string will be broadcast to system consoles prior to
power state change.


**Example**::

  power_state:
    mode: poweroff
    delay: 5
    message: Bye Bye


proxy
~~~~~
Curtin will put ``http_proxy``, ``https_proxy`` and ``no_proxy``
into its install environment.  This is in affect for curtin's process
and subprocesses.

**proxy**: A dictionary containing http_proxy, https_proxy, and no_proxy.

**Example**::

  proxy:
    http_proxy: http://squid.proxy:3728/
    https_proxy: http://squid.proxy:3728/
    no_proxy: localhost,127.0.0.1,10.0.2.1


reporting
~~~~~~~~~
Configure installation reporting (see Reporting section for details).

**Example**::

  reporting:
    maas:
      level: DEBUG
      type: webhook
      endpoint: http://localhost:8000/


restore_dist_interfaces
~~~~~~~~~~~~~~~~~~~~~~~
Curtin can restore a copy of /etc/network/interfaces built in to cloud images.

**restore_dist_interfaces**: *<boolean>*

If True, then Curtin will restore the interfaces file into the target.


**Example**::

  restore_dist_interfaces: True


sources
~~~~~~~
Specify the root image to install on to the target system.  The URI also
configures the method used to copy the image to the target system.

**sources**: *<List of source URIs>*

``source URI`` may be one of:

- **dd-**:  Use ``dd`` command to write image to target.
- **cp://**: Use ``rsync`` command to copy source directory to target.
- **file://**: Use ``tar`` command to extract source to target.
- **squashfs://**: Mount squashfs image and copy contents to target.
- **http[s]://**: Use ``wget | tar`` commands to extract source to target.
- **fsimage://** mount filesystem image and copy contents to target.
  Local file or url are supported. Filesystem can be any filesystem type
  mountable by the running kernel.
- **fsimage-layered://** mount layered filesystem image and copy contents to target.
  A ``fsimage-layered`` install source is a string representing one or more mountable
  images from a single local or remote directory.  The string is dot-separated where
  each value between the dots represents a particular image and the location of the
  name within the string encodes the order in which it is to be mounted.  The resulting
  list of images are downloaded (if needed) then mounted and overlayed into a single
  directory which is used as the source for installation.

**Image Name Pattern**

 [[<parent_layer>.]...]<layer name>.<file extension pattern>

Example::

 10-base.img
 minimal.img
 minimal.standard.live.squashfs
 http://example.io/standard.squashfs

**Layer Dependencies**

Layers are parts of the name seperated by dots. Any layer in the name will
be included as a dependency. The file extension pattern is used to find
related layers.

Examples:

 Base use case::

  /images
  ├── main.squashfs
  ├── main.upper.squashfs
  └── main.upper.debug.squashfs

 source='fsimage-layered://images/main.squashfs' -> images='/images/main.squashfs'
 source='fsimage-layered://images/main.upper.squashfs' -> images='/images/main.upper.squashfs, /images/main.squashfs'
 source='fsimage-layered://images/main.upper.debug.squashfs' -> images='/images/main.upper.debug.squashfs, /images/main.upper.squashfs, /images/main.squashfs'

 Multiple extensions::

  /images
  ├── main.squashfs
  ├── main.img
  ├── main.upper.squashfs
  ├── main.upper.img
  └── main.upper.debug.squashfs

 source='fsimage-layered://images/main.upper.squashfs' -> images='/images/main.upper.squashfs, /images/main.squashfs'
 source='fsimage-layered://images/main.upper.img' -> images='/images/main.upper.img, /images/main.img'

 Missing intermediary layer::

  /images
  ├── main.squashfs
  └── main.upper.debug.squashfs

If there is a missing image in the path to a leaf, an error will be raised

 source='fsimage-layered://images/main.squashfs' -> images='/images/main.squashfs'
 source='fsimage-layered://images/main.upper.debug.squashfs' -> Raised Error'

 Remote Layers::

  http://example.io/base.extended.debug.squashfs


The URI passed to ``fsimage-layered`` may be on a remote system.  Curtin
will parse the URI and then download each layer from the remote system.
This results in Curtin downloading the following URLs::

- http://example.io/base.squashfs
- http://example.io/base.extended.squashfs
- http://example.io/base.extended.debug.squashfs


**Example Cloud-image**::

  sources: 
    - https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-root.tar.gz

**Example Custom DD image**::

  sources: 
    - dd-img: https://localhost/raw_images/centos-6-3.img

**Example Copy from booted environment**::

  sources: 
    - cp:///

**Example squashfs from NFS mount**::
  sources:
    - squashfs:///media/filesystem.squashfs

**Example Copy from local tarball**::

  sources: 
    - file:///tmp/root.tar.gz


stages
~~~~~~
Curtin installation executes in stages.  At each stage, Curtin will look for
a list of commands to run at each stage by reading in from the Curtin config
*<stage_name>_commands* which is a dictionary and each key contains a list
of commands to run.  Users may override the stages value to control
what curtin stages execute.  During each stage, the commands are executed
in C Locale sort order.  Users should name keys in a NN-XXX format where NN
is a two-digit number to exercise control over execution order.

The following stages are defined in Curtin and 
run by default.

- **early**: *Preparing for Installation*

This stage runs before any actions are taken for installation.  By default
this stage does nothing.

- **partitioning**: *Select and partition disks for installation*

This stage runs ``curtin block-meta simple`` by default.

- **network**: *Probe and configure networking*

This stage runs ``curtin net-meta auto`` by default.

- **extract**: *Writing install sources to disk*

This stage runs ``curtin extract`` by default.

- **extract**: *Writing install sources to disk*

This stage runs ``curtin extract`` by default.

- **curthooks**: *Configuring installed system*

This stage runs ``curtin curthooks`` by default.

- **hooks**: *Finalizing installation*

This stage runs ``curtin hook`` by default.

- **late**: *Executing late commands*

This stage runs after Curtin has completed the installation.  By default
this stage does nothing.

**Example Custom Stages**::

  # Skip the whole install and just run `mystage`
  stages: ['early', 'late', 'mystage']
  mystage_commands:
     00-cmd: ['/usr/bin/foo']

**Example Early and Late commands**::

  early_commands:
      99-cmd:  ['echo', 'I ran last']
      00-cmd:  ['echo', 'I ran first']
  late_commands:
      50-cmd: ['curtin', 'in-target' '--', 'touch', '/etc/disable_overlayroot']
    

swap
~~~~
Curtin can configure a swapfile on the filesystem in the target system.
Size settings can be integer or string values with suffix.  Curtin
supports the following suffixes which multiply the value.

- **B**: *1*
- **K[B]**: *1 << 10*
- **M[B]**: *1 << 20*
- **G[B]**: *1 << 30*
- **T[B]**: *1 << 40*

Curtin will use a heuristic to configure the swapfile size if the ``size``
parameter is not set to a specific value.  The ``maxsize`` sets the upper
bound of the heuristic calculation.

**filename**: *<path to swap file>* 

Configure the filename of the swap file. Defaults to /swap.img

**maxsize**: *<Size string>*

Configure the max size of the swapfile, defaults to 8GB

**size**: *<Size string>*

Configure the exact size of the swapfile.  Setting ``size`` to 0 will
disable swap.

**Example**::

  swap:
    filename: swap.img
    size: None
    maxsize: 4GB


system_upgrade
~~~~~~~~~~~~~~
Control if Curtin runs `dist-upgrade` in target after install.  Defaults to
False.

**enabled**: *<boolean>*

**Example**::

  system_upgrade:
    enabled: False


write_files
~~~~~~~~~~~
Curtin supports writing out arbitrary data to a file.
``write_files`` accepts a dictionary of entries formatted as follows:

**path**: *<path and filename to save content>*

Specify the name and location of where to write the content.

**permissions**: *<Unix permission string>*

Specify the permissions mode as an integer or string of numbers.

**content**: *<data>*

Specify the content.

**Example**::

  write_files:
    f1:
      path: /file1
      content: !!binary |
        f0VMRgIBAQAAAAAAAAAAAAIAPgABAAAAwARAAAAAAABAAAAAAAAAAJAVAAAAAAA
    f2: {path: /file2, content: "foobar", permissions: '0666'}
