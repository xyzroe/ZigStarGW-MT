# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['ZigStarGW-MT.py'],
             pathex=['/Users/runner/work/ZigStarGW-MT/ZigStarGW-MT'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='ZigStarGW-MT',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None, 
          icon='ui/images/zigstar_tr_gl.icns')
app = BUNDLE(exe,
             name='ZigStarGW-MT.app',
             icon='ui/images/zigstar_tr_gl.icns',
             bundle_identifier=None,
             version='0.3.0')
