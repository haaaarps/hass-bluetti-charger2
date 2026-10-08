"""Constants for the Bluetti Charger 2 control integration."""

DOMAIN = "bluetti_charger2"

NAME_PREFIX = "CHARGER"

NOTIFY_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"

# Settings block. Register 15600 is a word of 2-bit flags (10 = off, 01 = on):
# bits 0-1 are the charging switch, bits 2-3 the mode (standard / silent), and
# the upper pairs follow the running state.
REG_FLAGS = 15600
BLOCK_START = 15600
BLOCK_WORDS = 10

# Only words the charger itself has been seen holding are ever written.
# Both are standard mode; nothing is written while the charger is in any
# other state.
WORD_OFF = 0xAA2A
WORD_ON = 0x5529

POLL_SECONDS = 60
# Charging takes a while to ramp up or down after a switch, so the readings
# are refreshed again at these delays (seconds) after each switch action.
FOLLOW_UP_SECONDS = (10, 30)
# Blocks read each poll: live readings, then the settings block.
READ_BLOCKS = ((15530, 20), (15600, 10))
HANDSHAKE_SECONDS = 20
# The read-only Bluetti BT integration polls the same charger, and the charger
# takes one Bluetooth connection at a time, so connecting can need a few goes.
CONNECT_ATTEMPTS = 6
CONNECT_RETRY_SECONDS = 6
