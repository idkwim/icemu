from .pin import Pin

class Chip:
    OUTPUT_PINS = []
    INPUT_PINS = []
    STARTING_HIGH = [] # pins that start high
    PIN_ORDER = None

    def __init__(self):
        for code in self.OUTPUT_PINS:
            pin = Pin(code, chip=self, output=True, high=(code in self.STARTING_HIGH))
            setattr(self, 'pin_{}'.format(pin.code), pin)
        for code in self.INPUT_PINS:
            pin = Pin(code, chip=self, high=(code in self.STARTING_HIGH))
            setattr(self, 'pin_{}'.format(pin.code), pin)
        self.vcc = Pin('VCC', chip=self, high=True)
        self.update()

    def __str__(self):
        inputs = ' '.join(str(self.getpin(code)) for code in self.INPUT_PINS)
        outputs = ' '.join(str(self.getpin(code)) for code in self.OUTPUT_PINS)
        return '{} I: {} O: {}'.format(self.__class__.__name__, inputs, outputs)

    def asciiart(self):
        if self.PIN_ORDER:
            pin_order = self.PIN_ORDER
        else:
            pin_order = self.INPUT_PINS + self.OUTPUT_PINS
        pins = list(self.getpins(pin_order))
        max_pin_name_len = max(len(p.code) for p in pins)
        if len(pins) % 2:
            pins.append(None)
        left_pins = pins[:len(pins) // 2]
        right_pins = reversed(pins[len(pins) // 2:])
        lines = []
        spacer = (max_pin_name_len + 1) * ' '
        lines.append(spacer + '_______' + spacer)
        for index, (left, right) in enumerate(zip(left_pins, right_pins)):
            larrow = '<' if left.output else '>'
            lpol = '+' if left.ishigh() else '-'
            sleft = left.code.rjust(max_pin_name_len) + larrow + '|' + lpol
            if right:
                rarrow = '>' if right.output else '<'
                rpol = '+' if right.ishigh() else '-'
                sright = rpol + '|' + rarrow + right.code.ljust(max_pin_name_len)
            else:
                sright = ' |     '

            if index == len(left_pins) - 1:
                spacer = '_'
            else:
                spacer = ' '
            line = sleft + 3 * spacer + sright
            lines.append(line)
        return '\n'.join(lines)

    def ispowered(self):
        return self.vcc.ishigh()

    def getpin(self, code):
        return getattr(self, 'pin_{}'.format(code.replace('~', '')))

    def getpins(self, codes):
        return (self.getpin(code) for code in codes)

    # Set multiple pins on the same chip and only update chips one all pins are updated.
    def setpins(self, low, high):
        updateself = False
        updatelist = set()
        for codes, val in [(low, False), (high, True)]:
            for pin in self.getpins(codes):
                if pin.high != val:
                    pin.high = val
                    if pin.output:
                       updatelist |= pin.propagate_to()
                    else:
                        updateself = True
        if updateself:
            self.update()
        for chip in updatelist:
            chip.update()

    def tick(self, us):
        pass

    def update(self):
        pass

    # Same as with setpins, but for wire_to()
    # Has to be called from the chip having the *input* pins
    def wirepins(self, chip, inputs, outputs):
        for icode, ocode in zip(inputs, outputs):
           ipin = self.getpin(icode)
           opin = chip.getpin(ocode)
           assert opin.output
           assert not ipin.output
           ipin.wires.add(opin)
           opin.wires.add(ipin)
        self.update()

class ActivableChip(Chip):
    ENABLE_PINS = [] # ~ means that low == enabled

    def is_enabled(self):
        for code in self.ENABLE_PINS:
            pin = self.getpin(code.replace('~', ''))
            enabled = pin.ishigh()
            if code.startswith('~'):
                enabled = not enabled
            if not enabled:
                return False
        return True

