import unittest
from typing import Iterable, Union

from servolib.lewansoul import LewanSoulServoBus, BROADCAST_ID


class MockSerial:
    def __init__(self):
        self.echo = False
        self.read_buffer = bytearray()
        self.write_buffer = bytearray()

    def set_read_buffer(self, read_buffer: Union[bytes, Iterable[int]]):
        self.read_buffer = bytearray(read_buffer)

    # Methods used by LewanSoulServoBus:

    def read(self, byte_count: int = 1) -> bytes:
        result, self.read_buffer = self.read_buffer[:byte_count], self.read_buffer[byte_count:]
        return bytes(result)

    def write(self, data: bytes) -> int:
        self.write_buffer.extend(data)

        if self.echo:
            self.read_buffer[0:0] = data

        return len(data)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class LewanSoulServoBusTest(unittest.TestCase):
    def assertWrittenIntsEqual(self, *ints: int):
        self.assertEqual(ints, tuple(self.serial.write_buffer))

    def setUp(self) -> None:
        super().setUp()

        self.serial = MockSerial()
        self.servos = LewanSoulServoBus(self.serial)

    def test_angle_limit_write(self):
        self.servos.angle_limit_write(1, 90, 180)
        self.assertWrittenIntsEqual(85, 85, 1, 7, 20, 119, 1, 238, 2, 123)

    def test_angle_offset_write(self):
        self.servos.angle_offset_write(1)
        self.assertWrittenIntsEqual(85, 85, 1, 3, 18, 233)

    def test_id_write(self):
        self.servos.id_write(1, 2)
        self.assertWrittenIntsEqual(85, 85, 1, 4, 13, 2, 235)

    def test_mode_write__motor(self):
        self.servos.mode_write(BROADCAST_ID, 'motor', 10)
        self.assertWrittenIntsEqual(85, 85, 254, 7, 29, 1, 0, 10, 0, 210)

    def test_mode_write__servo(self):
        self.servos.mode_write(BROADCAST_ID, 'servo')
        self.assertWrittenIntsEqual(85, 85, 254, 7, 29, 0, 0, 0, 0, 221)

    def test_move_time_write(self):
        self.servos.move_time_write(1, 2, 3)
        self.assertWrittenIntsEqual(85, 85, 1, 7, 1, 8, 0, 184, 11, 43)

    def test_pos_read(self, echo: bool = False):
        servo_id = 1

        self.serial.echo = self.servos.discard_echo = echo
        self.serial.set_read_buffer([85, 85, servo_id, 5, 28, 10, 0, 211])

        servo_pos = self.servos.pos_read(servo_id)

        self.assertWrittenIntsEqual(85, 85, servo_id, 3, 28, 223)
        self.assertAlmostEqual(2.4, servo_pos)

    def test_pos_read_echo(self):
        self.test_pos_read(echo=True)

    def test_set_powered__True(self):
        self.servos.set_powered(BROADCAST_ID, True)
        self.assertWrittenIntsEqual(85, 85, 254, 4, 31, 1, 221)

    def test_set_powered__False(self):
        self.servos.set_powered(BROADCAST_ID, False)
        self.assertWrittenIntsEqual(85, 85, 254, 4, 31, 0, 222)


if __name__ == '__main__':
    unittest.main()
