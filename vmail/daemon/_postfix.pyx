from libc.stdio cimport FILE, fopen, fclose, fread, feof, ferror, fseek, SEEK_CUR, SEEK_SET, ftell, sscanf
from libc.string cimport memset, strlen, strtok
from cpython.mem cimport PyMem_Malloc, PyMem_Free

cdef extern from "ctype.h":
    cdef int isascii (int c)
    cdef int iscntrl (int c)

cdef extern from "sys/param.h":
    cdef int NBBY

DEF REC_TYPE_SIZE  = 'C'
DEF REC_TYPE_TIME  = 'T'
DEF REC_TYPE_CTIME = 'c'
DEF REC_TYPE_FULL  = 'F'
DEF REC_TYPE_INSP  = 'I'
DEF REC_TYPE_FILT  = 'L'
DEF REC_TYPE_FROM  = 'S'
DEF REC_TYPE_DONE  = 'D'
DEF REC_TYPE_RCPT  = 'R'
DEF REC_TYPE_ORCP  = 'O'
DEF REC_TYPE_DRCP  = '/'
DEF REC_TYPE_WARN  = 'W'
DEF REC_TYPE_ATTR  = 'A'
DEF REC_TYPE_KILL  = 'K'

DEF REC_TYPE_RDR   = '>'
DEF REC_TYPE_FLGS  = 'f'
DEF REC_TYPE_DELAY = 'd'

DEF REC_TYPE_MESG  = 'M'

DEF REC_TYPE_CONT  = 'L'
DEF REC_TYPE_NORM  = 'N'
DEF REC_TYPE_DTXT  = 'w'

DEF REC_TYPE_XTRA  = 'X'

DEF REC_TYPE_RRTO  = 'r'
DEF REC_TYPE_ERTO  = 'e'
DEF REC_TYPE_PRIO  = 'P'
DEF REC_TYPE_PTR   = 'p'
DEF REC_TYPE_VERP  = 'V'

DEF REC_TYPE_DSN_RET    = '<'
DEF REC_TYPE_DSN_ENVID  = 'i'
DEF REC_TYPE_DSN_ORCPT  = 'o'
DEF REC_TYPE_DSN_NOTIFY = 'n'

DEF REC_TYPE_MILT_CONT  = 'm'

DEF REC_TYPE_END   = 'E'

DEF INIT          = 0
DEF IN_CHAR       = 1
DEF IN_CHAR_SPACE = 2

DEF IS_HEADER_NULL_TERMINATED = -1

cdef unsigned char REC_TYPES[256]
memset(REC_TYPES, 0, 256)
REC_TYPES[REC_TYPE_SIZE]  = 1 # first record, created by cleanup
REC_TYPES[REC_TYPE_TIME]  = 1 # arrival time, required
REC_TYPES[REC_TYPE_CTIME] = 1 # created time, optional
REC_TYPES[REC_TYPE_FULL]  = 1 # full name, optional
REC_TYPES[REC_TYPE_INSP]  = 1 # inspector transport
REC_TYPES[REC_TYPE_FILT]  = 1 # loop filter transport
REC_TYPES[REC_TYPE_FROM]  = 1 # sender, required
REC_TYPES[REC_TYPE_DONE]  = 1 # delivered recipient, optional
REC_TYPES[REC_TYPE_RCPT]  = 1 # todo recipient, optional
REC_TYPES[REC_TYPE_ORCP]  = 1 # original recipient, optional
REC_TYPES[REC_TYPE_DRCP]  = 1 # canceled recipient, optional
REC_TYPES[REC_TYPE_WARN]  = 1 # warning message time
REC_TYPES[REC_TYPE_ATTR]  = 1 # named attribute for extensions
REC_TYPES[REC_TYPE_KILL]  = 1 # killed record

REC_TYPES[REC_TYPE_RDR]   = 1 # redirect target
REC_TYPES[REC_TYPE_FLGS]  = 1 # cleanup processing flags
REC_TYPES[REC_TYPE_DELAY] = 1 # cleanup delay upon arrival

REC_TYPES[REC_TYPE_MESG]  = 1 # start message records

