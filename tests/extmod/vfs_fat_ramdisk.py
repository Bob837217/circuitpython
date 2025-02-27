try:
    import errno
    import os
except ImportError:
    print("SKIP")
    raise SystemExit

try:
    os.VfsFat
except AttributeError:
    print("SKIP")
    raise SystemExit


class RAMFS:
    SEC_SIZE = 512

    def __init__(self, blocks):
        self.data = bytearray(blocks * self.SEC_SIZE)

    def readblocks(self, n, buf):
        # print("readblocks(%s, %x(%d))" % (n, id(buf), len(buf)))
        for i in range(len(buf)):
            buf[i] = self.data[n * self.SEC_SIZE + i]
        return 0

    def writeblocks(self, n, buf):
        # print("writeblocks(%s, %x)" % (n, id(buf)))
        for i in range(len(buf)):
            self.data[n * self.SEC_SIZE + i] = buf[i]
        return 0

    def ioctl(self, op, arg):
        # print("ioctl(%d, %r)" % (op, arg))
        if op == 4:  # MP_BLOCKDEV_IOCTL_BLOCK_COUNT
            return len(self.data) // self.SEC_SIZE
        if op == 5:  # MP_BLOCKDEV_IOCTL_BLOCK_SIZE
            return self.SEC_SIZE


try:
    bdev = RAMFS(50)
except MemoryError:
    print("SKIP")
    raise SystemExit

os.VfsFat.mkfs(bdev)

print(b"FOO_FILETXT" not in bdev.data)
print(b"hello!" not in bdev.data)

vfs = os.VfsFat(bdev)
os.mount(vfs, "/ramdisk")

vfs.label = "label test"
print("label:", vfs.label)
print("statvfs:", vfs.statvfs("/ramdisk"))
print("getcwd:", vfs.getcwd())

try:
    vfs.stat("no_file.txt")
except OSError as e:
    print(e.errno == errno.ENOENT)

with vfs.open("foo_file.txt", "w") as f:
    f.write("hello!")
print(list(vfs.ilistdir()))

print("stat root:", vfs.stat("/")[:-3])  # timestamps differ across runs
print("stat file:", vfs.stat("foo_file.txt")[:-3])  # timestamps differ across runs

print(b"FOO_FILETXT" in bdev.data)
print(b"hello!" in bdev.data)

vfs.mkdir("foo_dir")
vfs.chdir("foo_dir")
print("getcwd:", vfs.getcwd())
print(list(vfs.ilistdir()))

with vfs.open("sub_file.txt", "w") as f:
    f.write("subdir file")

try:
    vfs.chdir("sub_file.txt")
except OSError as e:
    print(e.errno == errno.ENOENT)

vfs.chdir("..")
print("getcwd:", vfs.getcwd())

os.umount(vfs)

vfs = os.VfsFat(bdev)
print(list(vfs.ilistdir(b"")))

# list a non-existent directory
try:
    vfs.ilistdir(b"no_exist")
except OSError as e:
    print("ENOENT:", e.errno == errno.ENOENT)
