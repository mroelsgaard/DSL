import serial
import sys

def main(value):
    """
     value input is on/off
     turns frequency generator on/off
    """
    ser=serial.Serial('/dev/ttyACM0',9600)
    str2write='OUTP {}\n'.format(value).encode()
    #print(str2write)
    ser.write(str2write)
    ser.flush()
    ser.write(b'OUTP?\n')
    ser.flush()

    readedText = ser.readline()
    print('freq generator response: {}'.format(readedText))

    ser.close()

if __name__ == '__main__':
    value=sys.argv[1]
    print(sys.argv[0])

    main(value)
