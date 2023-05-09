"""
Import the `consume_events` management command from the `event-bus-kafka` package in order to expose it here.

This copies the approach currently used by the Discovery IDA.
"""
# pylint: disable=unused-import
from edx_event_bus_kafka.management.commands.consume_events import Command
