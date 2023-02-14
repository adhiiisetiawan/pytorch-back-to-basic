import gzip

from diskcache import FanoutCache, Disk
from diskcache.core import BytesType, MODE_BINARY, BytesIO


class GzipDisk(Disk):
    def store(self, value, read, key=None):
        if type(value) is BytesType:
            if read:
                value = value.read()
                read = False
            
            str_io = BytesIO()
            gz_file = gzip.GzipFile(mode='wb', compresslevel=1, fileobj=str_io)

            for offset in range(0, len(value), 2**30):
                gz_file.write(value[offset:offset+2**30])
            gz_file.close()

            value = str_io.getvalue()

        return super(GzipDisk, self).store(value, read)