REC_TYPES[REC_TYPE_CONT]  = 1 # long data record
REC_TYPES[REC_TYPE_NORM]  = 1 # normal data record
REC_TYPES[REC_TYPE_DTXT]  = 1 # padding (was: deleted data)

REC_TYPES[REC_TYPE_XTRA]  = 1 # start extracted records

REC_TYPES[REC_TYPE_RRTO]  = 1 # return-receipt, from headers
REC_TYPES[REC_TYPE_ERTO]  = 1 # errors-to, from headers
REC_TYPES[REC_TYPE_PRIO]  = 1 # priority
REC_TYPES[REC_TYPE_PTR]   = 1 # pointer indirection
REC_TYPES[REC_TYPE_VERP]  = 1 # VERP delimiters

REC_TYPES[REC_TYPE_DSN_RET]    = 1 # DSN full/hdrs
REC_TYPES[REC_TYPE_DSN_ENVID]  = 1 # DSN full/hdrs
REC_TYPES[REC_TYPE_DSN_ORCPT]  = 1 # DSN orig rcpt address
REC_TYPES[REC_TYPE_DSN_NOTIFY] = 1 # DSN notify flags

REC_TYPES[REC_TYPE_MILT_CONT]  = 1 #

REC_TYPES[REC_TYPE_END]   = 1 # terminator, required

# State machine
cdef int STATE_ENV    = 0
cdef int STATE_HEADER = 1
cdef int STATE_BODY   = 2

class QueueError(Exception):
    pass

class InvalidRecord(QueueError):
    pass

class InvalidSizeRecord(QueueError):
    pass

class TooManyLengthBits(QueueError):
    pass

cdef inline unsigned char bit(unsigned char x):
    return 1 << x

cdef inline int is_space_tab(char c):
    return (c == b' ' or c == b'\t')

cdef inline int is_text_record(unsigned char rec_type):
    return (rec_type == REC_TYPE_CONT or rec_type == REC_TYPE_NORM)

cdef inline unsigned char _valid_record_type(unsigned char record_type):
    return REC_TYPES[record_type]

cdef inline int _read_record_length(char *record, FILE *fp) except -1:
    cdef unsigned char len_byte
    cdef int shift = 0, length = 0, ret

    # Figure out the record data length. Taken from global/record.c that
    # comes with postfix.
    while True:
        if shift >= <int>(NBBY * sizeof(int)):
            raise TooManyLengthBits('Too many length bits, record type: %c' % record)

        ret = fread(&len_byte, 1, 1, fp)
        if ret != 1:
            if feof(fp):
                raise IOError('Unexpected EOF')

            if ferror(fp):
                raise IOError('file error')

        length |= (len_byte & ~bit(NBBY - 1)) << shift
        if (len_byte & bit(NBBY - 1)) == 0:
            break
        shift += NBBY - 1

    return length

cdef inline ssize_t is_header(char *str):
    return is_header_buf(str, IS_HEADER_NULL_TERMINATED)

cdef ssize_t is_header_buf(char *string, ssize_t str_len):
    cdef unsigned char *cp
    cdef int state
    cdef int c
    cdef ssize_t length = 0

    state = INIT
    cp = <unsigned char *>string
    while True:
        c = cp[0]
        cp += 1
        if str_len != IS_HEADER_NULL_TERMINATED:
            str_len -= 1
            if str_len <= 0:
                return 0

        if c == '\t' or c == ' ':
            if state == IN_CHAR:
                state = IN_CHAR_SPACE
            if state == IN_CHAR_SPACE:
                continue
            return 0
        elif c == ':':
            return length if (state == IN_CHAR or state == IN_CHAR_SPACE) else 0
        else:
            if c == 0 or not isascii(c) or iscntrl(c):
                return 0
            if state == INIT:
                state = IN_CHAR
            if state == IN_CHAR:
                length += 1
                continue
            return 0


    return 0

def valid_record_type(record_type):
    cdef unsigned char rtype
    try:
        rtype =  record_type
    except TypeError:
        rtype = ord(record_type)

    return _valid_record_type(rtype)

