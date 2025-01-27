#
# Copyright 2017 Ettus Research, a National Instruments Company
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
"""
dboard base implementation module
"""

from usrp_mpm.mpmlog import get_logger
from usrp_mpm.mpmutils import to_native_str

class DboardManagerBase:
    """
    Base class for daughterboard controls
    """
    #########################################################################
    # Overridables
    #
    # These values are meant to be overridden by the according subclasses
    #########################################################################
    # Very important: A list of PIDs that apply to the current device. Must be
    # list, even if there's only one entry.
    pids = []
    # tuple of id and name of the first revision,
    # id and name of revisions are consecutive (2, B), (3, C), ...
    first_revision = (1, 'A')
    # See PeriphManager.mboard_sensor_callback_map for a description.
    rx_sensor_callback_map = {}
    # See PeriphManager.mboard_sensor_callback_map for a description.
    tx_sensor_callback_map = {}
    # A dictionary that maps chips or components to chip selects for SPI.
    # If this is given, a dictionary called self._spi_nodes is created which
    # maps these keys to actual spidev paths. Also throws a warning/error if
    # the SPI configuration is invalid.
    spi_chipselect = {}
    ### End of overridables #################################################

    def __init__(self, slot_idx, **kwargs):
        self.log = get_logger('dboardManager')
        self.slot_idx = slot_idx
        if 'eeprom_md' not in kwargs:
            self.log.debug("No EEPROM metadata given!")
        # In C++, we can only handle dicts if all the values are of the
        # same type. So we must convert them all to strings here:
        self.device_info = {
            key: to_native_str(kwargs.get('eeprom_md', {}).get(key, 'n/a'))
            for key in ('pid', 'serial', 'rev', 'eeprom_version')
        }
        self.log.trace("Dboard device info: `{}'".format(self.device_info))
        self._spi_nodes = self._init_spi_nodes(
            kwargs.get('spi_nodes', []),
            self.spi_chipselect
        )
        self.log.debug("spidev device node map: {}".format(self._spi_nodes))


    def _init_spi_nodes(self, spi_devices, chip_select_map):
        """
        Populates a spi_nodes dictionary.
        Note that this won't instantiate any spidev objects, it'll just map
        keys from chip_select_map to spidev nodes, and do a sanity check
        that enough nodes are available.
        """
        if len(spi_devices) < len(set(chip_select_map.values())):
            self.log.error("Expected {0} spi devices, found {1}".format(
                len(set(chip_select_map.values())), len(spi_devices),
            ))
            self.log.error("Not enough SPI devices found.")
            return {}
        return {
            spi_device: spi_devices[chip_select]
            for spi_device, chip_select in chip_select_map.items()
        }

    def init(self, args):
        """
        Run the dboard initialization. This typically happens at the beginning
        of a UHD session.

        Must be overridden. Must return True/False on success/failure.

        args -- A dictionary of arbitrary settings that can be used by the
                dboard code. Similar to device args for UHD.
        """
        raise NotImplementedError("DboardManagerBase::init() not implemented!")

    def deinit(self):
        """
        Power down the dboard. Does not have be implemented. If it does, it
        needs to be safe to call multiple times.
        """
        self.log.debug("deinit() called, but not implemented.")

    def tear_down(self):
        """
        Tear down all members that need to be specially handled before
        deconstruction.
        """

    def get_serial(self):
        """
        Return this daughterboard's serial number as a string. Will return an
        empty string if no serial can be found.
        """
        return self.device_info.get("serial", "")

    def get_revision(self):
        """
        Return this daughterboard's revision number as integer. Will return
        -1 if no revision can be found or revision is not an integer
        """
        try:
            return int(self.device_info.get('rev', '-1'))
        except ValueError:
            return -1

    def get_revision_string(self):
        """
        Converts revision number to string.
        """
        return chr(ord(self.first_revision[1])
                   + self.get_revision()
                   - self.first_revision[0])

    ##########################################################################
    # Clocking
    ##########################################################################
    def reset_clock(self, value):
        """
        Called when the motherboard is reconfiguring its clocks.
        """

    def update_ref_clock_freq(self, freq, **kwargs):
        """
        Call this function if the frequency of the reference clock changes.
        """
        self.log.warning("update_ref_clock_freq() called but not implemented")

    def get_master_clock_rate(self):
        """
        Return this device's master clock rate.

        Why is this part of the DboardManager, and not the PeriphManager?

        In most cases, the master clock rate is a property of a USRP, and is
        defined once per motherboard. However, it makes more sense to leave
        ownership of this API to the daughterboard, for a few reasons:
        - Many USRPs (E3x0 series, N310) manage the master clock rate through
          the daughterboard anyway.
        - All daughterboard classes either require or simply have access to
          the master clock rate
        - By putting this API here rather than into the PeriphManager class, we
          allow the option of having multiple master clock rates per USRP (one
          per daughterboard)
        - In UHD, the place where we need access to this value is always the
          dboard control code, rarely if ever the mpmd motherboard control code
        """
        raise NotImplementedError(
            "DboardManagerBase::get_master_clock_rate() not implemented!")

    ##########################################################################
    # Sensors
    ##########################################################################
    def get_sensors(self, direction, chan=0):
        """
        Return a list of RX daughterboard sensor names.

        direction needs to be either RX or TX.
        """
        assert direction.lower() in ('rx', 'tx')
        if direction.lower() == 'rx':
            return list(self.rx_sensor_callback_map.keys())
        # else:
        return list(self.tx_sensor_callback_map.keys())

    def get_sensor(self, direction, sensor_name, chan=0):
        """
        Return a dictionary that represents the sensor values for a given
        sensor. If the requested sensor sensor_name does not exist, throw an
        exception. direction is either RX or TX.

        See PeriphManager.get_mb_sensor() for a description of the return value
        format.
        """
        callback_map = \
            self.rx_sensor_callback_map if direction.lower() == 'rx' \
            else self.tx_sensor_callback_map
        if sensor_name not in callback_map:
            error_msg = "Was asked for non-existent sensor `{}'.".format(
                sensor_name
            )
            self.log.error(error_msg)
            raise RuntimeError(error_msg)
        return getattr(
            self, callback_map.get(sensor_name)
        )(chan)
