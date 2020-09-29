import unittest

from servolib.lewansoul import BROADCAST_ID, LewanSoulServoBus


class MockSerial:
    def __init__(self):
        self.echo = False
        self.is_closed = False
        self.read_buffer = bytearray()
        self.write_buffer = bytearray()

    def set_read_buffer(self, *ints: int):
        self.read_buffer = bytearray(ints)

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
        self.is_closed = True


class LewanSoulServoBusTest(unittest.TestCase):
    def assertWrittenIntsEqual(self, *ints: int):
        self.assertEqual(ints, tuple(self.serial.write_buffer))

    def assertReadBufferIsEmpty(self):
        self.assertEqual(0, len(self.serial.read_buffer))

    def setUp(self) -> None:
        super().setUp()

        self.serial = MockSerial()
        self.servos = LewanSoulServoBus(self.serial)

    def test_angle_limit_read(self):
        self.serial.set_read_buffer(85, 85, 2, 7, 21, 2, 1, 4, 3, 215)
        limits = self.servos.angle_limit_read(2)
        self.assertEqual((61.92, 185.28), limits)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 2, 3, 21, 229)

    def test_angle_limit_write(self):
        self.servos.angle_limit_write(1, 90, 180)
        self.assertWrittenIntsEqual(85, 85, 1, 7, 20, 119, 1, 238, 2, 123)

    def test_angle_offset_adjust(self):
        self.servos.angle_offset_adjust(1, 10, write=False)
        self.assertWrittenIntsEqual(85, 85, 1, 4, 17, 42, 191)

    def test_angle_offset_read(self):
        self.serial.set_read_buffer(85, 85, 1, 4, 19, 0x8A, 93)
        offset = self.servos.angle_offset_read(1)
        self.assertAlmostEqual(-28.32, offset)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 1, 3, 19, 232)

    def test_angle_offset_write(self):
        self.servos.angle_offset_write(1)
        self.assertWrittenIntsEqual(85, 85, 1, 3, 18, 233)

    def test_context_manager(self):
        self.assertFalse(self.serial.is_closed)

        with LewanSoulServoBus(self.serial):
            pass

        self.assertTrue(self.serial.is_closed)

    def test_id_write(self):
        self.servos.id_write(1, 2)
        self.assertWrittenIntsEqual(85, 85, 1, 4, 13, 2, 235)

    def test_is_powered(self):
        self.serial.set_read_buffer(85, 85, 2, 4, 32, 1, 216)
        is_powered = self.servos.is_powered(2)
        self.assertTrue(is_powered)
        self.assertWrittenIntsEqual(85, 85, 2, 3, 32, 218)

    def test_led_ctrl_read(self):
        self.serial.set_read_buffer(85, 85, 10, 4, 34, 1, 206)
        ctrl = self.servos.led_ctrl_read(10)
        self.assertFalse(ctrl)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 10, 3, 34, 208)

    def test_led_ctrl_write__False(self):
        self.servos.led_ctrl_write(2, False)
        self.assertWrittenIntsEqual(85, 85, 2, 4, 33, 1, 215)

    def test_led_ctrl_write__True(self):
        self.servos.led_ctrl_write(2, True)
        self.assertWrittenIntsEqual(85, 85, 2, 4, 33, 0, 216)

    def test_led_error_read(self):
        self.serial.set_read_buffer(85, 85, 9, 4, 36, 0x02, 204)
        result = self.servos.led_error_read(9)
        self.assertEqual((False, True, False), result)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 9, 3, 36, 207)

    def test_led_error_write(self):
        self.servos.led_error_write(2, True, False, True)
        self.assertWrittenIntsEqual(85, 85, 2, 4, 35, 5, 209)

    def test_mode_read__motor(self):
        self.serial.set_read_buffer(85, 85, 2, 7, 30, 1, 0, 2, 3, 210)
        mode = self.servos.mode_read(2)
        self.assertEqual(('motor', 770), mode)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 2, 3, 30, 220)

    def test_mode_read__servo(self):
        self.serial.set_read_buffer(85, 85, 2, 7, 30, 0, 0, 0, 0, 216)
        mode = self.servos.mode_read(2)
        self.assertEqual(('servo', None), mode)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 2, 3, 30, 220)

    def test_mode_write__motor(self):
        self.servos.mode_write(BROADCAST_ID, 'motor', 10)
        self.assertWrittenIntsEqual(85, 85, 254, 7, 29, 1, 0, 10, 0, 210)

    def test_mode_write__servo(self):
        self.servos.mode_write(BROADCAST_ID, 'servo')
        self.assertWrittenIntsEqual(85, 85, 254, 7, 29, 0, 0, 0, 0, 221)

    def test_move_speed_write(self):
        self.serial.set_read_buffer(85, 85, 2, 5, 28, 10, 0, 210)

        self.servos.move_speed_write(2, 12.4, 10)

        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(
            85, 85, 2, 3, 28, 222,
            85, 85, 2, 7, 1, 51, 0, 232, 3, 215
        )

    def test_move_start(self):
        self.servos.move_start(2)
        self.assertWrittenIntsEqual(85, 85, 2, 3, 11, 239)

    def test_move_stop(self):
        self.servos.move_stop(2)
        self.assertWrittenIntsEqual(85, 85, 2, 3, 12, 238)

    def test_move_time_read(self):
        self.serial.set_read_buffer(85, 85, 3, 7, 2, 0, 2, 3, 1, 237)
        result = self.servos.move_time_read(3)
        self.assertEqual((122.88, 0.259), result)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 3, 3, 2, 247)

    def test_move_time_write(self):
        self.servos.move_time_write(1, 2, 3)
        self.assertWrittenIntsEqual(85, 85, 1, 7, 1, 8, 0, 184, 11, 43)

    def test_move_time_wait_read(self):
        self.serial.set_read_buffer(85, 85, 3, 7, 8, 0, 2, 3, 1, 231)
        result = self.servos.move_time_wait_read(3)
        self.assertEqual((122.88, 0.259), result)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 3, 3, 8, 241)

    def test_move_time_wait_write(self):
        self.servos.move_time_wait_write(1, 2, 3)
        self.assertWrittenIntsEqual(85, 85, 1, 7, 7, 8, 0, 184, 11, 37)

    def test_pos_read(self, echo: bool = False):
        self.serial.echo = self.servos.discard_echo = echo
        self.serial.set_read_buffer(85, 85, 1, 5, 28, 10, 0, 211)
        servo_pos = self.servos.pos_read(1)
        self.assertAlmostEqual(2.4, servo_pos)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 1, 3, 28, 223)

    def test_pos_read_echo(self):
        self.test_pos_read(echo=True)

    def test_set_powered__False(self):
        self.servos.set_powered(BROADCAST_ID, False)
        self.assertWrittenIntsEqual(85, 85, 254, 4, 31, 0, 222)

    def test_set_powered__True(self):
        self.servos.set_powered(BROADCAST_ID, True)
        self.assertWrittenIntsEqual(85, 85, 254, 4, 31, 1, 221)

    def test_temp_read(self):
        self.serial.set_read_buffer(85, 85, 3, 4, 26, 80, 142)
        result = self.servos.temp_read(3, units='C')
        self.assertAlmostEqual(80.0, result)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 3, 3, 26, 223)

    def test_temp_max_limit_read(self):
        deg_c = 100
        deg_f = 212
        self.serial.set_read_buffer(85, 85, 2, 4, 25, deg_c, 124)
        result = self.servos.temp_max_limit_read(2)
        self.assertAlmostEqual(deg_f, result)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 2, 3, 25, 225)

    def test_temp_max_limit_write(self):
        self.servos.temp_max_limit_write(1, 75, units='C')
        self.assertWrittenIntsEqual(85, 85, 1, 4, 24, 75, 151)

    def test_velocity_read(self):
        self.serial.set_read_buffer(
            85, 85, 1, 5, 28, 10, 0, 211,
            85, 85, 1, 5, 28, 20, 0, 201
        )
        result = self.servos.velocity_read(1)
        self.assertEqual(1, len(result))
        # Allow for a fairly large delta; the velocity_read method depends on real-time processing
        self.assertAlmostEqual(24.0, result[0], delta=0.1)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(
            85, 85, 1, 3, 28, 223,
            85, 85, 1, 3, 28, 223
        )

    def test_vin_limit_read(self):
        self.serial.set_read_buffer(85, 85, 6, 7, 23, 1, 25, 2, 40, 151)
        result = self.servos.vin_limit_read(6)
        self.assertEqual((6.401, 10.242), result)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 6, 3, 23, 223)

    def test_vin_limit_write(self):
        self.servos.vin_limit_write(1, 4.5, 12)
        self.assertWrittenIntsEqual(85, 85, 1, 7, 22, 148, 17, 224, 46, 46)

    def test_vin_read(self):
        self.serial.set_read_buffer(85, 85, 7, 5, 27, 3, 30, 183)
        result = self.servos.vin_read(7)
        self.assertAlmostEqual(7.683, result)
        self.assertReadBufferIsEmpty()
        self.assertWrittenIntsEqual(85, 85, 7, 3, 27, 218)


if __name__ == '__main__':
    unittest.main()