cdef class QueueFile:

    cdef readonly char *filename
    cdef readonly bytes recipient
    cdef readonly list headers
    cdef readonly list records
    cdef readonly dict attributes
    cdef FILE *fp
    cdef bint envelope
    cdef bint header
    cdef bint body
    cdef int finished
    cdef int state
    cdef long data_offset
    cdef long data_size
    cdef unsigned char prev_type

    def __init__(self, char *filename, envelope=True, header=True, body=True):
        self.envelope = envelope
        self.header = header
        self.body = body
        self.data_offset = 0
        self.data_size = 0
        self.filename = filename
        self.finished = 0
        self.fp = fopen(filename, "rb")
        self.headers = []
        self.records = []
        self.attributes = {}
        self.state = STATE_ENV
        self.recipient = None

        if self.fp == NULL:
            raise IOError('Unable to open file')

    def read(self):
        """
        Read all the records contained within the queue file.
        """
        while True:
            try:
                self._py_read_record()
            except StopIteration:
                break

    cpdef close(self):
        """
        Close the file handle currently open for the queue file.
        """
        fclose(self.fp)

    cdef int _read_record(self, char *record) except -1:
        cdef int length, ret

        ret = fread(record, 1, 1, self.fp)
        if ret != 1:
            if feof(self.fp):
                return 0

            if ferror(self.fp):
                raise IOError('file error')

        record[1] = '\0'

        if _valid_record_type(record[0]) == 0:
            raise InvalidRecord('Invalid record type: %s' % record)

        return _read_record_length(record, self.fp)

    cdef int _read_record_value(self, int length, char **value) except -1:
        cdef int ret = 0

        value[0] = <char *>PyMem_Malloc(length + 1)
        if value[0] != NULL:
            ret = fread(value[0], length, 1, self.fp)
            if ret != 1:
                if feof(self.fp):
                    self.finished = 1
                if ferror(self.fp):
                    raise IOError('file reading error')
        return length

    cdef int _skip_record_value(self, int length) except -1:
        cdef int ret
        ret = fseek(self.fp, length, SEEK_CUR)
        if ret != 0:
            if ferror(self.fp):
                raise IOError('cannot seek')
        return 0

    cdef tuple _py_read_record(self):
        cdef char record[2]
        cdef char *buf = NULL, *k, *v
        cdef int length
        cdef tuple rec
        cdef bytes pyrec, pyval

        length = self._read_record(record)
        if length == 0 and self.finished:
            raise StopIteration

        if length > 0:
            self._read_record_value(length, &buf)
            buf[length] = '\0'

        if is_text_record(record[0]):
            if self.state == STATE_HEADER \
                and self.prev_type != REC_TYPE_CONT \
                and (buf == NULL or not (is_header(buf) or is_space_tab(buf[0]))):
                self.state = STATE_BODY

            if self.state == STATE_HEADER:
                if buf == NULL:
                    self.headers.append('')
                else:
                    self.headers.append(buf)

            if self.state == STATE_BODY and not self.body:
                fseek(self.fp, self.data_offset + self.data_size, SEEK_SET)

        elif record[0] == REC_TYPE_MESG:
            if self.state != STATE_ENV:
                pass
            self.state = STATE_HEADER

        elif record[0] == REC_TYPE_XTRA:
            self.state = STATE_ENV

        elif record[0] == REC_TYPE_END:
            if self.state != STATE_ENV:
                pass
            self.finished = 1

        elif record[0] == REC_TYPE_ATTR:
            k = strtok(buf, '=')
            v = strtok(NULL, '=')
            self.attributes[k] = v

        elif record[0] == REC_TYPE_RCPT:
            self.recipient = buf

        elif record[0] == REC_TYPE_SIZE:
            if sscanf(buf, "%ld %ld", &self.data_size, &self.data_offset) != 2 \
                or self.data_size <= 0 or self.data_size <= 0:
                raise InvalidSizeRecord('invalid size record: %.100s' % buf)

            if not self.envelope:
                fseek(self.fp, self.data_offset, SEEK_SET)

        self.prev_type = record[0]

        # Convert C strings to Python strings
        pyrec = record
        if buf != NULL:
            try:
                pyval = buf
            finally:
                PyMem_Free(buf)
        else:
            pyval = b''

        rec = (pyrec, pyval)
        self.records.append(rec)
        return rec

    def __del__(self):
        self.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.finished:
            raise StopIteration
        return self._py_read_record()
