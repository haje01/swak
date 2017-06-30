VERSION = (0, 1, 0)

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=VERSION,
    prodvers=VERSION,
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [
        StringStruct(u'FileDescription', u'Multi-Agent Service'),
        StringStruct(u'FileVersion', str(VERSION)),
        StringStruct(u'InternalName', u'swak'),
        StringStruct(u'OriginalFilename', u'swak.exe'),
        ])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
