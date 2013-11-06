#-*- coding:utf-8 -*-
import csv, cStringIO, codecs


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect,
                                 **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder("UTF-8")()
        try:
            self.stream._write(codecs.BOM_UTF8)
        except:
            self.stream.write(codecs.BOM_UTF8)

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        try:
            self.stream._write(data)
        except:
            self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)